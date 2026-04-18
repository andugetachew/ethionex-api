import requests

# Login
login = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"username": "testuser", "password": "testpass123"},
)

token = login.json()["access"]
headers = {"Authorization": f"Bearer {token}"}

# Clear wishlist
response = requests.delete("http://127.0.0.1:8000/api/wishlist/clear/", headers=headers)
print(response.json()["message"])
