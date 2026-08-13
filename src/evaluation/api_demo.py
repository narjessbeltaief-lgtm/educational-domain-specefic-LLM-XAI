"""
Demo script showing how to use the on-demand testing API.

This demonstrates the complete workflow:
1. Generate a test
2. Student answers questions one by one
3. Get final results
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000/api/testing"


def demo_student_test():
    """Complete workflow: generate test, answer questions, get results."""
    
    print("\n" + "="*70)
    print("ON-DEMAND TEST SYSTEM DEMO")
    print("="*70)
    
    # Step 1: Generate a new test
    print("\n[1] Generating new test for course 'Introduction to Biology'...")
    generate_response = requests.post(
        f"{BASE_URL}/generate",
        json={
            "course_name": "Introduction to Biology",
            "course_text": "This course covers cells, genetics, ecosystems, and evolution.",
            "n_questions": 10,
            "mcq_ratio": 0.5,
        }
    )
    
    if generate_response.status_code != 200:
        print(f"❌ Error: {generate_response.text}")
        return
    
    test_data = generate_response.json()
    test_id = test_data["test_id"]
    questions = test_data["questions"]
    
    print(f"✓ Test generated! Test ID: {test_id}")
    print(f"✓ Questions: {test_data['n_questions']}")
    
    # Step 2: Display questions and simulate student answering
    print(f"\n[2] Student 'John' taking the test...")
    student_name = "John"
    correct_count = 0
    total_score = 0
    
    student_answers = []
    
    for i, q in enumerate(questions[:5], 1):  # Answer first 5 questions for demo
        print(f"\n  Q{i}: {q['question']}")
        
        if q["type"] == "mcq":
            print(f"    Choices: {', '.join(q['choices'])}")
            # Simulate student answering (50% correct for demo)
            student_answer = q["answer"] if i % 2 == 0 else q["choices"][0]
        else:  # yes_no
            student_answer = q["answer"] if i % 2 == 0 else ("No" if q["answer"] == "Yes" else "Yes")
        
        print(f"    Student answer: {student_answer}")
        
        # Submit answer
        answer_response = requests.post(
            f"{BASE_URL}/answer",
            json={
                "test_id": test_id,
                "student_name": student_name,
                "question_num": i,
                "answer": student_answer,
            }
        )
        
        if answer_response.status_code == 200:
            feedback = answer_response.json()
            is_correct = feedback["is_correct"]
            score = feedback["score"]
            
            status = "✓ CORRECT" if is_correct else "✗ WRONG"
            print(f"    {status} (Score: {score}/10)")
            
            if is_correct:
                correct_count += 1
            total_score += score
            
            student_answers.append(feedback)
        else:
            print(f"    Error: {answer_response.text}")
    
    # Step 3: Get final results
    print(f"\n[3] Getting final results for {student_name}...")
    results_response = requests.get(
        f"{BASE_URL}/{test_id}/results/{student_name}"
    )
    
    if results_response.status_code == 200:
        results = results_response.json()
        print("\n" + "="*70)
        print("TEST RESULTS")
        print("="*70)
        print(f"Student: {results['student_name']}")
        print(f"Course: {results.get('course_name', results.get('topic', ''))}")
        print(f"Score: {results['total_score']}/{results['max_score']}")
        print(f"Percentage: {results['percentage']}%")
        print(f"Correct Answers: {correct_count}/{len(questions[:5])}")
        print("="*70)
        
        # Show answer breakdown
        print("\nDetailed Results:")
        for ans in results['answers'][:5]:
            status = "✓" if ans['is_correct'] else "✗"
            print(f"  {status} Q{ans['question_num']}: {ans['student_answer']} (Correct: {ans['correct_answer']})")
    else:
        print(f"❌ Error: {results_response.text}")
    
    # Step 4: Check test status
    print(f"\n[4] Checking test status...")
    status_response = requests.get(f"{BASE_URL}/status/{test_id}")
    
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"  Progress: {status['progress']}")
        print(f"  Remaining: {status['remaining']} questions")
    else:
        print(f"❌ Error: {status_response.text}")


def demo_curl_commands():
    """Show example curl commands for testing."""
    print("\n" + "="*70)
    print("API USAGE EXAMPLES (curl)")
    print("="*70)
    
    print("\n1. Generate a test:")
    print("""
curl -X POST http://localhost:8000/api/generation/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "topic": "machine learning",
    "n_questions": 20,
    "mcq_ratio": 0.5
  }'
    """)
    
    print("\n2. Submit an answer:")
    print("""
curl -X POST http://localhost:8000/api/testing/answer \\
  -H "Content-Type: application/json" \\
  -d '{
    "student_name": "John",
    "question_num": 1,
    "answer": "ResNet"
  }'
    """)
    
    print("\n3. Get test results:")
    print("""
curl -X GET http://localhost:8000/api/testing/abc123/results/John
    """)
    
    print("\n4. Get test status:")
    print("""
curl -X GET http://localhost:8000/api/testing/abc123/status
    """)


if __name__ == "__main__":
    print("\n⚠️  Make sure the API server is running:")
    print("   python -m uvicorn src.api.main:app --reload")
    
    try:
        demo_student_test()
        demo_curl_commands()
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API. Start the server first!")
        print("\nTo start the server:")
        print("  cd /home/narjess/Documents/summer_internship_july2026/code")
        print("  python -m uvicorn src.api.main:app --reload")
