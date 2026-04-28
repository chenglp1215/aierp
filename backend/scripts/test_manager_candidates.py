import requests

login_resp = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
print('Login status:', login_resp.status_code)
if login_resp.status_code == 200:
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    resp = requests.get('http://localhost:8000/api/v1/warehouses/manager-candidates', headers=headers)
    print('API status:', resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print('Candidates:', data)
    else:
        print('Error:', resp.text)
