import requests
import xml.etree.ElementTree as ET
import os
import json
import time
from datetime import datetime
import hashlib

api_url = "https://api.rotowire.com/Soccer/MLS/Lineups.php?key=b0d5ug2n1mtubrhr9s4n"
discord_webhook_url = "https://discord.com/api/webhooks/1382337930651111505/ZGsGppAr2JEFEwMD_6zPleJrvjwyw0p3OaEwds4oLkgi2-rfIZ7CoLWgbJCCYbclSdVB"
posted_file = "posted_lineups.json"
headers = {"User-Agent": "Mozilla/5.0"}

# Load saved lineup hashes
if os.path.exists(posted_file):
    with open(posted_file, "r") as f:
        posted_hashes = json.load(f)
else:
    posted_hashes = {}

try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    root = ET.fromstring(response.content)
except Exception as e:
    print("❌ Could not fetch lineups:", e)
    exit(1)

games = root.find("Games")
new_posts = 0

for game in games.findall("Game"):
    game_id = game.attrib.get("Id")
    kickoff = game.attrib.get("Date")
    kickoff_dt = datetime.fromisoformat(kickoff).strftime("%B %d, %I:%M %p")

    teams = game.find("Teams").findall("Team")
    if len(teams) != 2:
        continue

    team1, team2 = teams
    for team in [team1, team2]:
        team_name = team.findtext("Name", "Unknown Team")
        lineup_status = team.findtext("LineupStatus", "")
        if lineup_status not in ["X", "C"]:
            continue

        team_id = team.attrib.get("Id")
        opponent = team2.findtext("Name") if team == team1 else team1.findtext("Name")
        players = team.find("Players").findall("Player")[:11]
        player_names = [f"- {p.findtext('Firstname', '').strip()} {p.findtext('Lastname', '').strip()}" for p in players if p.findtext('Firstname') or p.findtext('Lastname')]

        if len(player_names) < 1:
            continue

        joined_lineup = "\n".join(player_names)
        lineup_hash = hashlib.sha1(joined_lineup.encode("utf-8")).hexdigest()
        post_key = f"{game_id}_{team_id}"  # ⬅️ No status included

        if posted_hashes.get(post_key) == lineup_hash:
            continue  # already posted

        embed = {
            "embeds": [
                {
                    "title": f"{'Confirmed' if lineup_status == 'C' else 'Expected'} Lineup: {team_name}",
                    "url": "https://www.rotowire.com/soccer/lineups.php?league=MLS",
                    "description": f"🆚 {opponent}\n🕒 Kickoff: {kickoff_dt}",
                    "color": 0x2ecc71 if lineup_status == "C" else 0xf1c40f,
                    "fields": [{"name": "Starting XI", "value": joined_lineup}],
                    "footer": {"text": "Full lineups → Rotowire"},
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }

        try:
            requests.post(discord_webhook_url, json=embed)
            posted_hashes[post_key] = lineup_hash
            new_posts += 1
            time.sleep(1.0)
        except Exception as e:
            print(f"❌ Error posting lineup for {team_name}:", e)

# Save updated hashes
with open(posted_file, "w") as f:
    json.dump(posted_hashes, f)

print(f"✅ Posted {new_posts} updated lineup(s).")
