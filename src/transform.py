import os
import glob
import json
import pandas as pd

def encontrar_ficheiro_recente(padrao_busca):
    """Encontra o ficheiro mais recente que condiz com o padrao."""
    ficheiros = glob.glob(padrao_busca)
    if not ficheiros:
        return None
    return max(ficheiros, key=os.path.getmtime)

def processar_rawg():
    print("Processando dados da RAWG...")
    caminho_rawg = os.path.join("data", "raw", "games_metadata_raw.json")
    
    if not os.path.exists(caminho_rawg):
        print("Aviso: Ficheiro RAWG nao encontrado em data/raw/")
        return None

    with open(caminho_rawg, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)
    
    lista_jogos = dados_brutos.get("results", [])
    df = pd.DataFrame(lista_jogos)
    
    colunas_interesse = ["id", "slug", "name", "released", "rating", "rating_top", "metacritic", "playtime"]
    df_limpo = df[[col for col in colunas_interesse if col in df.columns]].copy()
    
    df_limpo["metacritic"] = df_limpo["metacritic"].fillna(0).astype(int)
    df_limpo["released"] = pd.to_datetime(df_limpo["released"], errors='coerce').dt.strftime("%Y-%m-%d")
    df_limpo["released"] = df_limpo["released"].fillna("Unknown")
    
    df_limpo["nome_uniforme"] = df_limpo["name"].astype(str).str.lower().str.strip()
    df_limpo = df_limpo.rename(columns={"id": "rawg_id", "playtime": "rawg_estimated_playtime"})
    
    return df_limpo

def processar_twitch():
    print("Processando dados da Twitch...")
    caminho_twitch = encontrar_ficheiro_recente(os.path.join("data", "raw", "twitch_mass_stats_*.json"))
    
    if not caminho_twitch:
        print("Aviso: Nenhum ficheiro twitch_mass_stats_*.json encontrado em data/raw/")
        return None

    with open(caminho_twitch, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)
        
    lista_jogos = dados_brutos.get("jogos", [])
    df = pd.DataFrame(lista_jogos)
    
    df["streams_ao_vivo"] = df["streams_ao_vivo"].fillna(0).astype(int)
    df["total_viewers"] = df["total_viewers"].fillna(0).astype(int)
    df["viewer_medio"] = df["viewer_medio"].fillna(0).astype(int)
    df["viewer_max"] = df["viewer_max"].fillna(0).astype(int)
    df["viewer_min"] = df["viewer_min"].fillna(0).astype(int)
    
    if "linguas" in df.columns:
        df["linguas"] = df["linguas"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    
    df["nome_uniforme"] = df["nome"].astype(str).str.lower().str.strip()
    df_limpo = df.drop(columns=["nome"])
    
    return df_limpo

def processar_steamspy():
    print("Processando dados da Steam Spy...")
    caminho_steam = encontrar_ficheiro_recente(os.path.join("data", "raw", "steamspy_all_games_*.json"))
    
    if not caminho_steam:
        print("Aviso: Nenhum ficheiro steamspy_all_games_*.json encontrado em data/raw/")
        return None

    with open(caminho_steam, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)
        
    lista_jogos = dados_brutos.get("jogos", [])
    df = pd.DataFrame(lista_jogos)
    
    # Filtragem: Mantemos apenas jogos que mostram atividade real (ccu_peak > 0)
    total_antes = len(df)
    df = df[df["ccu_peak"] > 0].copy()
    total_depois = len(df)
    print(f"   Info: Filtrados {total_antes - total_depois} jogos inativos (ccu a zero) na Steam Spy.")
    
    # Remocao das colunas sem dados concretos solicitadas pelo utilizador
    colunas_para_remover = [
        "avg_playtime_forever", 
        "avg_playtime_2weeks", 
        "med_playtime_forever", 
        "med_playtime_2weeks"
    ]
    df = df.drop(columns=[col for col in colunas_para_remover if col in df.columns], errors='ignore')
    
    df["nome_uniforme"] = df["nome"].astype(str).str.lower().str.strip()
    df_limpo = df.drop(columns=["nome"])
    
    return df_limpo

def main():
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)
    
    df_rawg = processar_rawg()
    df_twitch = processar_twitch()
    df_steam = processar_steamspy()
    
    if df_rawg is not None:
        df_rawg.to_csv(os.path.join("data", "processed", "silver_rawg_games.csv"), index=False, encoding="utf-8")
    if df_twitch is not None:
        df_twitch.to_csv(os.path.join("data", "processed", "silver_twitch_stats.csv"), index=False, encoding="utf-8")
    if df_steam is not None:
        df_steam.to_csv(os.path.join("data", "processed", "silver_steamspy_market.csv"), index=False, encoding="utf-8")
        
    print("\nCriando o Dataset Consolidado (Merge)...")
    
    if df_rawg is not None and df_steam is not None:
        df_consolidado = pd.merge(df_rawg, df_steam, on="nome_uniforme", how="inner")
        print(f"   Cruzamento RAWG + Steam Spy gerou {len(df_consolidado)} correspondencias exatas.")
        
        if df_twitch is not None:
            df_consolidado = pd.merge(df_consolidado, df_twitch, on="nome_uniforme", how="left")
            colunas_twitch = ["streams_ao_vivo", "total_viewers", "viewer_medio", "viewer_max", "viewer_min", "top_streamer_viewers"]
            for col in colunas_twitch:
                if col in df_consolidado.columns:
                    df_consolidado[col] = df_consolidado[col].fillna(0)
            if "top_streamer" in df_consolidado.columns:
                df_consolidado["top_streamer"] = df_consolidado["top_streamer"].fillna("Nenhum")
        
        df_consolidado = df_consolidado.drop(columns=["nome_uniforme"])
        
        caminho_final = os.path.join("data", "processed", "silver_consolidated_games.csv")
        df_consolidado.to_csv(caminho_final, index=False, encoding="utf-8")
        print(f"Dataset Consolidado Silver salvo com sucesso em: {caminho_final}")
        print(f"Total de linhas prontas para analise: {len(df_consolidado)}")
    else:
        print("Erro: Nao foi possivel gerar o dataset consolidado devido a falta de fontes.")

    print("\nProcessamento da Semana 2 Concluido com sucesso!")

if __name__ == "__main__":
    main()