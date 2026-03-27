#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/selltrack"
APP_USER="selltrack"
REPO_URL="https://github.com/macraj/selltrack.git"

# --- Root check ---
if [[ $EUID -ne 0 ]]; then
    echo "Uruchom jako root: sudo bash install.sh"
    exit 1
fi

echo "==> Instalacja zaleznosci systemowych..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git

# --- App user ---
if ! id "$APP_USER" &>/dev/null; then
    echo "==> Tworzenie uzytkownika $APP_USER..."
    useradd -r -d "$APP_DIR" -s /usr/sbin/nologin "$APP_USER"
fi

# --- Clone or pull ---
if [[ -d "$APP_DIR/.git" ]]; then
    echo "==> Aktualizacja repozytorium..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull --ff-only
else
    echo "==> Klonowanie repozytorium..."
    mkdir -p "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
    chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
fi

cd "$APP_DIR"

# --- Virtualenv ---
echo "==> Konfiguracja virtualenv..."
if [[ ! -d "$APP_DIR/venv" ]]; then
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
fi
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --quiet -r requirements.txt

# --- Directories ---
echo "==> Tworzenie katalogow danych..."
sudo -u "$APP_USER" mkdir -p "$APP_DIR/data" "$APP_DIR/uploads" "$APP_DIR/exports"

# --- Systemd service ---
echo "==> Instalacja serwisu systemd..."
cp "$APP_DIR/selltrack.service" /etc/systemd/system/selltrack.service
systemctl daemon-reload
systemctl enable selltrack

echo "==> Uruchamianie SellTrack..."
systemctl restart selltrack

echo ""
echo "======================================"
echo "  SellTrack zainstalowany!"
echo "  Status:  systemctl status selltrack"
echo "  Logi:    journalctl -u selltrack -f"
echo "  Adres:   http://$(hostname -I | awk '{print $1}'):5000"
echo "======================================"
