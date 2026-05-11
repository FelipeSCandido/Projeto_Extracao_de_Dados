import os
import requests
import json
from dotenv import load_dotenv

# 1. Configuração de Variáveis de Ambiente [cite: 90]
# Carrega a API Key do teu ficheiro .env para garantir a segurança das credenciais [cite: 155, 179]
load_dotenv()
API_KEY = os.getenv("RAWG_API_KEY")

def extract_games_data(page_size=40):
    """
    Realiza a extração de metadados de jogos da API RAWG.
    Esta função cumpre o requisito de extração modular e logging mínimo[cite: 193, 203].
    """
    print(f"--- Iniciando Módulo de Extração (Semana 1) ---")
    
    if not API_KEY:
        print("Erro: RAWG_API_KEY não encontrada no ficheiro .env")
        return

    # Endpoint da API RAWG para listar jogos populares
    url = f"https://api.rawg.io/api/games?key={API_KEY}&page_size={page_size}"
    
    try:
        # Realizar o pedido à API [cite: 77]
        response = requests.get(url)
        response.raise_for_status() # Verifica se a requisição foi bem-sucedida
        data = response.json()
        
        # 2. Persistência de Dados Brutos (Camada Bronze/Raw) [cite: 202]
        # Os dados são guardados exatamente como chegam, sem transformações [cite: 195, 202]
        os.makedirs("data/raw", exist_ok=True) # Garante que a pasta existe [cite: 201]
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