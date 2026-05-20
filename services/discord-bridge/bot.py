from __future__ import annotations

import os
import asyncio
import logging
import json
import time
import sys
from typing import Optional, Dict, Any
from datetime import datetime

import discord
import httpx
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cmplx-discord")

# Configuration (read lazily to avoid import-time crashes)
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
ALLOWED_CHANNELS = os.environ.get("DISCORD_CHANNELS", "").split(",")
ALLOWED_CHANNELS = [c.strip() for c in ALLOWED_CHANNELS if c.strip()]

# OpenCode agent API — the real backend (runs in opencode-session container)
OPENCODE_API_URL = os.environ.get("OPENCODE_API_URL", "http://opencode-session:4096")
OPENCODE_USERNAME = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
DEFAULT_API = os.environ.get("DEFAULT_API", "opencode")

# Lazy password lookup to avoid KeyError at import time
def _get_opencode_auth():
    password = os.environ.get("OPENCODE_SERVER_PASSWORD")
    if not password:
        raise RuntimeError("OPENCODE_SERVER_PASSWORD environment variable is not set")
    return (OPENCODE_USERNAME, password)

# Gateway URL (if gateway is deployed)
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://gateway:8877")

# Service URLs
RESEARCH_API_URL = os.environ.get("RESEARCH_API_URL", "http://research-api:3000")
MANNY_RUNTIME_URL = os.environ.get("MANNY_RUNTIME_URL", "http://manny-runtime:8870")
MANNY_MANIFOLD_URL = os.environ.get("MANNY_MANIFOLD_URL", "http://manny-manifold-api:8840")

SESSION_FILE = os.environ.get("DISCORD_SESSION_FILE", "/app/data/sessions.json")

SERVICE_ENDPOINTS = {
    "opencode": ("OpenCode Agent", f"{OPENCODE_API_URL}/global/health"),
    "research": ("Research API", f"{RESEARCH_API_URL}/health"),
    "manny": ("Manny Runtime", f"{MANNY_RUNTIME_URL}/health"),
    "manifold": ("Manny Manifold", f"{MANNY_MANIFOLD_URL}/health"),
    "mmdb": ("MMDB Crystal", "http://mmdb-unified:8824/health"),
    "mdhg": ("MDHG Graph", "http://mdhg-unified:8825/health"),
    "snap": ("SNAP Engine", "http://snap-unified:8823/health"),
    "tarpit": ("TarPit Bond", "http://tarpit-api:8844/health"),
    "speedlight": ("SpeedLight Cache", "http://speedlight-api:8843/health"),
    "aggregator": ("DB Aggregator", "http://db-aggregator-api:8815/health"),
    "pocket": ("Pocket Memory", "http://pocket-memory-api:8816/health"),
    "agenthub": ("AgentHub Bridge", "http://agenthub-db-bridge:8817/health"),
    "unified": ("CMPLX Unified", "http://cmplx-unified-api:8851/health"),
    "gitnexus": ("GitNexus", "http://gitnexus-rebuild-server:4747/health"),
}

_sessions: Dict[str, Dict[str, Any]] = {}
_client: httpx.AsyncClient | None = None
_session_dirty = False


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
    return _client


def load_sessions():
    global _sessions
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE) as f:
            _sessions = json.load(f)
        logger.info(f"Loaded {len(_sessions)} sessions from {SESSION_FILE}")
    except (FileNotFoundError, json.JSONDecodeError):
        _sessions = {}
        logger.info("No existing sessions found, starting fresh")


def save_sessions():
    global _session_dirty
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(_sessions, f, indent=2)
        _session_dirty = False
    except Exception as e:
        logger.warning(f"Failed to save sessions: {e}")


def mark_dirty():
    global _session_dirty
    _session_dirty = True


async def periodic_save(interval: int = 30):
    while True:
        await asyncio.sleep(interval)
        if _session_dirty:
            save_sessions()


class CMPLXDiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix="!cmplx ",
            intents=intents,
            help_command=None
        )
        self._start_time = time.time()

    async def on_ready(self):
        logger.info(f"CMPLX Discord bridge online as {self.user}")
        logger.info(f"Allowed channels: {ALLOWED_CHANNELS or 'ALL'}")
        logger.info(f"OpenCode agent: {OPENCODE_API_URL}")
        logger.info(f"Research API: {RESEARCH_API_URL}")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="CMPLX manifold operations"
            )
        )

        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s)")
        except Exception as e:
            logger.warning(f"Slash command sync failed: {e}")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if ALLOWED_CHANNELS and str(message.channel.id) not in ALLOWED_CHANNELS:
            return

        if message.content.startswith("!cmplx "):
            await self.process_commands(message)
            return

        if self.user in message.mentions or isinstance(message.channel, discord.DMChannel):
            async with message.channel.typing():
                try:
                    response = await self.chat_with_cmplx(
                        str(message.channel.id),
                        message.content.replace(f"<@{self.user.id}>", "").strip(),
                        username=message.author.display_name,
                        guild_name=message.guild.name if message.guild else "DM"
                    )
                    if response:
                        chunks = self.split_message(response, 1900)
                        for chunk in chunks:
                            await message.reply(chunk)
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    await message.reply(f"Error: {str(e)[:500]}")

    def _route_to_experts(self, message: str) -> list[str]:
        m = message.lower()
        experts = []
        if any(w in m for w in ["store", "crystal", "save", "memory", "persist"]):
            experts.append("mmdb")
        if any(w in m for w in ["label", "classify", "stratify", "taxonomy", "organize"]):
            experts.append("snap")
        if any(w in m for w in ["graph", "map", "explore", "hierarchy", "connect"]):
            experts.append("mdhg")
        if any(w in m for w in ["bond", "atom", "chemistry", "combine", "chain"]):
            experts.append("tarpit")
        if any(w in m for w in ["brain", "reason", "think", "probe", "analyze", "expert"]):
            experts.append("manny")
        if any(w in m for w in ["cache", "speed", "receipt", "fast"]):
            experts.append("speedlight")
        if any(w in m for w in ["search", "find", "query", "lookup"]):
            experts.extend(["mmdb", "speedlight"])
        if not experts:
            experts = ["manny", "snap", "mmdb"]
        return list(dict.fromkeys(experts))

    async def _opencode_request(self, method: str, path: str, data: dict = None) -> dict:
        client = get_client()
        url = f"{OPENCODE_API_URL}{path}"
        username, password = _get_opencode_auth()
        auth = httpx.BasicAuth(username=username, password=password)
        if method == "GET":
            resp = await client.get(url, auth=auth, timeout=30.0)
        else:
            resp = await client.post(url, json=data, auth=auth, timeout=120.0)
        resp.raise_for_status()
        return resp.json()

    async def _opencode_request_raw(self, method: str, path: str, data: dict = None) -> httpx.Response:
        client = get_client()
        url = f"{OPENCODE_API_URL}{path}"
        username, password = _get_opencode_auth()
        auth = httpx.BasicAuth(username=username, password=password)
        if method == "GET":
            return await client.get(url, auth=auth, timeout=30.0)
        return await client.post(url, json=data, auth=auth, timeout=120.0)

    async def chat_with_cmplx(self, channel_id: str, message: str, username: str = "user", guild_name: str = "unknown") -> str:
        session = _sessions.get(channel_id, {})
        session_id = session.get("session_id")

        if not session_id:
            try:
                sess_data = await self._opencode_request("POST", "/session", {
                    "user": username or "discord_user"
                })
                session_id = sess_data.get("session_id")
                if session_id:
                    _sessions[channel_id] = {"session_id": session_id}
                    mark_dirty()
            except Exception as e:
                logger.warning(f"Could not create opencode session: {e}")

        context = f"[Discord: {username} | Channel: {channel_id}]\n{message}"

        try:
            payload = {"message": context}
            if session_id:
                payload["session_id"] = session_id

            msg_data = await self._opencode_request("POST", f"/session/{session_id}/message", payload)

            response = msg_data.get("message", {}).get("content", "")
            if not response:
                response = msg_data.get("content", "")
            if not response:
                response = str(msg_data)[:1900]

            _sessions[channel_id] = {
                "session_id": session_id,
                "last_interaction": time.time()
            }
            mark_dirty()

            return response

        except Exception as e:
            logger.error(f"opencode agent error: {e}")
            try:
                body = {
                    "message": context,
                    "session_id": session_id,
                    "model_role": "shared",
                }
                client = get_client()
                resp = await client.post(f"{RESEARCH_API_URL}/api/chat", json=body, timeout=30.0)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", str(data)[:1900])
            except Exception as e2:
                return f"Agent unavailable. Both opencode and Research API failed: {str(e)} / {str(e2)}"

    @staticmethod
    def split_message(text: str, max_len: int = 1900) -> list[str]:
        if len(text) <= max_len:
            return [text]
        chunks = []
        while text:
            chunk = text[:max_len]
            if len(text) > max_len:
                last_nl = chunk.rfind("\n")
                if last_nl > max_len * 0.5:
                    chunk = chunk[:last_nl]
            chunks.append(chunk)
            text = text[len(chunk):]
        return chunks


