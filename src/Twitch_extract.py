import requests
import os
import json
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# --- Token ---
def get_token():
    r = requests.post("https://id.twitch.tv/oauth2/token", params={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    })
    return r.json()["access_token"]

token = get_token()
headers = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {token}"
}

# --- 1. Top 20 jogos ---
jogos_r = requests.get("https://api.twitch.tv/helix/games/top", headers=headers, params={"first": 20})
jogos = jogos_r.json()["data"]
game_ids = [j["id"] for j in jogos]

# --- 2. Streams ao vivo ---
params = [("game_id", gid) for gid in game_ids]
params.append(("first", "100"))
streams_r = requests.get("https://api.twitch.tv/helix/streams", headers=headers, params=params)
streams = streams_r.json()["data"]

# --- 3. Agregar estatísticas ---
stats = {}
for i, jogo in enumerate(jogos):
    stats[jogo["id"]] = {
        "rank": i + 1,
        "game_id": jogo["id"],
        "nome": jogo["name"],
        "box_art_url": jogo["box_art_url"],
        "igdb_id": jogo.get("igdb_id", ""),
        "streams_ao_vivo": 0,
        "total_viewers": 0,
        "viewer_max": 0,
        "viewer_min": None,
        "viewer_medio": 0,
        "top_streamer": "",
        "top_streamer_viewers": 0,
        "linguas": []
    }

linguas_temp = {gid: set() for gid in stats}

for stream in streams:
    gid = stream["game_id"]
    if gid not in stats:
        continue
    s = stats[gid]
    viewers = stream["viewer_count"]
    s["streams_ao_vivo"] += 1
    s["total_viewers"] += viewers
    linguas_temp[gid].add(stream["language"])
    if viewers > s["viewer_max"]:
        s["viewer_max"] = viewers
        s["top_streamer"] = stream["user_name"]
        s["top_streamer_viewers"] = viewers
    if s["viewer_min"] is None or viewers < s["viewer_min"]:
        s["viewer_min"] = viewers

# Calcular médias e converter sets
for gid, s in stats.items():
    s["viewer_medio"] = round(s["total_viewers"] / s["streams_ao_vivo"]) if s["streams_ao_vivo"] > 0 else 0
    s["viewer_min"] = s["viewer_min"] or 0
    s["linguas"] = list(linguas_temp[gid])

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
dados = list(stats.values())

# --- 4. Exportar JSON ---
json_path = f"twitch_stats_{timestamp}.json"
output = {
    "gerado_em": datetime.now().isoformat(),
    "total_jogos": len(dados),
    "total_streams": sum(s["streams_ao_vivo"] for s in dados),
    "total_viewers": sum(s["total_viewers"] for s in dados),
    "jogos": dados
}
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"✅ JSON exportado: {json_path}")

# --- 5. Exportar CSV ---
csv_path = f"twitch_stats_{timestamp}.csv"
campos = ["rank", "game_id", "nome", "igdb_id", "streams_ao_vivo",
          "total_viewers", "viewer_medio", "viewer_max", "viewer_min",
          "top_streamer", "top_streamer_viewers", "linguas"]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=campos)
    writer.writeheader()
    for s in dados:
        row = {k: s[k] for k in campos}
        row["linguas"] = ", ".join(s["linguas"])  # lista → string no CSV
        writer.writerow(row)
print(f"✅ CSV exportado:  {csv_path}")