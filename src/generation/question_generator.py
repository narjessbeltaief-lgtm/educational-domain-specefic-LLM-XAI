"""
Intelligent question generation engine.

Given a topic/learning objective (optionally grounded via RAG retrieval
of course material), generates pedagogically relevant assessment
questions (MCQ, true/false, open-ended) using the configured LLM (Groq).

If no LLM backend is configured (no GROQ_API_KEY), falls back to a
deterministic offline generator so the rest of the app (API, UI, grading)
keeps working for local demos/tests without network access.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import logging
import random
from pathlib import Path
from threading import Lock
from typing import List, Optional

from src.llm import groq_client
from src.rag.retriever import format_context, retrieve

logger = logging.getLogger(__name__)

VALID_TYPES = {"mcq", "true_false", "open"}
_HISTORY_LOCK = Lock()
_HISTORY_ENV_VAR = "QUESTION_HISTORY_PATH"
_DEFAULT_HISTORY_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "generated_question_history.json"

_SYSTEM_PROMPT = """You are an expert instructional designer who writes pedagogically \
sound assessment questions for students. You write clear, unambiguous questions that \
test genuine understanding rather than trivia, and you avoid giving away the answer \
in the question's wording. Keep each question short, simple, and easy to read."""

_USER_PROMPT_TEMPLATE = """Generate exactly {n_questions} assessment questions about: "{topic}"

{context_block}

Question type policy: {type_policy}

Additional teacher instructions:
{teacher_instructions}

Return a JSON array where each element has this exact shape:
- "question": string, the question text
- "type": one of "mcq", "true_false", "open"
- "choices": for "mcq" a list of 4 plausible options (exactly one correct); for \
"true_false" the list ["True", "False"]; for "open" this must be null
- "answer": the correct choice text (for mcq/true_false, must exactly match one \
string in "choices") or, for "open" questions, a concise model/reference answer
- "explanation": one sentence on why that answer is correct (used later for grading \
transparency)

Respond with ONLY the JSON array, nothing else."""

_DEFAULT_TEACHER_INSTRUCTIONS = """Use the provided course material as the primary source of truth.

Quality requirements:
- Build questions directly from core concepts, definitions, rules, and examples in the course text.
- Prefer conceptual understanding and practical reasoning over memorization.
- Keep wording clear, concise, short, and student-friendly.
- Prefer simple sentences and avoid long preambles.
- Use a professional exam tone suitable for school/university assessments.
- Avoid ambiguous pronouns and vague wording; each question must be independently understandable.

For MCQ questions:
- Write exactly one unambiguously correct answer.
- Make distractors plausible and same-domain (not random or obviously wrong).
- Avoid options like 'all of the above' or 'none of the above'.
- Keep option length balanced and avoid giving away the answer by grammar clues.

For true/false questions:
- Write concrete, checkable statements grounded in the course material.
- Avoid vague wording and trick phrasing.
- Prefer statements that test understanding of relationships, conditions, or cause/effect.

Coverage requirements:
- Distribute questions across different parts of the provided material.
- Avoid repeating the same fact in multiple questions.
- Mix difficulty levels: easy recall, moderate understanding, and applied reasoning.

Output policy:
- Do not output placeholders, meta-commentary, or notes about missing data.
- If the course text includes a specific term, rule, or example, reflect it in the question stem or options.
- Return only valid questions derived from the available course content."""


def _build_context_block(topic: str, course_text: Optional[str], use_rag: bool, course_id: Optional[str], config: dict) -> str:
    if use_rag and course_id:
        chunks = retrieve(course_id, topic, config)
        if chunks:
            return (
                "Base the questions on this course material excerpt "
                "(prefer it over general knowledge when they conflict):\n\n"
                + format_context(chunks)
            )
    if course_text:
        # No RAG index available, but caller supplied raw text directly:
        # use a bounded prefix as grounding context.
        return (
            "Base the questions on this course material excerpt:\n\n"
            + course_text[:6000]
        )
    return "No specific course material was supplied; draw on general subject-matter knowledge."


