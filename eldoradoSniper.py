import json
import time
from pathlib import Path

import requests

# =========================
# CONFIG
# =========================
DISCORD_WEBHOOK_URL = "PASTE_YOUR_DISCORD_WEBHOOK_HERE"
MAX_PRICE_PER_ROBUX_USD = 0.00400
POLL_INTERVAL_SECONDS = 15
PAGE_SIZE = 150
STATE_FILE = Path("eldorado_seen.json")
MENTION_EVERYONE = True
ALERT_ROLE_ID = None  # e.g. "123456789012345678"

API_URL = "https://www.eldorado.gg/api/predefinedOffers/augmentedGame/offers"
LISTING_URL = "https://www.eldorado.gg/buy-robux/g/70-0-0"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36",
    "Referer": LISTING_URL,
}


def load_state():
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_state(state):
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"[WARN] Could not save state: {exc}")


def fetch_offers():
    params = {
        "gameId": "70",
        "category": "Currency",
        "pageIndex": 1,
        "pageSize": PAGE_SIZE,
    }
    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    payload = r.json()

    offers = []
    for item in payload.get("results", []):
        offer = item["offer"]
        user = item.get("user", {})
        price = offer["pricePerUnit"]
        price_usd = offer.get("pricePerUnitInUSD", price)
        offer_id = str(offer["id"])
        seo_alias = offer.get("gameSeoAlias", "buy-robux")

        offers.append({
            "id": offer_id,
            "seller": user.get("username", "unknown"),
            "price_usd": float(price_usd["amount"]),
            "native_price": float(price["amount"]),
            "currency": price["currency"],
            "quantity": int(offer.get("quantity", 0)),
            "min_quantity": int(offer.get("minQuantity", 0)),
            "delivery": offer.get("guaranteedDeliveryTime", "unknown"),
            "description": offer.get("description", ""),
            "url": f"https://www.eldorado.gg/{seo_alias}/og/{offer_id}",
        })

    offers.sort(key=lambda x: x["price_usd"])
    return offers


def send_webhook(offer, reason):
    if ALERT_ROLE_ID:
        mention = f"<@&{ALERT_ROLE_ID}>"
        allowed = {"roles": [ALERT_ROLE_ID], "parse": []}
    elif MENTION_EVERYONE:
        mention = "@everyone"
        allowed = {"everyone": True, "parse": ["everyone"]}
    else:
        mention = ""
        allowed = {"parse": []}

    total = offer["price_usd"] * offer["quantity"]

    # Keep enough room for the rest of the Discord message.
    description = str(offer.get("description", "")).strip()
    if not description:
        description = "No description provided."
    else:
        # Prevent @everyone/@here or other mentions inside seller text
        # from causing unintended pings.
        description = description.replace("@", "@\\u200b")
        if len(description) > 700:
            description = description[:697] + "..."

    content = (
        f"{mention}\n"
        f"🚨 **CHEAP ROBUX OFFER** ({reason})\n\n"
        f"💰 **${offer['price_usd']:.5f} / Robux**\n"
        f"📦 **{offer['quantity']:,} Robux**\n"
        f"💵 **${total:,.2f} total**\n"
        f"👤 Seller: `{offer['seller']}`\n"
        f"⏱️ Delivery: `{offer['delivery']}`\n"
        f"📝 **Description:**\n{description}\n"
        f"🔗 {offer['url']}"
    )

    r = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": content, "allowed_mentions": allowed},
        timeout=20,
    )
    r.raise_for_status()


def webhook_test():
    r = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": "✅ Eldorado Robux sniper started successfully."},
        timeout=20,
    )
    r.raise_for_status()


def main():
    if DISCORD_WEBHOOK_URL == "PASTE_YOUR_DISCORD_WEBHOOK_HERE":
        print("ERROR: Put your Discord webhook URL into DISCORD_WEBHOOK_URL first.")
        return

    print("Eldorado Robux Discord Sniper")
    print(f"Threshold: ${MAX_PRICE_PER_ROBUX_USD:.5f}/Robux")
    print(f"Polling every {POLL_INTERVAL_SECONDS}s")
    print("Press Ctrl+C to stop.\n")

    try:
        webhook_test()
        print("[OK] Discord webhook test sent.")
    except requests.RequestException as exc:
        print(f"[ERROR] Discord webhook failed: {exc}")
        return

    state = load_state()
    first_run = not bool(state)

    while True:
        try:
            offers = fetch_offers()
            if not offers:
                print("[WARN] No offers returned.")
            else:
                cheapest = offers[0]
                print(
                    f"[CHECK] Cheapest ${cheapest['price_usd']:.5f}/R | "
                    f"{cheapest['quantity']:,} R | {cheapest['seller']}"
                )

                if first_run:
                    # Do not spam alerts for listings that were already there.
                    for offer in offers:
                        state[offer["id"]] = offer["price_usd"]
                    save_state(state)
                    first_run = False
                    print(f"[INIT] Recorded {len(offers)} current offers.")
                else:
                    for offer in offers:
                        old = state.get(offer["id"])
                        new_price = offer["price_usd"]
                        qualifies = new_price <= MAX_PRICE_PER_ROBUX_USD

                        new_deal = old is None and qualifies
                        crossed_threshold = (
                            old is not None
                            and old > MAX_PRICE_PER_ROBUX_USD
                            and qualifies
                        )

                        if new_deal or crossed_threshold:
                            reason = "new offer" if new_deal else "price dropped"
                            try:
                                send_webhook(offer, reason)
                                print(
                                    f"[ALERT] {reason}: ${new_price:.5f}/R "
                                    f"{offer['id']}"
                                )
                            except requests.RequestException as exc:
                                print(f"[ERROR] Discord alert failed: {exc}")

                        state[offer["id"]] = new_price

                    save_state(state)

                # Keep state bounded to IDs currently present.
                if len(state) > PAGE_SIZE * 3:
                    current_ids = {o["id"] for o in offers}
                    state = {k: v for k, v in state.items() if k in current_ids}
                    save_state(state)

        except requests.HTTPError as exc:
            print(f"[ERROR] Eldorado HTTP error: {exc}")
        except requests.RequestException as exc:
            print(f"[ERROR] Network error: {exc}")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            print(f"[ERROR] Unexpected Eldorado JSON format: {exc}")
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as exc:
            print(f"[ERROR] Unexpected error: {exc}")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
