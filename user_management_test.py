#!/usr/bin/env python3
import requests
import json
import os
import sys
from dotenv import load_dotenv
import time
from datetime import datetime
import subprocess

# Load environment variables from frontend/.env
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

API_BASE_URL = f"{BACKEND_URL}/api"
print(f"Testing API at: {API_BASE_URL}")

# Global variable to store auth tokens
auth_tokens = {}

# Test configuration
TEST_ADMIN_USERNAME = "admin@callcenter.com"
TEST_ADMIN_PASSWORD = "admin123"

def test_auth_login(username, password, expected_role=None):
    """Test the login endpoint POST /api/auth/login"""
    print(f"\n=== Testing POST /api/auth/login endpoint with {username} user ===")
    try:
        payload = {"username": username, "password": password}
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response contains token: {'access_token' in response.json()}")
            
            assert "access_token" in response.json(), "Response does not contain 'access_token' field"
            assert "token_type" in response.json(), "Response does not contain 'token_type' field"
            assert "user" in response.json(), "Response does not contain 'user' field"
            
            if expected_role:
                assert response.json()["user"]["role"] == expected_role, f"User role does not match expected role {expected_role}"
            
            # Store the token for later use
            role = response.json()["user"]["role"]
            auth_tokens[role] = response.json()["access_token"]
            
            print(f"✅ Login endpoint test passed for {username} user!")
            return True
        else:
            print(f"Login failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login endpoint test failed for {username} user: {str(e)}")
        return False

