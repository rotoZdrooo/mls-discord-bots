import requests
import xml.etree.ElementTree as ET
import os
import json
import time
from datetime import datetime
import hashlib

# === CONFIGURATION ===
api_url = "https://api.rotowire.com/Soccer/MLS/Lineups.php?key=b0d5ug2n1mtubrhr9s4n"
discord_webhook_url = "https://discord.com/api/webhooks/1382337930651111505/ZGsGppAr2JEFEwMD_6zPleJrvjwyw0p3OaEwds4oLkgi2-rfIZ7CoLWgbJCCYbclSdVB"
posted_file = "posted_lineups.json"
headers = {"User-Agent": "Mozilla/5.0"}

# === LOAD POSTED HASH CACHE ===
if os.path.exists(posted_file):
    try:
        with open(posted_file, "r") as f:
            posted_hashes = json.load(f)
            if not isinstance(posted_hashes, dict):
                posted_hashes = {}
    except Exception:
        posted_hashes = {}
else:
    posted_hashes = {}

# === FETCH AND PARSE XML ===
try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    root = ET.fromstring(response.content)
except Exception as e:
    print("❌ Could not parse XML.")
    print("Reason:", e)
    exit(1)

new_posts = 0
games = root.find("Games")

for game in games.findall("Game"):
    game_id = game.attrib.get("Id")
    kickoff = game.attrib.get("Date")
    kickoff_dt = datetime.fromisoformat(kickoff).strftime("%B %d, %I:%M %p")

    teams = game.find("Teams")
    all_teams = teams.findall("Team")
    if len(all_teams) != 2:
        continue

    team1, team2 = all_teams

    for team in [team1, team2]:
        team_name = team.findtext("Name", "Unknown Team")
        lineup_status = team.findtext("LineupStatus", "")
        if lineup_status not in ["X", "C"]:
            continue

        team_id = team.attrib.get("Id")
        opponent = team2.findtext("Name") if team == team1 else team1.findtext("Name")

        # Extract 11-player starting XI
        players = team.find("Players")
        player_names = []
        for p in players.findall("Player")[:11]:
            first = p.findtext("Firstname", "").strip()
            last = p.findtext("Lastname", "").strip()
            if first or last:
                player_names.append(f"- {first} {last}")

        if len(player_names) < 1:
            continue

        joined_lineup = "\n".join(player_names)
        lineup_hash = hashlib.sha1(joined_lineup.encode("utf-8")).hexdigest()

        post_key = f"{game_id}_{team_id}_{lineup_status}"
        last_hash = posted_hashes.get(post_key)

        if last_hash == lineup_hash:
            print(f"⏩ Skipping unchanged {lineup_status} lineup for {team_name}")
            continue

        # Lineup status text
        status_label = "Confirmed Lineup" if lineup_status == "C" else "Expected Lineup"
        embed_color = 0x2ecc71 if lineup_status == "C" else 0xf1c40f

        embed = {
            "embeds": [
                {
                    "title": f"{status_label}: {team_name}",
                    "url": "https://www.rotowire.com/soccer/lineups.php?league=MLS",
                    "description": f"🆚 {opponent}\n🕒 Kickoff: {kickoff_dt}",
                    "color": embed_color,
                    "fields": [
                        {"name": "Starting XI", "value": joined_lineup}
                    ],
                    "footer": {
                        "text": "Full lineups → Rotowire",
                        "icon_url": "https://www.rotowire.com/images/logo.png"
                    }
                }
            ]
        }

        try:
            requests.post(discord_webhook_url, json=embed)
            time.sleep(1.1)
            posted_hashes[post_key] = lineup_hash
            new_posts += 1
            print(f"✅ Posted {status_label} for {team_name}")
        except Exception as post_err:
            print(f"❌ Error posting to Discord: {post_err}")

# === SAVE HASH CACHE EVEN IF NOTHING CHANGED ===
try:
    with open(posted_file, "w") as f:
        json.dump(posted_hashes, f)
    print("💾 Cache saved to posted_lineups.json")
except Exception as save_err:
    print("❌ Failed to save cache file:", save_err)

if new_posts == 0:
    print("✅ No new or changed lineups to post.")
else:
    print(f"✅ Posted {new_posts} updated lineup(s) to Discord.")