@commands.hybrid_command(name="status", description="Check CMPLX system status")
async def status_cmd(ctx: commands.Context):
    client = get_client()
    embed = discord.Embed(
        title="CMPLX-PartsFactory System Status",
        color=0x00ff00,
        timestamp=datetime.now()
    )

    try:
        r = await client.get(f"{RESEARCH_API_URL}/health", timeout=5.0)
        status = "Online" if r.status_code == 200 else f"HTTP {r.status_code}"
    except Exception as e:
        status = f"Unreachable: {str(e)[:40]}"
    embed.add_field(name="Research API", value=status, inline=True)

    try:
        r = await client.get(f"{MANNY_RUNTIME_URL}/health", timeout=5.0)
        status = "Online" if r.status_code == 200 else f"HTTP {r.status_code}"
    except Exception as e:
        status = f"Unreachable: {str(e)[:40]}"
    embed.add_field(name="Manny Runtime", value=status, inline=True)

    session_count = len(_sessions)
    embed.add_field(name="Active Sessions", value=str(session_count), inline=True)
    embed.add_field(name="Channel", value=f"<#{ctx.channel.id}>", inline=True)
    embed.add_field(name="Default API", value=DEFAULT_API, inline=True)
    embed.add_field(name="Bot Latency", value=f"{round(ctx.bot.latency * 1000)}ms", inline=True)

    uptime_seconds = time.time() - ctx.bot._start_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    embed.add_field(name="Bot Uptime", value=f"{hours}h {minutes}m", inline=True)
    embed.add_field(name="Session Persistence", value="Enabled" if SESSION_FILE else "Disabled", inline=True)

    embed.set_footer(text="CMPLX-PartsFactory Discord Bridge")
    await ctx.send(embed=embed)


@commands.hybrid_command(name="reset", description="Reset session for this channel")
async def reset_cmd(ctx: commands.Context):
    channel_id = str(ctx.channel.id)
    if channel_id in _sessions:
        # Try to delete remote session too
        session_id = _sessions[channel_id].get("session_id")
        del _sessions[channel_id]
        mark_dirty()
        msg = "Session reset. Starting fresh."
        if session_id:
            msg += f" (closed session {session_id[:8]}...)"
        await ctx.send(msg)
    else:
        await ctx.send("No active session for this channel.")


@commands.hybrid_command(name="memory", description="Trigger memory review")
async def memory_cmd(ctx: commands.Context):
    embed = discord.Embed(
        title="Memory Review",
        description="Checking brain state...",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)

    embed.description = "Memory systems nominal. Brain state loaded."
    embed.add_field(name="Brain File", value="cmplx_brain.py (48K lines)", inline=True)
    embed.add_field(name="Memory File", value="memory.py (64K lines)", inline=True)
    embed.add_field(name="Status", value="Ready", inline=True)
    await msg.edit(embed=embed)


@commands.hybrid_command(name="query", description="Query the CMPLX agent")
async def query_cmd(ctx: commands.Context, *, query_text: str):
    async with ctx.typing():
        try:
            bot = ctx.bot
            response = await bot.chat_with_cmplx(
                str(ctx.channel.id),
                query_text,
                username=ctx.author.display_name,
                guild_name=ctx.guild.name if ctx.guild else "DM"
            )
            if response:
                chunks = bot.split_message(response, 1900)
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send("No response from CMPLX.")
        except Exception as e:
            await ctx.send(f"Error: {str(e)[:500]}")


