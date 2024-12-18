import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test the health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("\nHealth Check Response:")
    print(json.dumps(response.json(), indent=2))

def test_chat():
    """Test the chat endpoint"""
    payload = {
        "user_id": "test_user",
        "message": "I can't login to spotify"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print("\nChat Response:")
    print(json.dumps(response.json(), indent=2))

def test_auth():
    """Test authentication endpoints"""
    import uuid
    test_email = f"test_{uuid.uuid4()}@example.com"

    
    signup_payload = {
        "email": test_email,
        "password": "testpassword123"
    }
    
    print("\nTesting Signup:")
    signup_response = requests.post(f"{BASE_URL}/auth/signup", json=signup_payload)
    print("Status Code:", signup_response.status_code)
    print("Raw Response:", signup_response.text)

    print("\nTesting Signin:")
    signin_response = requests.post(f"{BASE_URL}/auth/signin", json=signup_payload)
    print("Status Code:", signin_response.status_code)
    print("Raw Response:", signin_response.text)  # Added this line
    try:
        print(json.dumps(signin_response.json(), indent=2))
    except json.JSONDecodeError:
        print("Could not parse JSON response")

if __name__ == "__main__":
    print("Starting API tests...")
    
    try:
        test_health()
        test_chat()
        test_auth()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")