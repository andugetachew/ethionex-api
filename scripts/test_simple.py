import requests

# Login
login = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"username": "testuser", "password": "testpass123"},
)
print("Login status:", login.status_code)

if login.status_code == 200:
    token = login.json()["access"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test dashboard
    dashboard = requests.get(
        "http://127.0.0.1:8000/api/seller/dashboard/", headers=headers
    )
    print("Dashboard status:", dashboard.status_code)
    print("Dashboard text:", dashboard.text)