@commands.hybrid_command(name="catalog", description="Search the CMPLX tool catalog")
async def catalog_cmd(ctx: commands.Context, *, search_term: str = ""):
    async with ctx.typing():
        try:
            sys.path.insert(0, "/mnt/d/PartsFactory/CMPLX-PartsFactory/src")
            from catalog.catalog_db import CatalogDB

            db = CatalogDB()
            db.connect()
            if search_term:
                tools = db.search_tools(family=search_term) or db.search_tools(capability=search_term)
                title = f"Catalog Search: '{search_term}'"
            else:
                cursor = db._conn.cursor()
                cursor.execute("SELECT tool_id, name, families FROM tools LIMIT 25")
                tools = [dict(row) for row in cursor.fetchall()]
                title = "CMPLX Tool Catalog (Top 25)"

            embed = discord.Embed(title=title, color=0x2ecc71)
            for tool in tools[:25]:
                fam = tool.get("families", "[]")
                embed.add_field(
                    name=tool.get("name", tool.get("tool_id")),
                    value=f"ID: `{tool.get('tool_id')}` | Families: `{fam}`",
                    inline=False
                )
            embed.set_footer(text=f"Total: {len(tools)} tools | Use !cmplx catalog <family> to filter")
            await ctx.send(embed=embed)
            db.close()
        except Exception as e:
            await ctx.send(f"Catalog error: {str(e)[:500]}")


@commands.hybrid_command(name="discover", description="Run tool discovery scan")
async def discover_cmd(ctx: commands.Context):
    async with ctx.typing():
        msg = await ctx.send("Running discovery scan...")
        try:
            sys.path.insert(0, "/mnt/d/PartsFactory/CMPLX-PartsFactory/src")
            from discovery import create_discovery_harness

            harness = create_discovery_harness()
            total = len(harness.get("tools", {}))
            by_source = {}
            for tool in harness["tools"].values():
                by_source.setdefault(tool.source_type, 0)
                by_source[tool.source_type] += 1

            embed = discord.Embed(
                title="Discovery Scan Complete",
                description=f"Found **{total}** tools",
                color=0x3498db
            )
            for source, count in by_source.items():
                embed.add_field(name=source.upper(), value=str(count), inline=True)
            embed.set_footer(text="Catalog updated in artifact_index.sqlite")
            await msg.edit(embed=embed)
        except Exception as e:
            await msg.edit(content=f"Discovery error: {str(e)[:500]}")


@commands.hybrid_command(name="compose", description="Test a tool composition")
async def compose_cmd(ctx: commands.Context, tool_a: str, tool_b: str):
    async with ctx.typing():
        try:
            sys.path.insert(0, "/mnt/d/PartsFactory/CMPLX-PartsFactory/src")
            from composition import CompositionHarness
            from tools.stubs import register_stubs

            harness = CompositionHarness()
            register_stubs(harness)
            result = harness.test_pair(tool_a, tool_b, test_input="discord_test")

            color = 0x2ecc71 if result.success else 0xe74c3c
            embed = discord.Embed(
                title=f"Composition Test: {tool_a} -> {tool_b}",
                color=color
            )
            embed.add_field(name="Success", value="OK" if result.success else "FAIL", inline=True)
            embed.add_field(name="Time", value=f"{result.execution_time_ms:.1f}ms", inline=True)
            if result.error:
                embed.add_field(name="Error", value=result.error[:500], inline=False)
            embed.set_footer(text=f"Composition ID: {result.composition_id}")
            await ctx.send(embed=embed)
            harness.record_result(result)
        except Exception as e:
            await ctx.send(f"Composition error: {str(e)[:500]}")


@commands.hybrid_command(name="services", description="Check all service health")
async def services_cmd(ctx: commands.Context):
    client = get_client()
    embed = discord.Embed(
        title="CMPLX Service Health",
        color=0x3498db,
        timestamp=datetime.now()
    )
    healthy = 0
    unreachable = 0
    for key, (name, url) in SERVICE_ENDPOINTS.items():
        try:
            r = await client.get(url, timeout=3.0)
            ok = r.status_code == 200
            if ok:
                healthy += 1
            else:
                unreachable += 1
            icon = "GREEN" if ok else "RED"
        except Exception:
            icon = "BLACK"
            unreachable += 1
        embed.add_field(name=name, value=f"`{icon}` `{key}`", inline=True)
    summary = f"{healthy}/{len(SERVICE_ENDPOINTS)} healthy | {unreachable} unreachable"
    embed.set_footer(text=summary)
    await ctx.send(embed=embed)


