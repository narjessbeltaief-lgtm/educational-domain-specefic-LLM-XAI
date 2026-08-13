
"""
One-off preprocessing script: converts d2l-en chapter_computer-vision
markdown files into clean prose .txt files suitable for RAG indexing.

Strips code blocks, raw LaTeX-heavy lines, and markdown syntax, keeping
only readable explanatory text.

Usage:
    python scripts/clean_d2l_markdown.py <src_md_dir> <dest_txt_dir>
"""

import re
import sys
from pathlib import Path


def clean_markdown(text: str) -> str:
    # Remove fenced code blocks (```...```)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Remove d2l-specific tab directives and inline code
    text = re.sub(r"#@tab.*", "", text)
    text = re.sub(r"`[^`]*`", "", text)

    # Remove markdown headers/links/image syntax but keep the link text
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)          # images
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)       # [text](url) -> text
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)  # headers

    # Remove :numref:, :eqref: and similar directives
    text = re.sub(r":\w+:`[^`]*`", "", text)

    # Collapse excess blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def main():
    if len(sys.argv) != 3:
        print("Usage: python clean_d2l_markdown.py <src_md_dir> <dest_txt_dir>")
        sys.exit(1)

    src_dir = Path(sys.argv[1])
    dest_dir = Path(sys.argv[2])
    dest_dir.mkdir(parents=True, exist_ok=True)

    md_files = list(src_dir.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {src_dir}")
        sys.exit(1)

    for md_path in md_files:
        raw = md_path.read_text(encoding="utf-8")
        cleaned = clean_markdown(raw)

        # Skip files that end up nearly empty after cleaning (pure-code files)
        if len(cleaned) < 200:
            print(f"Skipping {md_path.name} (too little prose after cleaning)")
            continue

        out_path = dest_dir / (md_path.stem + ".txt")
        out_path.write_text(cleaned, encoding="utf-8")
        print(f"Wrote {out_path} ({len(cleaned)} chars)")


if __name__ == "__main__":
    main()
