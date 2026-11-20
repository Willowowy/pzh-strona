"""
Pobiera newsy z kanału Discord i zapisuje je do newsy.json + folderu newsy-img/.

Uruchamiany automatycznie przez GitHub Actions (.github/workflows/newsy.yml).
Ustawienia przychodzą ze zmiennych środowiskowych (sekretów GitHuba):

  DISCORD_TOKEN     – token bota
  KANAL_ID          – ID kanału z newsami
  ZATWIERDZAJACY    – (opcjonalnie) ID osób, których ✅ zatwierdza news, po przecinku.
                      Jeśli puste – wystarczy ✅ od kogokolwiek.

Wiadomość trafia na stronę, gdy:
  1. pierwsza linia zaczyna się od "# " (nagłówek Discorda) – to tytuł,
  2. pod nią jest jakiś tekst – to treść,
  3. ma najwyżej 2 obrazki,
  4. ma reakcję ✅ (od osoby z listy ZATWIERDZAJACY, jeśli lista jest ustawiona).
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://discord.com/api/v10"
ZATWIERDZ = "✅"
MAKS_OBRAZKOW = 2
ILE_WIADOMOSCI = 100  # ile ostatnich wiadomości z kanału sprawdzać (max 100)

KATALOG = Path(__file__).resolve().parent.parent  # główny folder strony
PLIK_JSON = KATALOG / "newsy.json"
FOLDER_IMG = KATALOG / "newsy-img"


# ---------------------------------------------------------------- Discord API
def zapytaj(sciezka, token):
    """GET do API Discorda, z obsługą limitu zapytań (429)."""
    req = urllib.request.Request(
        API + sciezka,
        headers={
            "Authorization": "Bot " + token,
            "User-Agent": "DiscordBot (https://github.com, 1.0) PZH-newsy",
        },
    )
    for _ in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as odp:
                return json.load(odp)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                czekaj = json.load(e).get("retry_after", 2)
                time.sleep(float(czekaj) + 0.5)
                continue
            raise
    raise RuntimeError("Discord ciągle odpowiada 429 (za dużo zapytań)")


def pobierz_plik(url, cel):
    req = urllib.request.Request(url, headers={"User-Agent": "PZH-newsy"})
    with urllib.request.urlopen(req, timeout=60) as odp:
        cel.write_bytes(odp.read())


# ---------------------------------------------------------------- filtr formatu
def wyczysc_tytul(linia):
    tytul = linia.lstrip("#").strip()
    tytul = tytul.replace("‼️", "").replace("‼", "")
    tytul = re.sub(r"\s{2,}", " ", tytul)
    return tytul.strip(" *_~")


def obrazki_z(wiadomosc):
    return [
        z for z in wiadomosc.get("attachments", [])
        if (z.get("content_type") or "").startswith("image/")
    ]


def to_jest_news(wiadomosc):
    """Zwraca (tytul, tresc) jeśli wiadomość pasuje do formatu, inaczej None."""
    tekst = (wiadomosc.get("content") or "").strip()
    if not tekst:
        return None
    linie = tekst.split("\n")
    pierwsza = linie[0].strip()
    if not pierwsza.startswith("# "):
        return None
    tytul = wyczysc_tytul(pierwsza)
    tresc = "\n".join(linie[1:]).strip()
    if not tytul or not tresc:
        return None
    if len(obrazki_z(wiadomosc)) > MAKS_OBRAZKOW:
        return None
    return tytul, tresc


def ma_ptaszek(wiadomosc):
    return any(
        r.get("emoji", {}).get("name") == ZATWIERDZ and r.get("count", 0) > 0
        for r in wiadomosc.get("reactions", [])
    )


def zatwierdzone(wiadomosc, kanal, token, zatwierdzajacy):
    if not ma_ptaszek(wiadomosc):
        return False
    if not zatwierdzajacy:
        return True
    emoji = urllib.parse.quote(ZATWIERDZ)
    osoby = zapytaj(f"/channels/{kanal}/messages/{wiadomosc['id']}/reactions/{emoji}?limit=100", token)
    return any(o["id"] in zatwierdzajacy for o in osoby)


# ---------------------------------------------------------------- główna część
def main():
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    kanal = os.environ.get("KANAL_ID", "").strip()
    zatwierdzajacy = {x.strip() for x in os.environ.get("ZATWIERDZAJACY", "").split(",") if x.strip()}
    if not token or not kanal:
        sys.exit("Brak DISCORD_TOKEN albo KANAL_ID – ustaw sekrety w GitHubie.")

    wiadomosci = zapytaj(f"/channels/{kanal}/messages?limit={ILE_WIADOMOSCI}", token)
    FOLDER_IMG.mkdir(exist_ok=True)

    newsy, potrzebne_pliki = [], set()
    for w in wiadomosci:  # Discord zwraca od najnowszych
        wynik = to_jest_news(w)
        if not wynik or not zatwierdzone(w, kanal, token, zatwierdzajacy):
            continue
        tytul, tresc = wynik

        obrazki = []
        for i, zal in enumerate(obrazki_z(w)):
            rozszerzenie = Path(zal["filename"]).suffix.lower() or ".png"
            nazwa = f"{w['id']}_{i}{rozszerzenie}"
            cel = FOLDER_IMG / nazwa
            # linki Discorda wygasają, więc ściągamy obrazek do siebie (tylko raz)
            if not cel.exists():
                pobierz_plik(zal["url"], cel)
            potrzebne_pliki.add(nazwa)
            obrazki.append(f"newsy-img/{nazwa}")

        autor = w.get("author", {})
        newsy.append({
            "id": w["id"],
            "tytul": tytul,
            "tresc": tresc,
            "autor": autor.get("global_name") or autor.get("username") or "Redakcja",
            "data": w["timestamp"],
            "edytowane": w.get("edited_timestamp"),
            "obrazki": obrazki,
        })

    # usuń obrazki newsów, których już nie ma (skasowane na Discordzie)
    for plik in FOLDER_IMG.iterdir():
        if plik.is_file() and not plik.name.startswith(".") and plik.name not in potrzebne_pliki:
            plik.unlink()

    PLIK_JSON.write_text(json.dumps(newsy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Zapisano {len(newsy)} newsów.")


if __name__ == "__main__":
    main()
