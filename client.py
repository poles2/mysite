import requests
import json

# TwÛj dedykowany klucz API
API_KEY = "a742e206b29653abe4d4188d9056ad36"

# Endpoint lokalny (moøesz pÛüniej podmieniÊ na zewnÍtrzny, gdy znasz poprawny adres)
API_URL = "http://127.0.0.1:3000/api/v1/balance"

def check_lightning_faucet():
    print("[*] £πczenie z Lightning Faucet przy uøyciu Twojego klucza API...")
    
    payload = {
        "api_key": API_KEY
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        response = requests.post(API_URL, data=payload, headers=headers, timeout=10)
        
        print(f"[+] Status HTTP: {response.status_code}")
        
        # PrÛba odczytu odpowiedzi jako JSON
        try:
            result = response.json()
            print("\n--- ODPOWIEDè Z API ---")
            print(json.dumps(result, indent=4))
        except json.JSONDecodeError:
            print("\n--- SUROWA TREå∆ ODPOWIEDZI ---")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"[!] B≥πd po≥πczenia sieciowego: {e}")

if __name__ == "__main__":
    check_lightning_faucet()
