# Secrets rotation runbook

All values previously hardcoded in `warriorfit/config/config_*.yml` and
`auto-deploy.sh` must be considered **compromised** — they are present in git
history and visible to anyone with read access to the repository.

## Secrets to rotate

| Secret | Old (leaked) value lived in | New source of truth |
|---|---|---|
| GitHub PAT (`GH_TOKEN`) | `auto-deploy.sh` (line 5) | systemd `EnvironmentFile=/etc/WarriorFit/deploy.env` (mode 0600) |
| Postgres password | `config_*.yml` `db.password` | env `WF_DB_PASSWORD` |
| HR API key | `config_*.yml` `hr.api_key` | env `WF_HR_API_KEY` |
| SMTP password | `config_*.yml` `mail.password` | env `WF_MAIL_PASSWORD` |
| App secret | `.env` `WF_SECRET_KEY` | env `WF_SECRET_KEY` (already runtime-only) |

## Rotation steps

1. **GitHub PAT** — open https://github.com/settings/tokens, revoke the
   `github_pat_11AAIGYNY0...` token, generate a new fine-scoped PAT (only
   `repo:read` for the deploy host), write it to
   `/etc/WarriorFit/deploy.env` as `GH_TOKEN=...`, `chmod 600`, `chown root`.
2. **Postgres** — `ALTER USER produser WITH PASSWORD '<new>';` on the prod
   DB; same for dev/test users. Update the password manager. Set
   `WF_DB_PASSWORD` in the deploy environment.
3. **HR API key** — coordinate with the HR-system owner to rotate
   `warrior_secret`; set `WF_HR_API_KEY` in the deploy environment.
4. **SMTP password** — rotate the mailbox password upstream; set
   `WF_MAIL_PASSWORD` in the deploy environment.
5. **App secret** — already runtime-only, but generate a fresh value:
   `openssl rand -hex 32` and update `/etc/WarriorFit/deploy.env`.

## History purge (optional but recommended)

The leaked secrets remain in git history even after this commit. To remove
them:

```bash
pip install git-filter-repo
git filter-repo --replace-text <(cat <<'EOF'
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==>***REVOKED***
Airborne%Warrior!1978==>***ROTATED***
ranger14==>***ROTATED***
warrior_secret==>***ROTATED***
R@nger&1401!==>***ROTATED***
EOF
)
git push --force-with-lease origin --all
git push --force-with-lease origin --tags
```

Coordinate with all collaborators before force-pushing — they will need to
re-clone. Even after rewriting history, treat the secrets as leaked and
rotate them anyway.

## Verifying the new flow

```bash
# Production
WF_SECRET_KEY=$(openssl rand -hex 32) \
WF_DB_PASSWORD=<new> \
WF_HR_API_KEY=<new> \
WF_MAIL_PASSWORD=<new> \
./deploy-prod.sh

# Smoke-test config loading without starting Shiny:
docker exec warriorfit-app python -c \
  "from warriorfit.config.appliccation_config import ApplicationConfig; \
   ApplicationConfig().load_config(); print('config OK')"
```

If a required `${VAR}` is missing the loader raises `KeyError` immediately,
so a misconfigured deploy fails fast instead of silently using empty
credentials.
