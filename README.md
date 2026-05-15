# Projeto de Extração de Dados 2º ano - 2º semestre

## 1. Visão Geral
Este projeto foi desenvolvido para a unidade curricular de Extração de Dados. O objetivo é construir um pipeline de ETL (Extract, Transform, Load) completo, focado no domínio de entretenimento, especificamente na indústria de videojogos.

Utilizamos a API da **RAWG** como fonte principal para extrair metadados de jogos, permitindo análises sobre tendências de popularidade, avaliações e distribuição por géneros.

## 2. Arquitetura do Projeto
O projeto segue uma estrutura modular para garantir a escalabilidade e organização do pipeline:

- **data/**: Armazenamento local de dados segregado por camadas.
  - `raw/`: Dados brutos extraídos da API em formato JSON (Camada Bronze).
  - `processed/`: Dados limpos e transformados (Camada Silver).
  - `final/`: Dados prontos para análise e visualização (Camada Gold).
- **src/**: Scripts Python modulares.
  - `extract.py`: Módulo responsável pela comunicação com a API e persistência dos dados brutos.
- **.env**: Ficheiro de configuração para variáveis de ambiente (protegido por .gitignore).

## 3. Tecnologias Utilizadas
- **Linguagem:** Python 3.x
- **Bibliotecas:** - `requests`: Para chamadas à API REST.
  - `python-dotenv`: Para gestão de credenciais e segurança.
  - `json`: Para manipulação de dados semiestruturados.
- **Versionamento:** Git & GitHub.

## 4. Como Executar (Semana 1)
1. Certifique-se de que tem o Python instalado.
2. Instale as dependências necessárias:
   ```bash
   pip install requests python-dotenv