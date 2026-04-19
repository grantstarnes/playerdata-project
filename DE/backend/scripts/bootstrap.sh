#!/usr/bin/env bash
# PlayerData Victus server bootstrap — run once with: sudo bash /tmp/bootstrap.sh
# Installs: uv, Ollama (bound to 0.0.0.0), Tailscale, UFW rules, lid-close fix,
# unattended-upgrades, and enables passwordless sudo for the deploy user.
#
# Revert NOPASSWD after setup with:
#   sudo rm /etc/sudoers.d/99-doorknob-nopasswd

set -euo pipefail

USER_NAME="doorknob"
DEPLOY_DIR="/home/${USER_NAME}/apps/playerdata"

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo bash $0" >&2
  exit 1
fi

say() { printf '\n\033[1;32m=== %s ===\033[0m\n' "$*"; }

say "1/9  Passwordless sudo for ${USER_NAME}"
echo "${USER_NAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/99-${USER_NAME}-nopasswd
chmod 440 /etc/sudoers.d/99-${USER_NAME}-nopasswd

say "2/9  apt update + baseline tools"
apt update -y
DEBIAN_FRONTEND=noninteractive apt install -y \
  curl wget git build-essential htop net-tools ufw \
  python3-venv python3-pip python3-dev jq ca-certificates

say "3/9  Install uv (fast Python package manager)"
if ! sudo -u ${USER_NAME} bash -lc 'command -v uv' >/dev/null 2>&1; then
  sudo -u ${USER_NAME} bash -lc 'curl -LsSf https://astral.sh/uv/install.sh | sh'
fi

say "4/9  Install Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

say "5/9  Bind Ollama to 0.0.0.0:11434 + keep models loaded 5 min"
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_KEEP_ALIVE=5m"
EOF
systemctl daemon-reload
systemctl restart ollama
sleep 3
systemctl is-active --quiet ollama || { echo "ollama failed to start"; exit 1; }

say "6/9  Install Tailscale (auth happens interactively after this script)"
if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi

say "7/9  UFW firewall rules"
ufw allow OpenSSH
ufw allow 8000/tcp comment 'FastAPI'
ufw allow from 192.168.0.0/16 to any port 11434 proto tcp comment 'Ollama LAN only'
ufw --force enable
ufw status verbose

say "8/9  Ignore lid-close (laptop stays awake with lid shut)"
sed -i 's/^#\?HandleLidSwitch=.*/HandleLidSwitch=ignore/' /etc/systemd/logind.conf
sed -i 's/^#\?HandleLidSwitchExternalPower=.*/HandleLidSwitchExternalPower=ignore/' /etc/systemd/logind.conf
grep -q '^HandleLidSwitch=ignore' /etc/systemd/logind.conf \
  || echo 'HandleLidSwitch=ignore' >> /etc/systemd/logind.conf
grep -q '^HandleLidSwitchExternalPower=ignore' /etc/systemd/logind.conf \
  || echo 'HandleLidSwitchExternalPower=ignore' >> /etc/systemd/logind.conf
systemctl restart systemd-logind

say "9/9  Deploy dir + unattended security upgrades"
sudo -u ${USER_NAME} mkdir -p "${DEPLOY_DIR}"
DEBIAN_FRONTEND=noninteractive apt install -y unattended-upgrades
dpkg-reconfigure -f noninteractive unattended-upgrades

printf '\n\033[1;36m=========================================================\033[0m\n'
printf '\033[1;36m  Bootstrap complete.\033[0m\n'
printf '\033[1;36m  Next (one interactive step):\033[0m\n'
printf '\033[1;36m    sudo tailscale up --ssh\033[0m\n'
printf '\033[1;36m  A browser URL will print — log in to your Tailscale account.\033[0m\n'
printf '\033[1;36m=========================================================\033[0m\n'
