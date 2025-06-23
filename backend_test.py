#!/usr/bin/env python3
import requests
import json
import os
import sys
from dotenv import load_dotenv
import time
from datetime import datetime
import subprocess
import websocket
import threading
import uuid

# Load environment variables from frontend/.env
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = "http://localhost:8001"  # Use localhost for testing

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

# Asterisk test configuration
TEST_ASTERISK_HOST = "92.46.62.34"
TEST_ASTERISK_PORT = 8088
TEST_ASTERISK_USERNAME = "smart-call-center"
TEST_ASTERISK_PASSWORD = "Almaty20252025"

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
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response contains call_stats: {'call_stats' in data}")
            
            assert "call_stats" in data, "Response does not contain 'call_stats' field"
            assert "operator_stats" in data, "Response does not contain 'operator_stats' field"
            assert "queue_stats" in data, "Response does not contain 'queue_stats' field"
            assert "period" in data, "Response does not contain 'period' field"
            
            print(f"✅ Dashboard stats endpoint test passed with {role} token!")
            return True
        else:
            print(f"Dashboard stats failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Dashboard stats endpoint test failed with {role} token: {str(e)}")
        return False

def test_dashboard_analytics_hourly(role):
    """Test the dashboard hourly analytics endpoint GET /api/dashboard/analytics/hourly"""
    print(f"\n=== Testing GET /api/dashboard/analytics/hourly endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/dashboard/analytics/hourly", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Only admin and manager should have access
        if role in ["admin", "manager"]:
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains hourly_data: {'hourly_data' in data}")
                
                assert "date" in data, "Response does not contain 'date' field"
                assert "hourly_data" in data, "Response does not contain 'hourly_data' field"
                assert "total_calls" in data, "Response does not contain 'total_calls' field"
                
                print(f"✅ Dashboard hourly analytics endpoint test passed with {role} token!")
                return True
            else:
                print(f"Dashboard hourly analytics failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Other roles should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Dashboard hourly analytics endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Dashboard hourly analytics endpoint test failed with {role} token: {str(e)}")
        return False

def test_dashboard_operator_performance(role):
    """Test the dashboard operator performance endpoint GET /api/dashboard/analytics/operator-performance"""
    print(f"\n=== Testing GET /api/dashboard/analytics/operator-performance endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/dashboard/analytics/operator-performance", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Admin, manager, and supervisor should have access
        if role in ["admin", "manager", "supervisor"]:
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains operators: {'operators' in data}")
                
                assert "period" in data, "Response does not contain 'period' field"
                assert "operators" in data, "Response does not contain 'operators' field"
                assert "summary" in data, "Response does not contain 'summary' field"
                
                print(f"✅ Dashboard operator performance endpoint test passed with {role} token!")
                return True
            else:
                print(f"Dashboard operator performance failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Operator should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Dashboard operator performance endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Dashboard operator performance endpoint test failed with {role} token: {str(e)}")
        return False

def test_dashboard_queue_performance(role):
    """Test the dashboard queue performance endpoint GET /api/dashboard/analytics/queue-performance"""
    print(f"\n=== Testing GET /api/dashboard/analytics/queue-performance endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/dashboard/analytics/queue-performance", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Admin and manager should have access
        if role in ["admin", "manager"]:
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains queues: {'queues' in data}")
                
                assert "period" in data, "Response does not contain 'period' field"
                assert "queues" in data, "Response does not contain 'queues' field"
                assert "summary" in data, "Response does not contain 'summary' field"
                
                print(f"✅ Dashboard queue performance endpoint test passed with {role} token!")
                return True
            else:
                print(f"Dashboard queue performance failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Other roles should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Dashboard queue performance endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Dashboard queue performance endpoint test failed with {role} token: {str(e)}")
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
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response contains timestamp: {'timestamp' in data}")
            
            assert "timestamp" in data, "Response does not contain 'timestamp' field"
            assert "asterisk" in data, "Response does not contain 'asterisk' field"
            assert "current_activity" in data, "Response does not contain 'current_activity' field"
            assert "today_summary" in data, "Response does not contain 'today_summary' field"
            
            print(f"✅ Dashboard realtime endpoint test passed with {role} token!")
            return True
        else:
            print(f"Dashboard realtime failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Dashboard realtime endpoint test failed with {role} token: {str(e)}")
        return False

def test_setup_asterisk_scan(role):
    """Test the setup asterisk scan endpoint POST /api/setup/asterisk/scan"""
    print(f"\n=== Testing POST /api/setup/asterisk/scan endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        
        # Test with real Asterisk credentials
        payload = {
            "host": TEST_ASTERISK_HOST,
            "port": TEST_ASTERISK_PORT,
            "username": TEST_ASTERISK_USERNAME,
            "password": TEST_ASTERISK_PASSWORD,
            "protocol": "ARI",
            "enabled": True
        }
        
        # Only admin should have access
        if role == "admin":
            response = requests.post(f"{API_BASE_URL}/setup/asterisk/scan", json=payload, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains success: {'success' in data}")
                
                assert "success" in data, "Response does not contain 'success' field"
                assert "asterisk_info" in data, "Response does not contain 'asterisk_info' field"
                assert "discovered" in data, "Response does not contain 'discovered' field"
                
                print(f"✅ Setup asterisk scan endpoint test passed with {role} token!")
                return True
            else:
                print(f"Setup asterisk scan failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Try to access with non-admin role
            response = requests.post(f"{API_BASE_URL}/setup/asterisk/scan", json=payload, headers=headers)
            # Other roles should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Setup asterisk scan endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Setup asterisk scan endpoint test failed with {role} token: {str(e)}")
        return False

def test_setup_operators_migrate(role):
    """Test the setup operators migrate endpoint POST /api/setup/operators/migrate"""
    print(f"\n=== Testing POST /api/setup/operators/migrate endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        
        # Test with sample migration data
        payload = {
            "extensions": [
                {
                    "extension": "1002",
                    "username": "operator_1002",
                    "name": "Operator 1002",
                    "email": "operator_1002@callcenter.com"
                }
            ],
            "default_group_id": None,
            "default_skills": ["general", "support"]
        }
        
        # Only admin should have access
        if role == "admin":
            response = requests.post(f"{API_BASE_URL}/setup/operators/migrate", json=payload, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains success: {'success' in data}")
                
                assert "success" in data, "Response does not contain 'success' field"
                assert "message" in data, "Response does not contain 'message' field"
                assert "data" in data, "Response does not contain 'data' field"
                
                print(f"✅ Setup operators migrate endpoint test passed with {role} token!")
                return True
            else:
                print(f"Setup operators migrate failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Try to access with non-admin role
            response = requests.post(f"{API_BASE_URL}/setup/operators/migrate", json=payload, headers=headers)
            # Other roles should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Setup operators migrate endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Setup operators migrate endpoint test failed with {role} token: {str(e)}")
        return False

def test_setup_queues_create(role):
    """Test the setup queues create endpoint POST /api/setup/queues/create"""
    print(f"\n=== Testing POST /api/setup/queues/create endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        
        # Test with sample queue data
        payload = {
            "queues": [
                {
                    "name": f"test_queue_{uuid.uuid4().hex[:8]}",
                    "description": "Test Queue",
                    "max_wait_time": 300,
                    "priority": 1
                }
            ]
        }
        
        # Only admin should have access
        if role == "admin":
            response = requests.post(f"{API_BASE_URL}/setup/queues/create", json=payload, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains success: {'success' in data}")
                
                assert "success" in data, "Response does not contain 'success' field"
                assert "message" in data, "Response does not contain 'message' field"
                assert "data" in data, "Response does not contain 'data' field"
                
                print(f"✅ Setup queues create endpoint test passed with {role} token!")
                return True
            else:
                print(f"Setup queues create failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Try to access with non-admin role
            response = requests.post(f"{API_BASE_URL}/setup/queues/create", json=payload, headers=headers)
            # Other roles should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Setup queues create endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Setup queues create endpoint test failed with {role} token: {str(e)}")
        return False

def test_setup_complete(role):
    """Test the setup complete endpoint POST /api/setup/complete"""
    print(f"\n=== Testing POST /api/setup/complete endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        
        # Test with sample setup data
        payload = {
            "asterisk_config": {
                "host": TEST_ASTERISK_HOST,
                "port": TEST_ASTERISK_PORT,
                "username": TEST_ASTERISK_USERNAME,
                "password": TEST_ASTERISK_PASSWORD,
                "protocol": "ARI",
                "enabled": True
            },
            "setup_options": {
                "create_demo_data": False,
                "initialize_queues": True
            }
        }
        
        # Only admin should have access
        if role == "admin":
            response = requests.post(f"{API_BASE_URL}/setup/complete", json=payload, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains success: {'success' in data}")
                
                assert "success" in data, "Response does not contain 'success' field"
                assert "message" in data, "Response does not contain 'message' field"
                assert "data" in data, "Response does not contain 'data' field"
                
                print(f"✅ Setup complete endpoint test passed with {role} token!")
                return True
            else:
                print(f"Setup complete failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Try to access with non-admin role
            response = requests.post(f"{API_BASE_URL}/setup/complete", json=payload, headers=headers)
            # Other roles should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Setup complete endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Setup complete endpoint test failed with {role} token: {str(e)}")
        return False

def test_notifications_settings(role):
    """Test the notifications settings endpoint GET /api/notifications/settings"""
    print(f"\n=== Testing GET /api/notifications/settings endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/notifications/settings", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response contains settings: {'settings' in data}")
            
            assert "success" in data, "Response does not contain 'success' field"
            assert "settings" in data, "Response does not contain 'settings' field"
            assert "version_info" in data, "Response does not contain 'version_info' field"
            
            print(f"✅ Notifications settings endpoint test passed with {role} token!")
            return True
        else:
            print(f"Notifications settings failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Notifications settings endpoint test failed with {role} token: {str(e)}")
        return False

def test_crm_info(role):
    """Test the CRM info endpoint GET /api/crm/info"""
    print(f"\n=== Testing GET /api/crm/info endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/crm/info", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response contains status: {'status' in data}")
            
            assert "status" in data, "Response does not contain 'status' field"
            assert "current_version" in data, "Response does not contain 'current_version' field"
            assert "description" in data, "Response does not contain 'description' field"
            
            print(f"✅ CRM info endpoint test passed with {role} token!")
            return True
        else:
            print(f"CRM info failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ CRM info endpoint test failed with {role} token: {str(e)}")
        return False

def test_crm_demo(role):
    """Test the CRM demo endpoint GET /api/crm/demo"""
    print(f"\n=== Testing GET /api/crm/demo endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/crm/demo", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Only admin should have access
        if role == "admin":
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains demo_mode: {'demo_mode' in data}")
                
                assert "demo_mode" in data, "Response does not contain 'demo_mode' field"
                assert "message" in data, "Response does not contain 'message' field"
                
                print(f"✅ CRM demo endpoint test passed with {role} token!")
                return True
            else:
                print(f"CRM demo failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Other roles should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ CRM demo endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ CRM demo endpoint test failed with {role} token: {str(e)}")
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

def test_admin_asterisk_connection_status(role):
    """Test the admin asterisk connection status endpoint GET /api/admin/asterisk/connection-status"""
    print(f"\n=== Testing GET /api/admin/asterisk/connection-status endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        response = requests.get(f"{API_BASE_URL}/admin/asterisk/connection-status", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Admin should have access
        if role == "admin":
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains connected: {'connected' in data}")
                
                assert "connected" in data, "Response does not contain 'connected' field"
                assert "status" in data, "Response does not contain 'status' field"
                assert "last_check" in data, "Response does not contain 'last_check' field"
                
                print(f"✅ Admin asterisk connection status endpoint test passed with {role} token!")
                return True
            else:
                print(f"Admin asterisk connection status failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Other roles should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Admin asterisk connection status endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Admin asterisk connection status endpoint test failed with {role} token: {str(e)}")
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
            assert "database" in response.json(), "Response does not contain 'database' field"
            assert "asterisk" in response.json(), "Response does not contain 'asterisk' field"
            assert "api" in response.json(), "Response does not contain 'api' field"
            assert "system" in response.json(), "Response does not contain 'system' field"
            
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

def test_update_operator(role):
    """Test updating operator information PUT /api/admin/users/{user_id}/operator"""
    print(f"\n=== Testing PUT /api/admin/users/{{user_id}}/operator endpoint with {role} token ===")
    try:
        if role not in auth_tokens:
            print(f"❌ No token available for {role} role")
            return False
            
        if not operator_user_id:
            print("❌ No operator user ID available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens[role]}"}
        
        # Only admin should have access
        if role == "admin":
            # Update operator data
            payload = {
                "extension": TEST_OPERATOR_EXTENSION,
                "skills": ["general", "support", "sales"],
                "max_concurrent_calls": 2
            }
            
            response = requests.put(f"{API_BASE_URL}/admin/users/{operator_user_id}/operator", json=payload, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains success: {'success' in data}")
                
                assert "success" in data, "Response does not contain 'success' field"
                assert "message" in data, "Response does not contain 'message' field"
                assert data["success"] == True, "Update was not successful"
                
                print("✅ Update operator endpoint test passed!")
                return True
            else:
                print(f"Update operator failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            # Try to access with non-admin role
            payload = {"extension": TEST_OPERATOR_EXTENSION}
            response = requests.put(f"{API_BASE_URL}/admin/users/{operator_user_id}/operator", json=payload, headers=headers)
            # Other roles should get 403 Forbidden
            assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
            print(f"✅ Update operator endpoint correctly denied access to {role} role!")
            return True
    except Exception as e:
        print(f"❌ Update operator endpoint test failed: {str(e)}")
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

def test_websocket_connection():
    """Test WebSocket connection /ws/connect"""
    print("\n=== Testing WebSocket connection /ws/connect ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        token = auth_tokens["admin"]
        ws_url = f"{BACKEND_URL.replace('https://', 'wss://')}/ws/connect?token={token}"
        
        # Define WebSocket callbacks
        def on_message(ws, message):
            print(f"WebSocket message received: {message[:100]}...")
            
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket closed: {close_status_code} - {close_msg}")
            
        def on_open(ws):
            print("WebSocket connection opened")
            # Send a ping message
            ws.send(json.dumps({"type": "ping"}))
            
        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Start WebSocket connection in a separate thread
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Wait for a short time to allow connection
        time.sleep(2)
        
        # Close the connection
        ws.close()
        
        print("✅ WebSocket connection test completed!")
        return True
    except Exception as e:
        print(f"❌ WebSocket connection test failed: {str(e)}")
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

def test_asterisk_connection():
    """Test connection to Asterisk server"""
    print("\n=== Testing POST /api/admin/settings/asterisk/test endpoint ===")
    try:
        if "admin" not in auth_tokens:
            print("❌ No admin token available")
            return False
            
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Test connection to real Asterisk
        payload = {
            "host": TEST_ASTERISK_HOST,
            "port": TEST_ASTERISK_PORT,
            "username": TEST_ASTERISK_USERNAME,
            "password": TEST_ASTERISK_PASSWORD,
            "protocol": "ARI",
            "enabled": True
        }
        
        response = requests.post(f"{API_BASE_URL}/admin/settings/asterisk/test", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            assert "success" in response.json(), "Response does not contain 'success' field"
            assert "message" in response.json(), "Response does not contain 'message' field"
            assert "data" in response.json(), "Response does not contain 'data' field"
            
            print("✅ Asterisk connection test passed!")
            return True
        else:
            print(f"Asterisk connection test failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Asterisk connection test failed: {str(e)}")
        return False

def run_dashboard_tests():
    """Run tests for dashboard endpoints"""
    print("\n=== Running dashboard endpoints tests ===")
    
    # Test admin login
    admin_login_result = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD, "admin")
    
    if not admin_login_result:
        print("❌ Skipping dashboard tests because admin login failed")
        return False
    
    # Test dashboard stats
    dashboard_stats_result = test_dashboard_stats("admin")
    
    # Test dashboard analytics hourly
    dashboard_hourly_result = test_dashboard_analytics_hourly("admin")
    
    # Test dashboard operator performance
    operator_performance_result = test_dashboard_operator_performance("admin")
    
    # Test dashboard queue performance
    queue_performance_result = test_dashboard_queue_performance("admin")
    
    # Test dashboard realtime
    realtime_result = test_dashboard_realtime("admin")
    
    # Print test summary
    print("\n=== Dashboard Endpoints Test Summary ===")
    print(f"Dashboard Stats: {'✅ PASSED' if dashboard_stats_result else '❌ FAILED'}")
    print(f"Dashboard Analytics Hourly: {'✅ PASSED' if dashboard_hourly_result else '❌ FAILED'}")
    print(f"Operator Performance: {'✅ PASSED' if operator_performance_result else '❌ FAILED'}")
    print(f"Queue Performance: {'✅ PASSED' if queue_performance_result else '❌ FAILED'}")
    print(f"Dashboard Realtime: {'✅ PASSED' if realtime_result else '❌ FAILED'}")
    
    all_passed = all([
        dashboard_stats_result,
        dashboard_hourly_result,
        operator_performance_result,
        queue_performance_result,
        realtime_result
    ])
    
    if all_passed:
        print("\n🎉 All dashboard endpoints tests passed successfully!")
    else:
        print("\n⚠️ Some dashboard endpoints tests failed. See details above.")
    
    return all_passed

def run_setup_wizard_tests():
    """Run tests for setup wizard endpoints"""
    print("\n=== Running setup wizard endpoints tests ===")
    
    # Test admin login if not already logged in
    if "admin" not in auth_tokens:
        admin_login_result = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD, "admin")
        if not admin_login_result:
            print("❌ Skipping setup wizard tests because admin login failed")
            return False
    
    # Test setup asterisk scan
    asterisk_scan_result = test_setup_asterisk_scan("admin")
    
    # Test setup operators migrate
    operators_migrate_result = test_setup_operators_migrate("admin")
    
    # Test setup queues create
    queues_create_result = test_setup_queues_create("admin")
    
    # Test setup complete
    setup_complete_result = test_setup_complete("admin")
    
    # Print test summary
    print("\n=== Setup Wizard Endpoints Test Summary ===")
    print(f"Asterisk Scan: {'✅ PASSED' if asterisk_scan_result else '❌ FAILED'}")
    print(f"Operators Migrate: {'✅ PASSED' if operators_migrate_result else '❌ FAILED'}")
    print(f"Queues Create: {'✅ PASSED' if queues_create_result else '❌ FAILED'}")
    print(f"Setup Complete: {'✅ PASSED' if setup_complete_result else '❌ FAILED'}")
    
    all_passed = all([
        asterisk_scan_result,
        operators_migrate_result,
        queues_create_result,
        setup_complete_result
    ])
    
    if all_passed:
        print("\n🎉 All setup wizard endpoints tests passed successfully!")
    else:
        print("\n⚠️ Some setup wizard endpoints tests failed. See details above.")
    
    return all_passed

def run_notification_crm_tests():
    """Run tests for notification and CRM endpoints"""
    print("\n=== Running notification and CRM endpoints tests ===")
    
    # Test admin login if not already logged in
    if "admin" not in auth_tokens:
        admin_login_result = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD, "admin")
        if not admin_login_result:
            print("❌ Skipping notification and CRM tests because admin login failed")
            return False
    
    # Test notifications settings
    notifications_settings_result = test_notifications_settings("admin")
    
    # Test CRM info
    crm_info_result = test_crm_info("admin")
    
    # Test CRM demo
    crm_demo_result = test_crm_demo("admin")
    
    # Print test summary
    print("\n=== Notification and CRM Endpoints Test Summary ===")
    print(f"Notifications Settings: {'✅ PASSED' if notifications_settings_result else '❌ FAILED'}")
    print(f"CRM Info: {'✅ PASSED' if crm_info_result else '❌ FAILED'}")
    print(f"CRM Demo: {'✅ PASSED' if crm_demo_result else '❌ FAILED'}")
    
    all_passed = all([
        notifications_settings_result,
        crm_info_result,
        crm_demo_result
    ])
    
    if all_passed:
        print("\n🎉 All notification and CRM endpoints tests passed successfully!")
    else:
        print("\n⚠️ Some notification and CRM endpoints tests failed. See details above.")
    
    return all_passed

def run_admin_panel_tests():
    """Run tests for improved admin panel endpoints"""
    print("\n=== Running improved admin panel endpoints tests ===")
    
    # Test admin login if not already logged in
    if "admin" not in auth_tokens:
        admin_login_result = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD, "admin")
        if not admin_login_result:
            print("❌ Skipping admin panel tests because admin login failed")
            return False
    
    # Test create operator
    create_operator_result = test_create_operator()
    
    # Test update operator
    if create_operator_result:
        update_operator_result = test_update_operator("admin")
    else:
        update_operator_result = False
        print("❌ Skipping update operator test because create operator failed")
    
    # Test asterisk connection status
    asterisk_status_result = test_admin_asterisk_connection_status("admin")
    
    # Test system info
    system_info_result = test_admin_system_info("admin")
    
    # Print test summary
    print("\n=== Admin Panel Endpoints Test Summary ===")
    print(f"Create Operator: {'✅ PASSED' if create_operator_result else '❌ FAILED'}")
    print(f"Update Operator: {'✅ PASSED' if update_operator_result else '❌ FAILED'}")
    print(f"Asterisk Connection Status: {'✅ PASSED' if asterisk_status_result else '❌ FAILED'}")
    print(f"System Info: {'✅ PASSED' if system_info_result else '❌ FAILED'}")
    
    all_passed = all([
        create_operator_result,
        update_operator_result,
        asterisk_status_result,
        system_info_result
    ])
    
    if all_passed:
        print("\n🎉 All admin panel endpoints tests passed successfully!")
    else:
        print("\n⚠️ Some admin panel endpoints tests failed. See details above.")
    
    return all_passed

def test_websocket():
    """Run WebSocket connection test"""
    print("\n=== Running WebSocket connection test ===")
    
    # Test admin login if not already logged in
    if "admin" not in auth_tokens:
        admin_login_result = test_auth_login(TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD, "admin")
        if not admin_login_result:
            print("❌ Skipping WebSocket test because admin login failed")
            return False
    
    # Test WebSocket connection
    websocket_result = test_websocket_connection()
    
    # Print test summary
    print("\n=== WebSocket Test Summary ===")
    print(f"WebSocket Connection: {'✅ PASSED' if websocket_result else '❌ FAILED'}")
    
    return websocket_result

def run_all_tests():
    """Run all tests and return overall result"""
    print("\n=== Running all backend API tests ===")
    
    # Test basic endpoints
    root_result = test_root_endpoint()
    health_result = test_health_endpoint()
    
    # Run dashboard tests
    dashboard_result = run_dashboard_tests()
    
    # Run setup wizard tests
    setup_result = run_setup_wizard_tests()
    
    # Run notification and CRM tests
    notification_crm_result = run_notification_crm_tests()
    
    # Run admin panel tests
    admin_result = run_admin_panel_tests()
    
    # Run WebSocket test
    websocket_result = test_websocket()
    
    # Check server logs
    logs_result = check_server_logs()
    
    # Print overall test summary
    print("\n=== Overall Test Summary ===")
    print(f"Basic Endpoints: {'✅ PASSED' if root_result and health_result else '❌ FAILED'}")
    print(f"Dashboard Endpoints: {'✅ PASSED' if dashboard_result else '❌ FAILED'}")
    print(f"Setup Wizard Endpoints: {'✅ PASSED' if setup_result else '❌ FAILED'}")
    print(f"Notification and CRM Endpoints: {'✅ PASSED' if notification_crm_result else '❌ FAILED'}")
    print(f"Admin Panel Endpoints: {'✅ PASSED' if admin_result else '❌ FAILED'}")
    print(f"WebSocket Connection: {'✅ PASSED' if websocket_result else '❌ FAILED'}")
    print(f"Server Logs Check: {'✅ PASSED' if logs_result else '⚠️ WARNINGS'}")
    
    all_passed = all([
        root_result,
        health_result,
        dashboard_result,
        setup_result,
        notification_crm_result,
        admin_result,
        websocket_result
    ])
    
    if all_passed:
        print("\n🎉 All backend API tests passed successfully!")
    else:
        print("\n⚠️ Some backend API tests failed. See details above.")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()