#!/usr/bin/env python3
import csv
import re
from collections import defaultdict
from pathlib import Path


SOURCE = Path("SCRAP UM ANO/vila_mascote_instagram_1_ano_negocios.csv")
OUT_DIR = Path("CATEGORIZACAO")

CATEGORIES = [
    "Gastronomia & Delivery",
    "Cafes, Padarias & Doces",
    "Mercados, Emporios & Conveniencia",
    "Saude & Clinicas",
    "Beleza & Estetica",
    "Academias, Esportes & Bem-Estar",
    "Moda, Calcados & Acessorios",
    "Casa, Decoracao & Organizacao",
    "Servicos para Casa",
    "Imoveis & Construcao",
    "Pets",
    "Educacao & Cursos",
    "Infantil & Familia",
    "Festas & Eventos",
    "Lojas & Presentes",
    "Instituicoes & Comunidade",
    "Revisar / Nao listar",
]

NON_LIST_NAMES = {
    "arraia da mascote",
    "brazucas",
    "cortaz",
    "encontrou seu predio ai?",
    "gostou da versao congelada da mascote? comenta aqui! 🧤👇",
    "natal",
    "o condominio conta com piscina, quadra, salao de festas e churrasqueira.😍",
    "seu bebelier vila mascote 2026 aconteceu hoje",
    "ta chegando o festival de baguete na recanto da mascote!",
    "tem novidade chegando aqui na mascote… 👀",
    "vila mascote",
    "🍴 entradas",
}

REVIEW_HANDLES = {
    "@1.ferrari": "Profissional citado dentro de outro negocio; avaliar se entra separado ou como contato do Hovet.",
    "@cortaz": "Conteudo/editorial, nao parece estabelecimento do guia.",
    "@marciabarbezan": "Profissional citado em talk-show; validar endereco/atendimento antes de listar.",
    "@marigonzalez": "Influenciadora/conteudo de campanha; provavelmente nao listar como estabelecimento.",
    "@m_leticia_": "Profissional citado dentro de outro negocio; avaliar se entra separado ou como contato do Hovet.",
    "@negociosapartets": "Conteudo/podcast; provavelmente nao listar como estabelecimento.",
    "@palomatsclerici": "Profissional citado dentro de outro negocio; avaliar se entra separado.",
}

