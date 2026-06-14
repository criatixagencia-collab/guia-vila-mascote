#!/usr/bin/env python3
"""
Geocode addresses from estabelecimentos_categorizados_v1.csv.

ArcGIS is the primary source because it returns address-level points for many
Vila Mascote streets. Nominatim often falls back to the middle of the street,
which creates misleading clusters on the guide map.
"""
import csv
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import ssl
import certifi

SOURCE = "CATEGORIZACAO/estabelecimentos_categorizados_v1.csv"
GEOCODES_OUT = "data/vila_mascote_geocodes.json"
USER_AGENT = "GuiaVilaMascote/1.0 (contato@guiamascote.com.br)"
DELAY = 0.25

MAP_LAT_MIN = -23.666
MAP_LAT_MAX = -23.630
MAP_LNG_MIN = -46.678
MAP_LNG_MAX = -46.652

TRUSTED_ADDR_TYPES = {
    "PointAddress",
    "StreetAddress",
    "Subaddress",
    "POI",
}

MIN_SCORE = 90


def normalize_address(addr):
    addr = re.sub(r"\s+", " ", addr).strip()
    addr = re.sub(r"[–—]", "-", addr)
    addr = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", addr)
    addr = re.sub(r"\s*/\s*\d{1,5}\b", "", addr)
    # Strip sala/loja/apto from end
    addr = re.sub(
        r"(?i)\s*[-–,]\s*(?:sala|loja|conjunto?|apto|bloco|casa|fundos)\s+\d{1,3}.*$",
        "", addr,
    )
    return addr.strip(" ,.-")


def normalize_street_label(value):
    value = normalize_address(value)
    replacements = [
        (r"(?i)\bav\.?\s+", "Avenida "),
        (r"(?i)\br\.?\s+", "Rua "),
        (r"(?i)\bsta\.?\s+", "Santa "),
        (r"(?i)\beng\.?\s+", "Engenheiro "),
        (r"(?i)\bprof\.?\s+", "Professor "),
    ]
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value)
    return normalize_address(value)


def extract_address_from_part(part):
    part = normalize_address(part)
    if not part:
        return ""

    number = r"(?:\d{1,3}(?:\.\d{3})+|\d{1,5})(?:\s*/\s*(?:\d{1,3}(?:\.\d{3})+|\d{1,5}))?"
    street_prefix = r"(?:av\.?|avenida|r\.?|rua|alameda|travessa|estrada|praca|praça|rodovia)"
    pattern = re.compile(
        rf"(?i)\b({street_prefix}\s+[^;]+?)\s*,?\s+({number})\b"
    )

    match = pattern.search(part)
    if not match:
        pattern = re.compile(
            rf"(?i)\b({street_prefix}\s+[^;]*?),\s*({number})\b"
        )
        match = pattern.search(part)

    if not match:
        return ""

    street = normalize_street_label(match.group(1))
    if len(street) > 70 or re.search(
        r"(?i)\b(?:quem passa|percebid[ao]|movimenta[cç][aã]o|funcionava|antiga|n[uú]mero|onde)\b",
        street,
    ):
        return ""
    house_number = normalize_address(match.group(2))
    house_number = re.sub(r"/.*$", "", house_number)
    return normalize_address(f"{street}, {house_number}")


