import telebot
from telebot import types
import json
import os

# ==============================
# CONFIG
# ==============================
ADMIN_ID = 1369798535
BOT_TOKEN = "8438924529:AAGKzTN-Rplj9BFrfFQCJZXHcK_JtmxzxfU"  # токен в коде как ты просил

bot = telebot.TeleBot(BOT_TOKEN)

# ==============================
# DATABASE
# ==============================
DB_FILE = "db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==============================
# START
# ==============================
@bot.message_handler(commands=["start"])
def start(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Попросить долг", "Посмотреть долг")
    bot.send_message(message.chat.id, "Добро пожаловать в ООО «Додеп банк» 💸", reply_markup=kb)

# ==============================
# REQUEST LOAN
# ==============================
@bot.message_handler(func=lambda m: m.text == "Попросить долг")
def request_loan(message):
    msg = bot.send_message(message.chat.id, "Введите сумму долга:")
    bot.register_next_step_handler(msg, ask_reason)

def ask_reason(message):
    amount = message.text

    if not amount.isdigit():
        return bot.send_message(message.chat.id, "Введите число!")

    message.chat.amount = int(amount)
    msg = bot.send_message(message.chat.id, "Введите причину:")
    bot.register_next_step_handler(msg, send_request)

def send_request(message):
    reason = message.text
    amount = message.chat.amount

    bot.send_message(
        ADMIN_ID,
        f"📩 *Заявка на долг*\n"
        f"От: @{message.from_user.username}\n"
        f"ID: {message.from_user.id}\n"
        f"Сумма: {amount}₽\n"
        f"Причина: {reason}",
        parse_mode="Markdown"
    )

    bot.send_message(message.chat.id, "Заявка отправлена!")

# ==============================
# CHECK LOAN
# ==============================
@bot.message_handler(func=lambda m: m.text == "Посмотреть долг")
def check_loan(message):
    db = load_db()
    user_id = str(message.from_user.id)

    debt = db.get(user_id, 0)

    bot.send_message(message.chat.id, f"Ваш долг: {debt}₽")

# ==============================
# ADMIN: EDIT DEBT
# ==============================
@bot.message_handler(commands=["edit"])
def edit_debt(message):
    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(message.chat.id, "Введите ID пользователя:")
    bot.register_next_step_handler(msg, ask_new_debt)

def ask_new_debt(message):
    user_id = message.text
    message.chat.edit_user = user_id

    msg = bot.send_message(message.chat.id, "Введите новый долг:")
    bot.register_next_step_handler(msg, save_new_debt)

def save_new_debt(message):
    new_debt = message.text

    if not new_debt.isdigit():
        return bot.send_message(message.chat.id, "Введите число!")

    user_id = message.chat.edit_user
    db = load_db()
    db[user_id] = int(new_debt)
    save_db(db)

    bot.send_message(message.chat.id, "Долг обновлён.")

# ==============================
# RUN
# ==============================
bot.polling(none_stop=True)
