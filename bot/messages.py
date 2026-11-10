"""
╔══════════════════════════════════════════╗
║   MULTI-CHECKER BOT — MESSAGES          ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
"""
from datetime import datetime

BANNER = "👑 *@NUTFRR*"


def welcome_msg(name: str, is_premium: bool, is_admin: bool) -> str:
    tier = "👑 Admin" if is_admin else ("💎 Premium" if is_premium else "🆓 Free")
    return (
        f"╔══════════════════════════╗\n"
        f"║  🎮 *MULTI-CHECKER BOT*  ║\n"
        f"╚══════════════════════════╝\n\n"
        f"👋 Welcome, *{name}*!\n"
        f"🏷️ Tier: {tier}\n\n"
        f"🔍 *Available Checkers:*\n"
        f"  🎮 Xbox Full Capture\n"
        f"  🎯 Fortnite API\n"
        f"  ⛏️ Minecraft API\n"
        f"  🎫 Game Pass\n"
        f"  🕹️ EA\n\n"
        f"{'✅ You have full access!' if (is_premium or is_admin) else '🔒 Premium required to check.'}\n\n"
        f"{BANNER}"
    )


def not_premium_msg() -> str:
    return (
        "🔒 *Premium Required*\n\n"
        "This feature requires a premium subscription.\n\n"
        "🎟️ Redeem a code: `/redeem YOUR-CODE`\n"
        "💰 Purchase access from: *@NUTFRR*\n\n"
        f"{BANNER}"
    )


def banned_msg() -> str:
    return (
        "🚫 *You have been banned.*\n\n"
        "Contact @NUTFRR to appeal.\n\n"
        f"{BANNER}"
    )


def help_msg() -> str:
    return (
        "📖 *HELP & COMMANDS*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "*Commands:*\n"
        "  `/start` — Main menu\n"
        "  `/status` — Your account info\n"
        "  `/redeem CODE` — Redeem premium code\n"
        "  `/help` — This message\n\n"
        "*Admin Commands:*\n"
        "  `/gencode USES DAYS` — Generate code\n"
        "  `/revoke CODE` — Revoke code\n"
        "  `/addpremium USER_ID DAYS` — Add premium\n"
        "  `/ban USER_ID` — Ban user\n"
        "  `/unban USER_ID` — Unban user\n"
        "  `/broadcast MSG` — Message all users\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "*How to Check:*\n"
        "1️⃣ Select checker from menu\n"
        "2️⃣ Choose thread speed\n"
        "3️⃣ Send .txt file or paste combos\n"
        "4️⃣ Format: `email:password`\n\n"
        f"{BANNER}"
    )


def status_msg(uid: int, name: str, is_premium: bool, expiry, checks: int) -> str:
    tier = "💎 Premium" if is_premium else "🆓 Free"
    exp_str = expiry.strftime("%d %b %Y") if expiry else "—"
    return (
        f"📊 *YOUR STATUS*\n\n"
        f"👤 Name: *{name}*\n"
        f"🆔 ID: `{uid}`\n"
        f"🏷️ Tier: {tier}\n"
        f"📅 Expires: `{exp_str}`\n"
        f"✅ Total Checks: `{checks:,}`\n\n"
        f"{BANNER}"
    )


def checker_menu_msg() -> str:
    return (
        "🔍 *SELECT CHECKER*\n\n"
        "🎮 *Xbox Full* — Gamertag, GamePass, Gold, country\n"
        "🎯 *Fortnite* — V-Bucks, skins, rare items, BP\n"
        "⛏️ *Minecraft* — Java, Bedrock, username, cape\n"
        "🎫 *Game Pass* — All subscription tiers + expiry\n"
        "🕹️ *EA* — EA Play, EA Pro, game library\n\n"
        f"{BANNER}"
    )


def threads_msg(checker_name: str) -> str:
    return (
        f"⚙️ *{checker_name}* — Select Speed\n\n"
        "🚀 **Fast (20T)** — Good balance, recommended\n"
        "⚡ **Turbo (40T)** — Max speed, may hit ratelimits\n"
        "🐢 **Safe (5T)** — Slow but clean\n\n"
        f"{BANNER}"
    )


def send_combos_msg(checker_name: str, threads: int) -> str:
    return (
        f"✅ *{checker_name}* — {threads} Threads\n\n"
        f"📂 *Send your combos now:*\n\n"
        f"• Upload a `.txt` file, **or**\n"
        f"• Paste combos directly in chat\n\n"
        f"Format: `email:password`\n"
        f"Max: **50,000 combos** per session\n\n"
        f"{BANNER}"
    )


