"""Extrai batalhas dos titulos e das listas de capitulos do canal BDA.

Dois formatos, ambos verificados no canal:
  clipe:       "(HYPE) NEO, APOLLO E TAVIN X JOTAPE, GURI E BARRETO | GRANDE FINAL | BDA 8 ANOS"
  compilacao:  "464a BDA (BATE-VOLTA) | TODAS AS BATALHAS" + capitulos na descricao:
               "00:00 HOGUE X GRAFITEH"
"""
import re
import unicodedata

# Separador de times. O que protege nao e o maiusculo, e a exigencia de espaco
# dos DOIS lados: "WL BXD" nao tem, entao nao quebra. Os videos antigos do canal
# usam minusculo ("KANT (SP) x DEVILZINHA (RJ)") -- 2.5 mil batalhas dependem disso.
SIDES = re.compile(r"\s+(?:X|VS\.?)\s+", re.I)
MEMBERS = re.compile(r"\s*[,&]\s*|\s+E\s+", re.I)
# Segmentos: o formato novo usa " | ", o antigo usa " - " ("x Dyloko - Final - #BDA27")
SEGMENT = re.compile(r"\s*\|\s*|\s+-\s*")
CHAPTER = re.compile(r"^\s*((?:\d{1,2}:)?\d{1,2}:\d{2})\s+(\S.*?)\s*$")
COMPILATION = re.compile(r"TODAS AS BATALHAS", re.I)
# Quatro grafias no canal: "473ª BDA", "472 BDAª", "383ª BATALHA DA ALDEIA", "#BDA36".
# O #BDA36 exige digito colado, senao "BDA 10 ANOS" viraria edicao 10.
EDITION_N = re.compile(r"(\d+)\s*[aª]?\s*(?:BDA|BATALHA\s+DA\s+ALDEIA)|#?BDA(\d+)", re.I)

# Hype que antecede o confronto: "(MAIOR FINAL DA HISTORIA) " ou "\U0001f525PEGOU FOGO\U0001f525 "
_SYMS = r"[^\w\s(),.|@-]+"  # @ fora: "@tavin x @andrade" seria comido pelo par
_PAREN = re.compile(r"^\s*(?:\([^)]*\)|\[[^\]]*\])\s*")  # "(HYPE)" e "[Duelo De Geracoes]"
_PAIRED = re.compile(rf"^\s*({_SYMS})[^|]*?\1\s*")   # emoji ... mesmo emoji
_LEAD = re.compile(rf"^\s*{_SYMS}\s*")


def hms(t):
    """'01:08:25' -> 4105 ; '06:09' -> 369"""
    p = [int(x) for x in t.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def slugify(name):
    """'JOTAPE' -> 'jotape' ; 'WL BXD' -> 'wl-bxd'"""
    n = "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c))
    return re.sub(r"[\s_-]+", "-", re.sub(r"[^\w\s-]", "", n).strip().lower())


def strip_hype(title):
    prev = None
    while prev != title:
        prev = title
        title = _LEAD.sub("", _PAIRED.sub("", _PAREN.sub("", title)))
    return title.strip()


def split_sides(matchup):
    """'NEO, APOLLO E TAVIN X JOTAPE' -> [['NEO','APOLLO','TAVIN'], ['JOTAPE']]

    Aceita 3+ lados: o canal tem 127 batalhas de tres ("Aline x DuRap x Harry").
    """
    parts = SIDES.split(matchup)
    if len(parts) < 2:
        return None  # nao e confronto
    teams = [[m.strip() for m in MEMBERS.split(p) if m.strip()] for p in parts]
    if not all(teams):
        return None
    # Legenda de Short cai aqui ("... x KROY SEMPRE PEGA FOGO! #bda #freestyle").
    # Nome de MC e curto e nao tem hashtag; o mais longo real tem 19 chars.
    if any(len(n) > 22 or "#" in n for t in teams for n in t):
        return None
    return teams


def parse_title(title):
    """-> (teams, phase, edition) ou None"""
    segs = [s.strip() for s in SEGMENT.split(strip_hype(title)) if s.strip()]
    for i, seg in enumerate(segs):
        teams = split_sides(seg)
        if not teams:
            continue
        rest = segs[i + 1:]
        # A edicao e o segmento que carrega numero de edicao -- nao da para assumir
        # que e o ultimo: "109a Batalha da Aldeia | Barueri | SP" termina em "SP".
        k = next((j for j, x in enumerate(rest) if edition_n(x)), None)
        if k is None and len(rest) > 1:
            k = len(rest) - 1
        return teams, (rest[0] if rest and k != 0 else None), (rest[k] if k is not None else None)
    return None


def edition_n(edition):
    m = EDITION_N.search(edition or "")
    return int(m.group(1) or m.group(2)) if m else None


def kind(title):
    if COMPILATION.search(title):
        return "compilation"
    return "clip" if parse_title(title) else "other"


def battles(title, description):
    """Todas as batalhas de um video: start_s, end_s, teams, phase, edition, source."""
    if COMPILATION.search(title):
        edition = strip_hype(title).split("|")[0].strip()
        # dict.fromkeys mata linha literalmente repetida, mas preserva duas
        # batalhas DIFERENTES no mesmo segundo -- o canal erra a minutagem
        # (ex. nDj6C6dLvzU tem duas em 01:22:58) e as duas sao reais.
        ch = sorted(dict.fromkeys(
            (hms(m.group(1)), m.group(2))
            for m in (CHAPTER.match(l) for l in (description or "").splitlines()) if m))
        starts = sorted({s for s, _ in ch})
        # fim = proximo segundo MAIOR, senao empate viraria trecho de duracao zero
        nxt = dict(zip(starts, starts[1:]))
        return [dict(start_s=start, end_s=nxt.get(start), teams=teams,
                     phase=None, edition=edition, source="chapter")
                for start, label in ch
                # FREESTYLE / ENTREVISTA / INTRODUCAO caem fora sozinhos
                for teams in [split_sides(label)] if teams]
    p = parse_title(title)
    if not p:
        return []
    teams, phase, edition = p
    return [dict(start_s=0, end_s=None, teams=teams, phase=phase,
                 edition=edition, source="title")]
