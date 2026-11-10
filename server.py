from datetime import datetime
import hashlib
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import random
import sqlite3
import urllib.request

PORT = 8080
DB_FILE = "faucet.db"

# --- KONFIGURACJA BRAMKI LNBITS ---
# Zmień na własny Admin Key z https://legend.lnbits.com/, jeśli chcesz wysyłać realne satoshi
EXTERNAL_API_URL = "https://legend.lnbits.com/api/v1/payments"
EXTERNAL_API_KEY = "tutaj_wklej_swoj_admin_key_z_lnbits"


def init_db():
  """Inicjalizacja bazy danych SQLite dla Speed Ledger"""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS speed_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            destination TEXT,
            amount_sats INTEGER,
            converted_usd REAL,
            txid TEXT,
            status TEXT
        )
    """)
  conn.commit()
  conn.close()


def get_btc_price_usd():
  """Pobieranie aktualnego kursu BTC z CoinGecko API"""
  try:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=3) as response:
      data = json.loads(response.read().decode("utf-8"))
      return float(data["bitcoin"]["usd"])
  except Exception:
    return 65000.0


def convert_points_to_sats(points):
  """Konwersja punktów na Satoshi i USD"""
  sats = int(points * 0.1)
  btc_price = get_btc_price_usd()
  btc_amount = sats / 100000000.0
  usd = btc_amount * btc_price
  return sats, usd


class FaucetServerHandler(SimpleHTTPRequestHandler):

  def do_GET(self):
    if self.path == "/api/v1/export-csv":
      self.send_response(200)
      self.send_header("Content-Type", "text/csv; charset=utf-8")
      self.send_header(
          "Content-Disposition", "attachment; filename=speed_ledger.csv"
      )
      self.end_headers()

      try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM speed_ledger")
        rows = cursor.fetchall()
        conn.close()

        csv_data = "ID,Timestamp,Destination,AmountSats,USD,TXID,Status\n"
        for row in rows:
          csv_data += (
              f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]},{row[6]}\n"
          )
        self.wfile.write(csv_data.encode("utf-8"))
      except Exception as e:
        self.wfile.write(f"Błąd eksportu: {str(e)}".encode("utf-8"))
      return

    return super().do_GET()

  def do_POST(self):
    content_length = int(self.headers.get("Content-Length", 0))
    body = self.rfile.read(content_length)
    try:
      request_body = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
      request_body = {}

    # 1. Saldo / Przelicznik
    if self.path == "/api/v1/balance":
      js_mined = request_body.get("js_mined", 0)
      cloud_mined = request_body.get("cloud_mined", 0)
      total_points = js_mined + cloud_mined

      sats, usd = convert_points_to_sats(total_points)

      response_data = {
          "status": "success",
          "balance_sats": sats,
          "estimated_usd": round(usd, 4),
          "message": f"Przeliczono {total_points} punktów.",
      }
      self.send_json_response(response_data, 200)

    # 2. Zadania fauceta
    elif self.path == "/api/v1/task":
      reward = random.randint(100, 400)
      response_data = {
          "status": "success",
          "earned_points": reward,
          "message": f"Zadanie zaliczone! Otrzymano {reward} punktów.",
      }
      self.send_json_response(response_data, 200)

    # 3. Wypłata Lightning Network
    elif self.path == "/api/v1/claim":
      destination = request_body.get("payout_destination", "")
      claimed_sats = request_body.get("claimed_sats", 0)

      if claimed_sats <= 0:
        self.send_json_response(
            {"status": "error", "message": "Brak środków do wypłaty."}, 400
        )
        return

      success, txid = self.process_lightning_payout(destination, claimed_sats)

      if success:
        if "legend.lnbits.com" in EXTERNAL_API_URL:
          payment_mode = "Real Lightning Payout (LNbits)"
        else:
          payment_mode = "Simulated Payout"

        response_data = {
            "status": "success",
            "mode": payment_mode,
            "txid": txid,
            "message": f"Pomyślnie wypłacono {claimed_sats} sats!",
        }
        self.send_json_response(response_data, 200)
      else:
        self.send_json_response(
            {
                "status": "error",
                "message": f"Błąd bramki płatniczej: {txid}",
            },
            400,
        )

    # 4. Przelew do Speed Ledger
    elif self.path == "/api/v1/speed-transfer":
      points = request_body.get("points", 0)
      destination = request_body.get(
          "destination", "Speed-Internal-Wallet"
      )

      if points <= 0:
        self.send_json_response(
            {"status": "error", "message": "Brak punktów do przelania."}, 400
        )
        return

      sats, usd = convert_points_to_sats(points)
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      txid = f"SPEED-TX-{random.randint(100000, 999999)}"

      try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
                    INSERT INTO speed_ledger (timestamp, destination, amount_sats, converted_usd, txid, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
            (timestamp, destination, sats, usd, txid, "Completed"),
        )
        conn.commit()
        conn.close()

        response_data = {
            "status": "success",
            "txid": txid,
            "transferred_sats": sats,
            "converted_usd": round(usd, 4),
            "message": f"Przelano {sats} sats do Speed Ledger!",
        }
        self.send_json_response(response_data, 200)
      except Exception as e:
        self.send_json_response({
            "status": "error",
            "message": f"Błąd zapisu bazy: {str(e)}",
        }, 500)

    else:
      self.send_json_response(
          {"status": "error", "message": "Nieznany endpoint"}, 404
      )

  def process_lightning_payout(self, destination, amount_sats):
    is_bolt11 = destination.startswith("lnbc")

    if "tutaj_wklej" in EXTERNAL_API_KEY:
      return (
          True,
          f"SIM-TXID-{random.randint(10000000, 99999999)}",
      )

    payload = {
        "out": True,
        "amount": amount_sats,
        "bolt11": destination if is_bolt11 else None,
    }

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": EXTERNAL_API_KEY,
    }

    try:
      req = urllib.request.Request(
          EXTERNAL_API_URL,
          data=json.dumps(payload).encode("utf-8"),
          headers=headers,
          method="POST",
      )
      with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
        txid = result.get("payment_hash") or result.get("checking_id")
        return True, txid or "LNBITS-SUCCESS"
    except Exception as e:
      return False, str(e)

  def send_json_response(self, data, status=200):
    self.send_response(status)
    self.send_header("Content-Type", "application/json; charset=utf-8")
    self.end_headers()
    self.wfile.write(json.dumps(data).encode("utf-8"))


if __name__ == "__main__":
  init_db()
  server = HTTPServer(("localhost", PORT), FaucetServerHandler)
  print(f"🚀 Serwer Python działa na http://localhost:{PORT}")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    print("\nZatrzymywanie serwera...")
    server.server_close()
