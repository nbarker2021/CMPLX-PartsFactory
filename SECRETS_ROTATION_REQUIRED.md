# Secrets Rotation Required

## Action Taken
Two `.env` files containing live secrets were deleted from disk on 2026-05-17:
- `CMPLX-PartsFactory/.env`
- `Unification Prototypes/configs/env_template/.env`

## Why?
The `.env` file contained hardcoded production credentials and API tokens that
must be considered compromised because they existed on disk in an unencrypted
working directory.

## What Must Be Rotated
Every secret below **must be revoked and regenerated** before services are restarted.

| Service | Variable | Rotation URL / Command |
|---------|----------|------------------------|
| Ngrok | `NGROK_AUTHTOKEN` | https://dashboard.ngrok.com/get-started/your-authtoken |
| OpenCode | `OPENCODE_SERVER_PASSWORD` | Generate a new strong password locally |
| OpenAI | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| OpenCode Go | `OPENCODE_GO_API_KEY` | Generate a new key in your OpenCode admin panel |
| Anthropic | `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys |
| GitHub | `GITHUB_TOKEN` | https://github.com/settings/tokens |
| Discord | `DISCORD_BOT_TOKEN` | https://discord.com/developers/applications |
| PostgreSQL | `POSTGRES_PASSWORD` | Rotate in your PostgreSQL instance |
| PostgreSQL Cache | `CACHE_POSTGRES_PASSWORD` | Rotate in your cache PostgreSQL instance |
| RabbitMQ | `RABBITMQ_PASS` | Rotate in your RabbitMQ management console |
| MinIO | `MINIO_ROOT_PASSWORD` | Rotate via MinIO admin API or console |

## How to Restore
1. Copy `.env.template` to `.env`.
2. Replace every `CHANGE_ME` placeholder with a newly-generated secret.
3. Set `OPENCODE_SERVER_PASSWORD` to a cryptographically-random string.
4. Do **not** commit `.env` to git.

## Verification
After rotation, run:
```bash
grep -E "(password|token|secret|key)" .env | grep -v "^#"
```
Confirm none of the values match the old ones.