def _validate_and_clean(raw_questions: list, n_questions: int, allow_open: bool) -> List[dict]:
    valid_types = {"mcq", "true_false", "open" if allow_open else "mcq"}
    if not allow_open:
        valid_types = {"mcq", "true_false"}

    cleaned = []
    for q in raw_questions:
        if not isinstance(q, dict):
            continue
        qtype = q.get("type")
        if qtype not in valid_types:
            continue
        if not q.get("question") or q.get("answer") in (None, ""):
            continue
        if qtype in ("mcq", "true_false"):
            choices = q.get("choices")
            if not isinstance(choices, list) or len(choices) < 2 or q["answer"] not in choices:
                continue
        else:  # open
            q["choices"] = None
        cleaned.append(
            {
                "question": _shorten_question_text(str(q["question"])),
                "type": qtype,
                "choices": q.get("choices"),
                "answer": q["answer"],
                "explanation": q.get("explanation", ""),
            }
        )
    return cleaned[:n_questions]


def _generate_with_llm(
    topic: str,
    n_questions: int,
    config: dict,
    course_text: Optional[str],
    use_rag: bool,
    course_id: Optional[str],
    mcq_ratio: float,
    allow_open: bool,
    generation_prompt: Optional[str],
) -> List[dict]:
    context_block = _build_context_block(topic, course_text, use_rag, course_id, config)
    if allow_open:
        type_policy = (
            f"Approximately {int(round(mcq_ratio * 100))}% multiple-choice (type 'mcq'); "
            "split the remainder between true/false (type 'true_false') and open-answer (type 'open')."
        )
    else:
        type_policy = (
            f"Approximately {int(round(mcq_ratio * 100))}% multiple-choice (type 'mcq') and "
            "the remainder true/false (type 'true_false'). Do not generate type 'open'."
        )

    teacher_instructions = (
        generation_prompt.strip()
        if generation_prompt and generation_prompt.strip()
        else _DEFAULT_TEACHER_INSTRUCTIONS
    )

    user_prompt = _USER_PROMPT_TEMPLATE.format(
        n_questions=n_questions,
        topic=topic,
        context_block=context_block,
        type_policy=type_policy,
        teacher_instructions=teacher_instructions,
    )

    result = groq_client.chat_json(_SYSTEM_PROMPT, user_prompt, config)
    if not isinstance(result, list):
        raise groq_client.GroqClientError("Expected a JSON array of questions from the LLM.")

    questions = _validate_and_clean(result, n_questions, allow_open=allow_open)
    if not questions:
        raise groq_client.GroqClientError("LLM returned no valid questions after validation.")
    return questions


def _generate_offline(
    topic: str,
    n_questions: int,
    mcq_ratio: float,
    course_text: Optional[str] = None,
    allow_open: bool = True,
    variant_salt: str = "",
) -> List[dict]:
    """Fallback generator used when no LLM backend is configured (or the
    LLM call fails). If `course_text` has enough real content, questions
    are extracted directly from it (see `_generate_from_text`) so they're
    actually about the uploaded material rather than generic filler.
    Otherwise falls back to topic-only generic placeholders.
    """
    if course_text and len(course_text.strip()) > 40:
        questions = _generate_from_text(
            course_text,
            n_questions,
            mcq_ratio,
            allow_open=allow_open,
            variant_salt=variant_salt,
        )
        if questions:
            return questions
    return _generate_generic(
        topic,
        n_questions,
        mcq_ratio,
        allow_open=allow_open,
        variant_salt=variant_salt,
    )


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "into", "such",
    "than", "then", "which", "who", "whom", "their", "there", "here", "also",
}


