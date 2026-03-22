#!/bin/bash
# ==============================================================================
# Desert Cubs – Server Auto Deploy Script
# ==============================================================================
# This script runs ON YOUR SERVER via a cron job (not GitHub Actions).
# Every 15 minutes it checks GitHub for new commits. If found, it pulls
# and restarts the app — so N8N's weekly blog updates go live automatically.
#
# This is SIMPLER than GitHub Actions because:
#   • No SSH key exposed to GitHub
#   • Server pulls on its own schedule
#   • Works even if GitHub Actions isn't configured
#
# ─── HOW TO SET UP ─────────────────────────────────────────────────────────
#
# STEP 1 — Find your app folder on the server (run these commands via SSH):
#
#   pwd                          # shows your current directory
#   ls ~/                        # look for your project folder
#   ls /var/www/                 # common location for web apps
#   find / -name "app.py" -not -path "*/\.*" 2>/dev/null  # search everywhere
#   ps aux | grep gunicorn       # shows the gunicorn process + its folder
#
#   Example output from ps aux:
#   ubuntu   1234  ... gunicorn --bind 0.0.0.0:5000 app:app
#   ^ the working directory is shown with: ls -la /proc/1234/cwd
#
# STEP 2 — Edit the 3 variables below
#
# STEP 3 — Upload this script to your server:
#   scp scripts/server_auto_deploy.sh ubuntu@YOUR_SERVER:~/scripts/
#   # OR just copy-paste the content via SSH
#
# STEP 4 — Set permissions and test:
#   chmod +x ~/scripts/server_auto_deploy.sh
#   ~/scripts/server_auto_deploy.sh          # run once to test
#
# STEP 5 — Add to crontab (runs every 15 minutes):
#   crontab -e
#   # Add this line:
#   */15 * * * * /home/ubuntu/scripts/server_auto_deploy.sh >> /home/ubuntu/logs/deploy.log 2>&1
#   # Replace /home/ubuntu with your actual home directory
#
# STEP 6 — Create the logs folder:
#   mkdir -p ~/logs
#
# That's it. From now on the server checks GitHub every 15 minutes.
# When N8N commits on Monday, the site updates within 15 minutes. ✅
# ==============================================================================

set -e

# ── EDIT THESE THREE LINES ───────────────────────────────────────────────────
APP_DIR="/home/ubuntu/desert-website"    # ← path where your app lives on server
SERVICE_NAME="gunicorn-desertcubs"       # ← your systemd service name
PYTHON_BIN="python3"                     # ← or path to venv: /home/ubuntu/venv/bin/python
# ─────────────────────────────────────────────────────────────────────────────

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Make sure the app folder exists
if [ ! -d "$APP_DIR" ]; then
  echo "[$TIMESTAMP] ERROR: APP_DIR '$APP_DIR' does not exist. Please update this script."
  exit 1
fi

cd "$APP_DIR"

# Fetch latest commit refs from GitHub (read-only, no changes yet)
git fetch origin main --quiet 2>&1

LOCAL_SHA=$(git rev-parse HEAD)
REMOTE_SHA=$(git rev-parse origin/main)

if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
  echo "[$TIMESTAMP] No changes. Already at $(git rev-parse --short HEAD)."
  exit 0
fi

# ── New commits found — deploy ───────────────────────────────────────────────
echo "[$TIMESTAMP] New commits found! Deploying..."
echo "[$TIMESTAMP]   Was: $(git rev-parse --short HEAD)"

git pull origin main 2>&1

echo "[$TIMESTAMP]   Now: $(git rev-parse --short HEAD)"

# Install any new Python dependencies
$PYTHON_BIN -m pip install -r requirements.txt --quiet 2>&1

# Restart the gunicorn service
# If you get "permission denied", add this to /etc/sudoers (run: sudo visudo):
#   ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart gunicorn-desertcubs
sudo systemctl restart "$SERVICE_NAME"

echo "[$TIMESTAMP] ✅ Deploy complete!"
