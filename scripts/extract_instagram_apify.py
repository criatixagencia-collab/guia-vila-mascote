#!/usr/bin/env python3
import argparse
import csv
import getpass
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ACTOR_ID = "apify~instagram-scraper"
PROFILE_URL = "https://www.instagram.com/vila.mascote/"
DEFAULT_LIMIT = 100
OUT_DIR = Path("SCRAP UM ANO")
KNOWN_GUIDE_PATH = Path("guia_vila_mascote_all.csv")
IGNORED_HANDLES = {"vila.mascote", "revistavilamascote"}
EMAIL_HANDLE_PARTS = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "icloud.com"}


def api_request(method, url, token, body=None):
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {message}") from exc


def start_run(token, limit, since=None):
    actor_input = {
        "directUrls": [PROFILE_URL],
        "resultsType": "posts",
        "resultsLimit": limit,
        "addParentData": False,
    }
    if since:
        actor_input["onlyPostsNewerThan"] = since
    encoded_actor = urllib.parse.quote(ACTOR_ID, safe="")
    url = f"https://api.apify.com/v2/acts/{encoded_actor}/runs"
    return api_request("POST", url, token, actor_input)["data"]


def wait_for_run(token, run_id):
    url = f"https://api.apify.com/v2/actor-runs/{run_id}"
    terminal = {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}
    last_status = None
    while True:
        run = api_request("GET", url, token)["data"]
        status = run["status"]
        if status != last_status:
            print(f"Apify run: {status}", flush=True)
            last_status = status
        if status in terminal:
            return run
        time.sleep(10)


def fetch_dataset_items(token, dataset_id):
    params = urllib.parse.urlencode({"format": "json", "clean": "1"})
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?{params}"
    return api_request("GET", url, token)


def compact_text(value):
    return re.sub(r"\s+", " ", (value or "")).strip()


def unique(values):
    cleaned = []
    for value in values:
        if value and value not in cleaned:
            cleaned.append(value)
    return cleaned


def clean_handle(value):
    value = (value or "").lower().lstrip("@").strip()
    match = re.match(r"[a-z0-9._]{2,30}", value)
    if not match:
        return ""
    handle = match.group(0).strip(".")
    if handle in EMAIL_HANDLE_PARTS or handle.endswith((".com", ".com.br")):
        return ""
    return handle


def extract_mentions(item):
    raw = item.get("mentions") or []
    if isinstance(raw, str):
        raw = [raw]
    caption = item.get("caption") or ""
    from_caption = re.findall(r"(?<![A-Za-z0-9._])@([A-Za-z0-9._]{2,30})", caption)
    handles = [clean_handle(value) for value in [*raw, *from_caption]]
    return unique([handle for handle in handles if handle and handle not in IGNORED_HANDLES])


def load_known_guide():
    if not KNOWN_GUIDE_PATH.exists():
        return {}
    known = {}
    with KNOWN_GUIDE_PATH.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            handle = clean_handle(row.get("instagram"))
            if handle:
                known[handle] = row.get("nome", "")
    return known


def display_name_from_handle(handle):
    if not handle:
        return ""
    words = re.split(r"[._]+", handle)
    if len(words) > 1:
        return " ".join(word.capitalize() for word in words if word)
    replacements = [
        ("vilamascote", " Vila Mascote"),
        ("restaurante", " Restaurante"),
        ("pizzaria", " Pizzaria"),
        ("padaria", " Padaria"),
        ("acessorios", " Acessórios"),
        ("clinica", " Clínica"),
        ("mascote", " Mascote"),
    ]
    name = handle
    for token, replacement in replacements:
        name = name.replace(token, replacement)
    return compact_text(name).title() or handle


def extract_phone(text):
    patterns = [
        r"(?:\+?55\s*)?\(?11\)?\s*9?\d{4}[-.\s]?\d{4}",
        r"(?:\+?55\s*)?\(?11\)?\s*\d{4}[-.\s]?\d{4}",
    ]
    phones = []
    for pattern in patterns:
        for match in re.findall(pattern, text):
            digits = re.sub(r"\D", "", match)
            if len(digits) in {10, 11, 12, 13}:
                if digits.startswith("55"):
                    digits = digits[2:]
                if digits not in phones:
                    phones.append(digits)
    return "; ".join(phones)


