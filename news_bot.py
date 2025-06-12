import requests
import xml.etree.ElementTree as ET
import os
import json
import time
from datetime import datetime

api_url = "https://api.rotowire.com/Soccer/News.php?key=b0d5ug2n1mtubrhr9s4n"
discord_webhook_url = "https://discord.com/api/webhooks/1382064061641920592/BbgLJGdnoIACx1sXGd482r1U-eTHPLQ-rAlPsOBnvycMMotTOtG200ISPGlsvv7WmtfR"
posted_ids_file = "posted_news_ids.json"
headers = {"User-Agent": "Mozilla/5.0"}

# Load previously posted IDs
if os.path.exists(posted_ids_file):
    with open(posted_ids_file, "r") as f:
        posted_ids = set(json.load(f))
else:
    posted_ids = set()

try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    root = ET.fromstring(response.content)
except Exception as e:
    print("❌ Failed to fetch or parse news:", e)
    exit(1)

new_posts = 0
for update in root.find("Updates").findall("Update")[:10]:  # check latest 10
    update_id = update.attrib.get("Id")
    if not update_id or update_id in posted_ids:
        continue

    headline = update.findtext("Headline", "No title")
    notes = update.findtext("Notes", "")
    player_elem = update.find("Player")
    player_name = f"{player_elem.findtext('FirstName', '')} {player_elem.findtext('LastName', '')}".strip() if player_elem is not None else "Unknown"
    link = "https://www.rotowire.com/soccer/"  # no direct link per player

    embed = {
        "embeds": [
            {
                "title": headline,
                "description": f"**{player_name}**\n\n{notes}",
                "url": link,
                "color": 0x3498db,
                "footer": {"text": "Full MLS coverage → Rotowire"},
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }

    try:
        requests.post(discord_webhook_url, json=embed)
        posted_ids.add(update_id)
        new_posts += 1
        time.sleep(1.0)
    except Exception as post_err:
        print("❌ Error posting:", post_err)

# Save updated ID list
with open(posted_ids_file, "w") as f:
    json.dump(list(posted_ids), f)

print(f"✅ Posted {new_posts} new article(s).")
