from pprint import pprint
from func import get_symbol, get_stock_price
#test
nvidia_symbol = get_symbol('Nvidia')
print(f"Nvidia stock symbol is {nvidia_symbol}")

pprint(get_stock_price(nvidia_symbol))