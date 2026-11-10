import sqlite3
import os

def show_payout_history():
    db_file = "payouts.db"
    
    if not os.path.exists(db_file):
        print(f"[B£¥D] Nie znaleziono pliku bazy danych '{db_file}'. Wykonaj najpierw wyp³atê przez serwer.")
        return

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Sprawdzamy czy tabela payouts w ogóle istnieje
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payouts';")
        if not cursor.fetchone():
            print("[B£¥D] Tabela 'payouts' nie istnieje w bazie danych.")
            conn.close()
            return

        # Pobieramy wpisy uwzglêdniaj¹ce nowe kolumny txid i status
        cursor.execute("""
            SELECT id, timestamp, destination, amount_sats, is_auto, txid, status 
            FROM payouts 
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        
        # Pobieramy równie¿ stan portfela z tabeli wallet_balance (jeœli istnieje)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wallet_balance';")
        wallet_total = 0
        if cursor.fetchone():
            cursor.execute("SELECT total_claimed_sats FROM wallet_balance WHERE id = 1")
            res = cursor.fetchone()
            if res:
                wallet_total = res[0]

        conn.close()

        if not rows:
            print("\nBaza danych 'payouts.db' jest pusta. Brak historii wyp³at.")
            return

        # Nag³ówek tabeli
        print("\n" + "=" * 115)
        print(f"{'ID':<4} | {'Data i Czas':<19} | {'Adres docelowy':<25} | {'Sats':<7} | {'Tryb':<6} | {'TXID (Skrócony)':<18} | {'Status'}")
        print("=" * 115)

        total_sats_listed = 0
        auto_count = 0
        manual_count = 0

        for row in rows:
            payout_id, timestamp, destination, amount, is_auto, txid, status = row
            total_sats_listed += amount
            
            mode = "Auto" if is_auto else "Rêczna"
            if is_auto:
                auto_count += 1
            else:
                manual_count += 1

            # Skracamy adres jeœli jest za d³ugi do tabeli
            short_dest = destination if len(destination) <= 25 else destination[:22] + "..."
            
            # Skracamy TXID do czytelnej postaci (np. a1b2c3...e5f6) lub wstawiamy "-"
            if txid:
                short_txid = f"{txid[:8]}...{txid[-6:]}"
            else:
                short_txid = "-"

            status_str = status if status else "Confirmed"

            print(f"{payout_id:<4} | {timestamp:<19} | {short_dest:<25} | {amount:<7} | {mode:<6} | {short_txid:<18} | {status_str}")

        print("=" * 115)
        print(f"PODSUMOWANIE Z LISTY: Wyp³acono w historii: {total_sats_listed} sats | Transakcji: {len(rows)} (Auto: {auto_count}, Rêczne: {manual_count})")
        if wallet_total > 0:
            print(f"SALDO PORTFELA (wallet_balance): £¹cznie zaksiêgowano w systemie: {wallet_total} sats")
        print("=" * 115 + "\n")

    except Exception as e:
        print(f"[B£¥D] Wyst¹pi³ problem podczas odczytu bazy danych: {e}")

if __name__ == "__main__":
    show_payout_history()
