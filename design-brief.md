Preciso do design de um site chamado **BDA Index**. É um índice de batalhas de
rap do canal da Batalha da Aldeia (BDA) no YouTube — a maior batalha de rimas do
Brasil, que rola toda segunda em Barueri (SP) desde 2016.

O site precisa parecer **parte da BDA**, não um projeto paralelo. Extraí a
identidade visual direta do site oficial (batalhadaaldeia.com.br) e ela está
especificada abaixo. Siga à risca.

---

# 1. Identidade visual (medida no site oficial, não invente)

## Cores
```
#000000   fundo da página — preto puro, não cinza-escuro
#1A1A1A   superfície de cards e blocos
#0F0F0F   superfície mais funda (seções alternadas)
#F59230   LARANJA — a cor da marca. É o único acento forte do site.
#FFFFFF   texto primário
#9CA3AF   texto secundário
#6B7280   texto terciário / metadados
#222222   bordas (1px solid) — o padrão dominante
#333333   bordas de destaque
#DC2626   vermelho, acento secundário e raro
```
O site é preto e laranja. Não introduza uma terceira cor de marca.

## Tipografia
- **Sora** (Google Fonts) para absolutamente todo o texto. Pesos 300 e 400 —
  o site oficial não usa bold pesado. Base 16px, metadados 12px, títulos de
  seção 42px e 36px.
- **Sedgwick Ave Display** (Google Fonts, estilo tag de grafite) com uso muito
  restrito e específico: **só para rótulos de edição e etiquetas curtas**,
  sempre em laranja `#F59230`, sempre pequeno (16–18px). No site oficial ela
  aparece exatamente assim: `BDA 473`, `campeões`. Nunca em títulos grandes,
  nunca em texto corrido. É uma assinatura, não uma fonte de display.

Esse contraste é a alma da estética: tipografia sóbria e limpa, com o grafite
entrando só como carimbo.

## Formas
- **Cantos retos são o padrão.** O site usa 0px de raio na esmagadora maioria
  dos elementos. Nada de cards arredondados por toda parte.
- **Pílulas (raio total)** para badges, tags e contadores — é a exceção, e é
  frequente.
- 8px de raio só em cards de mídia.
- Bordas de 1px em `#222222` separam blocos, no lugar de sombras.
- Gradientes existem só como fade preto sobre foto e nas bordas de carrossel.
  Nenhum gradiente colorido.

## Padrões de composição do site oficial
- Carrossel horizontal de edições com máscara de fade preto nas laterais.
- Marquee de texto repetido em loop (`PARTICIPE PARTICIPE PARTICIPE...`).
- Badges de nível com emoji e pílula (`🟣 Lendário`, `🟠 Épico`, `🏆`).
- Números grandes em laranja como âncora visual (`+2M seguidores`,
  `485 batalhas realizadas`).
- Fotografia real de evento, recorte largo, sempre com fade preto por cima.

---

# 2. O problema que o site resolve

O canal tem 10.556 vídeos. Para ver todas as batalhas de um MC específico, hoje
é garimpo manual na busca do YouTube. Pior quando a batalha está enterrada no
minuto 1h25 de uma compilação de 2h30.

O BDA Index resolve: escolhe o MC, vê todas as batalhas dele, cada uma abrindo
no segundo exato.

---

# 3. Os dados são reais e já existem — projete para eles

O índice já está construído. Não invente placeholder.

| | |
|---|---|
| batalhas indexadas | 7.877 |
| MCs | 1.656 |
| edições cobertas | 6ª a 473ª (2016 a 2026) |
| batalha mais vista | 17 milhões de views |

**Distribuição de MCs — isso define a tela principal:**
- BIG MIKE 594 batalhas · APOLLO 467 · REFEL 451 · LEVINSK 448 · KANT 441 ·
  GURI 417 · PRADO 366 · AJOTA 331 · DURAP 290 · NEO 267
- 954 MCs têm 2 ou mais batalhas
- 702 MCs têm exatamente 1 — e ~2% dessa cauda é ruído de legenda de Short
  (nomes tipo `DEVILZINHA PEGOU FOGO!`). A lista tem que ser ordenada por
  número de batalhas, nunca alfabética, para o ruído afundar sozinho.

**Formatos de batalha que cabem no mesmo card:**
```
NEO x JAYA                                     1 contra 1
LEVINSK & SOFIA x APOLLO & BTC                 duplas
NEO, APOLLO E TAVIN x JOTAPÊ, GURI E BARRETO   trios (até 3 por lado)
ALINE x DURAP x HARRY                          três lados (128 no acervo)
```

**Campos disponíveis por batalha:** thumbnail do YouTube (320x180), título do
vídeo, data, views, fase, edição, segundo de início e de fim, e os MCs de cada
lado.

**Campos que NÃO existem — não projete nada que dependa deles:**
- Não há foto, avatar ou bio de MC. Nenhuma. A identidade visual de um MC tem
  que sair só do nome — e aqui a Sedgwick Ave Display pode trabalhar.
- **Não há vencedor de batalha, nem ranking, nem W/L.** O site oficial tem
  campeão por *edição*, mas isso não está neste índice e não dá para inferir
  quem ganhou uma batalha individual.
- O campo "fase" está bagunçado na fonte: 214 valores distintos, com
  `Primeira fase`, `1ª FASE` e `PRIMEIRA FASE` convivendo.

---

# 4. As três telas

**1. Escolher o MC** — a porta de entrada. Busca que filtra conforme digita,
sobre 1.656 nomes. Precisa servir tanto quem já sabe o nome quanto quem quer
navegar e descobrir.

**2. Página do MC** — a tela que importa. Lista cronológica de todas as batalhas
dele. BIG MIKE tem 594: a lista é longa e a pessoa escaneia, não lê. Cada item
precisa entregar rápido: contra quem, que edição, quando, e se está dentro de
uma compilação (aí mostra o timestamp, ex. `em 01:25:10`). Clicar toca o vídeo
ali mesmo, já no ponto certo.

Detalhe que não pode parecer bug: a mesma batalha pode aparecer duas vezes —
uma como capítulo da transmissão completa, outra como clipe individual editado.
São duas formas legítimas de assistir, e o design precisa deixar isso legível.

**3. Confronto direto** — MC A contra MC B, todos os encontros ao longo dos
anos. NEO x PRADO, por exemplo, tem 13 confrontos desde 2018.

---

# 5. Restrições técnicas

- O vídeo toca por embed oficial do YouTube (iframe 16:9). Player não
  customizável, vídeo não baixável. Todo card precisa ter saída para o YouTube.
- Thumbnails vêm do YouTube em 320x180, com enquadramento e qualidade
  variáveis. Nada de hero full-bleed dependendo de imagem boa.
- **Mobile em primeiro lugar.** O público assiste batalha no celular.
- Site público de fã: sem login, sem conta de usuário.

---

# 6. O que eu preciso receber

As três telas, em mobile e desktop, com os estados difíceis resolvidos:
lista de 500+ itens, busca sem resultado, MC com uma única batalha, e batalha
de três lados.

Lembre que isto é uma ferramenta de consulta antes de ser um pôster: as pessoas
chegam procurando algo específico em listas longas. Legibilidade e densidade
ganham de efeito visual — mas dentro da estética preto-e-laranja da BDA, não em
um dashboard corporativo genérico.
