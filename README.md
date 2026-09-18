# Eldorado Robux Sniper

A lightweight Python tool that monitors Eldorado.gg Robux offers and sends alerts to Discord when a cheap offer is detected.

## Features

* 🔍 Monitors Eldorado Robux offers
* 💰 Detects offers below a configurable price per Robux
* 📉 Detects existing offers when their price drops below the threshold
* 🔔 Sends alerts through a Discord webhook
* 📦 Displays Robux quantity, seller, price, delivery time, and listing link
* 💾 Keeps track of previously seen offers
* 🚫 Doesn't spam alerts for existing listings when first started

## Requirements

* Python 3.10+
* `requests`

## Installation

Clone the repository:

```bash
git clone https://github.com/emilbrej/EldoradoRobuxSniper.git
cd eldorado-robux-sniper
```

Install the required dependency:

```bash
pip install -r requirements.txt
```

## Configuration

Open `sniper.py` and configure the following values:

```python
DISCORD_WEBHOOK_URL = "PASTE_YOUR_DISCORD_WEBHOOK_HERE"

MAX_PRICE_PER_ROBUX_USD = 0.00400
POLL_INTERVAL_SECONDS = 15
PAGE_SIZE = 150

MENTION_EVERYONE = True
ALERT_ROLE_ID = None
```

### Discord Webhook

Create a Discord webhook for the channel where you want to receive alerts and paste the webhook URL into `DISCORD_WEBHOOK_URL`.

**Never publish your actual webhook URL publicly.**

If you are making a public fork or contribution, keep the placeholder:

```text
PASTE_YOUR_DISCORD_WEBHOOK_HERE
```

## Running

Run the sniper with:

```bash
python sniper.py
```

When it starts successfully, it will send a test message to the configured Discord webhook.

The console will display the cheapest offer found during each check.

Example:

```text
Eldorado Robux Discord Sniper
Threshold: $0.00400/Robux
Polling every 15s
Press Ctrl+C to stop.

[OK] Discord webhook test sent.
[CHECK] Cheapest $0.00385/R | 10,000 R | ExampleSeller
```

## How Alerts Work

On the first run, the sniper records the currently available offers without sending alerts for them.

After that, it alerts when:

* A new offer appears below the configured price threshold.
* An existing offer drops from above the threshold to at or below the threshold.

For example, with:

```python
MAX_PRICE_PER_ROBUX_USD = 0.00400
```

an offer at `$0.00390` per Robux qualifies for an alert.

## Configuration Options

| Setting                   | Description                                             |
| ------------------------- | ------------------------------------------------------- |
| `MAX_PRICE_PER_ROBUX_USD` | Maximum price per Robux that triggers an alert          |
| `POLL_INTERVAL_SECONDS`   | Number of seconds between checks                        |
| `PAGE_SIZE`               | Number of offers requested                              |
| `MENTION_EVERYONE`        | Whether alerts mention `@everyone`                      |
| `ALERT_ROLE_ID`           | Optional Discord role to mention instead of `@everyone` |

## Files

```text
eldorado-robux-sniper/
├── sniper.py
├── requirements.txt
├── .gitignore
├── README.md
└── eldorado_seen.json
```

`eldorado_seen.json` is generated automatically while the program runs and is excluded from Git using `.gitignore`.

## Disclaimer

This project is an independent tool and is not affiliated with Eldorado.gg, Discord, or Roblox.

Use the tool responsibly and in accordance with the terms and policies of the services involved.
