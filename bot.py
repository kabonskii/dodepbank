import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

BOT_TOKEN = "8438924529:AAGKzTN-Rplj9BFrfFQCJZXHcK_JtmxzxfU"
ADMIN_ID = 1369798535  # ваш telegram id

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# === DATABASE SETUP ===

def init_db():
    conn = sqlite3.connect("dodep_bank.db")
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        name TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()

init_db()

def get_user_id(telegram_id, name):
    conn = sqlite3.connect("dodep_bank.db")
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute("INSERT INTO users (telegram_id, name) VALUES (?,?)",
                (telegram_id, name))
    conn.commit()

    return cur.lastrowid


# === BOT HANDLERS ===

@dp.message(Command("start"))
async def start(message: types.Message):
    get_user_id(message.from_user.id, message.from_user.full_name)

    kb = InlineKeyboardBuilder()
    kb.button(text="Попросить долг", callback_data="ask_loan")
    kb.button(text="Мой долг", callback_data="my_loan")

    await message.answer(
        "Добро пожаловать в ООО «Додеп Банк» 💸\nВыберите действие:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data == "ask_loan")
async def ask_loan(call: types.CallbackQuery):
    await call.message.answer("Введите сумму, которую хотите занять:")
    await call.answer()

    @dp.message()
    async def process_amount(message: types.Message):
        try:
            amount = int(message.text)
        except:
            await message.answer("Введите число!")
            return

        user_id = get_user_id(message.from_user.id, message.from_user.full_name)

        conn = sqlite3.connect("dodep_bank.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO loans (user_id, amount, status) VALUES (?,?,?)",
                    (user_id, amount, "pending"))
        conn.commit()

        loan_id = cur.lastrowid
        conn.close()

        await message.answer("Заявка отправлена!")

        await bot.send_message(
            ADMIN_ID,
            f"💰 Новая заявка №{loan_id}\n"
            f"Пользователь: {message.from_user.full_name}\n"
            f"Сумма: {amount}\n\n"
            f"/approve_{loan_id} — одобрить\n"
            f"/reject_{loan_id} — отклонить"
        )

@dp.message()
async def admin_commands(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    if message.text.startswith("/approve_"):
        loan_id = message.text.replace("/approve_", "")
        update_loan_status(loan_id, "approved")
        await message.answer(f"Заявка {loan_id} одобрена.")

    if message.text.startswith("/reject_"):
        loan_id = message.text.replace("/reject_", "")
        update_loan_status(loan_id, "rejected")
        await message.answer(f"Заявка {loan_id} отклонена.")

def update_loan_status(loan_id, status):
    conn = sqlite3.connect("dodep_bank.db")
    cur = conn.cursor()
    cur.execute(
        "UPDATE loans SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, loan_id)
    )
    conn.commit()
    conn.close()


@dp.callback_query(F.data == "my_loan")
async def my_loan(call: types.CallbackQuery):
    user_id = get_user_id(call.from_user.id, call.from_user.full_name)

    conn = sqlite3.connect("dodep_bank.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT amount, status, created_at FROM loans WHERE user_id=? "
        "ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    row = cur.fetchone()
    conn.close()

    if row:
        amount, status, created = row
        await call.message.answer(
            f"💳 Ваш последний долг:\n"
            f"Сумма: {amount} руб.\n"
            f"Статус: {status}\n"
            f"Дата: {created}"
        )
    else:
        await call.message.answer("У вас нет долгов.")

    await call.answer()

# === START BOT ===

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
