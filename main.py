#!/usr/bin/env python3

import re
import time
from datetime import datetime

import requests

# Configuration

ARTICLE = "Mitch_McConnell"  # e.g. "Mitch_McConnell"
CHECK_INTERVAL = 30  # seconds

API_URL = "https://en.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": "WikiMonitor/1.0 (your_email@example.com)"
}

# API

def get_revision_id():
    params = {
        "action": "query",
        "titles": ARTICLE,
        "prop": "revisions",
        "rvprop": "ids",
        "format": "json",
    }

    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()

    page = next(iter(response.json()["query"]["pages"].values()))

    if "revisions" not in page:
        raise RuntimeError(f"Article '{ARTICLE}' not found.")

    return page["revisions"][0]["revid"]


def get_article_state():
    params = {
        "action": "query",
        "titles": ARTICLE,
        "prop": "revisions|extracts",
        "rvprop": "ids",
        "exintro": True,
        "explaintext": True,
        "format": "json",
    }

    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()

    page = next(iter(response.json()["query"]["pages"].values()))

    if "revisions" not in page:
        raise RuntimeError(f"Article '{ARTICLE}' not found.")

    revid = page["revisions"][0]["revid"]

    text = page.get("extract", "").strip()

    if not text:
        raise RuntimeError("Article has no introduction.")

    match = re.match(r"^(.+?[.!?])(?:\s|$)", text, re.DOTALL)

    if match:
        sentence = " ".join(match.group(1).split())
    else:
        sentence = " ".join(text.split())

    return revid, sentence


# Main

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def main():
    print()
    log(f"Monitoring article: {ARTICLE}")

    last_revid, previous_sentence = get_article_state()

    log(f"Current revision: {last_revid}")
    print()
    print("Current first sentence:")
    print(previous_sentence)
    print()

    while True:
        try:
            time.sleep(CHECK_INTERVAL)

            current_revid = get_revision_id()

            if current_revid == last_revid:
                log("Checked - no changes.")
                continue

            log(f"Revision changed: {last_revid} -> {current_revid}")

            last_revid = current_revid

            _, current_sentence = get_article_state()

            if current_sentence != previous_sentence:
                print()
                print("First sentence changed:")
                print(f"OLD: {previous_sentence}")
                print(f"NEW: {current_sentence}")

                if " is " in previous_sentence and " was " in current_sentence:
                    print()
                    print("=" * 60)
                    print(" IS -> WAS change detected!")
                    print("=" * 60)

            previous_sentence = current_sentence

        except KeyboardInterrupt:
            print()
            log("Stopped.")
            break

        except Exception as e:
            log(f"Error: {e}")


if __name__ == "__main__":
    main()