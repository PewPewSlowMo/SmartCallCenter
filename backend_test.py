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
        assert response.json()["message"] == "CallCenter Analytics API v1.0.0", "Response message does not match expected output"
        
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

def test_auth_me(role):
    """Test the me endpoint GET /api/auth/me"""
    print(f"\n=== Testing GET /api/auth/me endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "username" in response.json(), "Response does not contain 'username' field"
        assert "role" in response.json(), "Response does not contain 'role' field"
        assert response.json()["role"] == role, f"User role does not match expected role {role}"
        
        print(f"✅ Me endpoint test passed with {role} token!")
        return True
    except Exception as e:
        print(f"❌ Me endpoint test failed with {role} token: {str(e)}")
        return False

def test_dashboard_stats(role):
    """Test the dashboard stats endpoint GET /api/dashboard/stats"""
    print(f"\n=== Testing GET /api/dashboard/stats endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/dashboard/stats", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response contains call_stats: {'call_stats' in response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "call_stats" in response.json(), "Response does not contain 'call_stats' field"
        assert "operator_stats" in response.json(), "Response does not contain 'operator_stats' field"
        assert "queue_stats" in response.json(), "Response does not contain 'queue_stats' field"
        assert "chart_data" in response.json(), "Response does not contain 'chart_data' field"
        
        print(f"✅ Dashboard stats endpoint test passed with {role} token!")
        return True
    except Exception as e:
        print(f"❌ Dashboard stats endpoint test failed with {role} token: {str(e)}")
        return False

def test_dashboard_realtime(role):
    """Test the dashboard realtime endpoint GET /api/dashboard/realtime"""
    print(f"\n=== Testing GET /api/dashboard/realtime endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/dashboard/realtime", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response contains operators_online: {'operators_online' in response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "operators_online" in response.json(), "Response does not contain 'operators_online' field"
        assert "operators_busy" in response.json(), "Response does not contain 'operators_busy' field"
        assert "calls_today" in response.json(), "Response does not contain 'calls_today' field"
        assert "ongoing_calls" in response.json(), "Response does not contain 'ongoing_calls' field"
        assert "last_updated" in response.json(), "Response does not contain 'last_updated' field"
        
        print(f"✅ Dashboard realtime endpoint test passed with {role} token!")
        return True
    except Exception as e:
        print(f"❌ Dashboard realtime endpoint test failed with {role} token: {str(e)}")
        return False

def test_admin_users(role):
    """Test the admin users endpoint GET /api/admin/users"""
    print(f"\n=== Testing GET /api/admin/users endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/admin/users", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Admin should have access
        if role == "admin":
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            assert isinstance(response.json(), list), "Response is not a list"
            assert len(response.json()) > 0, "Response list is empty"
            print(f"✅ Admin users endpoint test passed with {role} token!")
            return True
        # Other roles should get 403 Forbidden
        else:
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Admin users endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Admin users endpoint test failed with {role} token: {str(e)}")
        return False

def test_admin_groups(role):
    """Test the admin groups endpoint GET /api/admin/groups"""
    print(f"\n=== Testing GET /api/admin/groups endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/admin/groups", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Admin should have access
        if role == "admin":
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            assert isinstance(response.json(), list), "Response is not a list"
            assert len(response.json()) > 0, "Response list is empty"
            print(f"✅ Admin groups endpoint test passed with {role} token!")
            return True
        # Other roles should get 403 Forbidden
        else:
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Admin groups endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Admin groups endpoint test failed with {role} token: {str(e)}")
        return False

def test_admin_settings(role):
    """Test the admin settings endpoint GET /api/admin/settings"""
    print(f"\n=== Testing GET /api/admin/settings endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/admin/settings", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Admin should have access
        if role == "admin":
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            assert "call_recording" in response.json(), "Response does not contain 'call_recording' field"
            print(f"✅ Admin settings endpoint test passed with {role} token!")
            return True
        # Other roles should get 403 Forbidden
        else:
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Admin settings endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Admin settings endpoint test failed with {role} token: {str(e)}")
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

def test_admin_system_info(role):
    """Test the admin system info endpoint GET /api/admin/system/info"""
    print(f"\n=== Testing GET /api/admin/system/info endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/admin/system/info", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Admin should have access
        if role == "admin":
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            assert "users" in response.json(), "Response does not contain 'users' field"
            assert "groups" in response.json(), "Response does not contain 'groups' field"
            assert "queues" in response.json(), "Response does not contain 'queues' field"
            assert "operators" in response.json(), "Response does not contain 'operators' field"
            print(f"✅ Admin system info endpoint test passed with {role} token!")
            return True
        # Other roles should get 403 Forbidden
        else:
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Admin system info endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Admin system info endpoint test failed with {role} token: {str(e)}")
        return False

def test_operators_list(role):
    """Test the operators list endpoint GET /api/operators/"""
    print(f"\n=== Testing GET /api/operators/ endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/operators/", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Admin, manager, and supervisor should have access
        if role in ["admin", "manager", "supervisor"]:
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            assert isinstance(response.json(), list), "Response is not a list"
            print(f"✅ Operators list endpoint test passed with {role} token!")
            return True
        # Operator should get 403 Forbidden
        else:
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Operators list endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Operators list endpoint test failed with {role} token: {str(e)}")
        return False

def test_queues_list(role):
    """Test the queues list endpoint GET /api/queues/"""
    print(f"\n=== Testing GET /api/queues/ endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/queues/", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Admin, manager, and supervisor should have access
        if role in ["admin", "manager", "supervisor"]:
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            assert isinstance(response.json(), list), "Response is not a list"
            print(f"✅ Queues list endpoint test passed with {role} token!")
            return True
        # Operator should get 403 Forbidden
        else:
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Queues list endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Queues list endpoint test failed with {role} token: {str(e)}")
        return False

def check_server_logs():
    """Check server logs for errors"""
    print("\n=== Checking server logs for errors ===")
    try:
        # Get the last 100 lines of the backend log
        import subprocess
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.log"], 
            capture_output=True, 
            text=True
        )
        
        log_content = result.stdout
        error_keywords = ["error", "exception", "fail", "critical"]
        
        errors_found = False
        for line in log_content.split('\n'):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in error_keywords):
                print(f"Potential error in logs: {line}")
                errors_found = True
        
        if not errors_found:
            print("No obvious errors found in the server logs")
            return True
        else:
            print("⚠️ Potential errors found in server logs")
            return False
    except Exception as e:
        print(f"❌ Failed to check server logs: {str(e)}")
        return False

def test_cors():
    """Test CORS configuration"""
    print("\n=== Testing CORS configuration ===")
    try:
        headers = {
            'Origin': 'http://example.com',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'X-Requested-With'
        }
        
        # Options request to check CORS headers
        response = requests.options(f"{API_BASE_URL}/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"CORS Headers: {response.headers}")
        
        assert 'Access-Control-Allow-Origin' in response.headers, "CORS header missing: Access-Control-Allow-Origin"
        assert 'Access-Control-Allow-Methods' in response.headers, "CORS header missing: Access-Control-Allow-Methods"
        assert 'Access-Control-Allow-Headers' in response.headers, "CORS header missing: Access-Control-Allow-Headers"
        
        print("✅ CORS configuration test passed!")
        return True
    except Exception as e:
        print(f"❌ CORS configuration test failed: {str(e)}")
        return False

def test_create_operator():
    """Test creating an operator with extension"""
    print("\n=== Testing POST /api/admin/users endpoint to create operator ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Create operator with extension
        payload = {
            "username": TEST_OPERATOR_USERNAME,
            "email": f"{TEST_OPERATOR_USERNAME.lower()}@callcenter.com",
            "name": "Test Operator",
            "password": TEST_OPERATOR_PASSWORD,
            "role": "operator",
            "extension": TEST_OPERATOR_EXTENSION
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/users", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            assert "id" in response.json(), "Response does not contain 'id' field"
            assert response.json()["username"] == TEST_OPERATOR_USERNAME, "Username does not match"
            assert response.json()["role"] == "operator", "Role does not match"
            
            # Store operator user ID for later use
            global operator_user_id
            operator_user_id = response.json()["id"]
            
            print("✅ Create operator endpoint test passed!")
            return True
        else:
            print(f"Create operator failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Create operator endpoint test failed: {str(e)}")
        return False

def test_get_operator_info():
    """Test getting operator information"""
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

def test_virtual_asterisk_connection():
    """Test connection to virtual Asterisk server"""
    print("\n=== Testing POST /api/admin/settings/asterisk/test endpoint ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Test connection to demo.asterisk.com
        payload = {
            "host": "demo.asterisk.com",
            "port": 5038,
            "username": "admin",
            "password": "admin",
            "protocol": "AMI",
            "enabled": True
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/settings/asterisk/test", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            assert "success" in response.json(), "Response does not contain 'success' field"
            assert response.json()["success"] == True, "Connection test failed"
            
            print("✅ Virtual Asterisk connection test passed!")
            return True
        else:
            print(f"Virtual Asterisk connection test failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Virtual Asterisk connection test failed: {str(e)}")
        return False

def run_smart_call_center_tests():
    """Run tests for Smart Call Center login system"""
    print("\n=== Running Smart Call Center login system tests ===")
    
    # Test admin login
    admin_login_result = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD, "admin")
    
    # Test getting current user info
    if admin_login_result:
        auth_me_result = test_auth_me("admin")
    else:
        auth_me_result = False
        print("❌ Skipping auth/me test because admin login failed")
    
    # Test creating operator with extension
    if admin_login_result:
        create_operator_result = test_create_operator()
    else:
        create_operator_result = False
        print("❌ Skipping create operator test because admin login failed")
    
    # Test getting operator info
    if create_operator_result:
        operator_info_result = test_get_operator_info()
    else:
        operator_info_result = False
        print("❌ Skipping operator info test because create operator failed")
    
    # Test virtual Asterisk connection
    if admin_login_result:
        virtual_asterisk_result = test_virtual_asterisk_connection()
    else:
        virtual_asterisk_result = False
        print("❌ Skipping virtual Asterisk test because admin login failed")
    
    # Print test summary
    print("\n=== Smart Call Center Test Summary ===")
    print(f"Admin Login: {'✅ PASSED' if admin_login_result else '❌ FAILED'}")
    print(f"Get Current User: {'✅ PASSED' if auth_me_result else '❌ FAILED'}")
    print(f"Create Operator with Extension: {'✅ PASSED' if create_operator_result else '❌ FAILED'}")
    print(f"Get Operator Info: {'✅ PASSED' if operator_info_result else '❌ FAILED'}")
    print(f"Virtual Asterisk Connection: {'✅ PASSED' if virtual_asterisk_result else '❌ FAILED'}")
    
    all_passed = all([
        admin_login_result,
        auth_me_result,
        create_operator_result,
        operator_info_result,
        virtual_asterisk_result
    ])
    
    if all_passed:
        print("\n🎉 All Smart Call Center tests passed successfully!")
    else:
        print("\n⚠️ Some Smart Call Center tests failed. See details above.")
    
    return all_passed

def run_all_tests():
    """Run all tests and return overall result"""
    print("\n=== Running all backend API tests ===")
    
    # Run Smart Call Center tests
    smart_call_center_result = run_smart_call_center_tests()
    
    return smart_call_center_result

if __name__ == "__main__":
    run_all_tests()