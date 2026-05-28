# Memoria do Projeto - Guia Vila Mascote

Plano inicial:

- Criar um site igual ao Guia Campo Belo, mas voltado para o bairro da Vila Mascote, em Sao Paulo.
- O novo site vai se chamar **Guia Vila Mascote**.
- O projeto deve ficar dentro desta pasta: `guia vila mascote`.
- A ideia e usar o Guia Campo Belo como referencia de estrutura, visual e funcionamento, adaptando nome, textos, conteudo e identidade para Vila Mascote.

Contexto registrado em 16/05/2026.

---
**Atualização (17/05/2026):**

- **Levantamento de Dados:** Criamos um banco de dados inicial (`guia_vila_mascote.csv`) através de pesquisa web contendo 43 estabelecimentos reais do bairro, extraindo contatos (WhatsApp, Instagram) e segmentando os locais.
- **Nova Arquitetura de Categorias:** Diferente do Campo Belo (que era 90% focado em gastronomia), a Vila Mascote possui um ecossistema mais diverso (escolas, estética, pets, serviços). Para manter o design limpo, implementamos um **sistema de 2 níveis**:
  1. **Macro-Categorias:** 6 cards grandes na tela inicial (Gastronomia, Saúde/Beleza, Compras, Educação, Pet, Serviços).
  2. **Micro-Categorias (Pills):** Ao clicar em um card macro, a tela transiciona e revela os filtros específicos (ex: Japonês, Pizzaria, etc.) e os cards dos estabelecimentos correspondentes.
- **Desenvolvimento da UI:** Criados de forma isolada nesta pasta os arquivos `index.html`, `style.css` (tema Navy + Gold herdado) e `script.js` contendo a nova lógica de renderização em Javascript Vanilla.

---
**Atualização (28/05/2026):**

- **Extração Instagram @vila.mascote via Apify:** Rodamos o Actor oficial `apify/instagram-scraper` com limite de 100 posts públicos do perfil.
- **Arquivos gerados:** `data/vila_mascote_instagram_posts_raw.json` com o retorno bruto, `data/vila_mascote_instagram_posts.csv` com 100 posts normalizados, `data/vila_mascote_instagram_negocios.csv` com 57 negócios/contatos consolidados e `data/vila_mascote_instagram_novos_candidatos.csv` com 41 candidatos ainda não marcados como presentes no guia.
- **Campos extraídos:** nome provável, Instagram principal, categoria/subcategoria provável, telefone, email, endereço, oferta/cupom, data, métricas básicas e link do post de origem.
- **Observação:** A planilha consolidada marca `ja_no_guia` para ajudar a separar negócios já presentes na base atual de novos candidatos. Categorias e nomes são inferidos por heurística e devem passar por validação antes de entrar no `dados.js`.

---
**Atualização (28/05/2026 - lote regressivo 2):**

- **Extração antiga @vila.mascote:** Rodamos novo lote via Apify para o intervalo **14/01/2026 a 13/03/2026**, anterior ao primeiro bloco de 14/03/2026 a 27/05/2026.
- **Resultado do lote:** A Apify baixou 186 posts desde 14/01/2026 e o script filtrou localmente 86 posts dentro do intervalo alvo.
- **Arquivos gerados:** `data/vila_mascote_instagram_2026-01-14_a_2026-03-13_posts_raw.json`, `data/vila_mascote_instagram_2026-01-14_a_2026-03-13_posts.csv`, `data/vila_mascote_instagram_2026-01-14_a_2026-03-13_negocios.csv` e `data/vila_mascote_instagram_2026-01-14_a_2026-03-13_novos_candidatos.csv`.
- **Consolidação:** 53 negócios/contatos no lote, sendo 34 marcados como ainda não presentes no guia. Entre os novos, 29 têm telefone e 32 têm endereço extraído.
- **Sequência recomendada:** próximo bloco regressivo deve ser **14/11/2025 a 13/01/2026**.

---
**Atualização (28/05/2026 - scrap de 1 ano organizado):**

