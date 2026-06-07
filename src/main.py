from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import psycopg
import psycopg.rows
from contextlib import contextmanager
import os
import threading
import time
from typing import Optional
from pydantic import BaseModel

# ─── Configuração ─────────────────────────────────────────────────────────────

DATABASE_URL = "postgresql://neondb_owner:npg_o1eRVk2MsJgH@ep-empty-heart-alqacqb3-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require"

# ─── Keep-alive ───────────────────────────────────────────────────────────────

def keepalive_loop():
    while True:
        time.sleep(240)
        try:
            conn = psycopg.connect(DATABASE_URL)
            conn.execute("SELECT 1")
            conn.close()
        except Exception:
            pass

threading.Thread(target=keepalive_loop, daemon=True).start()

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="API Intermédia - Projeto Extração de Dados",
    description="API intermédia entre o frontend e a base de dados Neon PostgreSQL",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Ligação à BD ─────────────────────────────────────────────────────────────

@contextmanager
def get_conn():
    conn = psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ─── Modelos ──────────────────────────────────────────────────────────────────

class GameMetricCreate(BaseModel):
    rawg_id: int
    publisher_id: int
    developer_id: int
    appid: Optional[int] = None
    rating: Optional[float] = None
    metacritic: Optional[int] = None
    rawg_estimated_playtime: Optional[int] = None
    price: Optional[float] = None
    discount: Optional[int] = None
    owners_medio: Optional[int] = None
    ccu_peak: Optional[int] = None
    streams_ao_vivo: Optional[float] = None
    total_viewers: Optional[float] = None
    viewer_max: Optional[float] = None
    top_streamer_viewers: Optional[float] = None

class GameMetricUpdate(BaseModel):
    publisher_id: Optional[int] = None
    developer_id: Optional[int] = None
    appid: Optional[int] = None
    rating: Optional[float] = None
    metacritic: Optional[int] = None
    rawg_estimated_playtime: Optional[int] = None
    price: Optional[float] = None
    discount: Optional[int] = None
    owners_medio: Optional[int] = None
    ccu_peak: Optional[int] = None
    streams_ao_vivo: Optional[float] = None
    total_viewers: Optional[float] = None
    viewer_max: Optional[float] = None
    top_streamer_viewers: Optional[float] = None

class DimGameCreate(BaseModel):
    name: Optional[str] = None
    released: Optional[str] = None
    slug: Optional[str] = None

class DimPublisherCreate(BaseModel):
    publisher_name: str

class DimDeveloperCreate(BaseModel):
    developer_name: str

# ═════════════════════════════════════════════════════════════════════════════
# ESTADO
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/frontend", include_in_schema=False)
def serve_frontend():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="index.html não encontrado")
    return FileResponse(html_path, media_type="text/html")

@app.get("/", tags=["Estado"])
def root():
    return {"status": "online", "mensagem": "API Intermédia v2 a funcionar!"}

@app.get("/ping", tags=["Estado"])
def ping():
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "bd": "ligada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro de ligação: {str(e)}")

# ═════════════════════════════════════════════════════════════════════════════
# FACT_GAME_METRICS — colunas completas
# ═════════════════════════════════════════════════════════════════════════════

ALLOWED_ORDER = {
    "rawg_id","publisher_id","developer_id","appid","rating","metacritic",
    "rawg_estimated_playtime","price","discount","owners_medio","ccu_peak",
    "streams_ao_vivo","total_viewers","viewer_max","top_streamer_viewers"
}

@app.get("/metricas", tags=["Métricas de Jogos"])
def get_metricas(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
    metacritic_min: Optional[int] = None,
    metacritic_max: Optional[int] = None,
    price_max: Optional[float] = None,
    owners_min: Optional[int] = None,
    order_by: Optional[str] = Query(None),
    order_dir: Optional[str] = Query("desc"),
):
    conditions, params = [], []
    if rating_min is not None: conditions.append("rating >= %s"); params.append(rating_min)
    if rating_max is not None: conditions.append("rating <= %s"); params.append(rating_max)
    if metacritic_min is not None: conditions.append("metacritic >= %s"); params.append(metacritic_min)
    if metacritic_max is not None: conditions.append("metacritic <= %s"); params.append(metacritic_max)
    if price_max is not None: conditions.append("price <= %s"); params.append(price_max)
    if owners_min is not None: conditions.append("owners_medio >= %s"); params.append(owners_min)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    col = order_by if order_by in ALLOWED_ORDER else "rawg_id"
    direction = "ASC" if order_dir == "asc" else "DESC"

    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM fact_game_metrics {where} ORDER BY {col} {direction} NULLS LAST LIMIT %s OFFSET %s",
            params + [limit, offset]
        ).fetchall()
    return {"total": len(rows), "offset": offset, "data": rows}