def extract_email(text):
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return "; ".join(unique([email.lower().rstrip(".,;:") for email in emails]))


def extract_address(text):
    address_words = ("rua", "r.", "avenida", "av.", "alameda", "travessa", "praça", "praca", "largo")
    noise_markers = ("à venda", "a venda", "apartamento", "condomínio", "condominio")
    candidates = []
    for line in re.split(r"[\n\r]+", text):
        line_clean = compact_text(re.sub(r"^[^A-Za-zÀ-ÿ0-9]+", "", line))
        low = line_clean.lower()
        if any(marker in low for marker in noise_markers):
            continue
        if any(low.startswith(word) or f" {word} " in low for word in address_words):
            candidates.append(line_clean.strip(" -•|"))
    street_pattern = re.compile(
        r"(?<![A-Za-zÀ-ÿ])((?:rua|r\.|avenida|av\.|alameda|travessa|praça|praca|largo)\s+[^;\n]{3,110})",
        flags=re.I,
    )
    for match in street_pattern.findall(text):
        candidate = compact_text(match).strip(" -•|,.")
        low = candidate.lower()
        if re.search(r"\d{1,5}", candidate) and not any(marker in low for marker in noise_markers):
            candidates.append(candidate)
    return "; ".join(unique(candidates))


def infer_category(text):
    low = text.lower()
    rules = [
        ("Serviços", ("imóvel", "imoveis", "imóveis", "imobiliária", "imobiliaria", "corretor", "reforma", "obra", "pedreiro", "manutenção", "manutencao", "ar-condicionado", "refrigeração", "higienização", "impermeabilização", "costura", "sapataria")),
        ("Pet", ("pet shop", "petland", "pet ", "pets", "veterin", "cães", "caes", "gatos", "banho e tosa", "hospitalveterin")),
        ("Compras", ("loja", "moda", "roupa", "calçado", "calcado", "boutique", "mercado", "hortifruti", "floricultura", "semijoias", "acessórios", "acessorios", "prata 925")),
        ("Restaurante", ("restaurante", "pizza", "pizzaria", "burger", "hambúrguer", "hamburguer", "sushi", "rodízio", "rodizio", "bar ", "chopp", "cafeteria", "padaria", "doceria", "bolo", "doce", "açaí", "acai", "esfiha", "pastel", "marmita", "delivery", "culinária", "culinaria", "queijo", "queijaria", "sobremesa")),
        ("Saúde/Beleza", ("salão de beleza", "salao de beleza", "barbearia", "estética", "estetica", "spa", "clínica", "clinica", "dentista", "odont", "pilates", "fisioterapia", "terapia", "nutri", "harmonização", "harmonizacao", "sobrancelha", "unha", "academia", "fitness", "bike", "zumba", "yoga", "botox", "preenchimento", "depilação", "depilacao")),
        ("Educação", ("escola", "colégio", "colegio", "curso de inglês", "curso de ingles", "inglês", "ingles", "berçário", "bercario", "idioma", "teacher")),
    ]
    for category, keywords in rules:
        if any(keyword in low for keyword in keywords):
            return category
    return ""


