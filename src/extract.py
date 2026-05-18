import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RAWG_API_KEY")

def extract_games_data():
    print("--- Iniciando Modulo de Extracao Massiva (RAWG) ---")
    
    if not API_KEY:
        print("Erro: RAWG_API_KEY nao encontrada no ficheiro .env")
        return

    # Configuracao de limites para a extracao massiva
    page_size = 40  # Maximo permitido pela API por pedido
    max_paginas = 25  # 25 paginas x 40 jogos = 1000 jogos mais populares
    
    url_inicial = f"https://api.rawg.io/api/games?key={API_KEY}&page_size={page_size}"
    url_atual = url_inicial
    
    todos_jogos = []
    pagina_atual = 1
    
    try:
        os.makedirs("data/raw", exist_ok=True)
        output_path = "data/raw/games_metadata_raw.json"
        
        while url_atual and pagina_atual <= max_paginas:
            print(f"A descarregar pagina {pagina_atual} de {max_paginas} da RAWG...")
            
            response = requests.get(url_atual)
            response.raise_for_status()
            data = response.json()
            
            resultados_pagina = data.get("results", [])
            if not resultados_pagina:
                print("Info: Nao foram encontrados mais jogos no catalogo.")
                break
                
            todos_jogos.extend(resultados_pagina)
            
            # Atualiza a URL com o link da proxima pagina fornecido pela propria API
            url_atual = data.get("next")
            pagina_atual += 1
            
            # Descanso de seguranca para respeitar os limites de trafego do servidor
            time.sleep(0.2)
            
        # Montar a estrutura final identica ao formato original para nao quebrar o transform.py
        dados_finais = {
            "count": len(todos_jogos),
            "results": todos_jogos
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print(f"\nSucesso: {len(todos_jogos)} registos da RAWG extraidos com sucesso!")
        print(f"Ficheiro guardado em: {output_path}")
        
    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada a API: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    extract_games_data()