@app.get("/metricas/{rawg_id}", tags=["Métricas de Jogos"])
def get_metrica(rawg_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM fact_game_metrics WHERE rawg_id = %s", (rawg_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return row


@app.post("/metricas", tags=["Métricas de Jogos"], status_code=201)
def create_metrica(data: GameMetricCreate):
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    cols = ", ".join(fields.keys())
    placeholders = ", ".join(["%s"] * len(fields))
    with get_conn() as conn:
        row = conn.execute(
            f"INSERT INTO fact_game_metrics ({cols}) VALUES ({placeholders}) RETURNING *",
            list(fields.values())
        ).fetchone()
    return row


@app.patch("/metricas/{rawg_id}", tags=["Métricas de Jogos"])
def update_metrica(rawg_id: int, data: GameMetricUpdate):
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    set_clause = ", ".join([f"{k} = %s" for k in fields])
    with get_conn() as conn:
        row = conn.execute(
            f"UPDATE fact_game_metrics SET {set_clause} WHERE rawg_id = %s RETURNING *",
            list(fields.values()) + [rawg_id]
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return row


@app.delete("/metricas/{rawg_id}", tags=["Métricas de Jogos"])
def delete_metrica(rawg_id: int):
    with get_conn() as conn:
        row = conn.execute("DELETE FROM fact_game_metrics WHERE rawg_id = %s RETURNING rawg_id", (rawg_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return {"message": f"Métrica {rawg_id} eliminada"}

# ═════════════════════════════════════════════════════════════════════════════
# DIM_GAMES
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/jogos", tags=["Jogos"])
def get_jogos(limit: int = Query(50, ge=1, le=1000), offset: int = Query(0, ge=0)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM dim_games ORDER BY rawg_id LIMIT %s OFFSET %s", (limit, offset)).fetchall()
    return {"total": len(rows), "data": rows}

@app.get("/jogos/{rawg_id}", tags=["Jogos"])
def get_jogo(rawg_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM dim_games WHERE rawg_id = %s", (rawg_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return row

@app.post("/jogos", tags=["Jogos"], status_code=201)
def create_jogo(data: DimGameCreate):
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    cols = ", ".join(fields.keys())
    placeholders = ", ".join(["%s"] * len(fields))
    with get_conn() as conn:
        row = conn.execute(f"INSERT INTO dim_games ({cols}) VALUES ({placeholders}) RETURNING *", list(fields.values())).fetchone()
    return row

@app.delete("/jogos/{rawg_id}", tags=["Jogos"])
def delete_jogo(rawg_id: int):
    with get_conn() as conn:
        row = conn.execute("DELETE FROM dim_games WHERE rawg_id = %s RETURNING rawg_id", (rawg_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return {"message": f"Jogo {rawg_id} eliminado"}

# ═════════════════════════════════════════════════════════════════════════════
# DIM_PUBLISHERS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/publishers", tags=["Publishers"])
def get_publishers(limit: int = Query(50, ge=1, le=1000), offset: int = Query(0, ge=0)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM dim_publishers ORDER BY publisher_id LIMIT %s OFFSET %s", (limit, offset)).fetchall()
    return {"total": len(rows), "data": rows}

@app.get("/publishers/{pub_id}", tags=["Publishers"])
def get_publisher(pub_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM dim_publishers WHERE publisher_id = %s", (pub_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Publisher não encontrado")
    return row

@app.post("/publishers", tags=["Publishers"], status_code=201)
def create_publisher(data: DimPublisherCreate):
    with get_conn() as conn:
        row = conn.execute("INSERT INTO dim_publishers (publisher_name) VALUES (%s) RETURNING *", (data.publisher_name,)).fetchone()
    return row

@app.delete("/publishers/{pub_id}", tags=["Publishers"])
def delete_publisher(pub_id: int):
    with get_conn() as conn:
        row = conn.execute("DELETE FROM dim_publishers WHERE publisher_id = %s RETURNING publisher_id", (pub_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Publisher não encontrado")
    return {"message": f"Publisher {pub_id} eliminado"}

# ═════════════════════════════════════════════════════════════════════════════
# DIM_DEVELOPERS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/developers", tags=["Developers"])
def get_developers(limit: int = Query(50, ge=1, le=1000), offset: int = Query(0, ge=0)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM dim_developers ORDER BY developer_id LIMIT %s OFFSET %s", (limit, offset)).fetchall()
    return {"total": len(rows), "data": rows}

@app.get("/developers/{dev_id}", tags=["Developers"])
def get_developer(dev_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM dim_developers WHERE developer_id = %s", (dev_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Developer não encontrado")
    return row

@app.post("/developers", tags=["Developers"], status_code=201)
def create_developer(data: DimDeveloperCreate):
    with get_conn() as conn:
        row = conn.execute("INSERT INTO dim_developers (developer_name) VALUES (%s) RETURNING *", (data.developer_name,)).fetchone()
    return row

@app.delete("/developers/{dev_id}", tags=["Developers"])
def delete_developer(dev_id: int):
    with get_conn() as conn:
        row = conn.execute("DELETE FROM dim_developers WHERE developer_id = %s RETURNING developer_id", (dev_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Developer não encontrado")
    return {"message": f"Developer {dev_id} eliminado"}

# ═════════════════════════════════════════════════════════════════════════════
# ANALÍTICOS
# ═════════════════════════════════════════════════════════════════════════════

JOIN_SELECT = """
    SELECT
        g.name AS jogo, g.slug,
        p.publisher_name AS publisher,
        d.developer_name AS developer,
        f.rating, f.metacritic, f.appid, f.rawg_id,
        f.price, f.discount, f.owners_medio, f.ccu_peak,
        f.rawg_estimated_playtime, f.streams_ao_vivo,
        f.total_viewers, f.viewer_max, f.top_streamer_viewers
    FROM fact_game_metrics f
    LEFT JOIN dim_games g ON g.rawg_id = f.rawg_id
    LEFT JOIN dim_publishers p ON p.publisher_id = f.publisher_id
    LEFT JOIN dim_developers d ON d.developer_id = f.developer_id
"""

@app.get("/analise/top-metacritic", tags=["Análise"])
def top_metacritic(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.metacritic IS NOT NULL ORDER BY f.metacritic DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-rating", tags=["Análise"])
def top_rating(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.rating IS NOT NULL ORDER BY f.rating DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-owners", tags=["Análise"])
def top_owners(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.owners_medio IS NOT NULL ORDER BY f.owners_medio DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-viewers", tags=["Análise"])
def top_viewers(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.total_viewers IS NOT NULL AND f.total_viewers > 0 ORDER BY f.total_viewers DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-ccu", tags=["Análise"])
def top_ccu(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.ccu_peak IS NOT NULL ORDER BY f.ccu_peak DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-price", tags=["Análise"])
def top_price(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.price IS NOT NULL AND f.price > 0 ORDER BY f.price DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top", tags=["Análise"])
def top_generic(
    col: str = Query("metacritic", description="Coluna a ordenar"),
    limit: int = Query(50, ge=1, le=1000)
):
    allowed = {"rating","metacritic","price","discount","owners_medio","ccu_peak",
               "rawg_estimated_playtime","streams_ao_vivo","total_viewers",
               "viewer_max","top_streamer_viewers","appid","rawg_id","publisher_id","developer_id"}
    if col not in allowed:
        raise HTTPException(status_code=400, detail=f"Coluna inválida: {col}")
    with get_conn() as conn:
        rows = conn.execute(
            JOIN_SELECT + f" WHERE f.{col} IS NOT NULL ORDER BY f.{col} DESC NULLS LAST LIMIT %s",
            (limit,)
        ).fetchall()
    return {"data": rows}

@app.get("/analise/top-discount", tags=["Análise"])
def top_discount(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.discount IS NOT NULL AND f.discount > 0 ORDER BY f.discount DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-playtime", tags=["Análise"])
def top_playtime(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.rawg_estimated_playtime IS NOT NULL ORDER BY f.rawg_estimated_playtime DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-viewer-max", tags=["Análise"])
def top_viewer_max(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.viewer_max IS NOT NULL AND f.viewer_max > 0 ORDER BY f.viewer_max DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-streams", tags=["Análise"])
def top_streams(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.streams_ao_vivo IS NOT NULL AND f.streams_ao_vivo > 0 ORDER BY f.streams_ao_vivo DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-streamer", tags=["Análise"])
def top_streamer(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.top_streamer_viewers IS NOT NULL AND f.top_streamer_viewers > 0 ORDER BY f.top_streamer_viewers DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/top-appid", tags=["Análise"])
def top_appid(limit: int = Query(10, ge=1, le=1000)):
    with get_conn() as conn:
        rows = conn.execute(JOIN_SELECT + " WHERE f.appid IS NOT NULL ORDER BY f.appid DESC NULLS LAST LIMIT %s", (limit,)).fetchall()
    return {"data": rows}

@app.get("/analise/stats", tags=["Análise"])
def stats_gerais():
    with get_conn() as conn:
        stats = conn.execute("""
            SELECT
                COUNT(*) AS total_jogos,
                ROUND(AVG(rating)::numeric, 2) AS rating_medio,
                ROUND(AVG(metacritic)::numeric, 2) AS metacritic_medio,
                ROUND(AVG(price)::numeric, 2) AS preco_medio,
                MAX(owners_medio) AS max_owners,
                MAX(ccu_peak) AS max_ccu,
                MAX(total_viewers) AS max_viewers
            FROM fact_game_metrics
        """).fetchone()
        pubs = conn.execute("SELECT COUNT(*) AS total FROM dim_publishers").fetchone()
        devs = conn.execute("SELECT COUNT(*) AS total FROM dim_developers").fetchone()
    return {**stats, "total_publishers": pubs["total"], "total_developers": devs["total"]}