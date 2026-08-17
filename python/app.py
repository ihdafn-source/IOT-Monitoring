from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from flask import Flask, request
import threading
import asyncio
import json
import os


# ==========================
# KONFIGURASI
# ==========================

BOT_TOKEN = "GANTI_DENGAN_TOKEN_BARU"

GROUP_CHAT_ID = -5539374368

ADMIN_IDS = [
    1447200589
]

SETTINGS_FILE = "settings.json"

main_loop = None  # event loop bot, diisi otomatis pas bot start


# ==========================
# SETTINGS NOTIFIKASI
# ==========================

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        default = {"notif_enabled": True}
        save_settings(default)
        return default

    with open(SETTINGS_FILE, "r") as file:
        return json.load(file)


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4)


# ==========================
# START
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()
    status = "🔔 AKTIF" if settings.get("notif_enabled", True) else "🔕 NONAKTIF"

    await update.message.reply_text(
        f"Bot alert pompa siap memantau grup ini.\nStatus notifikasi: {status}"
    )


# ==========================
# COMMAND: /berhenti & /aktifkan
# ==========================

async def berhenti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Hanya admin yang bisa mengubah pengaturan notifikasi")
        return

    settings = load_settings()
    settings["notif_enabled"] = False
    save_settings(settings)

    await update.message.reply_text("🔕 Notifikasi alert telah dihentikan")


async def aktifkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Hanya admin yang bisa mengubah pengaturan notifikasi")
        return

    settings = load_settings()
    settings["notif_enabled"] = True
    save_settings(settings)

    await update.message.reply_text("🔔 Notifikasi alert telah diaktifkan kembali")


# ==========================
# BUTTON: Berhentikan Notifikasi
# ==========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Hanya admin yang bisa menghentikan notifikasi", show_alert=True)
        return

    if query.data == "stop_notif":
        settings = load_settings()
        settings["notif_enabled"] = False
        save_settings(settings)

        await query.answer("Notifikasi dihentikan")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "🔕 Notifikasi telah dihentikan.\nKetik /aktifkan untuk mengaktifkan kembali."
        )


# ==========================
# BROADCAST KE GRUP
# ==========================

async def broadcast(message):
    settings = load_settings()

    if not settings.get("notif_enabled", True):
        print("Notifikasi nonaktif, alert tidak dikirim")
        return

    tombol = [
        [InlineKeyboardButton("🔕 Berhentikan Notifikasi", callback_data="stop_notif")]
    ]

    await bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=message,
        reply_markup=InlineKeyboardMarkup(tombol)
    )


# ==========================
# WEBHOOK GRAFANA
# ==========================

server = Flask(__name__)


@server.route("/alert", methods=["POST"])
def alert():
    data = request.json
    print("Alert masuk:", data)

    alerts = data.get("alerts", [])

    for a in alerts:
        status = a.get("status")  # "firing" atau "resolved"
        labels = a.get("labels", {})
        values = a.get("values", {})

        nilai = list(values.values())[0] if values else "tidak diketahui"

        pesan = f"""
🚨 ALERT POMPA ({status.upper() if status else 'UNKNOWN'})

Sensor: {labels.get('alertname', 'Ultrasonic')}

Jarak terdeteksi:
{nilai} cm

Threshold testing: 20 cm

Cek dashboard Grafana.
"""

        if main_loop is not None:
            asyncio.run_coroutine_threadsafe(broadcast(pesan), main_loop)
        else:
            print("Bot belum siap, pesan dilewati")

    return "OK"


def run_server():
    server.run(host="0.0.0.0", port=5000, use_reloader=False)


# ==========================
# TELEGRAM BOT
# ==========================

async def post_init(application):
    global main_loop
    main_loop = asyncio.get_running_loop()


app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
bot = app.bot

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("berhenti", berhenti))
app.add_handler(CommandHandler("aktifkan", aktifkan))
app.add_handler(CallbackQueryHandler(button))

print("BOT TELEGRAM AKTIF")

threading.Thread(target=run_server, daemon=True).start()

app.run_polling()