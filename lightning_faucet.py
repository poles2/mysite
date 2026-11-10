import requests
import json
import time
import random
from datetime import datetime, timedelta

# --- KONFIGURACJA UŻYTKOWNIKA ---
API_KEY = "a742e206b29653abe4d4188d9056ad36"
LIGHTNING_ADDRESS = "piotr12@speed.app"  # Twój domyślny portfel

# Endpointy
BALANCE_URL = "https://lightningfaucet.com/api/v1/balance"
CLAIM_URL = "https://lightningfaucet.com/api/v1/claim"

LOG_FILE = "faucet_history.txt"

# --- USTAWIENIA CZASOWE I ANTYBOTOWE ---
CHECK_INTERVAL_HOURS = 1.0  # Jak często sprawdzać saldo (w godzinach)
MAX_RETRIES = 5             # Liczba prób w razie błędu sieciowego
MIN_WAIT = 7                # Minimalny losowy czas przerwy (sekundy)
MAX_WAIT = 18               # Maksymalny losowy czas przerwy (sekundy)

# Pula nagłówków do rotacji User-Agent
MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/24.0 Chrome/117.0.5938.60 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 14; Mobile; rv:123.0) Gecko/123.0 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

def write_log(message):
    """Zapisuje zdarzenie z datą i godziną do pliku logów"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def execute_claim(balance_amount):
    """Wysyła żądanie odebrania środków (claim) z zaawansowanym logowaniem błędów API"""
    payload = {
        "api_key": API_KEY,
        "wallet": LIGHTNING_ADDRESS,
        "amount": balance_amount
    }
    
    chosen_ua = random.choice(MOBILE_USER_AGENTS)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": chosen_ua
    }
    
    try:
        print(f"    [*] Zlecam wypłatę {balance_amount} sat na domyślny portfel: {LIGHTNING_ADDRESS}...")
        response = requests.post(CLAIM_URL, data=payload, headers=headers, timeout=10)
        
        # Bezpieczna próba odczytu odpowiedzi jako JSON (nawet przy kodzie błędnym np. 400)
        try:
            resp_data = response.json()
        except json.JSONDecodeError:
            resp_data = response.text
        
        if response.status_code == 200:
            msg = f"WYPŁATA NA {LIGHTNING_ADDRESS} UDANA! Odpowiedź: {json.dumps(resp_data)}"
            print(f"    [+] {msg}")
            write_log(msg)
            return True
        else:
            # Szczegółowy log błędu zwrotnego z serwera (np. brakujący parametr lub zły format portfela)
            err_msg = f"ODRZUCONO WYPŁATĘ (HTTP {response.status_code}). Szczegóły serwera: {resp_data}"
            print(f"    [!] {err_msg}")
            write_log(err_msg)
            
    except Exception as e:
        err_msg = f"Wyjątek krytyczny podczas wysyłania żądania wypłaty: {e}"
        print(f"    [!] {err_msg}")
        write_log(err_msg)
        
    return False

def perform_check_and_claim():
    payload = {"api_key": API_KEY}
    attempt = 1
    
    while attempt <= MAX_RETRIES:
        chosen_ua = random.choice(MOBILE_USER_AGENTS)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": chosen_ua
        }
        
        try:
            response = requests.post(BALANCE_URL, data=payload, headers=headers, timeout=10)
            
            if response.status_code == 200 and "application/json" in response.headers.get("Content-Type", ""):
                data = response.json()
                print(f"    [+] Odczyt salda OK: {data}")
                write_log(f"Odczyt salda OK: {json.dumps(data)}")
                
                balance = int(data.get("balance", 0))
                
                if balance >= 1:
                    execute_claim(balance)
                else:
                    print("    [*] Saldo wynosi 0, brak środków do odebrania.")
                
                return True
            else:
                err_balance = f"Problem z odczytem salda (HTTP {response.status_code}). Treść: {response.text[:120]}"
                print(f"    [!] {err_balance}")
                write_log(err_balance)
                
        except requests.exceptions.RequestException as e:
            net_err = f"Błąd sieciowy podczas sprawdzania salda: {e}"
            print(f"    [!] {net_err}")
            
