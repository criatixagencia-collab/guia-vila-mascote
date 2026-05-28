#!/usr/bin/env python3
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SOURCE = Path("CATEGORIZACAO/estabelecimentos_categorizados_v1.csv")
OUTPUT = Path("data/vila_mascote_geocodes.json")
CENTER = (-23.6489, -46.6656)


def normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def clean_name(value):
    return normalize_space(value)


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

    return candidates[0] if candidates else ""


def query_for(address):
    address = normalize_space(address)
    if not address:
        return ""
    if "sao paulo" not in address.lower() and "são paulo" not in address.lower():
        address = f"{address}, Vila Mascote, Sao Paulo, SP, Brasil"
    return address


def fallback_coord(index, total):
    # Keep ungeocoded items visible around Vila Mascote instead of hiding them.
    ring = max(1, total)
    angle = (index * 137.508) % 360
    radius = 0.0014 + (index % 6) * 0.00035
    import math

    lat = CENTER[0] + math.sin(math.radians(angle)) * radius
    lng = CENTER[1] + math.cos(math.radians(angle)) * radius
    return round(lat, 7), round(lng, 7)


def geocode(address):
    url = "https://nominatim.openstreetmap.org/search?" + urlencode(
        {
            "q": query_for(address),
            "format": "json",
            "limit": 1,
            "countrycodes": "br",
            "viewbox": "-46.686,-23.636,-46.645,-23.661",
            "bounded": 0,
        }
    )
    request = Request(url, headers={"User-Agent": "GuiaVilaMascoteLocal/1.0"})
    with urlopen(request, timeout=18) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload:
        return None
    first = payload[0]
    return {
        "lat": round(float(first["lat"]), 7),
        "lng": round(float(first["lon"]), 7),
        "display_name": first.get("display_name", ""),
        "source": "nominatim",
    }


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cache = {}
    if OUTPUT.exists():
        cache = json.loads(OUTPUT.read_text(encoding="utf-8"))

    rows = []
    with SOURCE.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["acao_sugerida"] == "Listar":
                rows.append(row)

    changed = False
    for index, row in enumerate(rows, start=1):
        name = clean_name(row["nome"])
        address = extract_address(row["endereco"])
        key = f"{name}::{address}"
        if key in cache:
            continue

        entry = {
            "nome": name,
            "address": address,
            "query": query_for(address),
            "lat": None,
            "lng": None,
            "display_name": "",
            "source": "fallback",
        }

        if address:
            try:
                found = geocode(address)
                if found:
                    entry.update(found)
                time.sleep(1.05)
            except Exception as error:
                entry["error"] = str(error)

        if entry["lat"] is None or entry["lng"] is None:
            lat, lng = fallback_coord(index, len(rows))
            entry["lat"] = lat
            entry["lng"] = lng

        cache[key] = entry
        changed = True
        print(f"{index:03d}/{len(rows)} {name}: {entry['source']} {entry['lat']},{entry['lng']}")

    if changed:
        OUTPUT.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Geocodes em {OUTPUT}: {len(cache)} registros.")


if __name__ == "__main__":
    main()
