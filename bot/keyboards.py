"""
╔══════════════════════════════════════════╗
║   MULTI-CHECKER BOT — KEYBOARDS         ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_premium: bool, is_admin: bool) -> InlineKeyboardMarkup:
    rows = []
    if is_premium or is_admin:
        rows.append([
            InlineKeyboardButton("🎮 Checkers", callback_data="menu_checkers"),
        ])
    else:
        rows.append([
            InlineKeyboardButton("🔒 Checkers  [Premium]", callback_data="buy_premium"),
        ])
    rows.append([
        InlineKeyboardButton("📊 My Stats",   callback_data="my_status"),
        InlineKeyboardButton("🎟️ Redeem",     callback_data="redeem"),
    ])
    rows.append([
        InlineKeyboardButton("💎 Get Premium", callback_data="buy_premium"),
        InlineKeyboardButton("❓ Help",         callback_data="help"),
    ])
    if is_admin:
        rows.append([InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(rows)


def checker_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎮 Xbox Full", callback_data="chk_xbox"),
            InlineKeyboardButton("🎯 Fortnite",  callback_data="chk_fortnite"),
        ],
        [
            InlineKeyboardButton("⛏️ Minecraft",  callback_data="chk_minecraft"),
            InlineKeyboardButton("🎫 Game Pass",  callback_data="chk_gamepass"),
        ],
        [
            InlineKeyboardButton("🕹️ EA",         callback_data="chk_ea"),
        ],
        [InlineKeyboardButton("« Back", callback_data="back_main")],
    ])


def thread_speed_kb(checker: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Fast (20T)",  callback_data=f"threads_{checker}_20"),
            InlineKeyboardButton("⚡ Turbo (40T)", callback_data=f"threads_{checker}_40"),
        ],
        [
            InlineKeyboardButton("🐢 Safe (5T)",   callback_data=f"threads_{checker}_5"),
        ],
        [InlineKeyboardButton("« Back", callback_data="menu_checkers")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🛑 Stop Check", callback_data="check_stop")
    ]])


def back_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("« Main Menu", callback_data="back_main")
    ]])


def back_checkers_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("« Checkers", callback_data="menu_checkers"),
        InlineKeyboardButton("« Main Menu", callback_data="back_main"),
    ]])


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎟️ Gen Code",    callback_data="admin_gencode"),
            InlineKeyboardButton("📋 List Codes",  callback_data="admin_listcodes"),
        ],
        [
            InlineKeyboardButton("👥 Users",        callback_data="admin_listusers"),
            InlineKeyboardButton("📊 Stats",        callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🚫 Ban User",     callback_data="admin_ban"),
            InlineKeyboardButton("✅ Unban User",   callback_data="admin_unban"),
        ],
        [
            InlineKeyboardButton("💬 Broadcast",   callback_data="admin_broadcast"),
        ],
        [InlineKeyboardButton("« Main Menu", callback_data="back_main")],
    ])


def code_gen_duration_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("7 Days",   callback_data="cg_days_7"),
            InlineKeyboardButton("30 Days",  callback_data="cg_days_30"),
            InlineKeyboardButton("90 Days",  callback_data="cg_days_90"),
        ],
        [
            InlineKeyboardButton("180 Days", callback_data="cg_days_180"),
            InlineKeyboardButton("365 Days", callback_data="cg_days_365"),
        ],
        [InlineKeyboardButton("« Back", callback_data="admin_panel")],
    ])


def code_gen_uses_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1 Use",   callback_data="cg_uses_1"),
            InlineKeyboardButton("3 Uses",  callback_data="cg_uses_3"),
            InlineKeyboardButton("5 Uses",  callback_data="cg_uses_5"),
        ],
        [
            InlineKeyboardButton("10 Uses", callback_data="cg_uses_10"),
            InlineKeyboardButton("∞ Uses",  callback_data="cg_uses_999"),
        ],
        [InlineKeyboardButton("« Back", callback_data="admin_panel")],
    ])
