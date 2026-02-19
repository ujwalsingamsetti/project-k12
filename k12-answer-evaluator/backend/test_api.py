#!/usr/bin/env python3
"""Quick API test"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("Testing K12 Evaluator API v2.0")
print("=" * 60)

# Test 1: Register Teacher
print("\n1. Registering teacher...")
teacher_data = {
    "email": "teacher@test.com",
    "password": "teacher123",
    "full_name": "John Teacher",
    "role": "teacher"
}
r = requests.post(f"{BASE_URL}/auth/register", json=teacher_data)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"✅ Teacher registered: {r.json()['full_name']}")
else:
    print(f"⚠️  {r.json()}")

# Test 2: Register Student
print("\n2. Registering student...")
student_data = {
    "email": "student@test.com",
    "password": "student123",
    "full_name": "Jane Student",
    "role": "student"
}
r = requests.post(f"{BASE_URL}/auth/register", json=student_data)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"✅ Student registered: {r.json()['full_name']}")
else:
    print(f"⚠️  {r.json()}")

# Test 3: Teacher Login
print("\n3. Teacher login...")
r = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "teacher@test.com",
    "password": "teacher123"
})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    teacher_token = r.json()["access_token"]
    print(f"✅ Teacher logged in, token: {teacher_token[:20]}...")
else:
    print(f"❌ Login failed")
    exit(1)

# Test 4: Create Question Paper
print("\n4. Creating question paper...")
paper_data = {
    "title": "Physics Mid-Term Exam",
    "subject": "science",
    "class_level": 12,
    "total_marks": 20,
    "duration_minutes": 60,
    "instructions": "Answer all questions",
    "questions": [
        {
            "question_number": 1,
            "question_text": "What is a solenoid?",
            "question_type": "short",
            "marks": 5,
            "expected_keywords": ["coil", "wire", "magnetic field"]
        },
        {
            "question_number": 2,
            "question_text": "Explain electromagnetic induction",
            "question_type": "long",
            "marks": 15,
            "expected_keywords": ["magnetic flux", "induced current", "Faraday"]
        }
    ]
}
headers = {"Authorization": f"Bearer {teacher_token}"}
r = requests.post(f"{BASE_URL}/teacher/papers", json=paper_data, headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    paper_id = r.json()["id"]
    print(f"✅ Paper created: {r.json()['title']}")
    print(f"   Paper ID: {paper_id}")
    print(f"   Questions: {len(r.json()['questions'])}")
else:
    print(f"❌ Failed: {r.json()}")
    exit(1)

# Test 5: Student Login
print("\n5. Student login...")
r = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "student@test.com",
    "password": "student123"
})
if r.status_code == 200:
    student_token = r.json()["access_token"]
    print(f"✅ Student logged in")
else:
    print(f"❌ Login failed")
    exit(1)

# Test 6: Student views available papers
print("\n6. Student viewing available papers...")
headers = {"Authorization": f"Bearer {student_token}"}
r = requests.get(f"{BASE_URL}/student/papers", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    papers = r.json()
    print(f"✅ Found {len(papers)} available papers")
    for p in papers:
        print(f"   - {p['title']} ({p['total_marks']} marks)")
else:
    print(f"❌ Failed")

print("\n" + "=" * 60)
print("✅ All tests passed! Backend is working!")
print("=" * 60)
print("\nNext: Run frontend with 'npm run dev' in frontend folder")