def infer_subcategory(text):
    low = text.lower()
    rules = [
        ("Reformas", ("reforma", "obra", "pedreiro")),
        ("Imobiliária", ("imóvel", "imobiliária", "imobiliaria", "corretor")),
        ("Ar-condicionado", ("ar-condicionado", "refrigeração")),
        ("Limpeza de estofados", ("higienização", "impermeabilização", "estofado")),
        ("Costura/Sapataria", ("costura", "sapataria", "tênis day", "tenis day")),
        ("Hospital veterinário", ("hospital veterin", "veterinário", "veterinario")),
        ("Pet shop", ("pet shop", "petland", "banho e tosa")),
        ("Pizzaria", ("pizza", "pizzaria")),
        ("Hamburgueria", ("hambúrguer", "hamburguer", "burger")),
        ("Japonês", ("sushi", "rodízio japon", "rodizio japon")),
        ("Árabe", ("árabe", "arabe", "shawarma", "kebab")),
        ("Português", ("bacalhau", "português", "portugues")),
        ("Padaria", ("padaria", "café da manhã")),
        ("Doces/Bolos", ("bolos", "bolo ", "doceria", "sobremesa", "brigadeiro")),
        ("Queijaria", ("queijo", "queijaria")),
        ("Restaurante", ("restaurante", "prato principal", "menu experiência")),
        ("Moda/Acessórios", ("moda", "roupa", "semijoias", "acessórios", "acessorios", "prata 925")),
        ("Clínica multidisciplinar", ("multidisciplinar", "terapia aba", "integração sensorial", "terapia ocupacional")),
        ("Pilates/Fisioterapia", ("pilates", "fisioterapia", "lombalgia", "osteopata", "onda de choque", "liberação miofascial")),
        ("Clínica/Estética", ("estética", "estetica", "botox", "preenchimento", "harmonização", "harmonizacao")),
        ("Nutricionista", ("nutricionista", "nutri")),
        ("Academia/Fitness", ("academia", "fitness", "bike", "zumba", "yoga", "treino")),
        ("Escola de idiomas", ("inglês", "ingles", "teacher")),
    ]
    for subcategory, keywords in rules:
        if any(keyword in low for keyword in keywords):
            return subcategory
    return ""


def extract_offer(caption):
    lines = [compact_text(line).strip(" .:-|•") for line in (caption or "").splitlines()]
    lines = [line for line in lines if line]
    markers = ("off", "desconto", "cupom", "grátis", "gratis", "promoção", "promocao", "condições", "condicoes", "ganhe", "r$")
    offer_lines = []
    for line in lines[:10]:
        if "🎫" in line or any(marker in line.lower() for marker in markers):
            offer_lines.append(line)
        elif offer_lines and len(offer_lines) < 3 and re.search(r"r\$\s*\d", line.lower()):
            offer_lines.append(line)
    return compact_text(" | ".join(offer_lines))[:220]


def infer_name(caption, mentions, known_guide):
    primary = mentions[0] if mentions else ""
    if primary in known_guide:
        return known_guide[primary]
    if primary:
        return display_name_from_handle(primary)
    business_match = re.search(r"\b(?:da|do|de)\s+([A-ZÀ-Ý][A-Za-zÀ-ÿ0-9&'. ]{2,60}?)(?:,|\.|\s+já|\s+e\s+)", caption or "")
    if business_match:
        return compact_text(business_match.group(1)).strip()
    lines = [compact_text(line).strip(" .:-|•") for line in (caption or "").splitlines()]
    lines = [line for line in lines if line]
    for line in lines[:6]:
        if len(line) <= 80 and not line.startswith("#"):
            if not re.search(r"^(vila mascote|publi|parceria|post|confira|vem|hoje)\b", line.lower()):
                return line
    return ""


def normalize_items(items, known_guide):
    rows = []
    seen_urls = set()
    for item in items:
        url = item.get("url") or item.get("postUrl") or ""
        if url and url in seen_urls:
            continue
        seen_urls.add(url)
        caption = item.get("caption") or ""
        mentions = extract_mentions(item)
        primary = mentions[0] if mentions else ""
        hashtags = item.get("hashtags") or []
        if isinstance(hashtags, str):
            hashtags = [hashtags]
        text = "\n".join(
            compact_text(part)
            for part in [caption, item.get("alt") or "", item.get("locationName") or ""]
            if part
        )
        rows.append(
            {
                "nome_provavel": infer_name(caption, mentions, known_guide),
                "instagram_principal": "@" + primary if primary else "",
                "categoria_provavel": infer_category(text),
                "subcategoria_provavel": infer_subcategory(text),
                "ja_no_guia": "sim" if primary in known_guide else "não",
                "instagram_citado": "; ".join("@" + mention for mention in mentions),
                "telefone_extraido": extract_phone(text),
                "email_extraido": extract_email(text),
                "endereco_extraido": extract_address(caption),
                "oferta_extraida": extract_offer(caption),
                "localizacao_post": item.get("locationName") or "",
                "data_post": item.get("timestamp") or "",
                "tipo": item.get("type") or "",
                "curtidas": item.get("likesCount") or "",
                "comentarios": item.get("commentsCount") or "",
                "hashtags": "; ".join("#" + h.lstrip("#") for h in hashtags),
                "resumo_legenda": compact_text(caption)[:420],
                "link_post": url,
            }
        )
    return rows


