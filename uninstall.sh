#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Uruchom jako root: sudo bash uninstall.sh"
    exit 1
fi

echo "==> Zatrzymywanie serwisu..."
systemctl stop selltrack 2>/dev/null || true
systemctl disable selltrack 2>/dev/null || true
rm -f /etc/systemd/system/selltrack.service
systemctl daemon-reload

read -p "Usunac dane (baza, zdjecia, eksporty)? [t/N] " answer
if [[ "$answer" =~ ^[tT]$ ]]; then
    echo "==> Usuwanie /opt/selltrack..."
    rm -rf /opt/selltrack
    userdel -r selltrack 2>/dev/null || true
else
    echo "==> Usuwanie aplikacji (dane zachowane w /opt/selltrack/data, uploads, exports)..."
    rm -rf /opt/selltrack/venv /opt/selltrack/pages /opt/selltrack/__pycache__
    rm -f /opt/selltrack/*.py /opt/selltrack/*.txt /opt/selltrack/*.service /opt/selltrack/*.sh
fi

echo "SellTrack odinstalowany."
