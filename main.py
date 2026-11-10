"""
╔══════════════════════════════════════════╗
║   MULTI-CHECKER BOT — ENTRY POINT       ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
"""
import asyncio
import json
import logging
import os

from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from db.database import init_db
from bot.handlers import (
    cmd_start, cmd_help, cmd_status, cmd_redeem,
    cmd_gencode, cmd_revoke, cmd_addpremium, cmd_ban, cmd_unban, cmd_broadcast,
    on_callback, on_message,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN    = os.environ.get("BOT_TOKEN", "9091153277:AAEQeCL1AwooOzUJgJEP7tTEyVDtuW82UNk")
WEBHOOK_URL  = os.environ.get("WEBHOOK_URL", "")
WEBHOOK_PORT = int(os.environ.get("PORT", "8080"))

_SECRET = BOT_TOKEN.split(":")[1][:20]
WH_PATH = f"/webhook/{_SECRET}"


def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("help",        cmd_help))
    app.add_handler(CommandHandler("status",      cmd_status))
    app.add_handler(CommandHandler("redeem",      cmd_redeem))
    app.add_handler(CommandHandler("gencode",     cmd_gencode))
    app.add_handler(CommandHandler("revoke",      cmd_revoke))
    app.add_handler(CommandHandler("addpremium",  cmd_addpremium))
    app.add_handler(CommandHandler("ban",         cmd_ban))
    app.add_handler(CommandHandler("unban",       cmd_unban))
    app.add_handler(CommandHandler("broadcast",   cmd_broadcast))

    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(
        filters.Document.TXT | (filters.TEXT & ~filters.COMMAND),
        on_message,
    ))
    return app


async def main():
    init_db()
    logger.info("DB ready.")

    tg_app = build_app()

    if WEBHOOK_URL:
        # ── production: aiohttp handles webhook ──────────────────────────────
        aio_app = web.Application()

        async def tg_webhook(request):
            data   = await request.read()
            update = Update.de_json(json.loads(data), tg_app.bot)
            await tg_app.process_update(update)
            return web.Response()

        aio_app.router.add_post(WH_PATH, tg_webhook)
        aio_app.router.add_get("/health", lambda r: web.Response(text="ok"))

        await tg_app.initialize()
        await tg_app.bot.set_webhook(
            url=f"{WEBHOOK_URL.rstrip('/')}{WH_PATH}",
            drop_pending_updates=True,
        )
        await tg_app.start()

        runner = web.AppRunner(aio_app)
        await runner.setup()
        site   = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
        await site.start()
        logger.info("Webhook server on 0.0.0.0:%d", WEBHOOK_PORT)

        try:
            await asyncio.Event().wait()
        finally:
            await tg_app.stop()
            await tg_app.shutdown()
            await runner.cleanup()
    else:
        # ── local dev: polling ────────────────────────────────────────────────
        logger.info("Polling mode (no WEBHOOK_URL).")
        await tg_app.initialize()
        await tg_app.start()
        await tg_app.updater.start_polling(drop_pending_updates=True)
        try:
            await asyncio.Event().wait()
        finally:
            await tg_app.updater.stop()
            await tg_app.stop()
            await tg_app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
