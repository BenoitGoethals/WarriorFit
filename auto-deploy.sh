#!/bin/bash

cd /home/benoit/projects/WarriorFit

BEFORE=$(git rev-parse HEAD)

gh repo sync

AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" != "$AFTER" ]; then
  echo "[$(date)] Update detected! Running deploy..." >> /var/log/deploy.log
  sudo sh deploy.sh >> /var/log/deploy.log 2>&1
else
  echo "[$(date)] No update." >> /var/log/deploy.log
fi