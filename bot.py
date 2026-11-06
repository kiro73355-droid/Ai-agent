import os
import asyncio
from collections import defaultdict
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from google import genai
from google.genai import types as genai_types

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
client = genai.Client(api_key=GEMINI_KEY)

user_histories = defaultdict(list)

SYSTEM_INSTRUCTION = (
    "Siz Telegramdagi shaxsiy yordamchi AI agentsiz. Foydalanuvchiga har qanday savol, "
    "rejalar va kundalik vazifalarda aniq, muloyim va lo'nda javob berasiz. "
    "Muloqot tili: o'zbek tili."
)

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    user_histories[user_id].clear()
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "Men sizning shaxsiy Gemini AI yordamchingizman. Menga xohlagan savolingizni yozishingiz mumkin.\n"
        "Suhbat tarixini tozalash: /reset"
    )

@dp.message(Command("reset"))
async def handle_reset(message: types.Message):
    user_id = message.from_user.id
    user_histories[user_id].clear()
    await message.answer("Suhbat xotirasi tozalandi.")

@dp.message()
async def handle_ai_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text

    if not user_text:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    history = user_histories[user_id]
    history.append({"role": "user", "parts": [user_text]})

    if len(history) > 10:
        history = history[-10:]
        user_histories[user_id] = history

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=history,
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            )
        )
        ai_reply = response.text
        history.append({"role": "model", "parts": [ai_reply]})
        await message.answer(ai_reply)

    except Exception as e:
        await message.answer("Kechirasiz, javob olishda xatolik yuz berdi.")
        print(f"Xato: {e}")

async def main():
    print("Gemini AI Bot ishga tushirildi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