def combos_loaded_msg(checker_name: str, count: int, threads: int, preview: str, session_id: int) -> str:
    return (
        f"🚀 *{checker_name} — STARTED*\n\n"
        f"📋 Combos: `{count:,}`\n"
        f"⚡ Threads: `{threads}`\n"
        f"🆔 Session: `#{session_id}`\n\n"
        f"*Preview:*\n{preview}\n\n"
        f"🔄 Running... results will appear below.\n\n"
        f"{BANNER}"
    )


def progress_msg(checker: str, checked: int, total: int, hits: int, bad: int,
                 twofa: int, locked: int, cpm: int) -> str:
    pct  = int(checked / total * 100) if total else 0
    bar  = "█" * (pct // 10) + "░" * (10 - pct // 10)
    return (
        f"🔄 *{checker} — RUNNING*\n\n"
        f"`[{bar}] {pct}%`\n\n"
        f"✅ Checked: `{checked:,}/{total:,}`\n"
        f"🎯 Hits: `{hits}`\n"
        f"❌ Bad: `{bad}`\n"
        f"🔐 2FA: `{twofa}`\n"
        f"🔒 Locked: `{locked}`\n"
        f"⚡ CPM: `{cpm}`\n\n"
        f"{BANNER}"
    )


def session_done_msg(checker: str, checked: int, hits: int, bad: int,
                     twofa: int, locked: int, rate: int, elapsed: float) -> str:
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    cpm  = int(checked / (elapsed / 60)) if elapsed > 0 else 0
    return (
        f"✅ *{checker} — COMPLETE*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Results:*\n"
        f"  ✅ Checked: `{checked:,}`\n"
        f"  🎯 Hits: `{hits}`\n"
        f"  ❌ Bad: `{bad}`\n"
        f"  🔐 2FA: `{twofa}`\n"
        f"  🔒 Locked: `{locked}`\n"
        f"  ⚠️ Ratelimit: `{rate}`\n\n"
        f"⏱️ Time: `{mins}m {secs}s`\n"
        f"⚡ Avg CPM: `{cpm}`\n\n"
        f"{'📄 Hits file sent below.' if hits > 0 else '📭 No hits this run.'}\n\n"
        f"{BANNER}"
    )


# ── HIT CARDS ──────────────────────────────────────────────────────────────────

def xbox_hit_card(r: dict, n: int) -> str:
    gpu  = "✅ GPU" if r.get("game_pass_ultimate") else ("✅ PC GP" if r.get("game_pass_pc") else "❌ No GP")
    gold = f"✅ Gold ({r['gold_expiry']})" if r.get("xbox_live_gold") and r.get("gold_expiry") else ("✅ Gold" if r.get("xbox_live_gold") else "❌ No Gold")
    return (
        f"╔══════════════════════╗\n"
        f"║  🎮 XBOX HIT #{n}       ║\n"
        f"╚══════════════════════╝\n"
        f"📧 `{r['email']}`\n"
        f"🔑 `{r['password']}`\n\n"
        f"🎮 Gamertag: `{r.get('gamertag','?')}`\n"
        f"🏆 Gamerscore: `{r.get('gamerscore','?')}`\n"
        f"🎫 {gpu}\n"
        f"🏅 {gold}\n"
        f"🌍 Country: `{r.get('country','?')}`\n"
        f"📅 Created: `{r.get('created','?')}`\n\n"
        f"👑 @NUTFRR"
    )


def fortnite_hit_card(r: dict, n: int) -> str:
    rare = ", ".join(r.get("rare_skins", [])[:3]) or "none"
    bp   = f"✅ BP Lv.{r.get('bp_level',0)}" if r.get("battle_pass") else "❌ No BP"
    return (
        f"╔══════════════════════╗\n"
        f"║  🎯 FORTNITE HIT #{n}  ║\n"
        f"╚══════════════════════╝\n"
        f"📧 `{r['email']}`\n"
        f"🔑 `{r['password']}`\n\n"
        f"👤 IGN: `{r.get('display_name','?')}`\n"
        f"💰 V-Bucks: `{r.get('vbucks',0):,}`\n"
        f"👗 Skins: `{r.get('skins',0)}` | Emotes: `{r.get('emotes',0)}`\n"
        f"⛏️ Pickaxes: `{r.get('pickaxes',0)}` | Gliders: `{r.get('gliders',0)}`\n"
        f"🌟 Rare: `{rare}`\n"
        f"🎫 {bp}\n"
        f"📦 Total Items: `{r.get('total_items',0)}`\n\n"
        f"👑 @NUTFRR"
    )


def minecraft_hit_card(r: dict, n: int) -> str:
    java    = "✅ Java"    if r.get("java")    else "❌ Java"
    bedrock = "✅ Bedrock" if r.get("bedrock") else "❌ Bedrock"
    cape    = "✅ Cape"    if r.get("has_cape") else "❌ No Cape"
    return (
        f"╔══════════════════════╗\n"
        f"║  ⛏️ MINECRAFT HIT #{n}  ║\n"
        f"╚══════════════════════╝\n"
        f"📧 `{r['email']}`\n"
        f"🔑 `{r['password']}`\n\n"
        f"👤 Username: `{r.get('username','?')}`\n"
        f"🆔 UUID: `{r.get('uuid','?')[:12]}...`\n"
        f"☕ {java} | 🪨 {bedrock}\n"
        f"🧣 {cape}\n\n"
        f"👑 @NUTFRR"
    )


def gamepass_hit_card(r: dict, n: int) -> str:
    subs = ", ".join(r.get("all_subs", [])) or "unknown"
    gpu  = f"✅ GPU exp `{r['gpu_expiry']}`"  if r.get("game_pass_ultimate") else "❌ No GPU"
    pc   = f"✅ PC GP exp `{r['pc_expiry']}`" if r.get("game_pass_pc")       else "❌ No PC GP"
    gold = f"✅ Gold exp `{r['gold_expiry']}`" if r.get("xbox_live_gold")     else "❌ No Gold"
    return (
        f"╔══════════════════════╗\n"
        f"║  🎫 GAME PASS HIT #{n} ║\n"
        f"╚══════════════════════╝\n"
        f"📧 `{r['email']}`\n"
        f"🔑 `{r['password']}`\n\n"
        f"🎮 {gpu}\n"
        f"💻 {pc}\n"
        f"🏅 {gold}\n"
        f"🌍 Country: `{r.get('country','?')}`\n"
        f"📋 Subs: `{subs}`\n\n"
        f"👑 @NUTFRR"
    )


def ea_hit_card(r: dict, n: int) -> str:
    play = f"✅ EA Play exp `{r['ea_play_expiry']}`" if r.get("ea_play") else "❌ No EA Play"
    pro  = f"✅ EA Pro"  if r.get("ea_play_pro") else "❌ No EA Pro"
    games = ", ".join(r.get("games", [])[:5]) or "none"
    return (
        f"╔══════════════════════╗\n"
        f"║  🕹️ EA HIT #{n}         ║\n"
        f"╚══════════════════════╝\n"
        f"📧 `{r['email']}`\n"
        f"🔑 `{r['password']}`\n\n"
        f"👤 IGN: `{r.get('display_name','?')}`\n"
        f"🌍 Country: `{r.get('country','?')}`\n"
        f"🎮 {play}\n"
        f"💎 {pro}\n"
        f"📚 Games ({r.get('games_count',0)}): `{games}`\n\n"
        f"👑 @NUTFRR"
    )


HIT_CARDS = {
    "xbox":      xbox_hit_card,
    "fortnite":  fortnite_hit_card,
    "minecraft": minecraft_hit_card,
    "gamepass":  gamepass_hit_card,
    "ea":        ea_hit_card,
}


def hit_card(checker: str, result: dict, n: int) -> str:
    fn = HIT_CARDS.get(checker, xbox_hit_card)
    return fn(result, n)


def code_created_msg(code: str, uses: int, days: int) -> str:
    return (
        f"🎟️ *CODE GENERATED*\n\n"
        f"```\n{code}\n```\n\n"
        f"📋 Uses: `{uses}`\n"
        f"📅 Duration: `{days} days`\n\n"
        f"Share via: `/redeem {code}`\n\n"
        f"{BANNER}"
    )


def redeem_success_msg(days: int, expires_at) -> str:
    exp = expires_at.strftime("%d %b %Y %H:%M UTC")
    return (
        f"✅ *PREMIUM ACTIVATED!*\n\n"
        f"🎉 +{days} days added\n"
        f"📅 Expires: `{exp}`\n\n"
        f"You now have full access to all checkers!\n\n"
        f"{BANNER}"
    )


def admin_stats_msg(s: dict) -> str:
    return (
        f"📊 *BOT STATISTICS*\n\n"
        f"👥 Total Users: `{s['total_users']:,}`\n"
        f"💎 Premium: `{s['premium_users']:,}`\n"
        f"✅ Total Checks: `{s['total_checks']:,}`\n"
        f"🎯 Total Hits: `{s['total_hits']:,}`\n\n"
        f"{BANNER}"
    )
