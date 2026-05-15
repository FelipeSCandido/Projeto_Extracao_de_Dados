import requests
import json
import csv
import time
from datetime import datetime

BASE = "https://steamspy.com/api.php"

def get_top100(request_type):
    r = requests.get(BASE, params={"request": request_type})
    return r.json()

def get_app_details(appid):
    r = requests.get(BASE, params={"request": "appdetails", "appid": appid})
    return r.json()

def parse_owners(owners_str):
    # Converte "1,000,000 .. 2,000,000" para o valor médio
    try:
        parts = owners_str.replace(",", "").split("..")
        low = int(parts[0].strip())
        high = int(parts[1].strip())
        return low, high, (low + high) // 2
    except:
        return 0, 0, 0

def minutos_para_horas(minutos):
    return round(minutos / 60, 1)

# --- 1. Buscar Top 100 jogos (últimas 2 semanas) ---
print("A buscar Top 100 jogos...")
jogos_raw = get_top100("top100in2weeks")

dados = []
for i, (appid, info) in enumerate(jogos_raw.items(), 1):
    print(f"  [{i}/100] {info['name']}")

    owners_low, owners_high, owners_medio = parse_owners(info.get("owners", "0 .. 0"))
    preco = int(info.get("price", 0) or 0)
    preco_original = int(info.get("initialprice", 0) or 0)
    desconto = int(info.get("discount", 0) or 0)

    jogo = {
        "rank":                 i,
        "appid":                appid,
        "nome":                 info.get("name", ""),
        "developer":            info.get("developer", ""),
        "publisher":            info.get("publisher", ""),
        "genero":               info.get("genre", ""),
        "linguas":              info.get("languages", ""),
        "owners_range":         info.get("owners", ""),
        "owners_low":           owners_low,
        "owners_high":          owners_high,
        "owners_medio":         owners_medio,
        "score_rank":           info.get("score_rank", ""),
        "ccu_peak":             info.get("ccu", 0),
        "avg_playtime_total_h": minutos_para_horas(info.get("average_forever", 0)),
        "avg_playtime_2sem_h":  minutos_para_horas(info.get("average_2weeks", 0)),
        "med_playtime_total_h": minutos_para_horas(info.get("median_forever", 0)),
        "med_playtime_2sem_h":  minutos_para_horas(info.get("median_2weeks", 0)),
        "preco_atual_usd":      round(preco / 100, 2) if preco else 0,
        "preco_original_usd":   round(preco_original / 100, 2) if preco_original else 0,
        "desconto_pct":         desconto,
        "tags":                 ", ".join(info.get("tags", {}).keys()) if isinstance(info.get("tags"), dict) else ""
    }
    dados.append(jogo)
    time.sleep(1)  # respeitar rate limit: 1 req/seg

# --- 2. Exportar JSON ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
json_path = f"steamspy_top100_{timestamp}.json"

output = {
    "gerado_em":    datetime.now().isoformat(),
    "fonte":        "SteamSpy API — top100in2weeks",
    "total_jogos":  len(dados),
    "jogos":        dados
}
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\n✅ JSON exportado: {json_path}")

# --- 3. Exportar CSV ---
csv_path = f"steamspy_top100_{timestamp}.csv"
campos = [
    "rank", "appid", "nome", "developer", "publisher", "genero",
    "owners_range", "owners_low", "owners_high", "owners_medio",
    "score_rank", "ccu_peak",
    "avg_playtime_total_h", "avg_playtime_2sem_h",
    "med_playtime_total_h", "med_playtime_2sem_h",
    "preco_atual_usd", "preco_original_usd", "desconto_pct", "tags"
]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=campos)
    writer.writeheader()
    for jogo in dados:
        writer.writerow({k: jogo[k] for k in campos})
print(f"✅ CSV exportado:  {csv_path}")
