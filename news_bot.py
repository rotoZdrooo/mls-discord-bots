import requests
import xml.etree.ElementTree as ET
import os
import json
import time

# === CONFIGURATION ===
api_url = "https://api.rotowire.com/Soccer/News.php?key=b0d5ug2n1mtubrhr9s4n"
discord_webhook_url = "https://discord.com/api/webhooks/1382064061641920592/BbgLJGdnoIACx1sXGd482r1U-eTHPLQ-rAlPsOBnvycMMotTOtG200ISPGlsvv7WmtfR"
posted_ids_file = "posted_news_ids.json"
headers = {"User-Agent": "Mozilla/5.0"}

# === LOAD POSTED IDS ===
if os.path.exists(posted_ids_file):
    with open(posted_ids_file, "r") as f:
        posted_ids = set(json.load(f))
else:
    posted_ids = set()

# === FETCH & PARSE XML ===
try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    root = ET.fromstring(response.content)
except Exception as e:
    print("❌ Could not parse XML.")
    print("Reason:", e)
    print("HTTP status:", response.status_code)
    print("Response text:", response.text[:300])
    exit(1)

# === PROCESS RECENT NEWS ONLY ===
updates = root.find("Updates")
recent_updates = updates.findall("Update")[-5:]  # Only look at the last 5 updates
new_posts = 0

for update in recent_updates:
    news_id = update.attrib.get("Id")
    if not news_id or news_id in posted_ids:
        continue

    headline = update.findtext("Headline", "No Title")
    notes = update.findtext("Notes", "")
    date = update.findtext("DateTime", "Unknown Date")

    # === PLAYER INFO ===
    player = update.find("Player")
    if player is not None:
        player_id = player.attrib.get("Id", "")
        first = player.findtext("FirstName", "").strip()
        last = player.findtext("LastName", "").strip()
        full_name = f"{first} {last}"
        link_name = f"{first.lower().replace(' ', '-')}-{last.lower().replace(' ', '-')}"
        player_link = f"https://www.rotowire.com/soccer/player/{link_name}-{player_id}"
    else:
        full_name = "Unknown Player"
        player_link = "https://www.rotowire.com/soccer/"

    # === EMBED PAYLOAD ===
    embed = {
        "embeds": [
            {
                "title": headline,
                "url": player_link,
                "description": f"**{full_name}**\n\n{notes}",
                "color": 0x3498DB,
                "fields": [
                    {"name": "Published", "value": date}
                ],
                "footer": {"text": "Powered by Rotowire"}
            }
        ]
    }

    try:
        requests.post(discord_webhook_url, json=embed)
        time.sleep(1.1)  # prevent Discord rate-limiting
        posted_ids.add(news_id)
        new_posts += 1
    except Exception as post_err:
        print(f"❌ Error posting to Discord: {post_err}")

# === SAVE POSTED IDS ===
with open(posted_ids_file, "w") as f:
    json.dump(list(posted_ids), f)

if new_posts == 0:
    print("✅ No new updates to post.")
else:
    print(f"✅ Posted {new_posts} new article(s) to Discord.")



