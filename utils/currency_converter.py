import requests
import google_currency as converter #pip install google-currency
import json

def convert_to_usd(primary, amount):
    
    data = json.loads(converter.convert(primary, "USD", amount))
    
    return round(float(data["amount"]),2)

def convert_currency(primary, secondary, amount):
    
    data = json.loads(converter.convert(primary, secondary, amount))
    
    return round(float(data["amount"]), 2)

print(convert_currency("USD","KGS", 6.0))