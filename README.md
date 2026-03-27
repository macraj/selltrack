# SellTrack

Aplikacja do zarzadzania inwentarzem przedmiotow na sprzedaz z pelnym cyklem zycia ogloszen.

## Funkcjonalnosci

- CRUD przedmiotow z kategoriami i galeria zdjec
- Cykl zycia statusu: W magazynie → Aktywny → Sprzedany / Zdjety / Do likwidacji (automatyczne wygasanie)
- Wyszukiwanie, filtrowanie, sortowanie, paginacja
- Przetwarzanie zdjec (EXIF, resize, konwersja formatow)
- Eksport zdjec do ZIP
- Zarzadzanie kategoriami

## Stack

- **NiceGUI** (FastAPI + Vue/Quasar)
- **SQLAlchemy** (SQLite)
- **Pillow** (przetwarzanie obrazow)

## Uruchomienie lokalne

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Aplikacja startuje na `http://localhost:5000`

## Instalacja na serwerze (Debian)

```bash
git clone https://github.com/macraj/selltrack.git
cd selltrack
sudo bash install.sh
```

Skrypt instaluje zaleznosci, tworzy uzytkownika systemowego, konfiguruje serwis systemd i uruchamia aplikacje.

### Zarzadzanie serwisem

```bash
systemctl status selltrack
systemctl restart selltrack
journalctl -u selltrack -f
```

### Deinstalacja

```bash
sudo bash uninstall.sh
```

## Konfiguracja

Zmienne srodowiskowe (ustawiane w `selltrack.service` lub powloce):

| Zmienna | Domyslnie | Opis |
|---|---|---|
| `SELLTRACK_HOST` | `0.0.0.0` | Adres nasluchu |
| `SELLTRACK_PORT` | `5000` | Port |
| `SELLTRACK_DEBUG` | `false` | `1` / `true` wlacza hot-reload |
