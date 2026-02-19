import requests

r = requests.post("http://localhost:8000/api/auth/register", json={
    "email": "test2@test.com",
    "password": "test123",
    "full_name": "Test User",
    "role": "teacher"
})

print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
