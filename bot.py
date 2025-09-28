bot.py
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# Берём секреты из переменных окружения (не храните токен/карту в открытому коде)
BOT_TOKEN = os.getenv("8132763923:AAE5w5ZVwhkt7e0SZBS5Nw-xNHfNDDr7DrU")
CARD_NUMBER = os.getenv("9860 1606 0578 8241")

app = Application.builder().token(BOT_TOKEN).build()

# В памяти (простая реализация, при перезапуске всё сбросится)
pending_payments = {}        # { user_id: message_id_of_receipt }
global_admin_id = {"id": None}


# /start — запоминает первого, кто запустил бота, как админа
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if global_admin_id["id"] is None:
        global_admin_id["id"] = user.id
        await update.message.reply_text("✅ Siz admin sifatida belgilandingiz!")  # уведомление нового админа
    await update.message.reply_text(
        "🎮 Assalomu alaykum!\n\n"
        "💸 Bu bot orqali Steam hisobini to'ldirish mumkin.\n"
        "👉 To'lov uchun /pay buyrug'ini bosing."
    )


# /pay — показывает карту
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if CARD_NUMBER:
        await update.message.reply_text(
            f"💳 To‘lov uchun karta raqami:\n\n{CARD_NUMBER}\n\n"
            "📌 To‘lovni amalga oshirgach, chek (skrin) yuboring. Admin tasdiqlaydi.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("⚠️ Karta raqami sozlanmagan! Admin bilan bog'laning.")


# обработка фото (чеки)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    # сохраняем id сообщения с чеком
    pending_payments[user.id] = message.message_id

    # уведомляем админа с inline кнопками
    admin_id = global_admin_id["id"]
    if admin_id:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm:{user.id}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"reject:{user.id}")
            ]
        ])
        await context.bot.send_message(
            chat_id=admin_id,
            text=(
                f"📥 Yangi chek keldi!\n"
                f"👤 Foydalanuvchi: {user.full_name}\n"
                f"🆔 ID: {user.id}\n\n"
                "Skirnni ko'rish uchun botdagi chatga o'ting."
            ),
            reply_markup=keyboard
        )

    await message.reply_text("💳 To‘lovingiz tekshirish uchun yuborildi. Admin tasdiqlagach xabar olasiz.")


# inline callbacks (confirm / reject)
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # убирает спиннер
    data = query.data or ""
    action, user_id_str = data.split(":")
    user_id = int(user_id_str)

    # проверка прав
    if query.from_user.id != global_admin_id["id"]:
        await query.answer("⛔ Sizda ruxsat yo'q.", show_alert=True)
        return

    if user_id not in pending_payments:
        await query.message.edit_text("❗ Bu foydalanuvchida kutilayotgan to‘lov yo‘q.")
        return

    if action == "confirm":
        await context.bot.send_message(user_id, "✅ To‘lovingiz qabul qilindi! Rahmat 🙌\nSteam hisobingiz tez orada toʻldiriladi.")
        await query.message.edit_text(f"☑️ To‘lov tasdiqlandi (User ID: {user_id})")
    elif action == "reject":
        await context.bot.send_message(user_id, "❌ To‘lovingiz rad etildi. Iltimos, qayta yuboring yoki admin bilan bog‘laning.")
        await query.message.edit_text(f"🚫 To‘lov rad etildi (User ID: {user_id})")

    del pending_payments[user_id]
# /status — список ожидающих (только админ)
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != global_admin_id["id"]:
        await update.message.reply_text("⛔ Sizda ruxsat yo'q.")
        return
    if not pending_payments:
        await update.message.reply_text("🟢 Kutilayotgan to‘lovlar yo‘q.")
        return
    text = "📋 Kutilayotgan to‘lovlar:\n\n"
    for uid in pending_payments:
        text += f"• User ID: {uid}\n"
    await update.message.reply_text(text)


# Регистрируем хендлеры
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("pay", pay))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(CommandHandler("status", status))

if __name__ == "__main__":
    app.run_polling()
