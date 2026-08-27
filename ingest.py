"""YouTube Data API -> bda.db

  python ingest.py                 incremental (para no primeiro video ja conhecido)
  python ingest.py --full          backfill completo (~400 unidades de quota)
  python ingest.py --limit 200     amostra os N mais recentes (mede taxa de rejeicao)
  python ingest.py --dry           parseia e mostra o resumo, nao grava
  python ingest.py --reparse       re-parseia o que ja esta no banco, 0 de quota

Quota (10.000 unidades/dia): playlistItems 1/pagina de 50, videos 1/lote de 50.
NUNCA usar search.list -- custa 100 por chamada e trava em ~500 resultados.
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone

import httpx

import parse

API = "https://www.googleapis.com/youtube/v3"
CHANNEL = os.environ.get("BDA_CHANNEL", "UC12bjJeaHZy2AUBvPHJU3Ug")
DB = os.environ.get("BDA_DB", "bda.db")
quota = 0


def get(client, path, **params):
    global quota
    quota += 1
    r = client.get(f"{API}/{path}", params={**params, "key": os.environ["YT_API_KEY"]})
    if r.status_code != 200:
        sys.exit(f"YouTube API {r.status_code}: {r.text[:400]}")
    return r.json()


def video_ids(client, known, full, limit):
    """IDs da playlist de uploads, do mais novo para o mais antigo."""
    # ponytail: uploads playlist = UU + sufixo do canal. Invariante do YouTube,
    # economiza uma chamada channels.list. Se 404, e aqui que quebra.
    playlist, page, out, streak = "UU" + CHANNEL[2:], None, [], 0
    while True:
        d = get(client, "playlistItems", part="contentDetails", playlistId=playlist,
                maxResults=50, **({"pageToken": page} if page else {}))
        for it in d.get("items", []):
            vid = it["contentDetails"]["videoId"]
            out.append(vid)
            streak = streak + 1 if vid in known else 0
        if limit and len(out) >= limit:
            return out[:limit]
        if not full and streak >= 50:
            return out  # uma pagina inteira ja conhecida: o resto e passado
        page = d.get("nextPageToken")
        if not page:
            return out


def details(client, ids):
    for i in range(0, len(ids), 50):
        yield from get(client, "videos", part="snippet,contentDetails,statistics",
                       id=",".join(ids[i:i + 50]), maxResults=50).get("items", [])


def iso_seconds(d):
    """PT2H23M1S -> 8581"""
    n, total, mult = "", 0, {"H": 3600, "M": 60, "S": 1}
    for c in d.removeprefix("PT"):
        if c.isdigit():
            n += c
        else:
            total += int(n or 0) * mult.get(c, 0)
            n = ""
    return total


def mc_id(con, raw):
    slug = parse.slugify(raw)
    row = con.execute("SELECT mc_id FROM mc_alias WHERE raw=?", (slug,)).fetchone()
    if row:
        return row[0]
    con.execute("INSERT OR IGNORE INTO mc(slug,name) VALUES(?,?)", (slug, raw.strip()))
    mid = con.execute("SELECT id FROM mc WHERE slug=?", (slug,)).fetchone()[0]
    con.execute("INSERT OR IGNORE INTO mc_alias(raw,mc_id) VALUES(?,?)", (slug, mid))
    return mid


def index_video(con, vid, title, description):
    """Substitui as batalhas do video. Devolve quantas foram extraidas."""
    con.execute("DELETE FROM battle WHERE video_id=?", (vid,))
    con.execute("DELETE FROM parse_reject WHERE video_id=?", (vid,))
    found = parse.battles(title, description)
    for b in found:
        cur = con.execute(
            "INSERT INTO battle(video_id,start_s,end_s,phase,edition,edition_n,source)"
            " VALUES(?,?,?,?,?,?,?)",
            (vid, b["start_s"], b["end_s"], b["phase"], b["edition"],
             parse.edition_n(b["edition"]), b["source"]))
        for side, team in enumerate(b["teams"]):
            for name in team:
                con.execute("INSERT OR IGNORE INTO battle_mc(battle_id,mc_id,side) VALUES(?,?,?)",
                            (cur.lastrowid, mc_id(con, name), side))
    if not found:
        con.execute("INSERT INTO parse_reject(video_id,reason) VALUES(?,?)",
                    (vid, "compilacao sem capitulos" if parse.kind(title) == "compilation"
                     else "sem confronto no titulo"))
    return len(found)


def report(con, label):
    q = lambda s: con.execute(s).fetchone()[0]
    print(f"\n-- {label} --")
    print(f"videos {q('SELECT count(*) FROM video')} | batalhas {q('SELECT count(*) FROM battle')} "
          f"| MCs {q('SELECT count(*) FROM mc')} | rejeitados {q('SELECT count(*) FROM parse_reject')}")
    v = q("SELECT count(*) FROM video")
    if v:
        print(f"taxa de rejeicao: {q('SELECT count(*) FROM parse_reject') * 100 / v:.1f}%")
    print("top MCs:", ", ".join(
        f"{n}({c})" for n, c in con.execute(
            "SELECT m.name, count(*) c FROM battle_mc bm JOIN mc m ON m.id=bm.mc_id"
            " GROUP BY m.id ORDER BY c DESC LIMIT 15")))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--full", action="store_true")
    a.add_argument("--limit", type=int)
    a.add_argument("--dry", action="store_true")
    a.add_argument("--reparse", action="store_true")
    args = a.parse_args()

    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")  # SQLite ignora ON DELETE CASCADE sem isto
    con.executescript(open("schema.sql", encoding="utf-8").read())

    if args.reparse:
        rows = con.execute("SELECT id,title,description FROM video").fetchall()
        for vid, title, desc in rows:
            index_video(con, vid, title, desc or "")
        con.commit()
        return report(con, f"reparse de {len(rows)} videos (0 de quota)")

    known = {r[0] for r in con.execute("SELECT id FROM video")}
    with httpx.Client(timeout=30) as client:
        ids = video_ids(client, known, args.full, args.limit)
        todo = ids if (args.full or args.limit) else [i for i in ids if i not in known]
        print(f"{len(ids)} videos na playlist, {len(todo)} para buscar")
        now = datetime.now(timezone.utc).isoformat()
        for n, v in enumerate(details(client, todo), 1):
            s = v["snippet"]
            con.execute(
                "INSERT INTO video(id,title,description,published_at,duration_s,view_count,"
                "thumb,kind,fetched_at) VALUES(?,?,?,?,?,?,?,?,?)"
                " ON CONFLICT(id) DO UPDATE SET title=excluded.title,"
                " description=excluded.description, view_count=excluded.view_count,"
                " kind=excluded.kind, fetched_at=excluded.fetched_at",
                (v["id"], s["title"], s.get("description", ""), s["publishedAt"],
                 iso_seconds(v["contentDetails"]["duration"]),
                 int(v.get("statistics", {}).get("viewCount", 0)),
                 s["thumbnails"].get("medium", {}).get("url"),
                 parse.kind(s["title"]), now))
            try:
                index_video(con, v["id"], s["title"], s.get("description", ""))
            except Exception as e:  # 1 video ruim nao pode derrubar um run de 10 mil
                con.execute("DELETE FROM battle WHERE video_id=?", (v["id"],))
                con.execute("INSERT OR REPLACE INTO parse_reject(video_id,reason) VALUES(?,?)",
                            (v["id"], f"erro: {type(e).__name__}: {e}"[:180]))
            if n % 250 == 0 and not args.dry:
                print(f"  {n}/{len(todo)}...")
                con.commit()

    if args.dry:
        report(con, f"DRY RUN (quota gasta: {quota})")
        con.rollback()
    else:
        con.commit()
        report(con, f"gravado (quota gasta: {quota} de 10000)")


if __name__ == "__main__":
    main()
