import requests
import os
import json
import time
from datetime import datetime

api_url = "https://api.rotowire.com/Soccer/News.php?key=b0d5ug2n1mtubrhr9s4n"
discord_webhook_url = "https://discord.com/api/webhooks/1382064061641920592/BbgLJGdnoIACx1sXGd482r1U-eTHPLQ-rAlPsOBnvycMMotTOtG200ISPGlsvv7WmtfR"
posted_ids_file = "posted_news_ids.json"
headers = {"User-Agent": "Mozilla/5.0"}

# Load posted IDs
if os.path.exists(posted_ids_file):
    with open(posted_ids_file, "r") as f:
        posted_ids = set(json.load(f))
else:
    posted_ids = set()

try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    data = response.json().get("news", [])
except Exception as e:
    print("❌ Could not fetch news:", e)
    exit(1)

new_posts = 0
for item in data[:10]:  # check only the latest 10
    news_id = item.get("Id")
    if not news_id or news_id in posted_ids:
        continue

    headline = item.get("Headline", "No Title")
    notes = item.get("Notes", "")
    date = item.get("Updated", datetime.now().isoformat())
    player = item.get("Player", {})
    player_link = f"https://www.rotowire.com/soccer/player/{player.get('UrlSlug', '')}" if player else "https://www.rotowire.com/soccer/"
    full_name = f"{player.get('FirstName', '')} {player.get('LastName', '')}".strip()

    embed = {
        "embeds": [
            {
                "title": headline,
                "url": player_link,
                "description": f"**{full_name}**\n\n{notes}",
                "color": 0x3498DB,
                "fields": [{"name": "Published", "value": date}],
                "footer": {"text": "Full MLS coverage → Rotowire"}
            }
        ]
    }

    try:
        requests.post(discord_webhook_url, json=embed)
        time.sleep(1.0)
        posted_ids.add(news_id)
        new_posts += 1
    except Exception as post_err:
        print(f"❌ Error posting: {post_err}")

# Save updated IDs
with open(posted_ids_file, "w") as f:
    json.dump(list(posted_ids), f)

print(f"✅ Posted {new_posts} new article(s).")
