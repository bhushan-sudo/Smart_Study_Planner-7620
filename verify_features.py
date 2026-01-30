
import requests
import json
import os

BASE_URL = "http://localhost:5000/api"

def run_tests():
    print("Running verification tests...")
    
    # 1. Register/Login
    session = requests.Session()
    username = "test_user_ai"
    email = "test_ai@example.com"
    password = "password123"
    
    # Register/Login
    try:
        res = session.post(f"{BASE_URL}/auth/register", json={
             "username": username, "email": email, "password": password, "fullName": "Test User"
        })
    except:
        pass # maybe already exists
        
    res = session.post(f"{BASE_URL}/auth/login", json={
        "identifier": username, "password": password
    })
    
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return False
        
    data = res.json()
    token = data['token']
    user_id = data['user']['user_id']
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Logged in as user {user_id}")
    
    # 2. Test Profile Image Update (Mock)
    # Since upload requires multipart, we'll verify the USER update endpoint accepts profile_image_url
    res = session.put(f"{BASE_URL}/users/{user_id}", headers=headers, json={
        "profile_image_url": "http://example.com/avatar.png"
    })
    if res.status_code == 200 and res.json()['user'].get('profile_image_url') == "http://example.com/avatar.png":
        print("✅ Profile image update endpoint verified.")
    else:
        print(f"❌ Profile image update failed: {res.text}")

    # 3. Test Enhanced Task Creation & AI
    # Create task with NO date to trigger AI
    task_payload = {
        "title": "Study Quantum Physics",
        "description": "Hard stuff",
        "new_subject_name": "Physics 101", # Test new subject creation
        "new_subject_color": "#FF0000",
        "estimated_hours": 2,
        "priority": 3
        # No scheduled_date
    }
    
    print("Creating task to trigger AI...")
    try:
        res = session.post(f"{BASE_URL}/users/{user_id}/tasks", headers=headers, json=task_payload)
        if res.status_code == 201:
            data = res.json()
            task = data['task']
            suggestion = data.get('agent_suggestion')
            
            print(f"✅ Task created (ID: {task['task_id']})")
            
            # Verify subject was created
            if task['subject_id']:
                # Fetch subject to check name
                sub_res = session.get(f"{BASE_URL}/subjects/{task['subject_id']}", headers=headers)
                if sub_res.json()['subject']['subject_name'] == "Physics 101":
                    print("✅ New subject creation verified.")
                else:
                    print("❌ Subject name mismatch.")
            
            # Verify AI Suggestion
            if suggestion and "AI Suggestion" in suggestion:
                print(f"✅ AI Suggestion received: {suggestion[:50]}...")
            elif suggestion:
                print(f"⚠️ received message but maybe not AI: {suggestion}")
            else:
                print("❌ No AI suggestion received (Verify GEMINI_API_KEY is active).")
                
        else:
             print(f"❌ Task creation failed: {res.text}")
             
    except Exception as e:
        print(f"❌ Error during task test: {e}")

if __name__ == "__main__":
    run_tests()
