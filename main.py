import requests
import time
import os

# Récupère le webhook depuis les variables d'environnement Render
WEBHOOK_URL = os.environ.get("https://discord.com/api/webhooks/1475652057766563912/gM9QbKmPijywDkZhb2S4caxPizRs-_BkEjNat6szdv-Bt6OC86lRkRN_OxVpD6NSf8rN")
if not WEBHOOK_URL:
    print("ERREUR : WEBHOOK_URL non défini dans les variables d'environnement !")
    exit(1)

TICKER_URL = "https://www.simcompanies.com/api/v3/market-ticker/0/"
THRESHOLD = 2.3          # Change ce seuil si tu veux (ex. 2.0)
SCAN_INTERVAL = 300      # 300 secondes = 5 minutes (recommandé pour éviter rate-limit)

last_price = None

def get_apples_price():
    try:
        r = requests.get(TICKER_URL, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        # Convertit true/false JS en True/False Python
        text = r.text.replace('true', 'True').replace('false', 'False')
        data = eval(text)  # Structure simple → safe ici
        
        for item in data:
            if item.get("kind") == 3:  # Pommes
                return item.get("price"), item.get("is_up")
        return None, None
    except Exception as e:
        print(f"Erreur lors du scan : {e}")
        return None, None

def send_discord_alert(title, description, color=0xffff00):
    embed = {
        "title": title,
        "description": description,
        "color": color
    }
    payload = {"embeds": [embed]}
    try:
        requests.post(WEBHOOK_URL, json=payload)
        print(f"Alert envoyée : {title}")
    except Exception as e:
        print(f"Erreur envoi Discord : {e}")

print("Démarrage du monitoring pommes SimCompanies...")

while True:
    price, is_up = get_apples_price()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    
    if price is not None:
        if isinstance(price, str) and "sold out" in str(price).lower():
            print(f"[{now}] Pommes : SOLD OUT")
            if last_price != "sold out":
                send_discord_alert("Alerte SOLD OUT !", "Les pommes sont épuisées sur le marché !", 0xff0000)
            last_price = "sold out"
        else:
            trend = "↑ en hausse" if is_up else "↓ stable ou baisse"
            print(f"[{now}] Pommes : ${price:.2f} ({trend})")
            
            # Envoie alerte seulement si dessous du seuil ET c'est un nouveau bas
            if isinstance(price, (int, float)) and price < THRESHOLD:
                if last_price is None or last_price >= THRESHOLD or price < last_price:
                    msg = f"Prix bas détecté : **${price:.2f}** (sous {THRESHOLD}$) – {trend}\nHeure : {now}"
                    send_discord_alert("Alerte Prix Bas Pommes !", msg, 0xffaa00)
            
            last_price = price
    else:
        print(f"[{now}] Erreur : impossible de récupérer le prix")
    
    time.sleep(SCAN_INTERVAL)
