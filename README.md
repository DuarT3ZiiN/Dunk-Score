# Dunk-Score

Plataforma de previsões pré-jogo da NBA: probabilidade de vitória de cada time, total de pontos projetado, confiança do modelo e os fatores que mais pesam em cada confronto.

## Como funciona

```
Kaggle (histórico) ──► normalize ──► load ──┐
                                            ├──► Postgres ──► features (SQL) ──► modelo ──► API ──► frontend
balldontlie (ao vivo, via Celery) ──────────┘
```

- **Postgres** guarda tudo num esquema único (`DADOS/sql/init.sql`): `teams`, `games`, `team_game_stats` (uma linha por time por jogo) e `predictions`.
- **Features** (`BACKEND/app/services/features.py`): diferenças mandante − visitante nas médias dos últimos 10 jogos de cada time (pontos, rebotes, assistências, turnovers, aproveitamento de arremessos, % de vitórias) e nos dias de descanso. Só entram jogos **anteriores** à partida, e o mesmo SQL é usado no treino e na API.
- **Modelo** (`BACKEND/ml/train.py`): compara regressão logística, random forest e gradient boosting. A última temporada fica de fora como teste, o modelo é escolhido por validação cruzada temporal e o resultado é salvo em `BACKEND/ml/model.joblib`, junto com a versão e as métricas.
- **API** (FastAPI) serve os jogos com as previsões e calcula novas sob demanda.
- **Celery** sincroniza os jogos de ontem e de hoje com o balldontlie a cada 2 horas e recalcula as previsões do dia.
- **Frontend** (React + Vite + Tailwind) mostra os jogos de qualquer data e gera previsões pela interface.

## Estrutura

```
Dunk-Score/
├── BACKEND/
│   ├── app/
│   │   ├── routes/        # endpoints HTTP
│   │   ├── services/      # features, previsão, ingestão e provedores externos
│   │   └── tasks/         # jobs do Celery
│   ├── ml/train.py        # treino do modelo
│   └── tests/
├── DADOS/sql/init.sql     # esquema do banco (fonte da verdade)
├── DOCKER/                # docker-compose e .env
├── FRONTEND/              # app React
└── SCRIPTS/               # pipeline de dados históricos
```

## Pré-requisitos

- Docker e Docker Compose
- Python 3.11+ (para os scripts de dados e o treino, que rodam na sua máquina)
- O dataset [NBA Database do Kaggle](https://www.kaggle.com/datasets/wyattowalsh/basketball): basta o arquivo `csv/game.csv`

## Passo a passo

### 1. Configurar e subir os serviços

```bash
cd Dunk-Score/DOCKER
cp .env.example .env          # ajuste a senha; a chave do balldontlie é opcional
docker compose up -d --build
```

Isso sobe Postgres, Redis, API (http://localhost:8000/docs), worker e beat do Celery, além do frontend (http://localhost:5173).

> Se você já tinha rodado uma versão antiga do projeto, recrie o banco com `docker compose down -v` antes de subir. O esquema mudou.

### 2. Carregar o histórico

Com o Postgres rodando, a partir de `Dunk-Score/`:

```bash
python -m venv .venv && source .venv/bin/activate   # no Windows: .venv\Scripts\activate
pip install -r BACKEND/requirements.txt

mkdir -p data/raw/csv                     # coloque o game.csv do Kaggle aqui
python SCRIPTS/normalize_kaggle_nba.py    # gera data/processed/*.csv
python SCRIPTS/load_processed_to_postgres.py
python SCRIPTS/build_training_dataset.py  # --min-season 2000 por padrão
```

Os scripts leem as credenciais de `DOCKER/.env`. Para usar outra pasta de dados, defina `DUNK_DATA_DIR`. A carga pode ser repetida sem duplicar dados.

### 3. Treinar o modelo

```bash
cd BACKEND
python -m ml.train                        # --test-seasons N para segurar mais temporadas
```

O modelo vai para `BACKEND/ml/model.joblib`, que a API lê automaticamente (a pasta é montada no container). As métricas ficam em `BACKEND/ml/metrics.json`, incluindo a acurácia do baseline "o mandante sempre vence", para comparação.

### 4. Usar

Abra http://localhost:5173, escolha uma data com jogos (por exemplo, uma data da última temporada do dataset) e clique em **Gerar previsões**.

## API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Status da API |
| GET | `/games?date=AAAA-MM-DD` | Jogos de uma data, com previsão (padrão: hoje, no fuso de Nova York) |
| GET | `/games/today` | Jogos de hoje |
| GET | `/games/{id}` | Um jogo |
| POST | `/games/{id}/predict` | Calcula (ou recalcula) e salva a previsão do jogo |

A documentação interativa fica em http://localhost:8000/docs.

## Dados ao vivo

Com `BALLDONTLIE_API_KEY` no `.env`, o beat do Celery busca os jogos de ontem e de hoje a cada 2 horas e recalcula as previsões do dia. Para rodar na hora:

```bash
docker compose exec worker celery -A app.tasks.celery_app.celery call app.tasks.jobs.sync_games_today
```

Os times do balldontlie são casados com os do Kaggle pela sigla (BOS, LAL...). Jogos encerrados viram histórico para as features dos próximos.

## Testes

```bash
cd Dunk-Score/BACKEND
pytest
```

## Limitações conhecidas

- O plano gratuito do balldontlie só traz placares. Jogos sincronizados por ele alimentam as médias de pontos e o % de vitórias, mas não rebotes, assistências etc.; essas médias continuam vindo dos jogos do Kaggle mais recentes entre os últimos 10.
- O **total projetado** é a soma das médias recentes de pontos dos dois times, sem ajuste por ritmo nem pela defesa adversária.
- Lesões ainda não entram no modelo (há um provedor da Sportradar e a tabela `injuries`, mas nada os usa ainda).
