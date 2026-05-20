# CMPLX Discord Bridge

## Overview

This service bridges Discord messages to the CMPLX research API and manny-runtime. It allows you to interact with your CMPLX agent stack directly from Discord.

## Architecture

```
Discord Desktop App
        |
        v
Discord Bot Gateway (WebSocket)
        |
        v
+----------------------------------+
|  cmplx-discord-bridge (Docker)   |
|  - Discord client (discord.py)   |
|  - Health HTTP server (:8080)    |
+----------------------------------+
        | HTTP
        v
+----------------------------------+
|  research-api:3000 (existing)    |
|  - /api/chat (dual-model)        |
|  - /health                       |
+----------------------------------+
```

## Setup

### 1. Create Discord Bot

1. Go to https://discord.com/developers/applications
2. Click "New Application" → name it "CMPLX Bridge"
3. Go to "Bot" tab → click "Add Bot"
4. Under "Privileged Gateway Intents", enable **MESSAGE CONTENT INTENT**
5. Copy the **Token** (you'll need this)
6. Go to "OAuth2" → "URL Generator"
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Message History`
   - Copy the generated URL and open it to invite the bot to your server

### 2. Configure Environment

```bash
cd /mnt/d/PartsFactory/CMPLX-PartsFactory
cp .env.template .env
```

Edit `.env`:
```
DISCORD_BOT_TOKEN=YOUR_ACTUAL_TOKEN_HERE
DISCORD_CHANNELS=1234567890,0987654321  # optional: limit to specific channels
DEFAULT_API=research
```

To get a channel ID: Right-click channel → Copy Channel ID (enable Developer Mode in Discord settings)

### 3. Start the Bridge

```bash
# Option A: Standalone (connects to existing Docker stack)
docker compose -f docker-compose.cmplx-discord.yml up -d

# Option B: View logs
docker compose -f docker-compose.cmplx-discord.yml logs -f

# Option C: Stop
docker compose -f docker-compose.cmplx-discord.yml down
```

## Usage

### Automatic Responses

In configured channels, the bot automatically responds to any message:

```
You: How do I compose tools in CMPLX?
CMPLX-Bot: [responds via research-api dual-model deliberation]
```

### Commands

Prefix all commands with `!cmplx `:

| Command | Description |
|---------|-------------|
| `!cmplx status` | Check CMPLX system health |
| `!cmplx reset` | Reset session for this channel |
| `!cmplx memory` | Trigger memory review |

### Session Management

Each Discord channel gets its own session ID. The bot maintains conversation context per channel. Use `!cmplx reset` to start fresh.

## Troubleshooting

### Bot shows offline
- Check token is correct in `.env`
- Check logs: `docker compose -f docker-compose.cmplx-discord.yml logs`
- Verify bot has `MESSAGE CONTENT INTENT` enabled in Discord Developer Portal

### No responses
- Check `research-api` is running: `docker ps | grep research-api`
- Test API manually: `curl http://localhost:3000/health`
- Check Discord channel ID is in `DISCORD_CHANNELS` if set

### Health check fails
The bot exposes HTTP `:8080/health`. It returns 200 when connected to Discord, 503 when not ready.

## Files

- `services/discord-bridge/bot.py` — Discord bot implementation
- `services/discord-bridge/Dockerfile` — Container build
- `services/discord-bridge/requirements.txt` — Python dependencies
- `docker-compose.cmplx-discord.yml` — Compose orchestration
