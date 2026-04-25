#!/bin/bash
# One-shot: convert host-mounted /etc/WarriorFit/config_*.yml files from
# plaintext secrets to ${VAR} placeholders that the application loader
# resolves from the runtime environment.
#
# Run on the deploy host as root:
#   sudo bash scripts/sanitize_host_configs.sh
#
# Idempotent: re-running on already-sanitized files is a no-op.

set -euo pipefail

CONFIG_DIR="/etc/WarriorFit"
TARGETS=(
  "${CONFIG_DIR}/config_prod.yml"
  "${CONFIG_DIR}/config_test.yml"
)

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: must be run as root (writes to ${CONFIG_DIR})." >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"

# Use Python for safe YAML rewriting — sed-replacing values that contain
# regex metacharacters (e.g. R@nger&1401!) is fragile.
python3 - "$timestamp" "${TARGETS[@]}" <<'PY'
import os
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "ERROR: PyYAML not installed system-wide. Install with:\n"
        "  apt install python3-yaml   # Debian/Ubuntu\n"
        "or run inside the warriorfit-app container's venv.\n"
    )
    sys.exit(1)

PLACEHOLDERS = {
    ("db", "password"): "${WF_DB_PASSWORD}",
    ("hr", "api_key"): "${WF_HR_API_KEY}",
    ("mail", "password"): "${WF_MAIL_PASSWORD}",
}

timestamp = sys.argv[1]
files = sys.argv[2:]

for path_str in files:
    path = Path(path_str)
    if not path.exists():
        print(f"skip: {path} (not found)")
        continue

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        print(f"skip: {path} (not a YAML mapping)")
        continue

    changed = False
    for (section, key), placeholder in PLACEHOLDERS.items():
        sect = data.get(section)
        if not isinstance(sect, dict) or key not in sect:
            continue
        current = sect[key]
        if isinstance(current, str) and current.startswith("${") and current.endswith("}"):
            continue  # already a placeholder
        sect[key] = placeholder
        changed = True

    if not changed:
        print(f"ok:   {path} (already sanitized)")
        continue

    backup = path.with_suffix(path.suffix + f".bak-{timestamp}")
    shutil.copy2(path, backup)
    os.chmod(backup, 0o600)

    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(data, fh, default_flow_style=False, sort_keys=False)
    os.chmod(path, 0o640)

    print(f"done: {path}  (backup: {backup})")
PY

echo
echo "Next steps:"
echo "  1. Verify backups under ${CONFIG_DIR}/*.bak-${timestamp} contain the OLD secrets."
echo "  2. Rotate those secrets at the source (DB / HR / SMTP) — see"
echo "     documentation/SECRETS_ROTATION.md."
echo "  3. Put the NEW values in /etc/WarriorFit/deploy.env (mode 0600, root)"
echo "     as WF_DB_PASSWORD / WF_HR_API_KEY / WF_MAIL_PASSWORD / WF_SECRET_KEY."
echo "  4. Re-deploy with:"
echo "       sudo -E env \$(grep -v '^#' /etc/WarriorFit/deploy.env | xargs) \\"
echo "         ./deploy-prod.sh"
echo "  5. Once confirmed working, shred the .bak-${timestamp} files:"
echo "       shred -u ${CONFIG_DIR}/*.bak-${timestamp}"