def _extract_sentences(text: str) -> List[str]:
    """Split course text into usable, self-contained-looking sentences."""
    text = re.sub(r"\s+", " ", text).strip()
    raw = _SENTENCE_SPLIT_RE.split(text)
    sentences = []
    for s in raw:
        s = s.strip()
        # Keep sentences that look like real statements: reasonable length,
        # start with a capital letter, contain a verb-like word count.
        if 40 <= len(s) <= 240 and s[:1].isupper() and len(s.split()) >= 6:
            sentences.append(s)
    # De-duplicate while preserving order.
    seen = set()
    unique = []
    for s in sentences:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def _extract_key_terms(sentence: str) -> List[tuple]:
    """Heuristically extract candidate key terms (nouns/numbers/proper
    terms) from a sentence, without an NLP dependency: capitalized words
    (not sentence-initial), numbers, and long content words. Returns
    (term, type) pairs so swaps/distractors can stay within the same
    grammatical class and keep sentences readable."""
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}|\d+(?:\.\d+)?%?", sentence)
    terms: List[tuple] = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in _STOPWORDS:
            continue
        if w[0].isupper() and i != 0:
            terms.append((w, "proper"))
        elif w.isdigit() or "%" in w:
            terms.append((w, "number"))
        elif len(w) >= 7:
            terms.append((w, "noun"))
    seen = set()
    unique = []
    for t in terms:
        if t[0] not in seen:
            seen.add(t[0])
            unique.append(t)
    return unique


