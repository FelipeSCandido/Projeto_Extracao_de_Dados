import requests
import os
import json
import csv
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_token():
    r = requests.post("https://id.twitch.tv/oauth2/token", params={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    })
    r.raise_for_status()
    return r.json()["access_token"]

# --- Inicializacao ---
os.makedirs(os.path.join("data", "raw"), exist_ok=True)
token = get_token()
headers = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {token}"
}

stats_por_jogo = {}
# 10 paginas x 100 jogos = 1000 jogos (O limite absoluto permitido pela API da Twitch)
max_paginas_jogos = 10  
cursor_jogo = None

print("A iniciar a extracao no LIMITE MAXIMO da Twitch (Top 1000)...")

# --- 1. Paginacao de Jogos ---
for p in range(max_paginas_jogos):
    print(f"A buscar pagina {p+1} de jogos mais assistidos...")
    params_jogos = {"first": 100}
    if cursor_jogo:
        params_jogos["after"] = cursor_jogo
        
    try:
        res_jogos = requests.get("https://api.twitch.tv/helix/games/top", headers=headers, params=params_jogos)
        res_json = res_jogos.json()
        
        jogos_pagina = res_json.get("data", [])
        if not jogos_pagina:
            print(f"Fim de paginacao detetado pela API na pagina {p+1}.")
            break
            
        for jogo in jogos_pagina:
            gid = jogo["id"]
            stats_por_jogo[gid] = {
                "game_id": gid,
                "nome": jogo["name"],
                "igdb_id": jogo.get("igdb_id", ""),
                "streams_ao_vivo": 0,
                "total_viewers": 0,
                "viewer_max": 0,
                "viewer_min": None,
                "top_streamer": "",
                "top_streamer_viewers": 0,
                "linguas": set()
            }
            
        cursor_jogo = res_json.get("pagination", {}).get("cursor")
        if not cursor_jogo:
            print("Nao existem mais cursores de paginacao disponiveis.")
            break
            
        time.sleep(0.2) # Evitar rate limits agressivos
        
    except Exception as e:
        print(f"Aviso: Interrupcao na paginacao de jogos: {e}")
        break

# --- 2. Buscar Streams ---
game_ids = list(stats_por_jogo.keys())
print(f"\nMapeados {len(game_ids)} jogos validos. A extrair streams correspondentes...")

for i in range(0, len(game_ids), 100):
    lote_ids = game_ids[i:i+100]
    cursor_stream = None
    
    # Busca ate 3 paginas de streams por lote para garantir densidade de dados
    for _ in range(3):
        params_streams = [("game_id", gid) for gid in lote_ids]
        params_streams.append(("first", 100))
        if cursor_stream:
            params_streams.append(("after", cursor_stream))
            
        try:
            res_streams = requests.get("https://api.twitch.tv/helix/streams", headers=headers, params=params_streams)
            streams_json = res_streams.json()
            streams_data = streams_json.get("data", [])
            
            if not streams_data:
                break
                
            for stream in streams_data:
                gid = stream["game_id"]
                if gid not in stats_por_jogo:
                    continue
                    
                s = stats_por_jogo[gid]
                viewers = stream["viewer_count"]
                
                s["streams_ao_vivo"] += 1
                s["total_viewers"] += viewers
                s["linguas"].add(stream["language"])
                
                if viewers > s["viewer_max"]:
                    s["viewer_max"] = viewers
                    s["top_streamer"] = stream["user_name"]
                    s["top_streamer_viewers"] = viewers
                    
                if s["viewer_min"] is None or viewers < s["viewer_min"]:
                    s["viewer_min"] = viewers
                    
            cursor_stream = streams_json.get("pagination", {}).get("cursor")
            if not cursor_stream:
                break
            time.sleep(0.1)
        except Exception as e:
            print(f"Erro ao processar streams do lote {i}: {e}")
            break

# --- 3. Finalizar Dados ---
dados_finais = []
for gid, s in stats_por_jogo.items():
    s["viewer_medio"] = round(s["total_viewers"] / s["streams_ao_vivo"]) if s["streams_ao_vivo"] > 0 else 0
    s["viewer_min"] = s["viewer_min"] if s["viewer_min"] is not None else 0
    s["linguas"] = list(s["linguas"])
    dados_finais.append(s)

dados_finais = sorted(dados_finais, key=lambda x: x["total_viewers"], reverse=True)

# --- 4. Exportar Ficheiros ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
json_path = os.path.join("data", "raw", f"twitch_mass_stats_{timestamp}.json")
csv_path = os.path.join("data", "raw", f"twitch_mass_stats_{timestamp}.csv")

# JSON
output = {
    "gerado_em": datetime.now().isoformat(),
    "total_jogos_monitorizados": len(dados_finais),
    "jogos": dados_finais
}
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# CSV
campos = ["game_id", "nome", "igdb_id", "streams_ao_vivo", "total_viewers", 
          "viewer_medio", "viewer_max", "viewer_min", "top_streamer", "top_streamer_viewers"]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
    writer.writeheader()
    for s in dados_finais:
        row = {k: s[k] for k in campos}
        row["linguas"] = ", ".join(s["linguas"])
        writer.writerow(row)

print(f"\nExtracao maxima concluida com sucesso!")
print(f"Total de {len(dados_finais)} jogos guardados em data/raw.")