def merge_semicolon(values):
    parts = []
    for value in values:
        for part in str(value or "").split(";"):
            part = compact_text(part)
            if part and part not in parts:
                parts.append(part)
    return "; ".join(parts)


def aggregate_businesses(rows):
    grouped = {}
    for row in rows:
        key = row["instagram_principal"] or row["nome_provavel"].lower() or row["link_post"]
        grouped.setdefault(key, []).append(row)

    businesses = []
    for group_rows in grouped.values():
        latest = sorted(group_rows, key=lambda row: row["data_post"], reverse=True)[0]
        category_counts = {}
        subcategory_counts = {}
        for row in group_rows:
            if row["categoria_provavel"]:
                category_counts[row["categoria_provavel"]] = category_counts.get(row["categoria_provavel"], 0) + 1
            if row["subcategoria_provavel"]:
                subcategory_counts[row["subcategoria_provavel"]] = subcategory_counts.get(row["subcategoria_provavel"], 0) + 1
        category = max(category_counts, key=category_counts.get) if category_counts else ""
        subcategory = max(subcategory_counts, key=subcategory_counts.get) if subcategory_counts else ""
        businesses.append(
            {
                "nome_provavel": latest["nome_provavel"],
                "instagram_principal": latest["instagram_principal"],
                "categoria_provavel": category,
                "subcategoria_provavel": subcategory,
                "ja_no_guia": "sim" if any(row["ja_no_guia"] == "sim" for row in group_rows) else "não",
                "telefones": merge_semicolon(row["telefone_extraido"] for row in group_rows),
                "emails": merge_semicolon(row["email_extraido"] for row in group_rows),
                "enderecos": merge_semicolon(row["endereco_extraido"] for row in group_rows),
                "oferta_mais_recente": latest["oferta_extraida"],
                "ultimo_post": latest["data_post"],
                "quantidade_posts": len(group_rows),
                "links_posts": merge_semicolon(row["link_post"] for row in group_rows),
                "resumo_ultimo_post": latest["resumo_legenda"],
            }
        )
    return sorted(businesses, key=lambda row: row["ultimo_post"], reverse=True)


def item_date(item):
    return (item.get("timestamp") or "")[:10]


def filter_items_by_date(items, since=None, before=None):
    filtered = []
    for item in items:
        date = item_date(item)
        if since and date < since:
            continue
        if before and date >= before:
            continue
        filtered.append(item)
    return filtered


