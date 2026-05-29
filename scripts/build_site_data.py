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

CTA_RE = re.compile(
    r"(?i)\b(?:arraste|arrasta|confira|corre|link na bio|comenta aqui|chama|entre em contato|"
    r"garanta|aproveite|não perca|precisa conhecer|precisa experimentar|vale a pena|"
    r"parada obrigatória|dá uma olhada|olha só|fica a dica)\b"
)

FACT_RE = re.compile(
    r"(?i)\b(?:tem|oferece|trabalha com|conta com|fica|funciona|atende|especiali[sz]ad[ao]|"
    r"inclui|possui|são|há|anos|unidade|ambiente|serviços|produtos|aulas|curso|cardápio|"
    r"apartamento|empreendimento|plantas|lazer|delivery|encomendas|consultas|procedimentos)\b"
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
    celebration_discount = re.search(r"(?i)\b(\d+\s*%\s+de desconto)\b", value)
    if re.match(r"(?i)^(?:pra|para) comemorar\b", value) and celebration_discount:
        return clean_offer(celebration_discount.group(1), mention_label)
    if re.match(r"(?i)^(?:pra|para) comemorar\b", value):
        return ""
    value = re.sub(
        r"(?i)cheeseburger\s+de\s+R\$\s?[\d,.]+\s+por\s+(?:apenas\s+)?(R\$\s?[\d,.]+).*?"
        r"combo[^R]+R\$\s?[\d,.]+\s+por\s+(?:s[oó]\s+)?(R\$\s?[\d,.]+).*",
        r"Cheeseburger \1 + combo \2",
        value,
    )
    discount_match = re.search(r"(?i)(descontos?[^.]{0,54}?(?:at[eé]|a)\s+\d+\s*%\s*(?:off)?)", value)
    if discount_match:
        value = discount_match.group(1)
    value = re.sub(r"(?i)^🎫?\s*", "", value)
    value = re.sub(r"(?i)^promo(?:ção|cao) especial(?: pra data)?:\s*", "", value)
    value = re.sub(r"(?i)^cupom de desconto\s+", "Cupom ", value)
    value = re.sub(r"(?i)\s+(?:você|se você|que tal|a gente|sabe aquele|sabia que|precisa|chama|arraste|arrasta|tem dúvidas|quem busca|em breve|novidade|dica boa|nessa época|nesta época|nessas férias|hoje|manter).*$", "", value)
    value = re.sub(r"(?i)\s+(?:a|o)\s+[A-ZÁÉÍÓÚ][\wÀ-ÿ. ]{2,}\s+(?:é|tem|fica|atende|oferece|está|vai).*$", "", value)
    value = re.sub(r"(?i)\s+na escola\s+.*$", "", value)
    value = re.sub(r"(?i)\s+promoção válida.*$", "", value)
    value = re.sub(r"(?i)\s+somente dia.*$", "", value)
    value = re.sub(r"(?i)\s+válido somente.*$", "", value)
    value = re.sub(r"(?i)\s+durante todo o mês de\s+([a-zç]+).*", r" em \1", value)
    value = re.sub(r"(?i)\bpara os nossos seguidores\b", "para seguidores", value)
    value = re.sub(r"(?i)\bpara as nossas seguidoras\b", "para seguidoras", value)
    value = re.sub(r"(?i)\bapresentando um print desse post\b", "com print do post", value)
    value = re.sub(r"(?i)\bna compra de\b", "Na compra de", value)
    value = re.sub(r"\s+", " ", value).strip(" .-")
    if not re.match(r"(?i)^cupons?\b", value):
        value = value.lower()
        value = value[:1].upper() + value[1:]
    value = re.sub(r"(?i)^black friday:\s*descontos?.*?at[eé]\s*(\d+\s*%)", r"Black Friday: até \1 off", value)
    value = re.sub(r"(?i)^descontos?.*?black friday.*?at[eé]\s*(\d+\s*%)", r"Black Friday: até \1 off", value)
    value = re.sub(r"(?i)^black friday:\s*black friday", "Black Friday", value)
    value = re.sub(r"(?i)^black friday\b", "Black Friday", value)
    value = re.sub(r"(?i)^faça sua matrícula durante o mês de maio e ganhe uma mochila exclusiva", "Matrícula em maio: ganhe mochila exclusiva", value)
    value = re.sub(r"(?i)\boff\b", "off", value)
    value = re.sub(r"(?i)\bpix\b", "Pix", value)
    value = re.sub(r"(?i)\br\$", "R$", value)
    value = re.sub(r"(?i)\bbotocenter\b", "Botocenter", value)
    value = re.sub(r"(?i)\baromas\b", "aromas", value)
    value = re.sub(r"(?i)^cupom\s+([a-z0-9_-]+)$", lambda match: "Cupom " + match.group(1).upper(), value)
    value = re.sub(r"(?i)^cupons\s+([a-z0-9_-]+)\s+e\s+([a-z0-9_-]+)$", lambda match: "Cupons " + match.group(1).upper() + " e " + match.group(2).upper(), value)
    value = re.sub(r"\s+", " ", value).strip(" .-")
    if len(value) > 92:
        value = value[:92].rsplit(" ", 1)[0].rstrip(" ,;")
    return value


def extract_promotion(value, mention_label=""):
    text = strip_social_noise(value, mention_label)
    if not text or not PROMO_RE.search(text):
        return ""

    if re.search(r"(?i)\bvalor de venda\b", text[:320]) and not re.search(
        r"(?i)\b(?:off|desconto|cupom|promo|condi(?:ç|c)(?:ões|oes)|bônus|bonus)\b", text[:320]
    ):
        return ""

    code_matches = re.findall(r"(?i)\bcupom(?: de desconto)?\s+[\"“]?([a-z0-9][a-z0-9_-]{2,})", text)
    quoted_codes = re.findall(r'(?i)cupons?\s+[\"“]([^\"”]+)[\"”]\s+ou\s+[\"“]([^\"”]+)[\"”]', text)
    if quoted_codes:
        codes = [part for pair in quoted_codes for part in pair]
        return clean_offer("Cupons " + " e ".join(codes[:2]), mention_label)
    if code_matches:
        return clean_offer("Cupom " + code_matches[0].upper(), mention_label)

    sentences = split_sentences(text)
    clauses = []
    for sentence in sentences:
        clauses.extend(re.split(r"\s*[.;]\s*|\s{2,}", sentence))
    clauses = [normalize_space(clause.strip(" -:")) for clause in clauses if normalize_space(clause)]

    joined = " ".join(clauses[:4])
    price_deal = re.search(
        r"(?i)((?:[\wÀ-ÿ ]{0,28}\s+)?de\s+R\$\s?\d+[,.]?\d*\s+por\s+(?:apenas\s+)?R\$\s?\d+[,.]?\d*)",
        joined,
    )
    if price_deal:
        second_price = re.search(
            r"(?i)(combo[^.]{0,55}?de\s+R\$\s?\d+[,.]?\d*\s+por\s+(?:s[oó]\s+)?R\$\s?\d+[,.]?\d*)",
            joined,
        )
        offer = price_deal.group(1)
        if second_price:
            offer += " + " + second_price.group(1)
        return clean_offer(offer, mention_label)

    for clause in clauses:
        if re.search(r"(?i)\d+\s*%\s*(?:off|de desconto)|(?:off|desconto)[^.;]{0,28}\d+\s*%", clause):
            return clean_offer(clause, mention_label)

    for clause in clauses:
        if re.search(r"(?i)\bat[eé]\s+\d+\s*%\s*(?:off|de desconto)?", clause):
            prefix = "Black Friday: " if re.search(r"(?i)black friday|black november", text) else ""
            return clean_offer(prefix + clause, mention_label)

    for clause in clauses:
        if re.search(r"(?i)\b(?:matr[ií]cula gr[aá]tis|isen(?:ç|c)[aã]o de matr[ií]cula|primeira mensalidade|mensalidade)\b", clause):
            return clean_offer(clause, mention_label)

    for clause in clauses:
        if re.search(r"(?i)\bR\$\s?\d+[,.]?\d*\s*(?:off|de desconto|desconto)\b", clause):
            return clean_offer(clause, mention_label)

    for clause in clauses:
        if re.search(r"(?i)\b(?:entrega gr[aá]tis|avalia(?:ç|c)[aã]o gr[aá]tis|ganhe|brinde|bolsa exclusiva|mochila exclusiva)\b", clause):
            return clean_offer(clause, mention_label)

    for clause in clauses:
        if re.search(r"(?i)\bcondi(?:ç|c)(?:ões|oes) especiais\b", clause):
            if re.search(r"(?i)seguidores|seguidoras", clause):
                return "Condições especiais para seguidores"
            if re.search(r"(?i)moradores", clause):
                return "Condições especiais para moradores"
            return "Condições especiais"

    if re.search(r"(?i)\bblack friday|black november\b", text):
        return "Black Friday: condições especiais"
    if re.search(r"(?i)\bvalores promocionais\b", text):
        return "Valores promocionais"
    return ""


def clean_fact_sentence(sentence, mention_label):
    sentence = strip_social_noise(sentence, mention_label)
    sentence = re.sub(r"(?i)\s+(?:dá uma passadinha|da uma passadinha|querendo renovar|veja o caso|no próximo sábado|no proximo sábado|no próximo sabado|no proximo sabado).*$", "", sentence)
    sentence = re.sub(r"(?i)^dica especial (?:para|pra).+?:\s*", "", sentence)
    sentence = re.sub(r"(?i)^dica (?:boa|especial).+?:\s*", "", sentence)
    sentence = re.sub(r"(?i)^fomos (?:conhecer|visitar)\s+", "", sentence)
    sentence = re.sub(r"(?i)^a gente (?:foi|descobriu|adora descobrir|acompanhou de perto)\s+", "", sentence)
    sentence = re.sub(r"(?i)^se você (?:busca|procura|curte|quer|precisa|está procurando).+?,\s*", "", sentence)
    sentence = re.sub(r"(?i)^pra quem (?:ainda )?(?:não conhece|busca|procura|curte|quer).+?,\s*", "", sentence)
    sentence = re.sub(r"(?i)^para quem (?:ainda )?(?:não conhece|busca|procura|curte|quer).+?,\s*", "", sentence)
    sentence = re.sub(r"(?i)^você sabia que\s+", "", sentence)
    sentence = re.sub(r"(?i)^tem novidade chegando aqui no bairro!?\s*", "", sentence)
    sentence = re.sub(r"(?i)^novidade na mascote\s*", "", sentence)
    sentence = re.sub(r"(?i)^hoje\s+", "", sentence)
    sentence = re.sub(r"(?i)\b(?:ótim[ao]s?|excelentes?|imperdível|incrível|lind[ao]s?|delicios[ao]s?|"
                      r"chei[ao] de charme|parada obrigatória|super|muito aguardada|vale a pena|"
                      r"faz toda a diferença)\b", "", sentence)
    sentence = re.sub(r"(?i)\s+(?:arraste|arrasta|confira|corre|chama|link na bio|dá uma passadinha|da uma passadinha).*$", "", sentence)
    sentence = re.sub(r"\s+", " ", sentence).strip(" .-")
    if sentence and sentence[-1] not in ".!?":
        sentence += "."
    return sentence


def sentence_case(value):
    value = normalize_space(value)
    if not value:
        return ""
    upper_chars = sum(1 for char in value if char.isalpha() and char.isupper())
    alpha_chars = sum(1 for char in value if char.isalpha())
    if alpha_chars and upper_chars / alpha_chars > 0.65:
        value = value.lower()
    return value[:1].upper() + value[1:]


def trim_detail(value, max_len=180):
    value = normalize_space(value)
    value = re.sub(r"(?i)\b(?:pra você|para você|arraste|arrasta|confira|corre|chama|link na bio|dá uma passadinha|da uma passadinha|querendo renovar|veja o caso).*$", "", value)
    value = value.strip(" ,.;:-")
    cut = value
    if len(value) > max_len:
        cut = value[:max_len].rsplit(",", 1)[0].strip(" ,.;:-")
        if len(cut) < 70:
            cut = value[:max_len].rsplit(" ", 1)[0].strip(" ,.;:-")
    cut = re.sub(r"(?i)\s+\b(?:e|que|com|para|por|de|da|do|a|o|q|s|desc|ate|até)\b$", "", cut).strip(" ,.;:-")
    return cut


def is_fact_detail(value):
    if len(value) < 28:
        return False
    if CTA_RE.search(value) or PROMO_RE.search(value):
        return False
    if re.search(r"(?i)\b(?:comenta aqui|marque alguém|não perca|garanta já|aproveite|imperdível|"
                 r"te espera|apaixonados pelo que fazem|talento único|carinho|padrão que a gente|"
                 r"momento que fica pra sempre|querendo renovar|dá uma passadinha|veja o caso|"
                 r"tudo para transformar|modelo ideal|um detalhe que|uma escolha|de cair o|"
                 r"apaixonad[ao] pelo que faz|no próximo sábado|no proximo sabado)\b", value):
        return False
    return bool(FACT_RE.search(value) or re.search(r"\b\d+\b|m²|R\$", value))


def add_detail(details, detail):
    detail = normalize_space(detail).strip()
    if not detail:
        return
    normalized = normalize_space(re.sub(r"[^\wÀ-ÿ ]+", " ", detail.lower()))
    tokens = {token for token in normalized.split() if len(token) > 3}
    for existing in details:
        existing_normalized = normalize_space(re.sub(r"[^\wÀ-ÿ ]+", " ", existing.lower()))
        existing_tokens = {token for token in existing_normalized.split() if len(token) > 3}
        overlap = tokens & existing_tokens
        if normalized in existing_normalized or existing_normalized in normalized:
            return
        if tokens and existing_tokens and len(overlap) / min(len(tokens), len(existing_tokens)) >= 0.55:
            return
    details.append(detail)


def format_fact(template, detail):
    detail = sentence_case(detail).rstrip(".")
    if template.startswith(("Oferece", "Conta com", "Trabalha com", "Cardápio com", "Especializado em")):
        detail = detail[:1].lower() + detail[1:]
    return template.format(detail)


def extract_service_details(text, mention_label):
    text = strip_social_noise(text, mention_label)
    text = re.sub(r"(?i)\b(?:arraste|arrasta|confira|corre|link na bio).*$", "", text)
    details = []

    patterns = [
        (r"(?i)\btrabalha com\s+([^.!?]{18,220})", "Trabalha com {}."),
        (r"(?i)\b(?:por lá, você encontra|você encontra)\s+([^.!?]{18,220})", "Oferece {}."),
        (r"(?i)\boferece\s+([^.!?]{18,220})", "Oferece {}."),
        (r"(?i)\b(?:conta com|possui|tem)\s+([^.!?]{18,220})", "Conta com {}."),
        (r"(?i)\b(?:serviços como|serviços:|serviços para)\s+([^.!?]{18,220})", "Serviços: {}."),
        (r"(?i)\b(?:cardápio|menu)\s+(?:tem|inclui|com)\s+([^.!?]{18,220})", "Cardápio com {}."),
        (r"(?i)\b(?:especiali[sz]ad[ao] em)\s+([^.!?]{18,220})", "Especializado em {}."),
        (r"(?i)\b(?:apartamento|imóvel|empreendimento)\s+([^.!?]{18,220})", "Imóvel com {}."),
    ]

    for pattern, template in patterns:
        for match in re.finditer(pattern, text):
            detail = clean_fact_sentence(match.group(1), mention_label)
            if re.search(r"(?i)\b(?:novidade|chegando|talento único|comemora|festa|tudo para transformar|modelo ideal|um detalhe que|uma escolha|de cair o)\b", detail):
                continue
            detail = trim_detail(detail)
            if len(detail) < 16:
                continue
            add_detail(details, format_fact(template, detail))
            if len(details) >= 3:
                return details

    for sentence in split_sentences(text):
        if len(details) >= 3:
            break
        detail = clean_fact_sentence(sentence, mention_label)
        if not is_fact_detail(detail):
            continue
        if re.search(r"(?i)\b(?:novidade chegando|a gente|fomos|dica especial|comenta aqui)\b", detail):
            continue
        detail = trim_detail(detail, 210)
        add_detail(details, sentence_case(detail))

    return details


def summarize_description(value, category, subcategory, mention_label):
    base = f"{mention_label}: {subcategory.lower()} na Vila Mascote."
    details = extract_service_details(value, mention_label)
    summary = f"{base} {' '.join(details)}" if details else base
    summary = re.sub(r"\s+", " ", summary).strip(" .-")
    if summary and summary[-1] not in ".!?":
        summary += "."
    if len(summary) > 340:
        summary = summary[:337].rstrip(" ,;")
        summary = summary.rsplit(" ", 1)[0].rstrip(" ,;") + "."
    return summary


def clean_name(value):
    value = re.sub(r"\s+", " ", value or "").strip()
    replacements = {
        "Babbogiovannivilamascote": "Babbo Giovanni Vila Mascote",
        "Bacalhaudoguga": "Bacalhau do Guga",
        "Padariarecantodamascote": "Padaria Recanto da Mascote",
        "Pastelariavoze": "Pastelaria Vó Zé",
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


def build_search_terms(name, instagram, category, subcategory, categories, description, promotion):
    terms = []
    search_blob = " ".join(
        [
            name,
            instagram or "",
            category,
            subcategory,
            " ".join(categories),
            description or "",
            promotion or "",
        ]
    ).lower()

    if promotion:
        terms.extend(["Cupom", "Promoção", "Promocao", "Desconto", "Oferta"])

    if "bacalhau" in search_blob and "guga" in search_blob:
        terms.extend(
            [
                "restaurante português",
                "restaurante portugues",
                "português",
                "portugues",
                "comida portuguesa",
                "culinária portuguesa",
                "culinaria portuguesa",
                "bacalhau",
            ]
        )

    unique_terms = []
    for term in terms:
        term = normalize_space(term)
        if term and term not in unique_terms:
            unique_terms.append(term)
    return unique_terms


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
            description = summarize_description(row["resumo"], primary, row["subcategoria_final"], display_name)
            promotion = extract_promotion(row["resumo"], display_name)
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
                    "descricao": description,
                    "promocao": promotion,
                    "termosBusca": build_search_terms(
                        display_name,
                        row["instagram"],
                        primary,
                        row["subcategoria_final"],
                        categories,
                        description,
                        promotion,
                    ),
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
