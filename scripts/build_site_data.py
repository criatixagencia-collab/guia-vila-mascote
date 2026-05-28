#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path


SOURCE = Path("CATEGORIZACAO/estabelecimentos_categorizados_v1.csv")
GEOCODES = Path("data/vila_mascote_geocodes.json")
OUTPUT = Path("dados.js")


def clean_phone(value):
    phones = []
    for part in (value or "").split(";"):
        digits = re.sub(r"\D", "", part)
        if digits.startswith("55"):
            digits = digits[2:]
        if len(digits) in {10, 11} and digits not in phones:
            phones.append(digits)
    return phones


def first_part(value):
    for part in (value or "").split(";"):
        part = re.sub(r"\s+", " ", part).strip(" -")
        if part:
            return part
    return ""


def normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def extract_address(value):
    value = normalize_space(value)
    if not value:
        return ""

    candidates = []
    for part in re.split(r";|\n", value):
        part = normalize_space(part.strip(" .-"))
        if part:
            candidates.append(part)

    pattern = re.compile(
        r"(?i)\b(?:av\.?|avenida|r\.?|rua|alameda|travessa|estrada)\s+"
        r"[^;,.]+?(?:,\s*)?\d{1,5}(?:\s*[-–]\s*[^;,.]+)?"
    )
    for part in candidates:
        match = pattern.search(part)
        if match:
            return normalize_space(match.group(0))

    for part in candidates:
        if re.search(r"(?i)\b(?:av\.?|avenida|r\.?|rua)\b", part) and re.search(r"\d", part):
            return part

    return first_part(value)


def split_categories(value):
    categories = []
    for part in (value or "").split("|"):
        part = part.strip()
        if part and part not in categories:
            categories.append(part)
    return categories


def compact_description(value):
    value = re.sub(r"\s+", " ", value or "").strip()
    value = re.sub(r"^[🎫⚠️✅✨🚨\s]+", "", value).strip()
    if len(value) > 260:
        value = value[:257].rstrip() + "..."
    return value


