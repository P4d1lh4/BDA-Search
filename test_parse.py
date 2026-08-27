"""Asserts sobre titulos e capitulos REAIS capturados do canal BDA."""
import parse

# --- capitulos reais da 464a BDA (video D_b2zxoZjHM) ---
DESC_464 = """BATALHA DA ALDEIA - A MAIOR BATALHA DE RIMAS DO BRASIL

Contato: contato@batalhaaldeia.com.br
https://www.amazon.com.br/stores/Phil...

464a BDA (BATE-VOLTA) | TODAS AS BATALHAS

00:00 HOGUE X GRAFITEH
06:09 WL BXD X GOMES
12:46 JAPA X DEVILZINHA
22:33 ZAP X TITO
31:52 NEO X NAIA
39:23 PRADO X LEVINSK
49:46 MT X AJOTA
01:01:45 BRENNUZ X POETA GABRIELA
01:08:25 TITO X GRAFITEH
01:15:36 AJOTA X JAPA
01:25:10 NEO X WL BXD
01:37:25 LEVINSK X BRENNUZ
01:48:19 NEO X AJOTA
01:58:22 GRAFITEH X LEVINSK
02:08:28 LEVINSK X NEO
02:20:50 FREESTYLE
02:23:01 ENTREVISTA
"""

b = parse.battles("464a BDA (BATE-VOLTA) | TODAS AS BATALHAS", DESC_464)
assert len(b) == 15, f"esperava 15 batalhas, veio {len(b)}"          # FREESTYLE/ENTREVISTA fora
assert b[0]["teams"] == [["HOGUE"], ["GRAFITEH"]]
assert b[0]["start_s"] == 0 and b[0]["end_s"] == 369                  # deep-link tem fim
assert b[1]["teams"] == [["WL BXD"], ["GOMES"]], "X interno de BXD quebrou o split"
assert b[7]["start_s"] == 3705, "timestamp HH:MM:SS mal convertido"   # 01:01:45
assert b[7]["teams"] == [["BRENNUZ"], ["POETA GABRIELA"]]
assert b[-1]["end_s"] == 8450, "ultima batalha deve terminar no FREESTYLE"  # 02:20:50
assert all(x["edition"] == "464a BDA (BATE-VOLTA)" for x in b)
assert parse.edition_n(b[0]["edition"]) == 464

# --- o canal erra a minutagem: duas batalhas DIFERENTES no mesmo segundo ---
# (video real nDj6C6dLvzU, "BDA 446 (EDICAO DE DUPLAS)")
DUP = """01:22:58 LEVINSK E SOFIA X APOLLO E BTC
01:22:58 MAGRAO E PRADO X XAMUEL E TUBARAO
01:35:00 NEO X PRADO
01:35:00 NEO X PRADO
"""
d = parse.battles("BDA 446 | TODAS AS BATALHAS", DUP)
assert len(d) == 3, f"esperava 3 (2 reais no mesmo seg + 1 dedup literal), veio {len(d)}"
assert d[0]["start_s"] == d[1]["start_s"] == 4978, "as duas de 01:22:58 tem que sobreviver"
assert d[0]["end_s"] == d[1]["end_s"] == 5700, "fim = proximo segundo MAIOR, nao o empate"
assert d[2]["end_s"] is None

# --- titulos reais de clipes individuais ---
def one(title):
    r = parse.battles(title, "")
    assert len(r) == 1, f"nao parseou: {title!r}"
    return r[0]

t = one("PRADO X YOUNGUI | Grande Final | 473a BDA (Edicao Seletiva)")
assert t["teams"] == [["PRADO"], ["YOUNGUI"]]
assert t["phase"] == "Grande Final"
assert parse.edition_n(t["edition"]) == 473
assert t["start_s"] == 0 and t["source"] == "title"

t = one("(MAIOR FINAL DA HISTORIA) NEO, APOLLO E TAVIN X JOTAPE, GURI E BARRETO | GRANDE FINAL | BDA 8 ANOS")
assert t["teams"] == [["NEO", "APOLLO", "TAVIN"], ["JOTAPE", "GURI", "BARRETO"]], t["teams"]
assert t["edition"] == "BDA 8 ANOS"

