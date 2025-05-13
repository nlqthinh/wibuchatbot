import requests
from config import JINA_API_KEY

url = 'https://maxflowtech.com/'
headers = {
    'Authorization':  f'Bearer {JINA_API_KEY}'
}

response = requests.get(url, headers=headers, verify=False)
print(response.text)