OVERRIDES = {
    "@acaidabarravilamascote_": ("Cafes, Padarias & Doces", ["Cafes, Padarias & Doces", "Gastronomia & Delivery"], "Acai"),
    "@barbierobarbearia": ("Beleza & Estetica", ["Beleza & Estetica"], "Barbearia"),
    "@bichobatata_brinquedos": ("Infantil & Familia", ["Infantil & Familia", "Lojas & Presentes"], "Loja de brinquedos"),
    "@botocenter.vilamascote": ("Beleza & Estetica", ["Beleza & Estetica", "Saude & Clinicas"], "Estetica clinica"),
    "@buffet.vale.da.diversao": ("Infantil & Familia", ["Infantil & Familia", "Festas & Eventos"], "Buffet infantil"),
    "@camarimstar": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios", "Lojas & Presentes"], "Moda feminina"),
    "@casapalmarestaurante": ("Gastronomia & Delivery", ["Gastronomia & Delivery"], "Restaurante"),
    "@chefviking_boutiquedecarnes": ("Mercados, Emporios & Conveniencia", ["Mercados, Emporios & Conveniencia", "Gastronomia & Delivery"], "Boutique de carnes"),
    "@clinicamvbeauty": ("Beleza & Estetica", ["Beleza & Estetica", "Saude & Clinicas"], "Estetica clinica"),
    "@coffeelandia_": ("Cafes, Padarias & Doces", ["Cafes, Padarias & Doces", "Pets"], "Cafe pet friendly"),
    "@crescente.store": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios"], "Moda feminina"),
    "@capannopizzaria": ("Gastronomia & Delivery", ["Gastronomia & Delivery"], "Pizzaria"),
    "@corpus.balance": ("Saude & Clinicas", ["Saude & Clinicas", "Beleza & Estetica", "Academias, Esportes & Bem-Estar"], "Clinica / academia"),
    "@curumim.clinica": ("Saude & Clinicas", ["Saude & Clinicas", "Infantil & Familia"], "Clinica multidisciplinar"),
    "@espaco.artnails": ("Beleza & Estetica", ["Beleza & Estetica"], "Unhas / estetica"),
    "@fashiongrill_br": ("Gastronomia & Delivery", ["Gastronomia & Delivery"], "Hamburgueria"),
    "@fastescova.vilamascote": ("Beleza & Estetica", ["Beleza & Estetica"], "Salao / escovaria"),
    "@fecarvalho_makeup": ("Beleza & Estetica", ["Beleza & Estetica"], "Maquiagem"),
    "@garimpodesmeralda": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios", "Lojas & Presentes"], "Brecho boutique"),
    "@girasole.boutiquedosaromas": ("Casa, Decoracao & Organizacao", ["Casa, Decoracao & Organizacao", "Lojas & Presentes"], "Aromas / presentes"),
    "@grao_da_mascote": ("Mercados, Emporios & Conveniencia", ["Mercados, Emporios & Conveniencia", "Cafes, Padarias & Doces"], "Emporio"),
    "@graodamascote1": ("Mercados, Emporios & Conveniencia", ["Mercados, Emporios & Conveniencia"], "Hortifruti / organicos"),
    "@hering_vilamascote": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios"], "Moda"),
    "@hipsuplementos": ("Academias, Esportes & Bem-Estar", ["Academias, Esportes & Bem-Estar", "Mercados, Emporios & Conveniencia"], "Suplementos"),
    "@hope.vilamascote": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios"], "Lingerie / moda"),
    "@infinita_outlet": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios"], "Outlet"),
    "@infinitastore": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios"], "Moda feminina"),
    "@janasestetica": ("Beleza & Estetica", ["Beleza & Estetica", "Saude & Clinicas"], "Estetica clinica"),
    "@kasportsoficial": ("Festas & Eventos", ["Festas & Eventos", "Infantil & Familia"], "Eventos / recreacao"),
    "@katia.csilva": ("Pets", ["Pets"], "Veterinario"),
    "@kopenhagen_vila_mascote": ("Cafes, Padarias & Doces", ["Cafes, Padarias & Doces", "Lojas & Presentes"], "Chocolate / presentes"),
    "@lavupsp.vlmascote": ("Servicos para Casa", ["Servicos para Casa", "Mercados, Emporios & Conveniencia"], "Lavanderia"),
    "@lemesbarbearia": ("Beleza & Estetica", ["Beleza & Estetica"], "Barbearia"),
    "@livevilamascote": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios", "Academias, Esportes & Bem-Estar"], "Moda fitness"),
    "@livingempreendimentos": ("Imoveis & Construcao", ["Imoveis & Construcao"], "Construtora / lancamento"),
    "@luh.organizer": ("Casa, Decoracao & Organizacao", ["Casa, Decoracao & Organizacao", "Servicos para Casa"], "Organizacao"),
    "@musicinplay": ("Lojas & Presentes", ["Lojas & Presentes"], "Loja de musica"),
    "@mundinhooanimal": ("Pets", ["Pets", "Festas & Eventos"], "Pet / evento pet"),
    "@omolavanderia_vila_mascote": ("Servicos para Casa", ["Servicos para Casa", "Mercados, Emporios & Conveniencia"], "Lavanderia"),
    "@oticasdinizcatarina": ("Saude & Clinicas", ["Saude & Clinicas", "Mercados, Emporios & Conveniencia"], "Otica"),
    "@oticasdinizmascote": ("Saude & Clinicas", ["Saude & Clinicas", "Mercados, Emporios & Conveniencia"], "Otica"),
    "@plakianca_plaadulto": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios"], "Moda"),
    "@projetosfesta": ("Festas & Eventos", ["Festas & Eventos", "Lojas & Presentes"], "Festas / decoracao"),
    "@rededecisao": ("Educacao & Cursos", ["Educacao & Cursos", "Infantil & Familia"], "Escola"),
    "@restauratto": ("Servicos para Casa", ["Servicos para Casa"], "Costura / sapataria"),
    "@santalolla_vilamascote": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios"], "Calcados / acessorios"),
    "@seuestilodecor": ("Casa, Decoracao & Organizacao", ["Casa, Decoracao & Organizacao"], "Decoracao"),
    "@studio_velocity": ("Academias, Esportes & Bem-Estar", ["Academias, Esportes & Bem-Estar"], "Bike indoor"),
    "@ted_barbearia": ("Beleza & Estetica", ["Beleza & Estetica"], "Barbearia"),
    "@usetboy": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios"], "Moda masculina"),
    "@valen.vilakidsebarber": ("Beleza & Estetica", ["Beleza & Estetica", "Infantil & Familia"], "Barbearia infantil"),
    "@vemdahortasp": ("Mercados, Emporios & Conveniencia", ["Mercados, Emporios & Conveniencia"], "Hortifruti"),
    "@velocity.vilamascote": ("Academias, Esportes & Bem-Estar", ["Academias, Esportes & Bem-Estar"], "Bike indoor"),
    "@vilamascote.thebestacai": ("Cafes, Padarias & Doces", ["Cafes, Padarias & Doces", "Gastronomia & Delivery"], "Acai"),
    "@yourheropets": ("Pets", ["Pets"], "Pet shop / cuidados pet"),
    "@zophimodas": ("Moda, Calcados & Acessorios", ["Moda, Calcados & Acessorios"], "Moda feminina"),
}


