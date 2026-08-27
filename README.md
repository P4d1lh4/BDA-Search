# BDA Index

Escolhe um MC, vê todas as batalhas dele — cada uma abrindo no segundo exato,
inclusive as enterradas dentro das compilações de 2h30.

Indexa o canal oficial [BDA](https://www.youtube.com/@BatalhaDaAldeia)
(~10 mil vídeos) por dois caminhos:

| Formato | Fonte dos MCs |
|---|---|
| `PRADO X YOUNGUI \| Grande Final \| 473ª BDA` | título |
| `464ª BDA \| TODAS AS BATALHAS` + `00:00 HOGUE X GRAFITEH` | capítulos da descrição |

## Setup

1. Chave da API — em https://console.cloud.google.com/ crie um projeto,
   ative **YouTube Data API v3**, gere uma chave em *Credenciais*.
   Restrinja a chave a essa API. **Ela nunca vai para o browser.**

```bash
pip install -r requirements.txt
export YT_API_KEY=sua_chave_aqui
```

2. Amostra primeiro (~8 unidades de quota), para medir a taxa de rejeição:

```bash
python ingest.py --limit 200 --dry
```

**~30% de rejeicao e o normal aqui** (medido: 30,3% nos 10.556 videos). O
canal publica muito conteudo que nao e batalha: pixathons, entrevistas do
campeao, freestyles, "melhores rimas", anuncios de trio, shorts. Isso e o
parser acertando, nao errando.

O sinal de problema de verdade e um titulo rejeitado que **contem** confronto:

```sql
SELECT v.title FROM parse_reject p JOIN video v ON v.id = p.video_id
WHERE v.title LIKE '% X %' OR v.title LIKE '% VS %';
```
Se essa query voltar linhas, falta um caso em `parse.py`. Na amostra de 200
ela voltou 2 de 10.556 -- e os 2 eram bug meu, ja corrigido.

## Numeros do backfill (medidos, agosto de 2026)

| | |
|---|---|
| videos na playlist | 10.556 |
| batalhas indexadas | 7.960 |
| MCs | 1.840 |
| edicoes cobertas | 6ª a 473ª |
| quota gasta | 424 de 10.000 |
| rejeitados (nao sao batalha) | 3.203 |
| titulos rejeitados contendo confronto | 0 |

O canal usa formatos diferentes conforme a epoca, e o parser cobre todos:

```
Refel x Thyto -1ª FASE - #BDA36              (2017: minusculo, segmento com " - ")
Refel & Motta x LC & Vinicin (BH)            (times com "&")
KANT (SP) x DEVILZINHA (RJ) | 383ª BATALHA DA ALDEIA   (edicao por extenso)
Aline x DuRap x Harry | 149ª Batalha da Aldeia         (tres lados, 128 no acervo)
NEO, APOLLO E TAVIN X JOTAPÊ, GURI E BARRETO | BDA 8 ANOS
```

3. Backfill completo dos 10 mil vídeos (~400 de 10.000 unidades diárias):

```bash
python ingest.py --full
```

4. Sobe:

```bash
python -m uvicorn api:app --port 8000
```

## Manutenção

```bash
python ingest.py            # incremental, ~4 unidades (cron semanal)
python ingest.py --full     # refresh mensal: politica do YouTube exige revalidar
                            # dados armazenados a cada 30 dias
python ingest.py --reparse  # re-parseia o que ja esta no banco, 0 de quota
```

**Juntar MCs duplicados** (`NEO` e `NEO ZN` são a mesma pessoa):

Acontece de verdade — na amostra apareceram `PRADO` e `PRADO (SP)` separados:

```sql
UPDATE mc_alias SET mc_id = (SELECT id FROM mc WHERE slug='prado') WHERE raw='prado-sp';
```
depois `python ingest.py --reparse`. É por isso que `video` guarda a descrição
crua — recurar não custa quota.

## Armadilhas

- **Nunca usar `search.list`**: 100 unidades por chamada e trava em ~500
  resultados. Indexar por busca custaria 20.000 unidades e viria incompleto.
  A playlist de uploads (`UU…`) é o único caminho viável.
- **Não existe dado de vencedor** em lugar nenhum — nem título, nem descrição.
  Ranking W/L só com curadoria manual.
- Os vídeos `BATALHA DA ALDEIA #NNN` estão no canal PodpahTV e **não têm
  capítulos com MCs**. Por isso o índice usa só o canal oficial.
- **SQLite ignora `ON DELETE CASCADE` sem `PRAGMA foreign_keys = ON`.** Sem
  isso, cada `--reparse` deixa órfãos em `battle_mc` e as contagens de batalha
  por MC inflam para sempre. O pragma está em `ingest.py` e `api.py` — se
  abrir o banco por fora, ligue ele também.
- O canal escreve o ordinal em quatro grafias: `473ª BDA`, `472 BDAª`,
  `383ª BATALHA DA ALDEIA`, `#BDA36`.
- **A edicao nem sempre e o ultimo segmento**: `109ª Batalha da Aldeia | Barueri | SP`
  termina em `SP`. Por isso o parser procura o segmento que tem numero de edicao.
- O canal **erra minutagem**: `nDj6C6dLvzU` tem duas batalhas diferentes marcadas
  em `01:22:58`. As duas sao reais e as duas ficam no indice — por isso `battle`
  nao tem `UNIQUE(video_id, start_s)`. Os dois deep-links apontam para o mesmo
  ponto porque a fonte esta errada e nao da para saber qual e qual.
- Uma mesma batalha pode aparecer **duas vezes**: uma como capitulo da compilacao
  e outra como clipe individual. E proposital — o clipe e editado, o capitulo tem
  o contexto da transmissao. A UI diferencia (o capitulo mostra "em 48:07").

## Testes

```bash
python test_parse.py
```
Asserts sobre títulos e capítulos reais do canal, incluindo `WL BXD X GOMES`
(o `X` interno de `BXD` não pode quebrar o split) e `🔥PEGOU FOGO🔥` como prefixo.
