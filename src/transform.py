import os
import glob
import json
import pandas as pd

def encontrar_ficheiro_recente(padrao_busca):
    """Encontra o ficheiro mais recente que condiz com o padrão (útil para timestamps)."""
    ficheiros = glob.glob(padrao_busca)
    if not ficheiros:
        return None
    return max(ficheiros, key=os.path.getmtime)

def processar_rawg():
    print("🧹 Processando dados da RAWG...")
    caminho_rawg = os.path.join("data", "raw", "games_metadata_raw.json")
    
    if not os.path.exists(caminho_rawg):
        print("⚠️ Ficheiro RAWG não encontrado em data/raw/")
        return None

    with open(caminho_rawg, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)
    
    # Extrai a lista de jogos de dentro da chave 'results'
    lista_jogos = dados_brutos.get("results", [])
    
    df = pd.DataFrame(lista_jogos)
    
    # Seleção e limpeza de colunas essenciais
    colunas_interesse = ["id", "slug", "name", "released", "rating", "rating_top", "metacritic", "playtime"]
    df_limpo = df[[col for col in colunas_interesse if col in df.columns]].copy()
    
    # Tratamento de Nulos
    df_limpo["metacritic"] = df_limpo["metacritic"].fillna(0).astype(int)
    df_limpo["released"] = pd.to_datetime(df_limpo["released"]).dt.strftime("%Y-%m-%d")
    
    # Uniformização do nome para cruzamento futuro (letras minúsculas e sem espaços extra)
    df_limpo["nome_uniforme"] = df_limpo["name"].astype(str).str.lower().str.strip()
    
    return df_limpo

def processar_twitch():
    print("🧹 Processando dados da Twitch...")
    # Procura pelo ficheiro JSON mais recente da Twitch na pasta raw
    caminho_twitch = encontrar_ficheiro_recente(os.path.join("data", "raw", "twitch_stats_*.json"))
    
    if not camino_twitch:
        print("⚠️ Nenhum ficheiro twitch_stats_*.json encontrado em data/raw/")
        return None

    with open(caminho_twitch, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)
        
    lista_jogos = dados_brutos.get("jogos", [])
    df = pd.DataFrame(lista_jogos)
    
    # Limpeza e conversão de tipos
    df["streams_ao_vivo"] = df["streams_ao_vivo"].fillna(0).astype(int)
    df["total_viewers"] = df["total_viewers"].fillna(0).astype(int)
    df["viewer_medio"] = df["viewer_medio"].fillna(0).astype(int)
    
    # Converter a lista de línguas para uma string separada por vírgulas
    df["linguas"] = df["linguas"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    
    # Uniformização do nome para cruzamento
    df["nome_uniforme"] = df["nome"].astype(str).str.lower().str.strip()
    
    return df

def processar_steamspy():
    print("🧹 Processando dados da Steam Spy...")
    caminho_steam = encontrar_ficheiro_recente(os.path.join("data", "raw", "steamspy_top100_*.json"))
    
    if not caminho_steam:
        print("⚠️ Nenhum ficheiro steamspy_top100_*.json encontrado em data/raw/")
        return None

    with open(caminho_steam, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)
        
    # No teu script da semana 1, os jogos já estão na chave "jogos"
    lista_jogos = dados_brutos.get("jogos", [])
    df = pd.DataFrame(lista_jogos)
    
    # Uniformização do nome para cruzamento
    df["nome_uniforme"] = df["nome"].astype(str).str.lower().str.strip()
    
    return df

def main():
    # Garantir que a pasta da camada Silver existe
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)
    
    # 1. Processar cada dataset isoladamente
    df_rawg = processar_rawg()
    df_twitch = processar_twitch()
    df_steam = processar_steamspy()
    
    # 2. Guardar os 3 datasets limpos individuais (Camada Silver)
    if df_rawg is not None:
        caminho_salvar_rawg = os.path.join("data", "processed", "silver_rawg_games.csv")
        df_rawg.to_csv(caminho_salvar_rawg, index=False, encoding="utf-8")
        print(f"💾 Dataset Silver RAWG salvo em: {caminho_salvar_rawg}")
        
    if df_twitch is not None:
        caminho_salvar_twitch = os.path.join("data", "processed", "silver_twitch_stats.csv")
        df_twitch.to_csv(caminho_salvar_twitch, index=False, encoding="utf-8")
        print(f"💾 Dataset Silver Twitch salvo em: {caminho_salvar_twitch}")
        
    if df_steam is not None:
        caminho_salvar_steam = os.path.join("data", "processed", "silver_steamspy_market.csv")
        df_steam.to_csv(caminho_salvar_steam, index=False, encoding="utf-8")
        print(f"💾 Dataset Silver Steam Spy salvo em: {caminho_salvar_steam}")

    print("\n🚀 Processamento da Camada Silver concluído com sucesso!")

if __name__ == "__main__":
    main()