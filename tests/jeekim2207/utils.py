import requests

ROOT_URL = "http://localhost:8090"

def post_auth_token():
    url_path = "/api/v1/auth"
    url = ROOT_URL + url_path
    payload='email=guest%40lomin.ai&password=123456'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    token = None
    if response.status_code == 201:
        token = response.json().get("access_token")
    return token


# reqeust post upload file
def post_upload_file(file_path: str, token: str):
    url_path = "/api/v1/docx"
    url = ROOT_URL + url_path
    print(file_path)
    print(token)
    
    document_id = None
    with open(file_path, "rb") as f:
        response = requests.post(
            url,
            headers={"accept": f"application/json", "Authorization": f"Bearer {token}"},
            files={"file": f},
        )
        print(response.status_code)
        if response.status_code == 200:
            document_id = response.json().get("document_id")
        else:
            print(f"request error: {response.status_code} {response.json()}")

    return document_id