def write_outputs(items, rows, prefix=None):
    OUT_DIR.mkdir(exist_ok=True)
    if prefix:
        raw_path = OUT_DIR / f"{prefix}_posts_raw.json"
        post_path = OUT_DIR / f"{prefix}_posts.csv"
        legacy_path = None
        business_path = OUT_DIR / f"{prefix}_negocios.csv"
        candidates_path = OUT_DIR / f"{prefix}_novos_candidatos.csv"
    else:
        raw_path = OUT_DIR / "vila_mascote_instagram_posts_raw.json"
        post_path = OUT_DIR / "vila_mascote_instagram_posts.csv"
        legacy_path = OUT_DIR / "vila_mascote_instagram_extraido.csv"
        business_path = OUT_DIR / "vila_mascote_instagram_negocios.csv"
        candidates_path = OUT_DIR / "vila_mascote_instagram_novos_candidatos.csv"
    raw_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = [
        "nome_provavel",
        "instagram_principal",
        "categoria_provavel",
        "subcategoria_provavel",
        "ja_no_guia",
        "instagram_citado",
        "telefone_extraido",
        "email_extraido",
        "endereco_extraido",
        "oferta_extraida",
        "localizacao_post",
        "data_post",
        "tipo",
        "curtidas",
        "comentarios",
        "hashtags",
        "resumo_legenda",
        "link_post",
    ]
    paths = [post_path]
    if legacy_path:
        paths.append(legacy_path)
    for path in paths:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    business_fieldnames = [
        "nome_provavel",
        "instagram_principal",
        "categoria_provavel",
        "subcategoria_provavel",
        "ja_no_guia",
        "telefones",
        "emails",
        "enderecos",
        "oferta_mais_recente",
        "ultimo_post",
        "quantidade_posts",
        "links_posts",
        "resumo_ultimo_post",
    ]
    businesses = aggregate_businesses(rows)
    with business_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=business_fieldnames)
        writer.writeheader()
        writer.writerows(businesses)
    with candidates_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=business_fieldnames)
        writer.writeheader()
        writer.writerows([row for row in businesses if row["ja_no_guia"] == "não"])
    return raw_path, post_path, business_path, candidates_path, len(businesses)


def process_items(items, prefix=None):
    known_guide = load_known_guide()
    rows = normalize_items(items, known_guide)
    return (*write_outputs(items, rows, prefix=prefix), len(rows))


def parse_args():
    parser = argparse.ArgumentParser(description="Extrai e normaliza posts do Instagram via Apify.")
    parser.add_argument("limit", nargs="?", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--since", help="Data inicial inclusiva, em YYYY-MM-DD.")
    parser.add_argument("--before", help="Data final exclusiva, em YYYY-MM-DD.")
    parser.add_argument("--prefix", help="Prefixo dos arquivos gerados dentro de data/.")
    parser.add_argument("--input", default=str(OUT_DIR / "vila_mascote_instagram_posts_raw.json"))
    parser.add_argument("--process-only", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.process_only:
        raw_input_path = Path(args.input)
        items = json.loads(raw_input_path.read_text(encoding="utf-8"))
        filtered_items = filter_items_by_date(items, since=args.since, before=args.before)
        raw_path, post_path, business_path, candidates_path, business_count, row_count = process_items(filtered_items, prefix=args.prefix)
        print(f"Posts reprocessados: {len(items)}")
        print(f"Posts no intervalo: {len(filtered_items)}")
        print(f"Linhas normalizadas: {row_count}")
        print(f"Negócios consolidados: {business_count}")
        print(f"CSV por post: {post_path}")
        print(f"CSV por negócio: {business_path}")
        print(f"CSV novos candidatos: {candidates_path}")
        return

    token = getpass.getpass("Apify token: ").strip()
    if not token:
        raise SystemExit("Token vazio.")

    run = start_run(token, args.limit, since=args.since)
    print(f"Run id: {run['id']}", flush=True)
    finished = wait_for_run(token, run["id"])
    if finished["status"] != "SUCCEEDED":
        raise SystemExit(f"Run terminou com status {finished['status']}")

    dataset_id = finished["defaultDatasetId"]
    items = fetch_dataset_items(token, dataset_id)
    filtered_items = filter_items_by_date(items, since=args.since, before=args.before)
    raw_path, post_path, business_path, candidates_path, business_count, row_count = process_items(filtered_items, prefix=args.prefix)
    print(f"Posts baixados: {len(items)}")
    print(f"Posts no intervalo: {len(filtered_items)}")
    print(f"Linhas normalizadas: {row_count}")
    print(f"Negócios consolidados: {business_count}")
    print(f"JSON bruto: {raw_path}")
    print(f"CSV por post: {post_path}")
    print(f"CSV por negócio: {business_path}")
    print(f"CSV novos candidatos: {candidates_path}")


if __name__ == "__main__":
    main()
