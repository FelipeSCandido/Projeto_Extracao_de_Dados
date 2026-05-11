import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RAWG_API_KEY")

def extract_games_data(page_size=40):

    print(f"Módulo de Extração")
    
    if not API_KEY:
        print("Erro: RAWG_API_KEY não encontrada no ficheiro .env")
        return

    url = f"https://api.rawg.io/api/games?key={API_KEY}&page_size={page_size}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
      
        os.makedirs("data/raw", exist_ok=True)
        output_path = "data/raw/games_metadata_raw.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Sucesso: {len(data['results'])} registos extraídos e guardados em {output_path}")
        
    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada à API: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    # Execução do script principal [cite: 89]
    extract_games_data()
