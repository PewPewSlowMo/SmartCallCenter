#!/usr/bin/env python3
import requests
import json
import os
import sys
from dotenv import load_dotenv
import time

# Load environment variables from frontend/.env
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

API_BASE_URL = f"{BACKEND_URL}/api"
print(f"Testing API at: {API_BASE_URL}")

def test_root_endpoint():
    """Test the root endpoint GET /api/"""
    print("\n=== Testing GET /api/ endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert response.json() == {"message": "Hello World"}, "Response does not match expected output"
        
        print("✅ Root endpoint test passed!")
        return True
    except Exception as e:
        print(f"❌ Root endpoint test failed: {str(e)}")
        return False

def test_create_status():
    """Test the POST /api/status endpoint"""
    print("\n=== Testing POST /api/status endpoint ===")
    try:
        payload = {"client_name": "Test Client"}
        response = requests.post(f"{API_BASE_URL}/status", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "id" in response.json(), "Response does not contain 'id' field"
        assert response.json()["client_name"] == "Test Client", "client_name does not match input"
        assert "timestamp" in response.json(), "Response does not contain 'timestamp' field"
        
        print("✅ Create status test passed!")
        return True
    except Exception as e:
        print(f"❌ Create status test failed: {str(e)}")
        return False

def test_get_status():
    """Test the GET /api/status endpoint"""
    print("\n=== Testing GET /api/status endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response contains {len(response.json())} status records")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert isinstance(response.json(), list), "Response is not a list"
        
        # If we have records, check the structure of the first one
        if len(response.json()) > 0:
            first_record = response.json()[0]
            assert "id" in first_record, "Status record does not contain 'id' field"
            assert "client_name" in first_record, "Status record does not contain 'client_name' field"
            assert "timestamp" in first_record, "Status record does not contain 'timestamp' field"
        
        print("✅ Get status test passed!")
        return True
    except Exception as e:
        print(f"❌ Get status test failed: {str(e)}")
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

def run_all_tests():
    """Run all tests and return overall result"""
    print("\n=== Running all backend API tests ===")
    
    results = {
        "root_endpoint": test_root_endpoint(),
        "create_status": test_create_status(),
        "get_status": test_get_status(),
        "cors": test_cors(),
        "server_logs": check_server_logs()
    }
    
    print("\n=== Test Summary ===")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed successfully!")
    else:
        print("\n⚠️ Some tests failed. See details above.")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()