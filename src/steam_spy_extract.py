import requests
import json
import csv
import time
import os
from datetime import datetime

BASE = "https://steamspy.com/api.php"

def get_games_page(page):
    r = requests.get(BASE, params={"request": "all", "page": page})
    r.raise_for_status()
    return r.json()

def parse_owners(owners_str):
    try:
        parts = owners_str.replace(",", "").split("..")
        low = int(parts[0].strip())
        high = int(parts[1].strip())
        return low, high, (low + high) // 2
    except:
        return 0, 0, 0

def minutos_para_horas(minutos):
    return round(minutos / 60, 1)

# --- 1. Preparar Diretorio ---
os.makedirs(os.path.join("data", "raw"), exist_ok=True)

dados_totais = []
pagina = 0
contagem_jogos = 1

print("A iniciar a extracao TOTAL da Steam Spy...")

while True:
    print(f"A descarregar pagina {pagina}...")
    try:
        jogos_raw = get_games_page(pagina)
        
        if not jogos_raw or len(jogos_raw) == 0:
            print("Fim dos dados encontrados na API.")
            break
            
        for appid, info in jogos_raw.items():
            owners_low, owners_high, owners_medio = parse_owners(info.get("owners", "0 .. 0"))
            preco = int(info.get("price", 0) or 0)
            preco_original = int(info.get("initialprice", 0) or 0)
            desconto = int(info.get("discount", 0) or 0)

            jogo = {
                "rank_extracao":        contagem_jogos,
                "appid":                appid,
                "nome":                 info.get("name", ""),
                "developer":            info.get("developer", ""),
                "publisher":            info.get("publisher", ""),
                "price":                round(preco / 100, 2) if preco else 0,
                "initialprice":         round(preco_original / 100, 2) if preco_original else 0,
                "discount":             desconto,
                "owners_range":         info.get("owners", ""),
                "owners_low":           owners_low,
                "owners_high":          owners_high,
                "owners_medio":         owners_medio,
                "ccu_peak":             info.get("ccu", 0),
                "avg_playtime_forever": minutos_para_horas(info.get("average_forever", 0)),
                "avg_playtime_2weeks":  minutos_para_horas(info.get("average_2weeks", 0)),
                "med_playtime_forever": minutos_para_horas(info.get("median_forever", 0)),
                "med_playtime_2weeks":  minutos_para_horas(info.get("median_2weeks", 0))
            }
            dados_totais.append(jogo)
            contagem_jogos += 1
        
        pagina += 1
        time.sleep(1.1)  # Rate limit
        
    except Exception as e:
        print(f"Erro ao processar a pagina {pagina}: {e}")
        break

# --- 2. Exportar Ficheiros ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
json_path = os.path.join("data", "raw", f"steamspy_all_games_{timestamp}.json")
csv_path = os.path.join("data", "raw", f"steamspy_all_games_{timestamp}.csv")

# Exportar JSON
output = {
    "gerado_em": datetime.now().isoformat(),
    "fonte": "SteamSpy API - all",
    "total_jogos_extraidos": len(dados_totais),
    "jogos": dados_totais
}
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# Exportar CSV
if dados_totais:
    campos = list(dados_totais[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(dados_totais)

print(f"Extracao massiva Steam Spy concluida! Total de {len(dados_totais)} jogos.")
print(f"JSON: {json_path}")
print(f"CSV:  {csv_path}")