def normalize(value):
    value = (value or "").lower()
    replacements = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return re.sub(r"\s+", " ", value).strip()


def contains_any(text, terms):
    boundary_terms = {
        "bar",
        "cao",
        "caes",
        "cafe",
        "curso",
        "dog",
        "escola",
        "festa",
        "gato",
        "gatos",
        "jiu",
        "loja",
        "moda",
        "pet",
        "salao",
        "spa",
    }
    for term in terms:
        if term in boundary_terms:
            if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text):
                return True
        elif term in text:
            return True
    return False


def add_unique(items, value):
    if value and value not in items:
        items.append(value)


def classify(row):
    name = row["nome_provavel"]
    handle = row["instagram_principal"]
    text = normalize(" ".join([
        row.get("nome_provavel", ""),
        row.get("instagram_principal", ""),
        row.get("categoria_provavel", ""),
        row.get("subcategoria_provavel", ""),
        row.get("resumo_ultimo_post", ""),
    ]))
    categories = []
    subcategory = row.get("subcategoria_provavel") or ""
    action = "Listar"
    notes = []

    name_key = normalize(name)
    if name_key in NON_LIST_NAMES:
        return {
            "categoria_principal": "Revisar / Nao listar",
            "categorias_exibicao": "Revisar / Nao listar",
            "subcategoria_final": "Conteudo / post editorial",
            "acao_sugerida": "Nao listar",
            "observacao": "Nao parece estabelecimento independente; manter apenas como referencia do scrap.",
        }

    if handle in REVIEW_HANDLES:
        action = "Revisar"
        notes.append(REVIEW_HANDLES[handle])
    elif not handle:
        action = "Revisar"
        notes.append("Sem Instagram principal extraido; validar se e estabelecimento independente.")

    # Gastronomia e alimentos prontos
    if contains_any(text, ["restaurante", "delivery", "hamburg", "burger", "pizza", "pizzaria", "sushi", "japones", "arabe", "shawarma", "kebab", "bacalhau", "pastelaria", "pastel", "culinaria", "comida caseira"]):
        add_unique(categories, "Gastronomia & Delivery")
    if contains_any(text, ["padaria", "cafe", "cafeteria", "confeitaria", "bolo", "bolos", "doces", "sobremesa", "brigadeiro", "acai", "queijaria", "kopenhagen", "chocolate", "torta"]):
        add_unique(categories, "Cafes, Padarias & Doces")
    if contains_any(text, ["empório", "emporio", "horta", "hortifruti", "organica", "organico", "mercado", "boutique de carnes", "carnes", "suplement", "grao da mascote", "kopenhagen", "queijaria"]):
        add_unique(categories, "Mercados, Emporios & Conveniencia")

    # Saude, beleza e bem-estar
    if contains_any(text, ["clinica", "clinica", "dent", "odont", "oralsin", "toyomoto", "nutri", "psicolog", "psicanal", "terapia", "terapeuta", "acupuntura", "fisioterapia", "osteopata", "otica", "oticas", "oculos", "lentes", "multidisciplinar", "neuro", "raio-x"]):
        add_unique(categories, "Saude & Clinicas")
    if contains_any(text, ["estetica", "beauty", "botox", "preenchimento", "harmonizacao facial", "harmonizacao orofacial", "salao de beleza", "barbearia", "barber", "cabeleireira", "visagista", "unha", "nails", "depilacao", "head spa", "buddhaspa", "day spa", "fastescova"]):
        add_unique(categories, "Beleza & Estetica")
    if contains_any(text, ["academia", "fitness", "pilates", "yoga", "jiu-jitsu", "jiu jitsu", "krav", "futebol", "bike", "velocity", "treino", "wellhub", "gympass", "suplement"]):
        add_unique(categories, "Academias, Esportes & Bem-Estar")

    # Compras
    if contains_any(text, ["moda", "roupa", "roupas", "calcado", "calcados", "santalolla", "hering", "hope", "lingerie", "semijoia", "semijoias", "acessorio", "acessorios", "bolsa", "outlet", "brecho", "boutique", "fashion"]):
        add_unique(categories, "Moda, Calcados & Acessorios")
    if contains_any(text, ["decor", "cortina", "persiana", "marcenaria", "moveis", "moveis planejados", "aromas", "organizer", "organizacao", "casaellegance", "seuestilodecor", "luh organizer", "girasole"]):
        add_unique(categories, "Casa, Decoracao & Organizacao")
    if contains_any(text, ["bazar", "brinquedo", "brinquedos", "music", "instrument", "kopenhagen", "projetosfesta"]):
        add_unique(categories, "Lojas & Presentes")

    # Servicos, imoveis e casa
    if contains_any(text, ["reforma", "reparos", "pedreiro", "pintor", "eletricista", "encanador", "ar-condicionado", "refrigeracao", "higienizacao", "impermeabilizacao", "estofado", "lavanderia", "costura", "sapataria", "assistencia", "limpeza", "ecoville", "omo lavanderia", "lavup"]):
        add_unique(categories, "Servicos para Casa")
    if contains_any(text, ["imovel", "imoveis", "imobiliaria", "corretor", "corretora", "construtora", "incorporadora", "lancamento", "cyrela", "living", "remax", "apartamento", "locacao"]):
        add_unique(categories, "Imoveis & Construcao")

    # Pets, educacao, infantil, eventos e comunidade
    if contains_any(text, ["pet shop", "petland", "pet friendly", "yourheropets", "mundinhooanimal", "veterin", "cao", "caes", "cachorro", "gato", "gatos", "banho e tosa", "daycare", "hotel pet", "dog"]):
        add_unique(categories, "Pets")
    if contains_any(text, ["escola", "colegio", "idioma", "ingles", "curso de ingles", "matricula", "ludus", "rededecisao", "cultura inglesa", "isec"]):
        add_unique(categories, "Educacao & Cursos")
    if contains_any(text, ["infantil", "crianca", "criancas", "kids", "brinquedo", "brinquedos", "buffet", "diversao", "ludus", "neuroaprender"]):
        add_unique(categories, "Infantil & Familia")
    if contains_any(text, ["buffet", "festa", "evento", "arraia", "bloquinho", "carnaval", "projetosfesta", "kasports", "abadá", "abada"]):
        add_unique(categories, "Festas & Eventos")
    if contains_any(text, ["paroquia", "igreja", "instituto gabi", "solidariedade", "comunidade", "quem ajuda"]):
        add_unique(categories, "Instituicoes & Comunidade")

    # Ajustes de dupla entrada importantes.
    if contains_any(text, ["otica", "oticas", "oculos", "lentes"]):
        add_unique(categories, "Mercados, Emporios & Conveniencia")
        subcategory = "Otica"
    if contains_any(text, ["pilates", "fisioterapia", "osteopata"]):
        add_unique(categories, "Saude & Clinicas")
    if contains_any(text, ["botox", "preenchimento", "harmonizacao facial", "harmonizacao orofacial", "estetica clinica"]):
        add_unique(categories, "Saude & Clinicas")
    if contains_any(text, ["moda fitness"]):
        add_unique(categories, "Academias, Esportes & Bem-Estar")
    if contains_any(text, ["coffeelandia", "pet friendly"]):
        add_unique(categories, "Pets")

    if not categories:
        categories = ["Revisar / Nao listar"]
        action = "Revisar"
        notes.append("Categoria nao ficou clara pelo texto extraido.")

    if handle in OVERRIDES:
        primary, categories, subcategory = OVERRIDES[handle]

    if "Imoveis & Construcao" in categories and contains_any(text, ["imovel", "imoveis", "apartamento", "locacao", "lancamento", "construtora", "corretor"]):
        amenity_noise = {"Beleza & Estetica", "Infantil & Familia", "Festas & Eventos", "Casa, Decoracao & Organizacao", "Servicos para Casa", "Lojas & Presentes"}
        categories = [category for category in categories if category not in amenity_noise]
        if not categories:
            categories = ["Imoveis & Construcao"]
        if subcategory in {"Reformas", "Academia/Fitness", "Clínica/Estética", ""}:
            subcategory = "Imobiliaria / corretor"

    primary = choose_primary(categories, text)
    if handle in OVERRIDES:
        primary = OVERRIDES[handle][0]
    if not subcategory:
        subcategory = infer_subcategory(text, primary)

    return {
        "categoria_principal": primary,
        "categorias_exibicao": " | ".join(categories),
        "subcategoria_final": subcategory,
        "acao_sugerida": action,
        "observacao": " ".join(notes).strip(),
    }


