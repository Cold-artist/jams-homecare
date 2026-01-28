import requests
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:8000"
USER_EMAIL = "verify@test.com"
USER_PASS = "test1234"

s = requests.Session()

# 1. Register/Login
print("1. Registering/Logging in...")
reg_data = {
    'name': 'Verify User',
    'email': USER_EMAIL,
    'mobile': '9999999999',
    'password': USER_PASS,
    'submit': 'Create Account'
}

# Try registering
r = s.post(f"{BASE_URL}/register", data=reg_data)

# If already registered, login
if "Email already registered" in r.text or r.url == f"{BASE_URL}/register":
    print("   User exists, logging in...")
    login_data = {
        'email': USER_EMAIL,
        'password': USER_PASS,
        'submit': 'Login'
    }
    r = s.post(f"{BASE_URL}/login", data=login_data)

# 2. Submit Booking with Online Payment
print("2. Submitting Booking (Online Payment)...")
# First get CSRF token
r = s.get(f"{BASE_URL}/book-home-visit")
soup = BeautifulSoup(r.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

booking_data = {
    'csrf_token': csrf_token,
    'patient_name': 'Test Patient',
    'age': '45',
    'mobile': '9876543210',
    'email': USER_EMAIL,
    'address': 'Cyber City',
    'area': 'Haldwani',
    'service_type': 'medical_care',
    'preferred_date': '2025-12-31',
    'preferred_time': '10:00',
    'payment_method': 'online' # CRITICAL
}

r = s.post(f"{BASE_URL}/book-home-visit", data=booking_data, allow_redirects=False)

# 3. Verify Redirect
if r.status_code == 302 and '/payment/' in r.headers['Location']:
    payment_url = r.headers['Location']
    print(f"SUCCESS: Redirected to {payment_url}")
    
    # Extract Booking ID from URL
    booking_id = payment_url.split('/')[-1]
    
    # Check Payment Page
    r = s.get(BASE_URL + payment_url)
    if "Select Payment Method" in r.text and "Secure Checkout" in r.text:
       print("SUCCESS: Payment page loaded.")
       
       # 4. Simulate Payment Success (POST to Verify)
       verify_url = f"{BASE_URL}/payment/verify?booking_id={booking_id}"
       print(f"4. Simulating Payment Check to {verify_url}...")
       
       verify_data = {
           'razorpay_order_id': 'order_mock_test123',
           'razorpay_payment_id': 'pay_mock_test123',
           'razorpay_signature': 'mock_sig'
       }
       r = s.post(verify_url, data=verify_data)
       
       if r.status_code == 200 and "Payment Successful!" in r.text and "Receipt" in r.text:
           print("SUCCESS: Payment Verified & Premium Receipt Page Loaded!")
       elif r.status_code == 302 and "/payment/success/" in r.headers.get('Location', ''):
            print("SUCCESS: Payment Verified & Redirected to Success Page!")
       else:
           print(f"FAILURE: Verify Route returned {r.status_code}")
           # print(r.text[:200])

    else:
       print("FAILURE: Payment page content missing.")
else:
    print(f"FAILURE: No redirect. Status: {r.status_code}")
    print(r.text[:500])
