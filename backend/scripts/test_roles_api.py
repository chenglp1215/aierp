import requests

login_resp = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
print('Login status:', login_resp.status_code)
if login_resp.status_code == 200:
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    roles_resp = requests.get('http://localhost:8000/api/v1/auth/roles/', headers=headers)
    print('Roles status:', roles_resp.status_code)
    if roles_resp.status_code == 200:
        data = roles_resp.json()
        print('Total roles:', data.get('total'))
        for item in data.get('items', []):
            print(f"  {item.get('name')} - is_fixed: {item.get('is_fixed')}")
    else:
        print('Error:', roles_resp.text)
