# Guia Vila Mascote

Site local do Guia Vila Mascote, com estabelecimentos categorizados a partir da curadoria e dos scraps do Instagram `@vila.mascote`.

## Arquivos principais

- `index.html`: estrutura da página.
- `style.css`: identidade visual, responsividade, cards, mapa e tipografia.
- `script.js`: busca, filtros, cards e mapa.
- `dados.js`: dados gerados para o site.
- `scripts/build_site_data.py`: gera `dados.js` a partir da categorização.
- `scripts/geocode_vila_mascote.py`: gera coordenadas para o mapa.

## Dados

A base editorial fica em `CATEGORIZACAO/estabelecimentos_categorizados_v1.csv`.
O material bruto do Instagram fica em `SCRAP UM ANO`.

## Rodar localmente

Este site pode ser aberto diretamente pelo arquivo `index.html`. Para testar com servidor local:

```bash
python3 -m http.server 8787
```

Depois acesse `http://localhost:8787`.