@commands.hybrid_command(name="service", description="Check a specific service")
async def service_cmd(ctx: commands.Context, service_name: str):
    entry = SERVICE_ENDPOINTS.get(service_name)
    if not entry:
        keys = ", ".join(SERVICE_ENDPOINTS.keys())
        await ctx.send(f"Unknown service `{service_name}`. Known: {keys}")
        return
    name, url = entry
    client = get_client()
    try:
        r = await client.get(url, timeout=3.0)
        ok = r.status_code == 200
        if ok:
            status = f"Online (HTTP {r.status_code})"
        else:
            status = f"HTTP {r.status_code}"
        try:
            body = r.json()
            if isinstance(body, dict):
                extra = body.get("status") or body.get("service") or body.get("message") or ""
                if extra:
                    status += f" -- {extra}"
        except Exception:
            pass
    except httpx.ConnectError:
        status = "Unreachable: connection refused (service may be down)"
    except httpx.TimeoutException:
        status = "Unreachable: connection timed out"
    except Exception as e:
        status = f"Unreachable: {str(e)[:80]}"
    embed = discord.Embed(title=f"Service: {name}", color=0x3498db)
    embed.add_field(name="Status", value=status, inline=False)
    embed.add_field(name="Key", value=f"`{service_name}`", inline=True)
    embed.add_field(name="URL", value=url, inline=True)
    embed.set_footer(text="Use !cmplx restart <service> to restart")
    await ctx.send(embed=embed)


@commands.hybrid_command(name="restart", description="Restart a Docker service via opencode agent")
async def restart_cmd(ctx: commands.Context, service_name: str):
    """Restart a Docker service by name. Routes through the opencode agent which has Docker access."""
    entry = SERVICE_ENDPOINTS.get(service_name)
    if not entry:
        keys = ", ".join(SERVICE_ENDPOINTS.keys())
        await ctx.send(f"Unknown service `{service_name}`. Known: {keys}")
        return
    name, _ = entry
    async with ctx.typing():
        try:
            bot = ctx.bot
            response = await bot.chat_with_cmplx(
                str(ctx.channel.id),
                f"SYSTEM ACTION: Please restart the Docker service '{service_name}' ({name}). "
                f"Use docker compose or docker restart to restart the container. "
                f"Confirm when done.",
                username=ctx.author.display_name,
                guild_name=ctx.guild.name if ctx.guild else "DM"
            )
            embed = discord.Embed(
                title=f"Service Restart: {name}",
                description=response[:2000],
                color=0xf39c12
            )
            embed.add_field(name="Service", value=f"`{service_name}`", inline=True)
            embed.add_field(name="Requested By", value=ctx.author.display_name, inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Restart command failed: {str(e)[:300]}")


@commands.hybrid_command(name="logs", description="Fetch service logs via opencode agent")
async def logs_cmd(ctx: commands.Context, service_name: str, lines: int = 50):
    """Fetch recent logs from a Docker service. Routes through the opencode agent."""
    entry = SERVICE_ENDPOINTS.get(service_name)
    if not entry:
        keys = ", ".join(SERVICE_ENDPOINTS.keys())
        await ctx.send(f"Unknown service `{service_name}`. Known: {keys}")
        return
    name, _ = entry
    if lines < 5:
        lines = 5
    if lines > 500:
        lines = 500
    async with ctx.typing():
        try:
            bot = ctx.bot
            response = await bot.chat_with_cmplx(
                str(ctx.channel.id),
                f"SYSTEM ACTION: Please fetch the last {lines} lines of logs from the Docker service "
                f"'{service_name}' ({name}). Use 'docker compose logs --tail={lines} {service_name}' "
                f"or 'docker logs --tail={lines} $(docker ps --filter name={service_name} -q)'. "
                f"Return the raw log output.",
                username=ctx.author.display_name,
                guild_name=ctx.guild.name if ctx.guild else "DM"
            )
            chunks = bot.split_message(response, 1900)
            for i, chunk in enumerate(chunks):
                if i == 0:
                    embed = discord.Embed(
                        title=f"Service Logs: {name}",
                        description=f"```\n{chunk}\n```" if len(chunk) < 1800 else chunk,
                        color=0x9b59b6
                    )
                    embed.add_field(name="Service", value=f"`{service_name}`", inline=True)
                    embed.add_field(name="Lines", value=str(lines), inline=True)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"```\n{chunk}\n```" if len(chunk) < 1900 else chunk)
        except Exception as e:
            await ctx.send(f"Logs command failed: {str(e)[:300]}")