- **Pasta final dos scraps:** todos os arquivos dos lotes do Instagram foram movidos/gerados em `SCRAP UM ANO`.
- **Recorte solicitado:** de **27/05/2025 a 27/05/2026**. A consulta final foi feita desde 27/05/2025, mas os posts retornados começam em **29/05/2025**; não houve post público retornado em 27/05/2025 ou 28/05/2025.
- **Lotes criados:** `2026-03-14_a_2026-05-27`, `2026-01-14_a_2026-03-13`, `2025-11-14_a_2026-01-13`, `2025-09-14_a_2025-11-13`, `2025-07-14_a_2025-09-13`, `2025-05-27_a_2025-07-13`.
- **Consolidado final:** `SCRAP UM ANO/vila_mascote_instagram_1_ano_posts.csv` com 522 posts, `SCRAP UM ANO/vila_mascote_instagram_1_ano_negocios.csv` com 147 negócios consolidados e `SCRAP UM ANO/vila_mascote_instagram_1_ano_novos_candidatos.csv` com 115 candidatos ainda não marcados como presentes no guia.
- **Qualidade dos candidatos:** entre os 115 novos candidatos consolidados, 95 têm telefone e 96 têm endereço extraído.
- **Script:** `scripts/extract_instagram_apify.py` agora grava por padrão em `SCRAP UM ANO` e aceita `--since`, `--before` e `--prefix` para novos lotes.

---
**Atualização (28/05/2026 - categorização V1):**

- **Pasta criada:** `CATEGORIZACAO`.
- **Objetivo:** revisar a taxonomia do Guia Vila Mascote antes de aplicar qualquer mudança no site.
- **Arquivos:** `CATEGORIZACAO/taxonomia_categorias_v1.md`, `CATEGORIZACAO/estabelecimentos_categorizados_v1.md`, `CATEGORIZACAO/estabelecimentos_categorizados_v1.csv` e `CATEGORIZACAO/README.md`.
- **Modelo adotado:** cada estabelecimento pode ter uma categoria principal e múltiplas categorias de exibição. Exemplo: ótica aparece em Saúde & Clínicas e também em Mercados/Conveniência; pilates aparece em Academias/Bem-Estar e Saúde.
- **Resumo V1:** 147 itens analisados, 127 marcados como `Listar`, 8 como `Revisar` e 12 como `Nao listar`.

---
**Regra permanente de trabalho:**

- Todo desenvolvimento, curadoria, categorização, geração de dados e alteração de site do **Guia Vila Mascote** deve acontecer somente dentro da pasta `/Users/rafaeloliver/Downloads/guia cb/guia vila mascote`.
- O projeto **Guia Campo Belo** pode ser usado apenas como referência visual/estrutural quando necessário, mas seus arquivos não devem ser alterados, movidos ou misturados com os arquivos da Vila Mascote.
- Antes de aplicar mudanças grandes no site, explicar o plano e confirmar a direção com o usuário.

---
**Atualização (28/05/2026 - logo):**

- O arquivo original `logo mascote.png` tem três artes no mesmo PNG.
- Foi recortado somente o primeiro selo superior, conforme pedido, e salvo como `assets/logo-vila-mascote.png`.
- Ajuste posterior: o logo estava visualmente tangenciado; a arte foi recentralizada em uma tela transparente de 640x640 com 128px de margem em todos os lados, e o CSS do header/footer foi ajustado para exibir a marca com mais respiro.
- Ajuste posterior: o `index.html` principal passou a usar o novo logo metalizado processado a partir de `logo_metal.PNG`, salvo como `assets/logo-vila-mascote-metal.png`; o prototipo em `test01/` permanece com o logo anterior.
- Ajuste posterior: o topo do `test01` foi levado para o `index.html` principal em uma versão mais fina, com fundo azul limpo, sem a malha de quadrados, e com busca + seleção de categorias funcionando no hero.

---
**Atualização (28/05/2026 - site V1):**

- O site inicial do **Guia Vila Mascote** foi montado dentro desta pasta, sem misturar arquivos do Guia Campo Belo.
- `scripts/build_site_data.py` gera `dados.js` a partir de `CATEGORIZACAO/estabelecimentos_categorizados_v1.csv`.
- O `dados.js` usa somente itens com `acao_sugerida = Listar`, totalizando 127 estabelecimentos.
- `index.html`, `style.css` e `script.js` implementam busca, filtros por macro-categoria, subcategorias, ordenação e cards com ações para WhatsApp, Instagram, mapa e post de origem quando disponíveis.
- Repositório GitHub criado em `https://github.com/criatixagencia-collab/guia-vila-mascote`.
