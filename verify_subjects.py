
import requests
import json
import sys

BASE_URL = "http://localhost:5000/api"

def verify_subject_creation():
    print("Starting verification...")
    
    # 1. Create a test user
    username = "test_subject_user"
    email = "test_subject@example.com"
    password = "password123"
    
    # Try to login first, if fails then create
    login_payload = {"identifier": email, "password": password}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    
    if response.status_code == 200:
        token = response.json()['token']
        user_id = response.json()['user']['user_id']
        print("Logged in existing user.")
    else:
        # Create user
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "fullName": "Test Subject User"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        if response.status_code != 201:
            print(f"Failed to register: {response.text}")
            return
        token = response.json()['token']
        user_id = response.json()['user']['user_id']
        print("Created new user.")

    # 2. Create a subject with new fields
    headers = {"Authorization": f"Bearer {token}"}
    subject_payload = {
        "subject_name": "Advanced Physics",
        "priority": 3,
        "color_code": "#FF5733",
        "level": "University",
        "target_grade": "A+",
        "current_topic": "Quantum Mechanics",
        "sub_topics": "Wave Function, Schrodinger Equation, Uncertainty Principle"
    }
    
    response = requests.post(f"{BASE_URL}/users/{user_id}/subjects", json=subject_payload, headers=headers)
    
    if response.status_code != 201:
        print(f"Failed to create subject: {response.text}")
        return

    subject_data = response.json()['subject']
    print("Subject created successfully.")
    
    # 3. Verify fields
    errors = []
    if subject_data.get('level') != "University":
        errors.append(f"Level mismatch: {subject_data.get('level')}")
    if subject_data.get('target_grade') != "A+":
        errors.append(f"Target mismatch: {subject_data.get('target_grade')}")
    if subject_data.get('current_topic') != "Quantum Mechanics":
        errors.append(f"Topic mismatch: {subject_data.get('current_topic')}")
    
    if errors:
        print("Verification FAILED:")
        for err in errors:
            print(f"- {err}")
    else:
        print("Verification SUCCESS: All fields match!")

if __name__ == "__main__":
    verify_subject_creation()