def choose_primary(categories, text):
    priority_terms = [
        ("Imoveis & Construcao", ["imovel", "imoveis", "corretor", "construtora", "incorporadora", "lancamento", "apartamento"]),
        ("Pets", ["pet", "veterin", "cao", "gato", "dog"]),
        ("Educacao & Cursos", ["escola", "idioma", "ingles", "curso"]),
        ("Infantil & Familia", ["infantil", "buffet", "brinquedo", "kids"]),
        ("Servicos para Casa", ["reforma", "lavanderia", "ar-condicionado", "higienizacao", "costura", "sapataria"]),
        ("Saude & Clinicas", ["clinica", "dent", "odont", "nutri", "psicolog", "otica", "terapia", "fisioterapia"]),
        ("Beleza & Estetica", ["barbearia", "salao", "beauty", "estetica", "botox", "unha", "spa"]),
        ("Gastronomia & Delivery", ["restaurante", "delivery", "pizza", "sushi", "hamburg", "pastel"]),
        ("Cafes, Padarias & Doces", ["padaria", "cafe", "bolo", "doces", "acai", "kopenhagen"]),
        ("Mercados, Emporios & Conveniencia", ["emporio", "horta", "mercado", "suplement", "carnes"]),
        ("Moda, Calcados & Acessorios", ["moda", "roupa", "calcado", "acessorio", "bolsa", "outlet"]),
        ("Academias, Esportes & Bem-Estar", ["academia", "pilates", "fitness", "yoga", "jiu", "krav", "futebol"]),
        ("Casa, Decoracao & Organizacao", ["decor", "marcenaria", "moveis", "organizer", "aromas"]),
        ("Lojas & Presentes", ["bazar", "brinquedo", "music"]),
        ("Festas & Eventos", ["festa", "evento", "bloquinho"]),
        ("Instituicoes & Comunidade", ["paroquia", "instituto"]),
    ]
    for category, terms in priority_terms:
        if category in categories and contains_any(text, terms):
            return category
    return categories[0]


