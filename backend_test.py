import requests
import sys
import json
import time
from datetime import datetime

class CodeReviewAPITester:
    def __init__(self, base_url="https://review-boost-10.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.review_id = None
        self.auth_token = None
        self.test_user_email = f"test_{int(time.time())}@codemind.ai"

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, use_auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Add auth header if requested and token available
        if use_auth and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        if use_auth:
            print(f"Using auth: {'Yes' if self.auth_token else 'No token available'}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, files=files, headers=headers, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=60)

            print(f"Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {error_detail}")
                except:
                    print(f"Error text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_auth_signup(self):
        """Test user signup"""
        signup_data = {
            "email": self.test_user_email,
            "password": "testpass123",
            "name": "Test User"
        }
        
        success, response = self.run_test(
            "User Signup",
            "POST",
            "auth/signup",
            200,
            data=signup_data
        )
        
        if success and isinstance(response, dict):
            if 'access_token' in response:
                self.auth_token = response['access_token']
                print(f"✅ Signup successful, token received")
                return True
            else:
                print(f"❌ Signup response missing access_token")
                return False
        
        return success

    def test_auth_login(self):
        """Test user login"""
        login_data = {
            "email": self.test_user_email,
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and isinstance(response, dict):
            if 'access_token' in response:
                self.auth_token = response['access_token']
                print(f"✅ Login successful, token received")
                return True
            else:
                print(f"❌ Login response missing access_token")
                return False
        
        return success

    def test_auth_me(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200,
            use_auth=True
        )
        
        if success and isinstance(response, dict):
            expected_fields = ['id', 'email', 'name', 'created_at']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if missing_fields:
                print(f"❌ Missing user fields: {missing_fields}")
                return False
            
            if response.get('email') == self.test_user_email:
                print(f"✅ User info correct: {response.get('name')} ({response.get('email')})")
                return True
            else:
                print(f"❌ Email mismatch: expected {self.test_user_email}, got {response.get('email')}")
                return False
        
        return success

    def test_auth_invalid_login(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }
        
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,  # Unauthorized expected
            data=login_data
        )
        
        return success

    def test_auth_duplicate_signup(self):
        """Test signup with existing email"""
        signup_data = {
            "email": self.test_user_email,  # Same email as before
            "password": "testpass123",
            "name": "Duplicate User"
        }
        
        success, response = self.run_test(
            "Duplicate Email Signup",
            "POST",
            "auth/signup",
            400,  # Bad request expected
            data=signup_data
        )
        
        return success

    def test_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication"""
        # Temporarily clear token
        original_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test(
            "Protected Endpoint Without Auth",
            "GET",
            "auth/me",
            401,  # Unauthorized expected
            use_auth=True
        )
        
        # Restore token
        self.auth_token = original_token
        return success
    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_code_review_authenticated(self):
        """Test code review endpoint with authentication"""
        sample_code = '''var password = "admin123";
function getData() {
    for (var i = 0; i < 10000; i++) {
        console.log(i);
    }
}'''
        
        success, response = self.run_test(
            "Code Review (Authenticated)",
            "POST",
            "review",
            200,
            data={
                "code": sample_code,
                "language": "javascript",
                "filename": "test.js"
            },
            use_auth=True
        )
        
        if success and isinstance(response, dict):
            # Validate response structure
            required_fields = ['id', 'overall_score', 'quality_score', 'security_score', 
                             'performance_score', 'issues', 'summary', 'recommendations']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            # Store review ID for later tests
            self.review_id = response.get('id')
            print(f"✅ Review created with ID: {self.review_id}")
            print(f"Overall Score: {response.get('overall_score')}")
            print(f"Issues found: {len(response.get('issues', []))}")
            
            # Check if user_id is set for authenticated user
            if response.get('user_id'):
                print(f"✅ Review associated with user: {response.get('user_id')}")
            else:
                print("⚠️ Review not associated with user (user_id missing)")
            
            return True
        
        return success

    def test_file_upload_review(self):
        """Test file upload and review"""
        # Create a temporary Python file
        test_code = '''import os
import subprocess

def unsafe_function(user_input):
    # Security vulnerability: command injection
    result = subprocess.run(f"echo {user_input}", shell=True)
    return result

# Performance issue: inefficient loop
data = []
for i in range(10000):
    data.append(str(i))
    data = data  # Redundant assignment
'''
        
        files = {
            'file': ('test_security.py', test_code, 'text/plain')
        }
        
        success, response = self.run_test(
            "File Upload Review",
            "POST",
            "upload-review",
            200,
            files=files
        )
        
        if success and isinstance(response, dict):
            print(f"✅ File upload review completed")
            print(f"Filename: {response.get('filename')}")
            print(f"Language: {response.get('language')}")
            return True
        
        return success

    def test_history_authenticated(self):
        """Test history endpoint with authentication (should show user's reviews only)"""
        success, response = self.run_test(
            "Review History (Authenticated)",
            "GET",
            "history",
            200,
            use_auth=True
        )
        
        if success and isinstance(response, list):
            print(f"✅ Authenticated history retrieved: {len(response)} reviews")
            if len(response) > 0:
                print(f"Latest review: {response[0].get('filename', 'No filename')}")
                # Check if this is the user's review
                if self.review_id and any(r.get('id') == self.review_id for r in response):
                    print(f"✅ User's review found in history")
                else:
                    print("⚠️ User's review not found in history")
            return True
        
        return success

    def test_history_anonymous(self):
        """Test history endpoint without authentication (should show all reviews)"""
        # Temporarily clear token
        original_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test(
            "Review History (Anonymous)",
            "GET",
            "history",
            200
        )
        
        # Restore token
        self.auth_token = original_token
        
        if success and isinstance(response, list):
            print(f"✅ Anonymous history retrieved: {len(response)} reviews")
            return True
        
        return success

    def test_get_review_by_id(self):
        """Test getting specific review by ID"""
        if not self.review_id:
            print("⚠️ Skipping review by ID test - no review ID available")
            return True
        
        success, response = self.run_test(
            "Get Review by ID",
            "GET",
            f"review/{self.review_id}",
            200
        )
        
        if success and isinstance(response, dict):
            print(f"✅ Review retrieved by ID: {response.get('filename', 'No filename')}")
            return True
        
        return success

    def test_user_stats(self):
        """Test user statistics endpoint"""
        success, response = self.run_test(
            "User Statistics",
            "GET",
            "auth/stats",
            200,
            use_auth=True
        )
        
        if success and isinstance(response, dict):
            expected_fields = ['total_reviews', 'average_score', 'languages_used', 'recent_activity', 'score_trend']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if missing_fields:
                print(f"❌ Missing stats fields: {missing_fields}")
                return False
            
            print(f"✅ User stats retrieved:")
            print(f"  Total Reviews: {response.get('total_reviews')}")
            print(f"  Average Score: {response.get('average_score')}")
            print(f"  Languages Used: {len(response.get('languages_used', []))}")
            print(f"  Recent Activity: {len(response.get('recent_activity', []))}")
            print(f"  Score Trend: {len(response.get('score_trend', []))}")
            
            return True
        
        return success

    def test_resend_verification(self):
        """Test resending email verification"""
        success, response = self.run_test(
            "Resend Email Verification",
            "POST",
            "auth/resend-verification",
            200,
            use_auth=True
        )
        
        if success and isinstance(response, dict):
            if 'message' in response:
                print(f"✅ Verification resend response: {response.get('message')}")
                return True
            else:
                print(f"❌ Missing message in verification response")
                return False
        
        return success

    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token"""
        success, response = self.run_test(
            "Email Verification (Invalid Token)",
            "GET",
            "auth/verify/invalid-token-123",
            404  # Not found expected
        )
        
        return success

    def test_code_review_with_retry_logic(self):
        """Test code review with complex code to trigger retry logic"""
        complex_code = '''const apiKey = "secret123";
function process(data) {
    for (let i = 0; i < 100000; i++) {
        console.log(data[i]);
    }
}

// Security issues
eval("console.log('dangerous')");
document.write("<script>alert('xss')</script>");

// Performance issues
let result = "";
for (let i = 0; i < 10000; i++) {
    result += i.toString();
}

// Quality issues
var x = 1;
var y = 2;
if (x == y) {
    console.log("equal");
}'''
        
        success, response = self.run_test(
            "Code Review with Retry Logic",
            "POST",
            "review",
            200,
            data={
                "code": complex_code,
                "language": "javascript",
                "filename": "complex_test.js"
            },
            use_auth=True
        )
        
        if success and isinstance(response, dict):
            print(f"✅ Complex code review completed")
            print(f"Overall Score: {response.get('overall_score')}")
            print(f"Security Score: {response.get('security_score')}")
            print(f"Performance Score: {response.get('performance_score')}")
            print(f"Quality Score: {response.get('quality_score')}")
            print(f"Issues found: {len(response.get('issues', []))}")
            
            # Check for fallback response indicators
            summary = response.get('summary', '')
            if 'temporarily unavailable' in summary.lower() or 'timeout' in summary.lower():
                print("⚠️ Fallback response detected - AI service may have timed out")
            else:
                print("✅ Full AI analysis completed successfully")
            
            return True
        
        return success

    def test_error_handling(self):
        """Test error handling with invalid requests"""
        print("\n🔍 Testing Error Handling...")
        
        # Test empty code
        success, _ = self.run_test(
            "Empty Code Error",
            "POST",
            "review",
            422,  # Validation error expected
            data={"code": "", "language": "python"}
        )
        
        # Test invalid review ID
        success2, _ = self.run_test(
            "Invalid Review ID",
            "GET",
            "review/invalid-id-123",
            404
        )
        
        return success or success2  # At least one error handling test should pass

def main():
    print("🚀 Starting CodeMind AI Backend API Tests")
    print("=" * 50)
    
    tester = CodeReviewAPITester()
    
    # Run all tests in order
    tests = [
        ("Basic API", tester.test_root_endpoint),
        ("Auth - Signup", tester.test_auth_signup),
        ("Auth - Login", tester.test_auth_login),
        ("Auth - Get User Info", tester.test_auth_me),
        ("Auth - Invalid Login", tester.test_auth_invalid_login),
        ("Auth - Duplicate Signup", tester.test_auth_duplicate_signup),
        ("Auth - Protected Without Token", tester.test_protected_endpoint_without_auth),
        ("Auth - Resend Verification", tester.test_resend_verification),
        ("Auth - Invalid Email Verification", tester.test_verify_email_invalid_token),
        ("Code Review (Authenticated)", tester.test_code_review_authenticated),
        ("Code Review with Retry Logic", tester.test_code_review_with_retry_logic),
        ("File Upload Review", tester.test_file_upload_review),
        ("User Statistics", tester.test_user_stats),
        ("History (Authenticated)", tester.test_history_authenticated),
        ("History (Anonymous)", tester.test_history_anonymous),
        ("Get Review by ID", tester.test_get_review_by_id),
        ("Error Handling", tester.test_error_handling)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            test_func()
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
