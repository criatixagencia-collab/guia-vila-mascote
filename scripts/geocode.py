#!/usr/bin/env python3
"""
Geocode addresses from estabelecimentos_categorizados_v1.csv using Nominatim (OSM).
Generates data/vila_mascote_geocodes.json used by build_site_data.py.
"""
import csv
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
DELAY = 1.1  # Nominatim requires max 1 req/sec


def normalize_address(addr):
    addr = re.sub(r"\s+", " ", addr).strip()
    addr = re.sub(r"[–—]", "-", addr)
    # Strip sala/loja/apto from end
    addr = re.sub(
        r"(?i)\s*[-–,]\s*(?:sala|loja|conjunto?|apto|bloco|casa|fundos)\s+\d{1,3}.*$",
        "", addr,
    )
    return addr.strip(" ,.-")


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

            pattern = re.compile(
                r"(?i)\b(?:av\.?|avenida|r\.?|rua|alameda|travessa|estrada|praca|praça|rodovia)\s+"
                r"[^;,.]+?(?:,\s*)?\d{1,5}(?:\s*[-–]\s*[^;,.]+)?"
            )
            addr = ""
            for part in candidates:
                match = pattern.search(part)
                if match:
                    addr = normalize_address(match.group(0))
                    break
            if not addr:
                for part in candidates:
                    if re.search(r"(?i)\b(?:av\.?|avenida|r\.?|rua)\b", part) and re.search(r"\d", part):
                        addr = normalize_address(part)
                        break
            if not addr and candidates:
                addr = normalize_address(candidates[0])

            if addr:
                key = f"{name}::{addr}"
                rows.append((name, addr, key))
    return rows


def build_search(addr):
    a = addr.strip(" ,.-")
    if not re.search(r"(?i)vila mascote|são paulo|sp", a):
        a += ", Vila Mascote, São Paulo - SP"
    return a


def geocode(search):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": search, "format": "json", "limit": 1, "addressdetails": 0}
    )
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        data = json.loads(resp.read())
        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lng": float(data[0]["lon"]),
                "source": "nominatim",
                "display_name": data[0].get("display_name", ""),
            }
    return None


def load_existing():
    if os.path.exists(GEOCODES_OUT):
        with open(GEOCODES_OUT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    rows = extract_addresses()
    # Deduplicate by search key (name::address format)
    seen = {}
    for name, addr, key in rows:
        if key not in seen:
            seen[key] = {"display_name": name, "raw_addr": addr}

    geocodes = load_existing()
    to_geocode = {k: v for k, v in seen.items() if k not in geocodes}

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
            result = geocode(search_addr)
            if result:
                geocodes[key] = result
                success += 1
                print(f"OK ({result['lat']:.5f}, {result['lng']:.5f})")
            else:
                print("Sem resultado")
        except Exception as e:
            print(f"ERRO: {e}")
        time.sleep(DELAY)

    os.makedirs("data", exist_ok=True)
    with open(GEOCODES_OUT, "w", encoding="utf-8") as f:
        json.dump(geocodes, f, ensure_ascii=False, indent=2)

    print(f"\nFeito! {success}/{len(to_geocode)} geocodificados.")
    print(f"Total no arquivo: {len(geocodes)}")


if __name__ == "__main__":
    main()