def infer_subcategory(text, primary):
    rules = [
        ("Otica", ["otica", "oticas", "oculos", "lentes"]),
        ("Imobiliaria / corretor", ["imovel", "imobiliaria", "corretor", "remax"]),
        ("Construtora / lancamento", ["construtora", "incorporadora", "lancamento", "cyrela", "living"]),
        ("Veterinario / hospital pet", ["veterin", "hospital veterin"]),
        ("Pet shop / banho e tosa", ["pet shop", "banho e tosa"]),
        ("Pilates / fisioterapia", ["pilates", "fisioterapia", "osteopata"]),
        ("Academia / studio", ["academia", "fitness", "bike", "velocity"]),
        ("Arte marcial / esporte", ["jiu-jitsu", "jiu jitsu", "krav", "futebol"]),
        ("Clinica estetica", ["botox", "preenchimento", "harmonizacao", "estetica"]),
        ("Salao / barbearia", ["salao", "barbearia", "barber", "cabeleireira", "fastescova"]),
        ("Odontologia", ["odont", "dent", "oralsin", "toyomoto"]),
        ("Psicologia / terapias", ["psicolog", "psicanal", "terapia", "acupuntura"]),
        ("Nutricionista", ["nutri"]),
        ("Pizzaria", ["pizza", "pizzaria"]),
        ("Hamburgueria", ["hamburg", "burger"]),
        ("Japones / sushi", ["sushi", "japones"]),
        ("Arabe", ["arabe", "shawarma", "kebab"]),
        ("Padaria", ["padaria"]),
        ("Doces / confeitaria", ["bolo", "doces", "confeitaria", "brigadeiro", "torta"]),
        ("Acai", ["acai"]),
        ("Moda / acessorios", ["moda", "roupa", "acessorio", "bolsa", "outlet"]),
        ("Decoracao", ["decor", "cortina", "persiana", "aromas"]),
        ("Marcenaria / moveis", ["marcenaria", "moveis"]),
        ("Lavanderia", ["lavanderia", "lavup"]),
        ("Limpeza / higienizacao", ["limpeza", "higienizacao", "impermeabilizacao", "estofado"]),
        ("Reformas / manutencao", ["reforma", "pedreiro", "eletricista", "encanador"]),
        ("Ar-condicionado", ["ar-condicionado", "refrigeracao"]),
        ("Escola de idiomas", ["ingles", "idioma"]),
        ("Escola / educacao infantil", ["escola", "colegio", "ludus"]),
        ("Buffet / festas infantis", ["buffet", "festa infantil", "diversao"]),
        ("Loja de brinquedos", ["brinquedo"]),
        ("Emporio / hortifruti", ["emporio", "horta", "hortifruti", "grao"]),
        ("Suplementos", ["suplement"]),
        ("Instituicao / comunidade", ["paroquia", "instituto"]),
    ]
    for subcategory, terms in rules:
        if contains_any(text, terms):
            return subcategory
    return primary


