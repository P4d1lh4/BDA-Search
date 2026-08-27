"""API do BDA Index.  uvicorn api:app --reload"""
import os
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

DB = os.environ.get("BDA_DB", "bda.db")
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, check_same_thread=False)
con.row_factory = sqlite3.Row
con.execute("PRAGMA foreign_keys = ON")  # SQLite ignora ON DELETE CASCADE sem isto
app = FastAPI(title="BDA Index")

BATTLE_COLS = """b.id, b.video_id, b.start_s, b.end_s, b.phase, b.edition, b.edition_n,
                 b.source, v.title, v.thumb, v.published_at, v.view_count, v.duration_s"""


def with_teams(rows):
    """Anexa os dois lados de cada batalha. Uma query para o lote inteiro."""
    out = [dict(r) | {"teams": []} for r in rows]
    by_id = {b["id"]: b for b in out}
    if by_id:
        qs = ",".join("?" * len(by_id))
        for r in con.execute(
                f"SELECT bm.battle_id, bm.side, m.slug, m.name FROM battle_mc bm"
                f" JOIN mc m ON m.id = bm.mc_id WHERE bm.battle_id IN ({qs})"
                f" ORDER BY bm.side", list(by_id)):
            t = by_id[r["battle_id"]]["teams"]
            while len(t) <= r["side"]:
                t.append([])
            t[r["side"]].append({"slug": r["slug"], "name": r["name"]})
    return out


@app.get("/api/mcs")
def mcs(q: str = "", limit: int = 50):
    """Autocomplete. ~600 MCs -- LIKE responde em microssegundos, FTS5 seria peso morto."""
    return [dict(r) for r in con.execute(
        "SELECT m.slug, m.name, count(*) battles FROM mc m JOIN battle_mc bm ON bm.mc_id = m.id"
        " WHERE m.slug LIKE ? GROUP BY m.id ORDER BY battles DESC LIMIT ?",
        (f"%{q.lower()}%", limit))]


@app.get("/api/mcs/{slug}")
def mc(slug: str):
    row = con.execute("SELECT id, slug, name FROM mc WHERE slug = ?", (slug,)).fetchone()
    if not row:
        raise HTTPException(404, "MC nao encontrado")
    battles = with_teams(con.execute(
        f"SELECT {BATTLE_COLS} FROM battle_mc bm"
        " JOIN battle b ON b.id = bm.battle_id JOIN video v ON v.id = b.video_id"
        " WHERE bm.mc_id = ? ORDER BY v.published_at DESC, b.start_s", (row["id"],)))
    return {"mc": dict(row), "battles": battles}


@app.get("/api/h2h/{a}/{b}")
def h2h(a: str, b: str):
    """Confronto direto: mesma batalha, lados opostos."""
    battles = with_teams(con.execute(
        f"SELECT {BATTLE_COLS} FROM battle_mc x"
        " JOIN battle_mc y ON y.battle_id = x.battle_id AND y.side != x.side"
        " JOIN battle b ON b.id = x.battle_id JOIN video v ON v.id = b.video_id"
        " JOIN mc ma ON ma.id = x.mc_id JOIN mc mb ON mb.id = y.mc_id"
        " WHERE ma.slug = ? AND mb.slug = ? ORDER BY v.published_at DESC", (a, b)))
    return {"a": a, "b": b, "battles": battles}


@app.get("/api/stats")
def stats():
    """Numeros do cabecalho. Uma linha, o cliente busca uma vez por sessao."""
    return dict(con.execute(
        "SELECT (SELECT count(*) FROM battle) battles,"
        " (SELECT count(DISTINCT mc_id) FROM battle_mc) mcs,"
        " min(b.edition_n) ed_min, max(b.edition_n) ed_max,"
        " min(v.published_at) first_at, max(v.published_at) last_at"
        " FROM battle b JOIN video v ON v.id = b.video_id").fetchone())


@app.get("/api/editions")
def editions(limit: int = 12):
    """Carrossel das ultimas edicoes."""
    return [dict(r) for r in con.execute(
        "SELECT b.edition_n n, count(*) battles, max(v.published_at) published_at"
        " FROM battle b JOIN video v ON v.id = b.video_id WHERE b.edition_n IS NOT NULL"
        " GROUP BY b.edition_n ORDER BY b.edition_n DESC LIMIT ?", (limit,))]


@app.get("/api/editions/{n}")
def edition(n: int):
    return {"edition_n": n, "battles": with_teams(con.execute(
        f"SELECT {BATTLE_COLS} FROM battle b JOIN video v ON v.id = b.video_id"
        " WHERE b.edition_n = ? ORDER BY v.published_at, b.start_s", (n,)))}


@app.get("/api/pairs")
def pairs(limit: int = 8):
    """Confrontos mais fartos.  side desigual: parceiro de time nunca vira par.
    min/max no JOIN canonizam o par -- senao NEO x PRADO e PRADO x NEO viram
    dois grupos, porque quem fica no lado 0 muda de batalha para batalha."""
    return [dict(r) for r in con.execute(
        "SELECT m1.slug a, m1.name an, m2.slug b, m2.name bn, count(*) n"
        " FROM battle_mc x JOIN battle_mc y ON y.battle_id = x.battle_id AND y.side > x.side"
        " JOIN mc m1 ON m1.id = min(x.mc_id, y.mc_id)"
        " JOIN mc m2 ON m2.id = max(x.mc_id, y.mc_id)"
        " GROUP BY m1.id, m2.id ORDER BY n DESC LIMIT ?", (limit,))]


if os.path.isdir("web"):
    app.mount("/", StaticFiles(directory="web", html=True), name="web")
