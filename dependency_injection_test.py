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
TEST_ADMIN_USERNAME = "admin"
TEST_ADMIN_PASSWORD = "admin"
TEST_OPERATOR_USERNAME = "TestOperator"
TEST_OPERATOR_PASSWORD = "password123"
TEST_OPERATOR_EXTENSION = "1001"
TEST_MANAGER_USERNAME = "TestManager"
TEST_MANAGER_PASSWORD = "password123"

# Global variables for user IDs
operator_user_id = None
manager_user_id = None

def test_root_endpoint():
    """Test the root endpoint GET /api/"""
    print("\n=== Testing GET /api/ endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "message" in response.json(), "Response does not contain 'message' field"
        
        print("✅ Root endpoint test passed!")
        return True
    except Exception as e:
        print(f"❌ Root endpoint test failed: {str(e)}")
        return False

def test_health_endpoint():
    """Test the health endpoint GET /api/health"""
    print("\n=== Testing GET /api/health endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "status" in response.json(), "Response does not contain 'status' field"
        assert "database" in response.json(), "Response does not contain 'database' field"
        assert "timestamp" in response.json(), "Response does not contain 'timestamp' field"
        
        print("✅ Health endpoint test passed!")
        return True
    except Exception as e:
        print(f"❌ Health endpoint test failed: {str(e)}")
        return False

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

def test_admin_settings_get():
    """Test the admin settings endpoint GET /api/admin/settings"""
    print("\n=== Testing GET /api/admin/settings endpoint ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        response = requests.get(f"{API_BASE_URL}/admin/settings", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "call_recording" in response.json(), "Response does not contain 'call_recording' field"
        
        print("✅ Admin settings GET endpoint test passed!")
        return True
    except Exception as e:
        print(f"❌ Admin settings GET endpoint test failed: {str(e)}")
        return False

def test_admin_settings_update():
    """Test the admin settings update endpoint PUT /api/admin/settings"""
    print("\n=== Testing PUT /api/admin/settings endpoint ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # First get current settings
        get_response = requests.get(f"{API_BASE_URL}/admin/settings", headers=headers)
        if get_response.status_code != 200:
            print(f"❌ Failed to get current settings: {get_response.status_code}")
            return False
            
        current_settings = get_response.json()
        print(f"Current settings: {current_settings}")
        
        # Update settings with new values
        update_payload = {
            "call_recording": not current_settings.get("call_recording", True),
            "auto_answer_delay": 5,
            "max_call_duration": 3600,
            "queue_timeout": 300,
            "callback_enabled": True,
            "sms_notifications": False,
            "email_notifications": True,
            "asterisk_config": {
                "host": "asterisk.example.com",
                "port": 5038,
                "username": "admin",
                "password": "password",
                "protocol": "AMI",
                "enabled": False
            }
        }
        
        response = requests.put(f"{API_BASE_URL}/admin/settings", json=update_payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            assert "call_recording" in response.json(), "Response does not contain 'call_recording' field"
            assert response.json()["call_recording"] == update_payload["call_recording"], "call_recording value not updated"
            assert response.json()["auto_answer_delay"] == update_payload["auto_answer_delay"], "auto_answer_delay value not updated"
            
            print("✅ Admin settings PUT endpoint test passed!")
            return True
        else:
            print(f"Update failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Admin settings PUT endpoint test failed: {str(e)}")
        return False

def test_asterisk_connection_test():
    """Test the Asterisk connection test endpoint POST /api/admin/settings/asterisk/test"""
    print("\n=== Testing POST /api/admin/settings/asterisk/test endpoint ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Test payload with mock Asterisk server details
        test_payload = {
            "host": "asterisk.example.com",
            "port": 5038,
            "username": "admin",
            "password": "password",
            "protocol": "AMI",
            "enabled": True
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/settings/asterisk/test", json=test_payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # We expect a 200 response even if the connection fails, since we're just testing the API
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "success" in response.json(), "Response does not contain 'success' field"
        assert "message" in response.json(), "Response does not contain 'message' field"
        
        # The connection will likely fail since we're using mock data, but the API should work
        print(f"Response: {response.json()}")
        print("✅ Asterisk connection test endpoint test passed!")
        return True
    except Exception as e:
        print(f"❌ Asterisk connection test endpoint test failed: {str(e)}")
        return False

def test_create_operator_user():
    """Test creating an operator user with extension POST /api/admin/users"""
    print("\n=== Testing POST /api/admin/users endpoint (create operator) ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Create operator user with extension
        operator_payload = {
            "username": TEST_OPERATOR_USERNAME,
            "email": "testoperator@example.com",
            "name": "Test Operator",
            "password": TEST_OPERATOR_PASSWORD,
            "role": "operator",
            "extension": TEST_OPERATOR_EXTENSION
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/users", json=operator_payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            assert "id" in response.json(), "Response does not contain 'id' field"
            assert response.json()["username"] == operator_payload["username"], "Username does not match"
            assert response.json()["role"] == "operator", "Role does not match"
            
            # Store the operator user ID for later tests
            global operator_user_id
            operator_user_id = response.json()["id"]
            
            print("✅ Create operator user endpoint test passed!")
            return True
        else:
            print(f"Create operator failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Create operator user endpoint test failed: {str(e)}")
        return False

def test_create_manager_user():
    """Test creating a manager user without extension POST /api/admin/users"""
    print("\n=== Testing POST /api/admin/users endpoint (create manager) ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Create manager user without extension
        manager_payload = {
            "username": TEST_MANAGER_USERNAME,
            "email": "testmanager@example.com",
            "name": "Test Manager",
            "password": TEST_MANAGER_PASSWORD,
            "role": "manager"
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/users", json=manager_payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            assert "id" in response.json(), "Response does not contain 'id' field"
            assert response.json()["username"] == manager_payload["username"], "Username does not match"
            assert response.json()["role"] == "manager", "Role does not match"
            
            # Store the manager user ID for later tests
            global manager_user_id
            manager_user_id = response.json()["id"]
            
            print("✅ Create manager user endpoint test passed!")
            return True
        else:
            print(f"Create manager failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Create manager user endpoint test failed: {str(e)}")
        return False

def test_get_operator_info():
    """Test getting operator info GET /api/admin/users/{user_id}/operator"""
    print("\n=== Testing GET /api/admin/users/{user_id}/operator endpoint ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        if not operator_user_id:
            print("❌ No operator user ID available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        response = requests.get(f"{API_BASE_URL}/admin/users/{operator_user_id}/operator", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            assert "extension" in response.json(), "Response does not contain 'extension' field"
            assert response.json()["extension"] == TEST_OPERATOR_EXTENSION, "Extension does not match"
            
            print("✅ Get operator info endpoint test passed!")
            return True
        else:
            print(f"Get operator info failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Get operator info endpoint test failed: {str(e)}")
        return False

def test_get_manager_operator_info():
    """Test getting operator info for a manager (should return None) GET /api/admin/users/{user_id}/operator"""
    print("\n=== Testing GET /api/admin/users/{user_id}/operator endpoint for manager ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        if not manager_user_id:
            print("❌ No manager user ID available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        response = requests.get(f"{API_BASE_URL}/admin/users/{manager_user_id}/operator", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json() if response.text else 'None'}")
            
            # For a manager, we expect null/None response
            assert response.text == "null" or response.json() is None, "Expected null response for manager"
            
            print("✅ Get manager operator info endpoint test passed!")
            return True
        else:
            print(f"Get manager operator info failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Get manager operator info endpoint test failed: {str(e)}")
        return False

def run_dependency_injection_tests():
    """Run all tests for dependency injection fixes"""
    print("\n=== Running dependency injection tests ===")
    
    # Test basic endpoints
    test_root_endpoint()
    test_health_endpoint()
    
    # Login as admin
    admin_login_success = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD, "admin")
    if not admin_login_success:
        print("❌ Admin login failed, cannot proceed with further tests")
        return False
    
    # Test admin settings endpoints
    settings_get_success = test_admin_settings_get()
    settings_update_success = test_admin_settings_update()
    
    # Test Asterisk connection test endpoint
    asterisk_test_success = test_asterisk_connection_test()
    
    # Test user creation with extension
    operator_create_success = test_create_operator_user()
    manager_create_success = test_create_manager_user()
    
    # Test operator info endpoint
    operator_info_success = False
    manager_info_success = False
    if operator_create_success:
        operator_info_success = test_get_operator_info()
    if manager_create_success:
        manager_info_success = test_get_manager_operator_info()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Admin Login: {'✅ PASSED' if admin_login_success else '❌ FAILED'}")
    print(f"Admin Settings GET: {'✅ PASSED' if settings_get_success else '❌ FAILED'}")
    print(f"Admin Settings PUT: {'✅ PASSED' if settings_update_success else '❌ FAILED'}")
    print(f"Asterisk Connection Test: {'✅ PASSED' if asterisk_test_success else '❌ FAILED'}")
    print(f"Create Operator User: {'✅ PASSED' if operator_create_success else '❌ FAILED'}")
    print(f"Create Manager User: {'✅ PASSED' if manager_create_success else '❌ FAILED'}")
    print(f"Get Operator Info: {'✅ PASSED' if operator_info_success else '❌ FAILED'}")
    print(f"Get Manager Operator Info: {'✅ PASSED' if manager_info_success else '❌ FAILED'}")
    
    all_passed = (
        admin_login_success and
        settings_get_success and
        settings_update_success and
        asterisk_test_success and
        operator_create_success and
        manager_create_success and
        operator_info_success and
        manager_info_success
    )
    
    if all_passed:
        print("\n🎉 All dependency injection tests passed successfully!")
    else:
        print("\n⚠️ Some dependency injection tests failed. See details above.")
    
    return all_passed

if __name__ == "__main__":
    run_dependency_injection_tests()