def strip_social_noise(value, mention_label=""):
    value = re.sub(r"@\w+(?:[._]\w+)*", mention_label, value or "")
    value = re.sub(r"#\w+", "", value)
    value = re.sub(r"[\U00010000-\U0010ffff]", " ", value)
    value = re.sub(r"[🎫⚠️✅✨🚨💪🤩😍☺️💈💞🏋️‍♀️🏋🏻💊🧘‍♀️💛🔥👀🍕🍟🕦📍🍣🇯🇵🍜😋🍽️🥰🤝💝🧖‍♀️🌿💆‍♀️🛋️🏠🪚🛠️📚🏫⚽🎈🛍️🧸🦷👄💉🩻❣️🧰❄️🧺🚀🎉]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" .-")
    return value


PROMO_RE = re.compile(
    r"(?i)\b(?:off|desconto|cupom|promo(?:ção|cao)|gr[aá]tis|ganhe|brinde|condi(?:ç|c)(?:ões|oes)|"
    r"valores promocionais|black friday|r\$\s*\d|isenc(?:ao|ão)|matr[ií]cula|bolsa exclusiva)\b"
)


def split_sentences(value):
    value = normalize_space(value)
    if not value:
        return []
    parts = re.split(r"(?<=[.!?])\s+|(?:\s+[•]\s+)", value)
    return [normalize_space(part.strip(" -•")) for part in parts if normalize_space(part)]


def cut_offer_context(value):
    transition = re.compile(
        r"(?i)\s+(?:se você|que tal|a gente|fomos|nessa época|na unidade|o studio|a loja|as pizzas|dica boa|"
        r"você está|você não precisa|o que já era|tem dúvidas|hoje a gente|manter|precisa conhecer|"
        r"você sabia|novidade|na escola|a unidade|a clínica|a empresa|a loja|o restaurante|para completar|"
        r"e o melhor|corre porque|arraste|arrasta)\b"
    )
    match = transition.search(value)
    if match and match.start() >= 24:
        return value[:match.start()]
    return value


def clean_offer(value, mention_label=""):
    value = strip_social_noise(value, mention_label)
    special = re.search(r"(?i)promo(?:ção|cao) especial pra data:\s*(.+)", value)
    if special:
        value = special.group(1)
    value = cut_offer_context(value)
    value = re.sub(r"(?i)^cupom de desconto\s+", "Cupom ", value)
    value = re.sub(r"(?i)\s+promoção válida.*$", "", value)
    value = re.sub(r"(?i)\s+somente dia.*$", "", value)
    value = re.sub(r"(?i)\s+válido somente.*$", "", value)
    value = re.sub(r"\s+", " ", value).strip(" .-")
    if len(value) > 150:
        value = value[:147].rstrip(" ,;") + "..."
    return value


def extract_promotion(value, mention_label=""):
    text = strip_social_noise(value, mention_label)
    if not text or not PROMO_RE.search(text):
        return ""

    promo_words = re.compile(
        r"(?i)\b(?:off|desconto|cupom|promo(?:ção|cao)|gr[aá]tis|ganhe|brinde|condi(?:ç|c)(?:ões|oes)|"
        r"black friday|isenc(?:ao|ão)|matr[ií]cula|bolsa exclusiva)\b"
    )
    if re.search(r"(?i)\bvalor de venda\b", text[:320]) and not promo_words.search(text[:320]):
        return ""

    if PROMO_RE.search(text[:280]):
        return clean_offer(text[:280], mention_label)

    match = PROMO_RE.search(text)
    start = max(0, match.start() - 50)
    end = min(len(text), match.end() + 90)
    window = text[start:end]
    if re.search(r"(?i)\bvalor de venda\b", window) and not promo_words.search(window):
        return ""
    return clean_offer(window, mention_label)


def summarize_description(value, category, subcategory, mention_label):
    text = strip_social_noise(value, mention_label)
    promotion = extract_promotion(value, mention_label)
    if promotion:
        text = normalize_space(text.replace(promotion, "", 1))

    cleanup_patterns = [
        r"(?i)^dica especial (?:para|pra) quem (?:é|mora) (?:da|na) vila mascote[!.]?\s*",
        r"(?i)^fomos visitar\s+",
        r"(?i)^a gente foi (?:conhecer|visitar|até)\s+",
        r"(?i)^você sabia que\s+",
        r"(?i)^arraste para o lado.*$",
        r"(?i)^arrasta pro lado.*$",
    ]
    for pattern in cleanup_patterns:
        text = re.sub(pattern, "", text).strip()
    text = re.sub(r"(?i)^e quer .*?\ba gente\b", "A gente", text).strip()
    text = re.sub(r"^a\s+(?=[A-ZÁÉÍÓÚ])", "", text).strip()

    sentences = split_sentences(text)
    chosen = []
    for sentence in sentences:
        if PROMO_RE.search(sentence):
            continue
        if re.search(r"(?i)\b(?:arraste|arrasta|confira|corre|link na bio|comenta aqui)\b", sentence):
            continue
        sentence = normalize_space(sentence)
        if len(sentence) < 22:
            continue
        chosen.append(sentence)
        if len(" ".join(chosen)) >= 170 or len(chosen) == 2:
            break

    base = f"{mention_label} é uma opção de {subcategory.lower()} na Vila Mascote."
    detail = ""
    for sentence in chosen:
        if normalize_text := normalize_space(sentence):
            if normalize_text.lower().startswith(mention_label.lower()):
                continue
            detail = normalize_text
            break

    if detail:
        summary = f"{base} {detail}"
    elif chosen:
        summary = f"{base} {chosen[0]}"
    else:
        summary = base

    summary = re.sub(r"\s+", " ", summary).strip(" .-")
    if summary and summary[-1] not in ".!?":
        summary += "."
    if len(summary) > 240:
        summary = summary[:237].rstrip(" ,;") + "..."
    return summary


def clean_name(value):
    value = re.sub(r"\s+", " ", value or "").strip()
    replacements = {
        "Babbogiovannivilamascote": "Babbo Giovanni Vila Mascote",
        "Bacalhaudoguga": "Bacalhau do Guga",
        "Padariarecantodamascote": "Padaria Recanto da Mascote",
        "Hiatari Vila Mascote": "Hiatari Vila Mascote",
        "Vittelis Restaurante": "Vittelis Restaurante",
        "Tres Chic Acessorios": "Tres Chic Acessórios",
        "Pilatesspacoequilibrium": "Pilates Spaço Equilibrium",
        "Otocleanhigienizacao": "OtoClean Higienização",
        "Saboriecozinhaartesanal": "Saboriê Cozinha Artesanal",
        "Arabianmixfood": "Arabian Mix Food",
        "Dramarciabusato": "Dra. Márcia Busato",
        "Dradeboradsouza": "Dra. Débora Souza",
        "Alinenaveganutri": "Aline Navega Nutri",
        "Clínicaamandabeauty": "Clínica Amanda Beauty",
        "Clínicanavsaude": "Clínica NAV Saúde",
        "Clínicatoyomoto": "Clínica Toyomoto",
        "Clínicamvbeauty": "Clínica MV Beauty",
        "Curumim Clinica": "Curumim Clínica",
        "Buddhaspa Vilamascote": "Buddha Spa Vila Mascote",
        "Vollstudiosvilamascote": "Voll Studios Vila Mascote",
        "Velocity Vilamascote": "Velocity Vila Mascote",
        "Fitclass Vila Mascote": "FitClass Vila Mascote",
        "Guigojj Vilamascote": "Guigo Jiu-Jitsu Vila Mascote",
        "Kravmaga Vila Mascote": "Krav Maga Vila Mascote",
        "Petlandsp Vilamascote": "Petland Vila Mascote",
        "Hovet Mascote": "Hovet Mascote",
        "Doglandiadaycare": "Doglândia Daycare",
        "Yourheropets": "Your Hero Pets",
        "Mundinhooanimal": "Mundinho Animal",
        "Scheidimoveis Vila Mascote": "Scheid Imóveis Vila Mascote",
        "Vieiranegocios": "Vieira Negócios",
        "Souasuacorretora": "Sou a Sua Corretora",
        "Elitufanini Remax": "Eli Tufanini Remax",
        "Karinamustafaimoveis": "Karina Mustafa Imóveis",
        "Marcusalmeida Imoveis": "Marcus Almeida Imóveis",
        "Imoveismoedaforte": "Imóveis Moeda Forte",
        "Livingempreendimentos": "Living Empreendimentos",
        "Econconstrutora": "Econ Construtora",
        "Oticasdiniz Mascote": "Óticas Diniz Mascote",
        "Oticasdinizcatarina": "Óticas Diniz Catarina",
        "Omolavanderia Vila Mascote": "OMO Lavanderia Vila Mascote",
        "Lavupsp Vlmascote": "LavUp Vila Mascote",
        "Thermo_tagg": "Thermo Tagg",
        "Arranjosexpress Vilamascote": "Arranjos Express Vila Mascote",
        "Hering_vilamascote": "Hering Vila Mascote",
        "Santalolla_vilamascote": "Santa Lolla Vila Mascote",
        "Live Vila Mascote": "LIVE! Vila Mascote",
        "Hope Vilamascote": "Hope Vila Mascote",
        "Infinita Outlet": "Infinita Outlet",
        "Kopenhagen_vila_mascote": "Kopenhagen Vila Mascote",
        "Chefviking Boutiquedecarnes": "Chef Viking Boutique de Carnes",
        "Grao Da Mascote": "Grão da Mascote",
        "Graoda Mascote1": "Grão da Mascote",
        "Vemdahortasp": "Vem da Horta SP",
        "Hipsuplementos": "Hip Suplementos",
        "Coffeelandia_": "Coffeelândia",
        "Casadobentopaesartesanais": "Casa do Bento Pães Artesanais",
        "Queijariacave381": "Queijaria Cave 381",
        "Atelie.juguedes": "Ateliê Ju Guedes",
        "Julianaguedes Confeitaria": "Juliana Guedes Confeitaria",
        "Acaidabarravilamascote": "Açaí da Barra Vila Mascote",
        "Vilamascote Thebestacai": "The Best Açaí Vila Mascote",
        "Escolaludus": "Escola Ludus",
        "Culturainglesa Vilamascote": "Cultura Inglesa Vila Mascote",
        "Isec.idiomas": "ISEC Idiomas",
        "Rededecisao": "Rede Decisão",
        "Buffet Vale Da Diversao": "Buffet Vale da Diversão",
        "Bichobatata Brinquedos": "Bicho Batata Brinquedos",
    }
    return replacements.get(value, value)


def main():
    records = []
    geocodes = {}
    if GEOCODES.exists():
        geocodes = json.loads(GEOCODES.read_text(encoding="utf-8"))

    with SOURCE.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["acao_sugerida"] != "Listar":
                continue
            categories = split_categories(row["categorias_exibicao"])
            primary = row["categoria_principal"]
            if primary not in categories:
                categories.insert(0, primary)
            raw_name = normalize_space(row["nome"])
            display_name = clean_name(raw_name)
            address = extract_address(row["endereco"])
            geocode = geocodes.get(f"{raw_name}::{address}", {})
            records.append(
                {
                    "id": len(records) + 1,
                    "nome": display_name,
                    "categoriaPrincipal": primary,
                    "categorias": categories,
                    "subcategoria": row["subcategoria_final"],
                    "endereco": address,
                    "lat": geocode.get("lat"),
                    "lng": geocode.get("lng"),
                    "mapSource": geocode.get("source", ""),
                    "telefones": clean_phone(row["telefone"]),
                    "instagram": row["instagram"].lstrip("@"),
                    "descricao": summarize_description(row["resumo"], primary, row["subcategoria_final"], display_name),
                    "promocao": extract_promotion(row["resumo"], display_name),
                    "ultimoPost": row["ultimo_post"],
                    "postsAno": int(row["posts_no_ano"] or 0),
                    "jaNoGuia": row["ja_no_guia"] == "sim",
                    "origem": "Instagram @vila.mascote",
                    "linksPosts": [part.strip() for part in row["links_posts"].split(";") if part.strip()],
                }
            )

    content = "/**\n"
    content += " * DADOS GERADOS AUTOMATICAMENTE\n"
    content += " * Fonte: CATEGORIZACAO/estabelecimentos_categorizados_v1.csv\n"
    content += f" * Total de estabelecimentos listaveis: {len(records)}\n"
    content += " */\n\n"
    content += "const dados = "
    content += json.dumps(records, ensure_ascii=False, indent=2)
    content += ";\n"
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"Gerado {OUTPUT} com {len(records)} registros.")


if __name__ == "__main__":
    main()