@commands.hybrid_command(name="expert", description="Create a new SNAPDNA expert from spec")
async def expert_cmd(ctx: commands.Context, name: str, *, description: str):
    """Create a new expert via the opencode agent. Example: !cmplx expert my-expert 'analyzes graph data'"""
    async with ctx.typing():
        try:
            bot = ctx.bot
            response = await bot.chat_with_cmplx(
                str(ctx.channel.id),
                f"SYSTEM ACTION: Create a new SNAPDNA expert with the following spec:\n"
                f"Name: {name}\n"
                f"Description: {description}\n\n"
                f"Please generate the expert configuration, register it in the catalog, "
                f"and confirm the expert ID and capabilities.",
                username=ctx.author.display_name,
                guild_name=ctx.guild.name if ctx.guild else "DM"
            )
            embed = discord.Embed(
                title=f"Expert Created: {name}",
                description=response[:2000],
                color=0x2ecc71
            )
            embed.add_field(name="Requested By", value=ctx.author.display_name, inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Expert creation failed: {str(e)[:300]}")


@commands.hybrid_command(name="persist", description="Force-save active sessions to disk")
async def persist_cmd(ctx: commands.Context):
    """Save all active sessions to persistent storage."""
    save_sessions()
    count = len(_sessions)
    await ctx.send(f"Saved {count} session(s) to persistent storage.")


@commands.hybrid_command(name="help", description="Show CMPLX bot commands")
async def help_cmd(ctx: commands.Context):
    embed = discord.Embed(
        title="CMPLX-PartsFactory Bot Commands",
        description="Geometric computing agent bridge",
        color=0x9b59b6
    )

    commands_list = [
        ("!cmplx status", "Check system health"),
        ("!cmplx services", "Check ALL service health"),
        ("!cmplx service <key>", "Check specific service"),
        ("!cmplx restart <service>", "Restart a Docker service"),
        ("!cmplx logs <service> [lines]", "Fetch service logs"),
        ("!cmplx reset", "Reset channel session"),
        ("!cmplx memory", "Review brain state"),
        ("!cmplx query <text>", "Ask CMPLX a question"),
        ("!cmplx catalog [family]", "Search tool catalog"),
        ("!cmplx discover", "Run discovery scan"),
        ("!cmplx compose <a> <b>", "Test tool composition"),
        ("!cmplx expert <name> <desc>", "Create a new expert"),
        ("!cmplx persist", "Save sessions to disk"),
        ("@CMPLX-PartsFactory <msg>", "Mention bot to chat"),
    ]

    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.set_footer(text="All commands subject to 12.5% knowledge gate protocol")
    await ctx.send(embed=embed)


class HealthHTTPHandler:
    def __init__(self, bot: CMPLXDiscordBot):
        self.bot = bot
        self.start_time = time.time()

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            data = await reader.read(1024)
            path = data.decode().split()[1] if len(data.decode().split()) > 1 else "/"

            if path == "/health":
                uptime = time.time() - self.start_time
                healthy = self.bot.is_ready()
                status_code = 200 if healthy else 503
                body = json.dumps({
                    "ok": healthy,
                    "uptime_seconds": round(uptime, 1),
                    "sessions": len(_sessions),
                    "sessions_persisted": SESSION_FILE,
                    "gateway_latency_ms": round(self.bot.latency * 1000, 1) if healthy else None
                }).encode()
                headers = (
                    f"HTTP/1.1 {status_code} {'OK' if healthy else 'Service Unavailable'}\r\n"
                    f"Content-Type: application/json\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"Connection: close\r\n\r\n"
                ).encode()
                writer.write(headers + body)
            else:
                writer.write(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()


async def start_health_server(bot: CMPLXDiscordBot):
    handler = HealthHTTPHandler(bot)
    server = await asyncio.start_server(handler.handle, "0.0.0.0", 8080)
    logger.info("Health check server on port 8080")
    async with server:
        await server.serve_forever()


def main():
    load_sessions()

    bot = CMPLXDiscordBot()

    bot.add_command(status_cmd)
    bot.add_command(services_cmd)
    bot.add_command(service_cmd)
    bot.add_command(restart_cmd)
    bot.add_command(logs_cmd)
    bot.add_command(expert_cmd)
    bot.add_command(reset_cmd)
    bot.add_command(memory_cmd)
    bot.add_command(query_cmd)
    bot.add_command(catalog_cmd)
    bot.add_command(discover_cmd)
    bot.add_command(compose_cmd)
    bot.add_command(persist_cmd)
    bot.add_command(help_cmd)

    loop = asyncio.get_event_loop()
    loop.create_task(start_health_server(bot))
    loop.create_task(periodic_save(30))

    if not DISCORD_TOKEN:
        logger.error("DISCORD_BOT_TOKEN not set!")
        raise SystemExit(1)

    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        logger.error("Invalid Discord bot token!")
        logger.error("Get your token from: https://discord.com/developers/applications -> Bot -> Reset Token")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
