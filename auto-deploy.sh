#!/bin/bash
set -e  # Exit immediately if a command fails

# Store token in a separate file, not hardcoded in the script
export GH_TOKEN="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"

cd /home/benoit/projects/WarriorFit || exit 1

BEFORE=$(git rev-parse HEAD)

gh repo sync 2>&1 || { echo "[$(date)] gh repo sync failed." >> /home/benoit/log/deploy.log; exit 1; }

AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" != "$AFTER" ]; then
  echo "[$(date)] Update detected! Running deploy..." >> /var/log/deploy.log
  sudo sh deploy.sh >> /home/benoit/log/deploy.log 2>&1
else
  echo "[$(date)] No update." >> /home/benoit/log/deploy.log
fi