def markdown_escape(value):
    return (value or "").replace("|", "\\|").replace("\n", " ")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    with SOURCE.open(encoding="utf-8", newline="") as file:
        source_rows = list(csv.DictReader(file))

    rows = []
    for row in source_rows:
        classification = classify(row)
        rows.append({
            "nome": row["nome_provavel"],
            "instagram": row["instagram_principal"],
            **classification,
            "posts_no_ano": row["quantidade_posts"],
            "ultimo_post": row["ultimo_post"][:10],
            "telefone": row["telefones"],
            "endereco": row["enderecos"],
            "ja_no_guia": row["ja_no_guia"],
            "resumo": row["resumo_ultimo_post"],
            "links_posts": row["links_posts"],
        })

    rows.sort(key=lambda row: (row["categoria_principal"], row["nome"].lower()))

    csv_path = OUT_DIR / "estabelecimentos_categorizados_v1.csv"
    fieldnames = [
        "nome",
        "instagram",
        "categoria_principal",
        "categorias_exibicao",
        "subcategoria_final",
        "acao_sugerida",
        "observacao",
        "posts_no_ano",
        "ultimo_post",
        "telefone",
        "endereco",
        "ja_no_guia",
        "resumo",
        "links_posts",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    taxonomy_path = OUT_DIR / "taxonomia_categorias_v1.md"
    taxonomy_path.write_text(build_taxonomy_doc(), encoding="utf-8")

    md_path = OUT_DIR / "estabelecimentos_categorizados_v1.md"
    md_path.write_text(build_listing_doc(rows), encoding="utf-8")

    print(f"Gerado: {taxonomy_path}")
    print(f"Gerado: {md_path}")
    print(f"Gerado: {csv_path}")
    print(f"Total: {len(rows)} estabelecimentos/itens")


def build_taxonomy_doc():
    return """# Taxonomia V1 - Guia Vila Mascote

Esta e uma proposta inicial para revisar os estabelecimentos coletados no scrap de 1 ano da @vila.mascote.

Regra principal: um estabelecimento pode aparecer em mais de uma categoria. A categoria principal representa a identidade mais forte do negocio; as categorias de exibicao representam os caminhos pelos quais o usuario pode tentar encontra-lo.

## Categorias

1. Gastronomia & Delivery: restaurantes, pizzarias, hamburguerias, comida japonesa/arabe/portuguesa, marmitas, delivery e pratos prontos.
2. Cafes, Padarias & Doces: padarias, cafes, confeitarias, bolos, doces, chocolates, acai, queijarias e sobremesas.
3. Mercados, Emporios & Conveniencia: hortifruti, empórios, suplementos, boutique de carnes, lojas praticas de bairro, oticas e conveniencias.
4. Saude & Clinicas: clinicas medicas, odontologia, oticas, nutricao, psicologia, fisioterapia, acupuntura, terapias e clinicas multidisciplinares.
5. Beleza & Estetica: saloes, barbearias, unhas, maquiagem, depilacao, botox, harmonizacao, spa e estetica facial/corporal.
6. Academias, Esportes & Bem-Estar: academias, pilates, yoga, bike indoor, jiu-jitsu, krav maga, futebol, studios e suplementacao esportiva.
7. Moda, Calcados & Acessorios: roupas, moda fitness, lingerie, calcados, bolsas, semijoias, brechos, outlets e acessorios.
8. Casa, Decoracao & Organizacao: decoracao, cortinas, moveis, marcenaria, aromas, organizacao e itens para casa.
9. Servicos para Casa: reformas, manutencao, limpeza de estofados, lavanderia, costura, sapataria, ar-condicionado e assistencia.
10. Imoveis & Construcao: imobiliarias, corretores, construtoras, incorporadoras, lancamentos, venda e locacao.
11. Pets: pet shops, veterinarios, hospital veterinario, banho e tosa, daycare e hotel pet.
12. Educacao & Cursos: escolas, cursos de idiomas, reforco, cursos livres e atividades formativas.
13. Infantil & Familia: buffets infantis, brinquedos, atividades para criancas, moda infantil e servicos familiares.
14. Festas & Eventos: buffets, festas, eventos, decoracao de festa e ativacoes.
15. Lojas & Presentes: bazares, brinquedos, chocolates/presentes, lojas de musica e produtos presenteaveis.
16. Instituicoes & Comunidade: paroquias, institutos, acoes sociais e entidades comunitarias.
17. Revisar / Nao listar: posts editoriais, eventos sem negocio claro, duplicidades ou itens que precisam validacao antes de entrar no guia.

## Exemplos de dupla categoria

- Otica: Saude & Clinicas + Mercados, Emporios & Conveniencia.
- Pilates/fisioterapia: Academias, Esportes & Bem-Estar + Saude & Clinicas.
- Estetica clinica: Beleza & Estetica + Saude & Clinicas.
- Queijaria ou chocolate: Cafes, Padarias & Doces + Mercados, Emporios & Conveniencia.
- Moda fitness: Moda, Calcados & Acessorios + Academias, Esportes & Bem-Estar.
- Buffet infantil: Infantil & Familia + Festas & Eventos.
- Cafe pet friendly: Cafes, Padarias & Doces + Pets.
"""


def build_listing_doc(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["categoria_principal"]].append(row)

    lines = [
        "# Estabelecimentos Categorizados V1",
        "",
        "Fonte: `SCRAP UM ANO/vila_mascote_instagram_1_ano_negocios.csv`.",
        "",
        "Esta lista e uma proposta inicial para revisao. Nada foi aplicado ao site ainda.",
        "",
    ]
    for category in CATEGORIES:
        items = grouped.get(category, [])
        if not items:
            continue
        lines.append(f"## {category} ({len(items)})")
        lines.append("")
        lines.append("| Estabelecimento | Instagram | Subcategoria | Aparece tambem em | Acao | Obs |")
        lines.append("|---|---|---|---|---|---|")
        for row in items:
            extra_categories = " / ".join(
                category_name
                for category_name in row["categorias_exibicao"].split(" | ")
                if category_name != row["categoria_principal"]
            )
            lines.append(
                "| "
                + " | ".join([
                    markdown_escape(row["nome"]),
                    markdown_escape(row["instagram"]),
                    markdown_escape(row["subcategoria_final"]),
                    markdown_escape(extra_categories),
                    markdown_escape(row["acao_sugerida"]),
                    markdown_escape(row["observacao"]),
                ])
                + " |"
            )
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
