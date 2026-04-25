#!/bin/bash
set -e  # Exit immediately if a command fails

# GH_TOKEN must be supplied by the calling environment (e.g. a systemd
# EnvironmentFile=/etc/WarriorFit/deploy.env, mode 0600, root-owned).
# It is intentionally NOT stored in this script so it is never committed.
if [ -z "${GH_TOKEN}" ]; then
  echo "ERROR: GH_TOKEN environment variable is not set." >&2
  exit 1
fi
export GH_TOKEN

LOG_FILE="/home/benoit/log/deploy.log"
cd /home/benoit/projects/WarriorFit || exit 1

BEFORE=$(git rev-parse HEAD)
gh repo sync 2>&1 || {
  echo "[$(date)] gh repo sync failed." >> "$LOG_FILE"
  exit 1
}
AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" != "$AFTER" ]; then
  echo "[$(date)] Update detected! Running deploy..." >> "$LOG_FILE"
  sudo sh deploy.sh >> "$LOG_FILE" 2>&1
else
  echo "[$(date)] No update." >> "$LOG_FILE"
fi
