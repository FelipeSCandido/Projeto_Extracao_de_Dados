# Projeto de Extracao, Transformacao e Carregamento de Dados - Videojogos

## 1. Visao Geral
Este projeto desenvolve um pipeline de ETL (Extract, Transform, Load) completo focado na industria de videojogos. O objetivo e cruzar dados de catalogos, mercado financeiro e popularidade em tempo real para gerar insights multidimensionais sobre o setor.

## 2. Fontes de Dados (Camada Bronze - Raw)
O sistema realiza a extracao massiva a partir de 3 APIs distintas:
- **RAWG API:** Metadados de catalogo, datas de lancamento e notas da critica (Metacritic).
- **Steam Spy API:** Dados comerciais, estimativas de vendas (owners), precos, descontos e pico de jogadores ativos (ccu_peak).
- **Twitch API:** Audiencia ao vivo, contagem de streams ativas, linguas faladas e streamers do momento.

## 3. Arquitetura do Projeto e Camadas de Dados
O projeto segue uma estrutura modular e organizada por camadas de maturidade de dados:
- **data/**: Armazenamento local segregado.
  - `raw/`: Dados brutos extraidos das APIs em formato JSON/CSV (Camada Bronze).
  - `processed/`: Dados limpos, padronizados e consolidados num unico CSV (Camada Silver).
- **src/**: Scripts Python modulares.
  - `extract.py`, `steam_spy_extract.py`, `Twitch_extract.py`: Captura de dados.
  - `transform.py`: Executa a limpeza, filtragem de ruido e o cruzamento das fontes.
  - `load.py`: Modela os dados em Star Schema e envia para a cloud (Semana 3).

## 4. Engenharia de Dados e Transformacao (Camada Silver)
Limpeza, tratamento de nulos, uniformizacao de chaves textuais e consolidacao das 3 APIs num unico dataset achatado (`silver_consolidated_games.csv`), garantindo a integridade dos dados e removendo ruidos (como jogos inativos).

## 5. Modelacao Dimensional e Camada Gold (Semana 3)
Os dados da Camada Silver foram estruturados num modelo dimensional (Star Schema) e carregados para uma base de dados PostgreSQL na cloud (plataforma Neon) utilizando a biblioteca SQLAlchemy.

### Tabelas de Dimensao (Filtros Analiticos):
- **`dim_games`**: Metadados do jogo (`rawg_id`, `slug`, `name`, `released`).
- **`dim_publishers`**: Lista unica de editoras (`publisher_id`, `publisher_name`).
- **`dim_developers`**: Lista unica de estudios de desenvolvimento (`developer_id`, `developer_name`).

### Tabela de Factos (Metricas Quantitativas):
- **`fact_game_metrics`**: Centraliza as chaves estrangeiras de ligacao e as metricas do projeto: `appid`, `rating`, `metacritic`, `rawg_estimated_playtime`, `price`, `discount`, `owners_medio`, `ccu_peak`, `streams_ao_vivo`, `total_viewers`, `viewer_max`, `top_streamer_viewers`.

## 6. Como Executar o Pipeline Completo

1. Certifique-se de que as credenciais estao configuradas no ficheiro `.env` (incluindo a `NEON_DB_URL`).
2. Execute os extratores para atualizar a Camada Bronze:
   ```powershell
   python src/extract.py
   python src/steam_spy_extract.py
   python src/Twitch_extract.py
   ```
3. Execute a transformacao para gerar a Camada Silver:
   ```powershell
   python src/transform.py
   ```
4. Execute o carregamento para a base de dados Cloud (Camada Gold):
   ```powershell
   python src/load.py
   ```
5. Inicie a API intermedia a partir da raiz do projeto para servir o Frontend:
   ```powershell
   python -m uvicorn src.main:app --reload
   ```
   No fim da execucao, abra o seguinte link no seu navegador para ver os graficos analiticos: http://127.0.0.1:8000/frontend

## 7. Estrutura Completa de Diretorios do Projeto
```text
.
├── data/
│   ├── raw/                 # Camada Bronze: Ficheiros brutos JSON/CSV
│   └── processed/           # Camada Silver: Ficheiros limpos e consolidados
├── src/
│   ├── extract.py           # Script de extracao massiva da RAWG
│   ├── steam_spy_extract.py # Script de extracao da Steam Spy
│   ├── Twitch_extract.py    # Script de extracao da Twitch
│   ├── transform.py         # Script de higienizacao e cruzamento (Merge)
│   ├── load.py              # Script de carga dimensional para a Cloud
│   └── main.py              # FastAPI Backend (Servidor e rotas de dados)
├── .env                     # Chaves de API e credenciais da BD (Ignorado)
├── .gitignore               # Filtro de seguranca para chaves e dados pesados
├── index.html               # Frontend Oficial (Graficos interativos Chart.js)
└── README.md                # Documentacao oficial do projeto
```
## 8. Tecnologias e Dependencias
- **Linguagem Base:** Python 3.10 ou superior.
- **Base de Dados Cloud:** Neon Serverless PostgreSQL.
- **Bibliotecas Python Utilizadas:**
  - `pandas`: Processamento de matrizes e tratamento de dados.
  - `requests`: Consumo de endpoints das APIs REST.
  - `sqlalchemy`: Conexao e interacao abstrata com o motor SQL.
  - `psycopg2-binary`: Driver nativo de comunicacao com o PostgreSQL.
  - `python-dotenv`: Isolamento seguro de credenciais locais.
