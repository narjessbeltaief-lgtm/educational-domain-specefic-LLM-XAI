import json
import random
from typing import List, Dict
from src.generation.question_generator import generate_questions
from src.utils.config_loader import load_config


# Mock student profiles
STUDENTS = {
    "Student_A": {"name": "Alice", "level": "excellent", "accuracy": 0.90},
    "Student_B": {"name": "Bob", "level": "good", "accuracy": 0.80},
    "Student_C": {"name": "Charlie", "level": "average", "accuracy": 0.70},
    "Student_D": {"name": "Diana", "level": "below_average", "accuracy": 0.50},
    "Student_E": {"name": "Eve", "level": "poor", "accuracy": 0.30},
    "Student_F": {"name": "Frank", "level": "random", "accuracy": 0.50},
}


def generate_student_answer(question: dict, accuracy: float) -> str:
    """Generate a student answer based on their accuracy level."""
    correct_answer = question["answer"]
    
    # Determine if this answer should be correct or wrong
    if random.random() < accuracy:
        return correct_answer
    
    # Generate a wrong answer
    if question["type"] == "mcq":
        wrong_choices = [c for c in question["choices"] if c != correct_answer]
        return random.choice(wrong_choices) if wrong_choices else correct_answer
    else:  # yes_no
        return "No" if correct_answer == "Yes" else "Yes"


def grade_student(student_id: str, student_name: str, questions: List[dict], 
                  accuracy: float, config: dict) -> Dict:
    """Grade a student's answers for all questions."""
    results = {
        "student_id": student_id,
        "student_name": student_name,
        "total_questions": len(questions),
        "answers": [],
        "total_score": 0,
        "max_score": 0,
    }
    
    for i, question in enumerate(questions):
        # Generate student's answer based on accuracy
        student_answer = generate_student_answer(question, accuracy)
        
        # Check if answer is correct
        is_correct = student_answer == question["answer"]
        
        score = 10 if is_correct else 0
        
        results["answers"].append({
            "question_num": i + 1,
            "question": question["question"],
            "type": question["type"],
            "correct_answer": question["answer"],
            "student_answer": student_answer,
            "is_correct": is_correct,
            "score": score,
        })
        
        results["total_score"] += score
        results["max_score"] += 10
    
    results["percentage"] = round((results["total_score"] / results["max_score"]) * 100, 2)
    
    return results


def run_batch_test(topic: str, n_questions: int = 20):
    """Generate test, grade 6 students, output results."""
    cfg = load_config()
    
    print("\n" + "="*70)
    print(f"BATCH TEST GENERATION & GRADING")
    print("="*70)
    
    # Step 1: Generate questions
    print(f"\n[1] Generating {n_questions} questions on '{topic}'...")
    questions = generate_questions(
        topic=topic,
        n_questions=n_questions,
        config=cfg,
        use_rag=True,
        mcq_ratio=0.5,
    )
    print(f"✓ Generated {len(questions)} questions")
    print(f"   - MCQ: {sum(1 for q in questions if q['type'] == 'mcq')}")
    print(f"   - Yes/No: {sum(1 for q in questions if q['type'] == 'yes_no')}")
    
    # Step 2: Grade each student
    print(f"\n[2] Grading {len(STUDENTS)} students...")
    all_results = []
    
    for student_id, student_info in STUDENTS.items():
        print(f"   Grading {student_info['name']} ({student_info['level']})...", end=" ")
        result = grade_student(
            student_id=student_id,
            student_name=student_info["name"],
            questions=questions,
            accuracy=student_info["accuracy"],
            config=cfg,
        )
        all_results.append(result)
        print(f"✓ {result['total_score']}/{result['max_score']} ({result['percentage']}%)")
    
    # Step 3: Print summary table
    print("\n" + "="*70)
    print("SUMMARY - All Students")
    print("="*70)
    print(f"{'Student':<15} {'Level':<18} {'Score':<12} {'Percentage':<10}")
    print("-"*70)
    for result in all_results:
        student_info = STUDENTS[result["student_id"]]
        score_str = f"{result['total_score']}/{result['max_score']}"
        print(f"{result['student_name']:<15} {student_info['level']:<18} {score_str:<12} {result['percentage']}%")
    print("="*70)
    
    # Step 4: Save to JSON
    output = {
        "test_info": {
            "topic": topic,
            "n_questions": len(questions),
            "n_students": len(all_results),
            "q_breakdown": {
                "mcq": sum(1 for q in questions if q["type"] == "mcq"),
                "yes_no": sum(1 for q in questions if q["type"] == "yes_no"),
            }
        },
        "questions": questions,
        "student_results": all_results,
    }
    
    with open("test_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Detailed results saved to test_results.json")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_batch_test(topic="machine learning", n_questions=20)