def _clean_phrase(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip('"“”'"'"' ,;:.')


def _shorten_question_text(text: str, max_length: int = 120) -> str:
    """Keep question stems short and easy to scan."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(?:\(?\d+\)?[\s\-.:]*)", "", text)
    text = re.sub(r"^(?:Question\s+\d+[\s\-.:]*)", "", text, flags=re.I)
    text = re.sub(r"^(According to (the )?(course material|text|lesson),\s*)", "", text, flags=re.I)
    text = re.sub(r"^(In the course material,\s*)", "", text, flags=re.I)
    if len(text) <= max_length:
        return text
    cut = text.rfind(" ", 0, max_length - 1)
    if cut <= 0:
        cut = max_length - 1
    return text[:cut].rstrip(" ,;:") + "…"


def _normalize_question_stem(question: str) -> str:
    question = _shorten_question_text(question, max_length=220)
    question = re.sub(r"\s+", " ", question).strip().lower()
    question = re.sub(r"[\"'`]+", "", question)
    return question.strip(" ?!.,;:")


def _history_path() -> Path:
    override = os.environ.get(_HISTORY_ENV_VAR, "").strip()
    return Path(override).expanduser() if override else _DEFAULT_HISTORY_PATH


def _load_question_history() -> dict:
    path = _history_path()
    if not path.exists():
        return {"courses": {}}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {"courses": {}}
        data.setdefault("courses", {})
        return data
    except Exception:
        return {"courses": {}}


def _save_question_history(history: dict) -> None:
    path = _history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(history, handle, indent=2, ensure_ascii=True)
    tmp_path.replace(path)


def _course_history_key(topic: str, course_text: Optional[str], course_id: Optional[str]) -> str:
    if course_text and course_text.strip():
        basis = f"{topic}\n{course_text.strip()}"
    elif course_id:
        basis = f"{topic}\n{course_id}"
    else:
        basis = topic
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()


def _unique_new_questions(questions: List[dict], seen_questions: Optional[set[str]] = None) -> List[dict]:
    unique_questions: List[dict] = []
    batch_seen: set[str] = set()
    for question in questions:
        stem = _normalize_question_stem(str(question.get("question", "")))
        if not stem or stem in batch_seen or (seen_questions is not None and stem in seen_questions):
            continue
        batch_seen.add(stem)
        unique_questions.append(question)
    return unique_questions


def _extract_answer_and_subject(sentence: str) -> tuple[str, str, str]:
    """Derive a direct question stem hint and answer phrase from a sentence.

    Returns:
        (question_type, subject_hint, answer_phrase)

    question_type is one of: "uses", "called", "describes".
    """
    sentence_clean = _clean_phrase(sentence)
    sentence_l = sentence_clean.lower()

    pattern_map = [
        (
            "uses",
            [
                r"\b(?:use|uses|used|using|employs|employ|utilise|utilizes|utilise|utilisé(?:e)?(?:s)?|utilisé(?:e)?(?:es)?(?: pour)?)\b",
            ],
        ),
        (
            "called",
            [
                r"\b(?:is called|are called|called|est appelé(?:e)?(?:s)?|s'appelle|sont appelés?)\b",
            ],
        ),
        (
            "describes",
            [
                r"\b(?:is|are|means|refers to|describes|describe|explains|explique|signifie|désigne)\b",
            ],
        ),
    ]

    for question_type, patterns in pattern_map:
        for pattern in patterns:
            match = re.search(pattern, sentence_l)
            if not match:
                continue
            start = match.start()
            end = match.end()
            subject_hint = _clean_phrase(sentence_clean[:start])
            answer_phrase = _clean_phrase(sentence_clean[end:])
            if subject_hint and answer_phrase:
                return question_type, subject_hint, answer_phrase

    words = sentence_clean.split()
    subject_hint = " ".join(words[: min(8, len(words))])
    answer_phrase = sentence_clean
    return "describes", _clean_phrase(subject_hint), _clean_phrase(answer_phrase)


def _build_choice_pool(answer_phrase: str, fallback_pool: List[str]) -> List[str]:
    choices = []
    seen = set()

    def add_choice(choice: str) -> None:
        candidate = _clean_phrase(choice)
        if not candidate:
            return
        key = candidate.lower()
        if key in seen:
            return
        seen.add(key)
        choices.append(candidate)

    add_choice(answer_phrase)
    for item in fallback_pool:
        add_choice(item)
        if len(choices) >= 4:
            break

    generic_distractors = [
        "manual procedure",
        "rule-based method",
        "unrelated concept",
        "random choice",
        "traditional approach",
        "general principle",
    ]
    for item in generic_distractors:
        if len(choices) >= 4:
            break
        add_choice(item)

    while len(choices) < 4:
        add_choice(f"alternative option {len(choices) + 1}")

    random.shuffle(choices)
    return choices


def _generate_from_text(
    course_text: str,
    n_questions: int,
    mcq_ratio: float,
    allow_open: bool = True,
    variant_salt: str = "",
) -> List[dict]:
    """Extraction-based generator: builds real MCQ/true-false/open questions
    directly from sentences and key terms found in the supplied course text.
    Used as the offline fallback so generated questions are actually about
    the uploaded material even without an LLM backend configured.
    """
    sentences = _extract_sentences(course_text)
    if len(sentences) < 2:
        return []

    random.seed(f"{course_text[:500]}|{variant_salt}")  # deterministic per-variant, not per-run

    # Pools drawn from across the whole document, used as distractors and
    # as fallback choices for direct comprehension questions.
    all_terms_by_type: dict = {"proper": [], "number": [], "noun": []}
    sentence_terms: List[List[tuple]] = []
    answer_phrases: List[str] = []
    for s in sentences:
        terms = _extract_key_terms(s)
        sentence_terms.append(terms)
        for term, ttype in terms:
            if term not in all_terms_by_type[ttype]:
                all_terms_by_type[ttype].append(term)
        _, _, answer_phrase = _extract_answer_and_subject(s)
        if answer_phrase and answer_phrase not in answer_phrases:
            answer_phrases.append(answer_phrase)

    shuffled_idx = list(range(len(sentences)))
    random.shuffle(shuffled_idx)

    def _distractor_pool(term: str, ttype: str) -> List[str]:
        return [t for t in all_terms_by_type[ttype] if t.lower() != term.lower()]

    def make_mcq(idx: int) -> Optional[dict]:
        sentence = sentences[idx]
        terms = sentence_terms[idx]
        question_type, subject_hint, answer_phrase = _extract_answer_and_subject(sentence)
        fallback_pool = [p for p in answer_phrases if p.lower() != answer_phrase.lower()]

        if question_type == "uses":
            question_text = (
                f"What is used for {subject_hint}?" if subject_hint else "What method is described?"
            )
        elif question_type == "called":
            question_text = (
                f"What is {subject_hint} called?" if subject_hint else "What is the concept called?"
            )
        else:
            question_text = (
                f"What does the text say about {subject_hint}?" if subject_hint else "What is the main idea?"
            )

        choices = _build_choice_pool(answer_phrase, fallback_pool)
        if len(choices) < 4:
            return None
        return {
            "question": question_text,
            "type": "mcq",
            "choices": choices,
            "answer": answer_phrase,
            "explanation": f'The course material states: "{sentence}"',
        }

    def make_true_false(idx: int) -> Optional[dict]:
        sentence = sentences[idx]
        question_type, subject_hint, answer_phrase = _extract_answer_and_subject(sentence)
        make_false = random.random() < 0.5
        if make_false:
            if question_type == "uses":
                statement = f"{subject_hint} uses {random.choice([p for p in answer_phrases if p.lower() != answer_phrase.lower()] or ['an unrelated method'])}."
            elif question_type == "called":
                statement = f"{subject_hint} is called {random.choice([p for p in answer_phrases if p.lower() != answer_phrase.lower()] or ['something else'])}."
            else:
                statement = f"The course material says that {subject_hint} means {random.choice([p for p in answer_phrases if p.lower() != answer_phrase.lower()] or ['an unrelated idea'])}."
            answer = "False"
        else:
            statement = sentence
            answer = "True"
        return {
            "question": f"True or False: {statement}",
            "type": "true_false",
            "choices": ["True", "False"],
            "answer": answer,
            "explanation": f'The course material states: "{sentence}"',
        }

    def make_open(idx: int) -> dict:
        sentence = sentences[idx]
        return {
            "question": _shorten_question_text(f"What is the main idea of this sentence? {sentence}"),
            "type": "open",
            "choices": None,
            "answer": sentence,
            "explanation": "",
        }

    questions: List[dict] = []
    idx_pool = list(shuffled_idx)
    attempts = 0
    while len(questions) < n_questions and attempts < len(idx_pool) * 3:
        idx = idx_pool[attempts % len(idx_pool)]
        attempts += 1
        r = random.random()
        q = None
        if r < mcq_ratio:
            q = make_mcq(idx)
        elif random.random() < 0.6 or not allow_open:
            q = make_true_false(idx)
        else:
            q = make_open(idx)
        if q is not None:
            questions.append(q)

    return questions


def _generate_generic(
    topic: str,
    n_questions: int,
    mcq_ratio: float,
    allow_open: bool = True,
    variant_salt: str = "",
) -> List[dict]:
    """Last-resort generator used when no usable course text is available.

    This path still aims to produce classroom-like questions by using
    domain-aware templates inferred from the topic string.
    """
    random.seed(f"{topic}|{variant_salt}")
    questions: List[dict] = []
    topic_l = topic.lower()

    grammar_keywords = {"english", "grammar", "verb", "verbs", "tense", "language"}
    math_keywords = {"math", "algebra", "calculus", "geometry", "statistics"}
    programming_keywords = {"python", "java", "programming", "code", "algorithm", "data structure"}

    def in_domain(keywords: set[str]) -> bool:
        return any(k in topic_l for k in keywords)

    # Domain-specific pools: used to produce non-placeholder, classroom-ready
    # items even when detailed course text is not provided.
    english_irregular = [
        ("go", "gone"), ("write", "written"), ("eat", "eaten"), ("see", "seen"),
        ("take", "taken"), ("speak", "spoken"), ("break", "broken"), ("choose", "chosen"),
    ]

    def english_mcq(i: int) -> dict:
        verb, participle = random.choice(english_irregular)
        distractors = [p for v, p in english_irregular if p != participle]
        choices = random.sample(distractors, 3) + [participle]
        random.shuffle(choices)
        return {
            "question": f"What is the past participle of the verb '{verb}'?",
            "type": "mcq",
            "choices": choices,
            "answer": participle,
            "explanation": f"The past participle form of '{verb}' is '{participle}'.",
        }

    def english_true_false(i: int) -> dict:
        verb, participle = random.choice(english_irregular)
        make_false = random.random() < 0.5
        if make_false:
            wrong = random.choice([p for _, p in english_irregular if p != participle])
            statement = f"The past participle of '{verb}' is '{wrong}'."
            answer = "False"
        else:
            statement = f"The past participle of '{verb}' is '{participle}'."
            answer = "True"
        return {
            "question": f"True or False: {statement}",
            "type": "true_false",
            "choices": ["True", "False"],
            "answer": answer,
            "explanation": f"Correct form: '{verb}' -> '{participle}'.",
        }

    def math_mcq(i: int) -> dict:
        bank = [
            ("2x + 3 = 11", "x = 4", ["x = 3", "x = 5", "x = 14"]),
            ("5x = 20", "x = 4", ["x = 5", "x = 15", "x = 20"]),
            ("x^2 = 49", "x = 7 or x = -7", ["x = 7 only", "x = -7 only", "x = 49"]),
        ]
        expr, correct, wrong = random.choice(bank)
        choices = wrong + [correct]
        random.shuffle(choices)
        return {
            "question": f"Solve: {expr}",
            "type": "mcq",
            "choices": choices,
            "answer": correct,
            "explanation": "Apply inverse operations carefully and check the solution.",
        }

    def math_true_false(i: int) -> dict:
        statements = [
            ("The graph of y = 2x + 1 is a straight line.", "True"),
            ("A triangle can have two right angles.", "False"),
            ("The mean is always one of the values in the data set.", "False"),
        ]
        st, ans = random.choice(statements)
        return {
            "question": f"True or False: {st}",
            "type": "true_false",
            "choices": ["True", "False"],
            "answer": ans,
            "explanation": "Use the relevant rule/definition to verify the statement.",
        }

    def programming_mcq(i: int) -> dict:
        bank = [
            ("Which data structure follows FIFO order?", "Queue", ["Stack", "Tree", "Graph"]),
            ("What is the time complexity of binary search on a sorted array?", "O(log n)", ["O(n)", "O(n log n)", "O(1)"]),
            ("Which statement best describes a Python list?", "It is mutable and ordered.", ["It is immutable.", "It stores only integers.", "It cannot contain duplicates."]),
        ]
        q, correct, wrong = random.choice(bank)
        choices = wrong + [correct]
        random.shuffle(choices)
        return {
            "question": q,
            "type": "mcq",
            "choices": choices,
            "answer": correct,
            "explanation": "Match the concept to its standard definition/behavior.",
        }

    def programming_true_false(i: int) -> dict:
        statements = [
            ("A stack follows Last-In First-Out (LIFO) order.", "True"),
            ("Hash table lookup is always O(n).", "False"),
            ("A recursive function must have a base case.", "True"),
        ]
        st, ans = random.choice(statements)
        return {
            "question": f"True or False: {st}",
            "type": "true_false",
            "choices": ["True", "False"],
            "answer": ans,
            "explanation": "Check the core property of the concept in the statement.",
        }

    def make_mcq(i: int) -> dict:
        if in_domain(grammar_keywords):
            return english_mcq(i)
        if in_domain(math_keywords):
            return math_mcq(i)
        if in_domain(programming_keywords):
            return programming_mcq(i)

        correct = f"Accurate definition of a key idea in {topic}"
        distractors = [
            f"Partially correct statement missing an essential condition in {topic}",
            f"Common misconception about {topic}",
            f"Overly broad statement that does not specifically define {topic}",
        ]
        choices = distractors + [correct]
        random.shuffle(choices)
        return {
            "question": f"Which option best matches {topic}?",
            "type": "mcq",
            "choices": choices,
            "answer": correct,
            "explanation": "The correct option states the concept precisely and without contradiction.",
        }

    def make_true_false(i: int) -> dict:
        if in_domain(grammar_keywords):
            return english_true_false(i)
        if in_domain(math_keywords):
            return math_true_false(i)
        if in_domain(programming_keywords):
            return programming_true_false(i)

        ans = "True" if random.random() > 0.5 else "False"
        statement = (
            f"Mastery of {topic} depends on understanding definitions, applying rules, and checking edge cases."
            if ans == "True"
            else f"In {topic}, memorizing terms alone is always sufficient for solving all problems."
        )
        return {
            "question": f"True or False: {statement}",
            "type": "true_false",
            "choices": ["True", "False"],
            "answer": ans,
            "explanation": "Evaluate whether the statement aligns with sound practice in the subject.",
        }

    def make_open(i: int) -> dict:
        return {
            "question": f"Explain the main idea of {topic}.",
            "type": "open",
            "choices": None,
            "answer": f"A concise explanation of the main ideas in {topic}.",
            "explanation": "",
        }

    for i in range(n_questions):
        r = random.random()
        if r < mcq_ratio:
            q = make_mcq(i)
        elif random.random() < 0.7 or not allow_open:
            q = make_true_false(i)
        else:
            q = make_open(i)
        questions.append(q)
    return questions


def generate_questions(
    topic: str,
    n_questions: int,
    config: dict,
    course_text: Optional[str] = None,
    use_rag: bool = False,
    course_id: Optional[str] = None,
    mcq_ratio: float = 0.5,
    allow_open: bool = True,
    generation_prompt: Optional[str] = None,
) -> List[dict]:
    """Generate pedagogically relevant questions for a given topic.

    Tries the configured LLM (Groq) first, optionally grounded in course
    material via RAG retrieval (if `use_rag` and `course_id` point at a
    built index) or a raw `course_text` excerpt. Falls back to a
    deterministic offline generator if no LLM backend is configured or the
    LLM call fails, so the app degrades gracefully rather than breaking.

    Returns:
        List of question dicts: {question, type, choices, answer, explanation}
    """
    history_key = _course_history_key(topic, course_text, course_id)
    with _HISTORY_LOCK:
        history = _load_question_history()
        course_history = history.setdefault("courses", {}).setdefault(history_key, {"stems": []})
        seen_questions = set(course_history.get("stems", []))

    if groq_client.is_available():
        try:
            generated_questions = _generate_with_llm(
                topic=topic,
                n_questions=n_questions,
                config=config,
                course_text=course_text,
                use_rag=use_rag,
                course_id=course_id,
                mcq_ratio=mcq_ratio,
                allow_open=allow_open,
                generation_prompt=generation_prompt,
            )
        except Exception as exc:  # noqa: BLE001 - any LLM/parsing failure should degrade, not crash
            logger.warning("LLM question generation failed, falling back to offline generator: %s", exc)
            generated_questions = []
            for attempt in range(8):
                candidate_questions = _generate_offline(
                    topic,
                    n_questions,
                    mcq_ratio,
                    course_text=course_text,
                    allow_open=allow_open,
                    variant_salt=f"{history_key}:{attempt}",
                )
                for question in _unique_new_questions(candidate_questions, seen_questions):
                    generated_questions.append(question)
                    seen_questions.add(_normalize_question_stem(str(question.get("question", ""))))
                    if len(generated_questions) >= n_questions:
                        break
                if len(generated_questions) >= n_questions:
                    break
    else:
        logger.info("No LLM backend configured (GROQ_API_KEY unset); using offline generator.")
        generated_questions = []
        for attempt in range(8):
            candidate_questions = _generate_offline(
                topic,
                n_questions,
                mcq_ratio,
                course_text=course_text,
                allow_open=allow_open,
                variant_salt=f"{history_key}:{attempt}",
            )
            for question in _unique_new_questions(candidate_questions, seen_questions):
                generated_questions.append(question)
                seen_questions.add(_normalize_question_stem(str(question.get("question", ""))))
                if len(generated_questions) >= n_questions:
                    break
            if len(generated_questions) >= n_questions:
                break

    generated_questions = generated_questions[:n_questions]

    with _HISTORY_LOCK:
        history = _load_question_history()
        course_history = history.setdefault("courses", {}).setdefault(history_key, {"stems": []})
        stored_stems = set(course_history.get("stems", []))
        for question in generated_questions:
            stem = _normalize_question_stem(str(question.get("question", "")))
            if stem:
                stored_stems.add(stem)
        course_history["stems"] = sorted(stored_stems)
        _save_question_history(history)

    return generated_questions