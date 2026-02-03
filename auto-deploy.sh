#!/bin/bash

cd /home/benoit/projects/WarriorFit

# Store current commit
BEFORE=$(git rev-parse HEAD)

# Sync repo
gh repo sync

# Get latest commit after sync
AFTER=$(git rev-parse HEAD)

# If repo was updated, run deploy
if [ "$BEFORE" != "$AFTER" ]; then
  echo "Update detected! Running deploy..."
  sudo sh deploy.sh
else
  echo "No update."
fi