# Projeto de Extracao e Transformacao de Dados - Videojogos

## 1. Visao Geral
Este projeto desenvolve um pipeline de ETL (Extract, Transform, Load) completo focado na industria de videojogos. O objetivo e cruzar dados de catalogos, mercado financeiro e popularidade em tempo real para gerar insights multidimensionais sobre o setor.

## 2. Fontes de Dados (Camada Bronze - Raw)
O sistema realiza a extracao massiva a partir de 3 APIs distintas:
- **RAWG API:** Metadados de catalogo, datas de lancamento e notas da critica (Metacritic). Extracao configurada via paginacao automatica para os 1000 jogos mais populares.
- **Steam Spy API:** Dados comerciais, estimativas de vendas (owners), precos, descontos e pico de jogadores ativos (ccu_peak) para mais de 83.000 jogos.
- **Twitch API:** Audiencia ao vivo, contagem de streams ativas, linguas faladas e principais streamers do momento para os 1000 jogos mais assistidos.

## 3. Arquitetura do Projeto e Camadas de Dados
O projeto segue uma estrutura modular e organizada por camadas de maturidade de dados:

- **data/**: Armazenamento local segregado.
  - `raw/`: Dados brutos extraidos das APIs em formato JSON/CSV (Camada Bronze).
  - `processed/`: Dados limpos, padronizados e consolidados em formato CSV (Camada Silver).
- **src/**: Scripts Python modulares.
  - `extract.py`: Realiza a paginacao massiva e captura os dados da RAWG.
  - `steam_spy_extract.py`: Extrai o catalogo completo de jogos da Steam Spy com controle de rate limit.
  - `Twitch_extract.py`: Captura os jogos de topo e as suas respetivas transmissoes ao vivo na Twitch.
  - `transform.py`: Executa a limpeza, filtragem de ruido e o cruzamento das fontes.

## 4. Engenharia de Dados e Transformacao (Camada Silver)
No modulo de transformacao (`transform.py`), foram aplicadas as seguintes regras de negocio e tecnicas de saneamento:
1. **Tratamento de Nulos:** Substituicao de valores ausentes no Metacritic por zero e strings de data invalidas por "Unknown".
2. **Uniformizacao de Chaves:** Criacao da coluna `nome_uniforme` (letras minusculas e remocao de espacos em branco) em todas as fontes para garantir o alinhamento de texto.
3. **Filtragem de Ruido:** Remocao de milhares de jogos inativos da Steam Spy cujo pico de jogadores simultaneos (`ccu_peak`) era igual a zero, otimizando o dataset.
4. **Consolidacao (Merge):** Realizacao de um *Inner Join* entre RAWG e Steam Spy, seguido de um *Left Join* com a Twitch, gerando o ficheiro final unificado `silver_consolidated_games.csv` com mais de 780 registos prontos para analise.

## 5. Como Executar o Pipeline (Semana 2)

1. Certifique-se de que as credenciais estao configuradas no ficheiro `.env`.
2. Execute os extratores para atualizar a Camada Bronze:
   ```powershell
   python src/extract.py
   python src/steam_spy_extract.py
   python src/Twitch_extract.py
3. Execute o script de transformacao para gerar os ficheiros da Camada Silver:
   python src/transform.py