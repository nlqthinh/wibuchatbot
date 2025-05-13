import requests
from config import JINA_API_KEY

url = 'https://fptshop.com.vn/tin-tuc/danh-gia/kham-pha-web-phim-anime-hay-nhat-danh-cho-tin-do-anime-166165'
headers = {
    'Authorization':  f'Bearer {JINA_API_KEY}'
}

response = requests.get(url, headers=headers, verify=False)
print(response.text)