t = one("\U0001f525PEGOU FOGO\U0001f525 JHONY, BRENNUZ E GRAFITEH X KROY, BASK E JAPA | PRIMEIRA FASE | BDA 9 ANOS")
assert t["teams"] == [["JHONY", "BRENNUZ", "GRAFITEH"], ["KROY", "BASK", "JAPA"]], t["teams"]

t = one("(VIBE INSANA) ZULUZAO, SCHULER E XAMUEL X CHRIS, DEVILZINHA E WINNIT | PRIMEIRA FASE | BDA 7 ANOS")
assert t["teams"][1] == ["CHRIS", "DEVILZINHA", "WINNIT"]

# 2 segmentos: nao inventa edicao repetindo a fase
t = one("PRADO X NEO | GRANDE FINAL")
assert t["phase"] == "GRANDE FINAL" and t["edition"] is None

# --- ordinal aparece nas DUAS ordens no canal ---
assert parse.edition_n("473ª BDA (Edicao Seletiva)") == 473
assert parse.edition_n("472 BDAª (Edicao 45 segundos)") == 472, "ordinal depois da sigla"
assert parse.edition_n("464a BDA (BATE-VOLTA)") == 464
for nao in ["BDA 8 ANOS", "Etapa Manaus", "SELETIVA DA BDA 10 ANOS", "BDA NO JOAO ROCK 2026"]:
    assert parse.edition_n(nao) is None, f"{nao!r} nao e edicao numerada"

# --- batalha de tres lados (127 reais no canal) ---
t = one("Aline x DuRap x Harry | PRE FASE | 149a Batalha da Aldeia | Barueri")
assert t["teams"] == [["Aline"], ["DuRap"], ["Harry"]], t["teams"]
assert parse.edition_n(t["edition"]) == 149, "edicao nao e o ultimo segmento aqui (termina em Barueri)"
assert t["phase"] == "PRE FASE"

# --- formatos antigos do canal ---
t = one("KANT (SP) x DEVILZINHA (RJ)  | PRIMEIRA FASE | 383a BATALHA DA ALDEIA")
assert t["teams"] == [["KANT (SP)"], ["DEVILZINHA (RJ)"]], "x minusculo tem que valer"
assert parse.edition_n(t["edition"]) == 383
t = one("Refel & Motta x LC & Vinicin (BH)  | SEGUNDA FASE | 53a Batalha da Aldeia")
assert t["teams"] == [["Refel", "Motta"], ["LC", "Vinicin (BH)"]], t["teams"]
t = one("Thiago x Dyloko - Grande Final - #BDA27")
assert t["teams"] == [["Thiago"], ["Dyloko"]] and t["phase"] == "Grande Final"
assert parse.edition_n(t["edition"]) == 27, "#BDA27"
assert parse.edition_n("BDA 10 ANOS") is None, "aniversario nao e edicao 10"

# --- o que NAO pode virar batalha ---
for junk in ["BATALHA DA ALDEIA #470 - Edicao de duplas mistas",   # live da Podpah, sem MCs
             "MELHORES RIMAS de TODOS OS ANIVERSARIOS BDA!",
             "Batalha da Aldeia - Zuluzao | Alva |JayA Luuck |Tavin"]:
    assert parse.battles(junk, "") == [], f"lixo virou batalha: {junk!r}"
    assert parse.kind(junk) == "other"

assert parse.kind("PRADO X YOUNGUI | Grande Final | 473a BDA") == "clip"
assert parse.kind("464a BDA | TODAS AS BATALHAS") == "compilation"

# --- normalizacao de MC ---
assert parse.slugify("JOTAPÊ".replace("Ê", "Ê")) == "jotape"
assert parse.slugify("WL BXD") == "wl-bxd"
assert parse.slugify("POETA GABRIELA") == "poeta-gabriela"

print("ok - todos os asserts passaram")
