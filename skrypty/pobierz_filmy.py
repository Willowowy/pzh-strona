"""
Pobiera najnowsze filmy z kanału YouTube (z publicznego kanału RSS, bez klucza API)
i zapisuje je do filmy.json. Shorty są pomijane.

Jeśli YouTube akurat nie odpowiada, skrypt NIE nadpisuje starego filmy.json –
strona dalej pokazuje ostatnie znane filmy.
"""

import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

KANAL_ID = "UCUktYQ_61Mw5TWSnmMdpUmA"  # @polskizwiazekhydraulikow
ILE_FILMOW = 3                        # 1 duży + 2 mniejsze na stronie

RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={KANAL_ID}"
PLIK_JSON = Path(__file__).resolve().parent.parent / "filmy.json"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def main():
    try:
        req = urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0 PZH-filmy"})
        with urllib.request.urlopen(req, timeout=30) as odp:
            drzewo = ET.fromstring(odp.read())
    except Exception as e:
        print(f"Nie udało się pobrać RSS z YouTube ({e}) – zostawiam stary filmy.json.")
        return

    filmy = []
    for wpis in drzewo.findall("atom:entry", NS):
        vid = wpis.findtext("yt:videoId", namespaces=NS)
        link = wpis.find("atom:link[@rel='alternate']", NS)
        href = link.get("href", "") if link is not None else ""
        if not vid or "/shorts/" in href:
            continue
        filmy.append({
            "id": vid,
            "tytul": wpis.findtext("atom:title", default="", namespaces=NS),
            "data": wpis.findtext("atom:published", default="", namespaces=NS),
        })
        if len(filmy) >= ILE_FILMOW:
            break

    if not filmy:
        print("RSS nie zawierał filmów – zostawiam stary filmy.json.")
        return

    PLIK_JSON.write_text(json.dumps(filmy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Zapisano {len(filmy)} filmów. Najnowszy: {filmy[0]['tytul']}")


if __name__ == "__main__":
    sys.exit(main())
