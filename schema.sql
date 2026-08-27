-- Camada crua: exatamente o que a API do YouTube devolveu. O parser nunca muta.
-- Reprocessar o parsing custa 0 de quota porque a descricao fica aqui.
CREATE TABLE IF NOT EXISTS video (
  id           TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  description  TEXT,
  published_at TEXT,
  duration_s   INTEGER,
  view_count   INTEGER,
  thumb        TEXT,
  kind         TEXT,           -- clip | compilation | other
  fetched_at   TEXT            -- politica do YouTube: refresh a cada 30 dias
);

CREATE TABLE IF NOT EXISTS mc (
  id   INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

-- Knob manual de curadoria: aponte 'neo-zn' para o id do NEO e rode --reparse.
CREATE TABLE IF NOT EXISTS mc_alias (
  raw    TEXT PRIMARY KEY,
  mc_id  INTEGER NOT NULL REFERENCES mc(id)
);

CREATE TABLE IF NOT EXISTS battle (
  id         INTEGER PRIMARY KEY,
  video_id   TEXT NOT NULL REFERENCES video(id) ON DELETE CASCADE,
  start_s    INTEGER NOT NULL,
  end_s      INTEGER,
  phase      TEXT,
  edition    TEXT,
  edition_n  INTEGER,
  source     TEXT              -- title | chapter
);

CREATE TABLE IF NOT EXISTS battle_mc (
  battle_id INTEGER NOT NULL REFERENCES battle(id) ON DELETE CASCADE,
  mc_id     INTEGER NOT NULL REFERENCES mc(id),
  side      INTEGER NOT NULL,
  PRIMARY KEY (battle_id, mc_id)
);

CREATE TABLE IF NOT EXISTS parse_reject (
  video_id TEXT PRIMARY KEY REFERENCES video(id) ON DELETE CASCADE,
  reason   TEXT
);

CREATE INDEX IF NOT EXISTS ix_battle_mc_mc    ON battle_mc(mc_id);
CREATE INDEX IF NOT EXISTS ix_battle_video    ON battle(video_id);
CREATE INDEX IF NOT EXISTS ix_video_published ON video(published_at DESC);