def extract_addresses():
    """Returns list of (raw_name, address, search_key) tuples."""
    rows = []
    with open(SOURCE, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = re.sub(r"\s+", " ", (row.get("nome") or "")).strip()
            if not name:
                continue
            value = (row.get("endereco") or "").strip()
            if not value:
                continue

            candidates = []
            for part in re.split(r";|\n", value):
                part = re.sub(r"\s+", " ", part).strip(" .-")
                if part:
                    candidates.append(part)

            addr = ""
            for part in candidates:
                addr = extract_address_from_part(part)
                if addr:
                    break
            if not addr:
                for part in candidates:
                    if re.search(r"(?i)\b(?:av\.?|avenida|r\.?|rua)\b", part) and re.search(r"\d", part):
                        addr = normalize_street_label(part)
                        break
            if not addr and candidates:
                addr = normalize_street_label(candidates[0])

            if addr:
                key = f"{name}::{addr}"
                rows.append((name, addr, key))
    return rows


def build_search(addr):
    a = normalize_street_label(addr).strip(" ,.-")
    if not re.search(r"(?i)são paulo|sao paulo|sp", a):
        a += ", São Paulo - SP, Brasil"
    return a


def in_map_bounds(lat, lng):
    return MAP_LAT_MIN <= lat <= MAP_LAT_MAX and MAP_LNG_MIN <= lng <= MAP_LNG_MAX


def geocode_arcgis(search):
    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?" + urllib.parse.urlencode(
        {
            "SingleLine": search,
            "f": "json",
            "outFields": "Match_addr,Addr_type,Score",
            "maxLocations": 5,
            "countryCode": "BRA",
            "location": "-46.665,-23.648",
            "searchExtent": "-46.690,-23.670,-46.640,-23.620",
        }
    )
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        data = json.loads(resp.read())

    candidates = data.get("candidates", [])
    for candidate in candidates:
        attrs = candidate.get("attributes", {})
        location = candidate.get("location") or {}
        score = float(attrs.get("Score") or candidate.get("score") or 0)
        addr_type = attrs.get("Addr_type") or ""
        if location.get("y") is None or location.get("x") is None:
            continue
        lat = float(location.get("y"))
        lng = float(location.get("x"))
        if (
            score >= MIN_SCORE
            and addr_type in TRUSTED_ADDR_TYPES
            and in_map_bounds(lat, lng)
        ):
            return {
                "lat": round(lat, 7),
                "lng": round(lng, 7),
                "source": "arcgis",
                "display_name": attrs.get("Match_addr", ""),
                "score": score,
                "addr_type": addr_type,
                "query": search,
            }

    if candidates:
        first = candidates[0]
        attrs = first.get("attributes", {})
        location = first.get("location") or {}
        return {
            "lat": round(float(location.get("y")), 7) if location.get("y") is not None else None,
            "lng": round(float(location.get("x")), 7) if location.get("x") is not None else None,
            "source": "",
            "display_name": attrs.get("Match_addr", ""),
            "score": float(attrs.get("Score") or first.get("score") or 0),
            "addr_type": attrs.get("Addr_type") or "",
            "query": search,
            "rejected": "low_score_or_out_of_bounds",
        }
    return None


def load_existing():
    if os.path.exists(GEOCODES_OUT):
        with open(GEOCODES_OUT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def should_refresh(existing, force=False):
    if force:
        return True
    if not existing:
        return True
    if existing.get("rejected") or existing.get("error"):
        return False
    return existing.get("source") != "arcgis"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Regenerate every current address.")
    args = parser.parse_args()

    rows = extract_addresses()
    # Deduplicate by search key (name::address format)
    seen = {}
    for name, addr, key in rows:
        if key not in seen:
            seen[key] = {"display_name": name, "raw_addr": addr}

    existing_geocodes = load_existing()
    geocodes = {k: existing_geocodes[k] for k in seen if k in existing_geocodes}
    to_geocode = {k: v for k, v in seen.items() if should_refresh(geocodes.get(k), args.force)}

    print(f"Total entradas unicas: {len(seen)}")
    print(f"Ja geocodificados: {len(geocodes)}")
    print(f"Para geocodificar: {len(to_geocode)}")

    if not to_geocode:
        print("Nada a fazer.")
        return

    success = 0
    for i, (key, info) in enumerate(to_geocode.items(), 1):
        search_addr = build_search(info["raw_addr"])
        sys.stdout.write(f"[{i}/{len(to_geocode)}] {info['display_name'][:30]}... ")
        sys.stdout.flush()
        try:
            result = geocode_arcgis(search_addr)
            if result:
                geocodes[key] = result
                if result.get("source"):
                    success += 1
                    print(f"OK ({result['lat']:.5f}, {result['lng']:.5f}) {result.get('addr_type', '')} {result.get('score', '')}")
                else:
                    print(f"REJEITADO {result.get('addr_type', '')} {result.get('score', '')} ({result.get('lat')}, {result.get('lng')})")
            else:
                geocodes[key] = {
                    "lat": None,
                    "lng": None,
                    "source": "",
                    "display_name": "",
                    "query": search_addr,
                    "rejected": "no_result",
                }
                print("Sem resultado")
        except Exception as e:
            geocodes[key] = {
                "lat": None,
                "lng": None,
                "source": "",
                "display_name": "",
                "query": search_addr,
                "error": str(e),
            }
            print(f"ERRO: {e}")
        time.sleep(DELAY)

    os.makedirs("data", exist_ok=True)
    with open(GEOCODES_OUT, "w", encoding="utf-8") as f:
        json.dump(geocodes, f, ensure_ascii=False, indent=2)

    print(f"\nFeito! {success}/{len(to_geocode)} geocodificados.")
    print(f"Total no arquivo: {len(geocodes)}")


if __name__ == "__main__":
    main()