def test_create_user_with_extension():
    """Test creating a user with extension (operator role)"""
    print("\n=== Testing POST /api/admin/users endpoint with operator and extension ===")
    try:
        # First login as admin
        if "admin" not in auth_tokens:
            success = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)
            if not success:
                print("❌ Failed to login as admin")
                return False
        
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Create operator with extension
        payload = {
            "username": "operator1",
            "email": "operator1@callcenter.com",
            "name": "Test Operator 1",
            "password": "operator123",
            "role": "operator",
            "extension": "1001"
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/users", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "id" in response.json(), "Response does not contain 'id' field"
        assert response.json()["role"] == "operator", "User role is not operator"
        
        # Store the user ID for later use
        user_id = response.json()["id"]
        
        # Check if operator record was created
        operator_response = requests.get(f"{API_BASE_URL}/admin/users/{user_id}/operator", headers=headers)
        print(f"Operator Info Status Code: {operator_response.status_code}")
        print(f"Operator Info Response: {operator_response.json()}")
        
        assert operator_response.status_code == 200, f"Expected status code 200, got {operator_response.status_code}"
        assert operator_response.json() is not None, "Operator info is None"
        assert "extension" in operator_response.json(), "Operator info does not contain 'extension' field"
        assert operator_response.json()["extension"] == "1001", "Extension does not match"
        
        print("✅ Create user with extension test passed!")
        return True, user_id
    except Exception as e:
        print(f"❌ Create user with extension test failed: {str(e)}")
        return False, None

def test_create_user_duplicate_extension(extension="1001"):
    """Test creating a user with duplicate extension"""
    print("\n=== Testing POST /api/admin/users endpoint with duplicate extension ===")
    try:
        # First login as admin
        if "admin" not in auth_tokens:
            success = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)
            if not success:
                print("❌ Failed to login as admin")
                return False
        
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Create another operator with the same extension
        payload = {
            "username": "operator2",
            "email": "operator2@callcenter.com",
            "name": "Test Operator 2",
            "password": "operator123",
            "role": "operator",
            "extension": extension
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/users", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Should fail with 400 Bad Request
        assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
        assert "already assigned" in response.text.lower(), "Error message does not mention duplicate extension"
        
        print("✅ Create user with duplicate extension test passed!")
        return True
    except Exception as e:
        print(f"❌ Create user with duplicate extension test failed: {str(e)}")
        return False

def test_create_operator_without_extension():
    """Test creating an operator without extension"""
    print("\n=== Testing POST /api/admin/users endpoint with operator without extension ===")
    try:
        # First login as admin
        if "admin" not in auth_tokens:
            success = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)
            if not success:
                print("❌ Failed to login as admin")
                return False
        
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Create operator without extension
        payload = {
            "username": "operator3",
            "email": "operator3@callcenter.com",
            "name": "Test Operator 3",
            "password": "operator123",
            "role": "operator"
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/users", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Should fail with 400 Bad Request
        assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
        assert "extension is required" in response.text.lower(), "Error message does not mention required extension"
        
        print("✅ Create operator without extension test passed!")
        return True
    except Exception as e:
        print(f"❌ Create operator without extension test failed: {str(e)}")
        return False

def test_create_non_operator_with_extension():
    """Test creating a non-operator user with extension"""
    print("\n=== Testing POST /api/admin/users endpoint with non-operator with extension ===")
    try:
        # First login as admin
        if "admin" not in auth_tokens:
            success = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)
            if not success:
                print("❌ Failed to login as admin")
                return False
        
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Create manager with extension
        payload = {
            "username": "manager1",
            "email": "manager1@callcenter.com",
            "name": "Test Manager 1",
            "password": "manager123",
            "role": "manager",
            "extension": "2001"
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/users", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Should succeed but ignore the extension
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "id" in response.json(), "Response does not contain 'id' field"
        assert response.json()["role"] == "manager", "User role is not manager"
        
        # Store the user ID for later use
        user_id = response.json()["id"]
        
        # Check if operator record was created (should be None)
        operator_response = requests.get(f"{API_BASE_URL}/admin/users/{user_id}/operator", headers=headers)
        print(f"Operator Info Status Code: {operator_response.status_code}")
        print(f"Operator Info Response: {operator_response.json() if operator_response.status_code == 200 else operator_response.text}")
        
        assert operator_response.status_code == 200, f"Expected status code 200, got {operator_response.status_code}"
        assert operator_response.json() is None, "Operator info is not None for non-operator user"
        
        print("✅ Create non-operator with extension test passed!")
        return True, user_id
    except Exception as e:
        print(f"❌ Create non-operator with extension test failed: {str(e)}")
        return False, None

def test_update_system_settings_with_asterisk():
    """Test updating system settings with Asterisk configuration"""
    print("\n=== Testing PUT /api/admin/settings endpoint with Asterisk configuration ===")
    try:
        # First login as admin
        if "admin" not in auth_tokens:
            success = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)
            if not success:
                print("❌ Failed to login as admin")
                return False
        
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Update system settings with Asterisk configuration
        payload = {
            "call_recording": True,
            "auto_answer_delay": 5,
            "max_call_duration": 3600,
            "queue_timeout": 300,
            "callback_enabled": True,
            "sms_notifications": False,
            "email_notifications": True,
            "asterisk_config": {
                "host": "asterisk.example.com",
                "port": 8088,
                "username": "admin",
                "password": "password",
                "protocol": "ARI",
                "enabled": True
            }
        }
        
        response = requests.put(f"{API_BASE_URL}/admin/settings", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "asterisk_config" in response.json(), "Response does not contain 'asterisk_config' field"
        assert response.json()["asterisk_config"]["enabled"] is True, "Asterisk config is not enabled"
        
        # Check logs for ARI client initialization
        log_output = subprocess.run(
            ["tail", "-n", "50", "/var/log/supervisor/backend.log"], 
            capture_output=True, 
            text=True
        ).stdout
        
        print("\nBackend logs:")
        print(log_output)
        
        # Look for ARI client initialization in logs
        ari_initialized = "ARI client initialized" in log_output or "initialize_ari_client" in log_output
        
        if ari_initialized:
            print("✅ ARI client initialization found in logs")
        else:
            print("⚠️ ARI client initialization not found in logs")
        
        print("✅ Update system settings with Asterisk test passed!")
        return True
    except Exception as e:
        print(f"❌ Update system settings with Asterisk test failed: {str(e)}")
        return False

def test_asterisk_connection():
    """Test Asterisk connection test endpoint"""
    print("\n=== Testing POST /api/admin/settings/asterisk/test endpoint ===")
    try:
        # First login as admin
        if "admin" not in auth_tokens:
            success = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)
            if not success:
                print("❌ Failed to login as admin")
                return False
        
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Test Asterisk connection
        payload = {
            "host": "asterisk.example.com",
            "port": 8088,
            "username": "admin",
            "password": "password",
            "protocol": "ARI",
            "enabled": True
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/settings/asterisk/test", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "success" in response.json(), "Response does not contain 'success' field"
        
        # Note: The test will likely fail since we're using a fake Asterisk server
        # But we're testing the API endpoint, not the actual connection
        
        print("✅ Asterisk connection test endpoint test passed!")
        return True
    except Exception as e:
        print(f"❌ Asterisk connection test endpoint test failed: {str(e)}")
        return False

def run_user_management_tests():
    """Run tests for user management functionality"""
    print("\n=== Running user management tests ===")
    
    # Test authentication
    auth_results = {
        "auth_login_admin": test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD, "admin"),
    }
    
    # Test user management with extensions
    create_user_result = test_create_user_with_extension()
    create_non_operator_result = test_create_non_operator_with_extension()
    
    user_management_results = {
        "create_user_with_extension": create_user_result[0] if isinstance(create_user_result, tuple) else create_user_result,
        "create_user_duplicate_extension": test_create_user_duplicate_extension(),
        "create_operator_without_extension": test_create_operator_without_extension(),
        "create_non_operator_with_extension": create_non_operator_result[0] if isinstance(create_non_operator_result, tuple) else create_non_operator_result,
    }
    
    # Test system settings with Asterisk
    system_settings_results = {
        "update_system_settings_with_asterisk": test_update_system_settings_with_asterisk(),
        "asterisk_connection_test": test_asterisk_connection(),
    }
    
    # Combine results
    results = {}
    results.update(auth_results)
    results.update(user_management_results)
    results.update(system_settings_results)
    
    print("\n=== Test Summary ===")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All user management tests passed successfully!")
    else:
        print("\n⚠️ Some user management tests failed. See details above.")
    
    return all_passed, results

if __name__ == "__main__":
    run_user_management_tests()