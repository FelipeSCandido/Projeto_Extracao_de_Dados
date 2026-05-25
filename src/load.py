import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def get_engine():
    """Obtem a ligacao a base de dados PostgreSQL no Neon."""
    load_dotenv()
    db_url = os.getenv("NEON_DB_URL")
    
    if not db_url:
        print("Erro: A variavel NEON_DB_URL nao esta definida no ficheiro .env")
        return None
        
    try:
        engine = create_engine(db_url)
        print("Ligacao ao Neon PostgreSQL estabelecida com sucesso!")
        return engine
    except Exception as e:
        print(f"Erro ao ligar ao Neon: {e}")
        return None

def criar_esquema_estrela(df):
    """Transforma a tabela achatada Silver num Esquema em Estrela (Gold)."""
    print("A modelar os dados para o Esquema em Estrela (Star Schema)...")
    
    # 1. Dimensao: Publishers (Editoras)
    dim_publishers = pd.DataFrame({"publisher_name": df["publisher"].dropna().unique()})
    dim_publishers["publisher_id"] = dim_publishers.index + 1
    
    # 2. Dimensao: Developers (Estudios)
    dim_developers = pd.DataFrame({"developer_name": df["developer"].dropna().unique()})
    dim_developers["developer_id"] = dim_developers.index + 1
    
    # 3. Dimensao: Games (Detalhes do Jogo)
    dim_games = df[["rawg_id", "slug", "name", "released"]].copy().drop_duplicates(subset=["rawg_id"])
    
    # Mapeamento para construir a Tabela de Factos
    # Fazer merge para trazer os IDs das dimensoes para o dataframe principal
    df_fact = pd.merge(df, dim_publishers, left_on="publisher", right_on="publisher_name", how="left")
    df_fact = pd.merge(df_fact, dim_developers, left_on="developer", right_on="developer_name", how="left")
    
    # 4. Tabela de Factos (Metricas e Chaves Estrangeiras)
    colunas_fact = [
        "rawg_id", "publisher_id", "developer_id", "appid", 
        "rating", "metacritic", "rawg_estimated_playtime",
        "price", "discount", "owners_medio", "ccu_peak",
        "streams_ao_vivo", "total_viewers", "viewer_max", "top_streamer_viewers"
    ]
    
    fact_game_metrics = df_fact[colunas_fact].copy()
    
    # Tratamento final para nulos nas chaves da Tabela de Factos
    fact_game_metrics["publisher_id"] = fact_game_metrics["publisher_id"].fillna(0).astype(int)
    fact_game_metrics["developer_id"] = fact_game_metrics["developer_id"].fillna(0).astype(int)
    
    return dim_publishers, dim_developers, dim_games, fact_game_metrics

def carregar_dados(engine, dim_pub, dim_dev, dim_games, fact_metrics):
    """Carrega os DataFrames para tabelas SQL no Neon."""
    print("A carregar as tabelas para a Cloud (Neon)...")
    
    try:
        # Carregar Dimensoes (Tabelas de suporte/filtros)
        dim_pub.to_sql("dim_publishers", engine, if_exists="replace", index=False)
        print(" Tabela dim_publishers carregada.")
        
        dim_dev.to_sql("dim_developers", engine, if_exists="replace", index=False)
        print(" Tabela dim_developers carregada.")
        
        dim_games.to_sql("dim_games", engine, if_exists="replace", index=False)
        print(" Tabela dim_games carregada.")
        
        # Carregar Factos (Tabela central de metricas)
        fact_metrics.to_sql("fact_game_metrics", engine, if_exists="replace", index=False)
        print(" Tabela central fact_game_metrics carregada.")
        
        print("\nProcesso de Load (Camada Gold) concluido com sucesso!")
        
    except Exception as e:
        print(f"Erro durante o carregamento para o Neon: {e}")

def main():
    print("--- Iniciando Modulo de Carregamento (Semana 3) ---")
    
    caminho_silver = os.path.join("data", "processed", "silver_consolidated_games.csv")
    
    if not os.path.exists(caminho_silver):
        print(f"Erro: Ficheiro nao encontrado em {caminho_silver}")
        return
        
    # 1. Ler os dados processados da Camada Silver
    print("A ler dados processados...")
    df_silver = pd.read_csv(caminho_silver)
    
    # 2. Conectar a Base de Dados
    engine = get_engine()
    if not engine:
        return
        
    # 3. Modelar os dados (Star Schema)
    dim_pub, dim_dev, dim_games, fact_metrics = criar_esquema_estrela(df_silver)
    
    # 4. Carregar na Cloud
    carregar_dados(engine, dim_pub, dim_dev, dim_games, fact_metrics)

if __name__ == "__main__":
    main()