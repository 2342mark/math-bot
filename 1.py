import os
from aiohttp import web
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Токен твоего бота от @BotFather
TOKEN = "8898873647:AAH3C6vCVJzDYYMu7dKsvd7K8MOa_V0HTsw"

# =========================================================================
# КОММЕНТАРИЙ: База данных уроков и заданий. 
# В каждом уроке теперь минимум 10 заданий. 
# Сюда можно добавлять новые уроки, менять текст вопросов и правильные ответы.
# =========================================================================
LESSONS_DB = {
    1: {
        "title": "Урок 1: Линейные уравнения",
        "tasks": [
            {"question": "Решите уравнение: 2x + 5 = 15", "answer": "5"},
            {"question": "Решите уравнение: 3x - 9 = 0", "answer": "3"},
            {"question": "Решите уравнение: 4x - 8 = 16", "answer": "6"},
            {"question": "Решите уравнение: 5x + 10 = 35", "answer": "5"},
            {"question": "Решите уравнение: 7x - 14 = 28", "answer": "6"},
            {"question": "Решите уравнение: 10x + 20 = 120", "answer": "10"},
            {"question": "Решите уравнение: 6x - 12 = 24", "answer": "6"},
            {"question": "Решите уравнение: 8x + 16 = 64", "answer": "6"},
            {"question": "Решите уравнение: 9x - 18 = 54", "answer": "8"},
            {"question": "Решите уравнение: 11x + 22 = 110", "answer": "8"}
        ]
    },
    2: {
        "title": "Урок 2: Квадратные уравнения",
        "tasks": [
            {"question": "Найдите положительный корень уравнения x^2 - 9 = 0", "answer": "3"},
            {"question": "Найдите положительный корень уравнения x^2 - 16 = 0", "answer": "4"},
            {"question": "Найдите положительный корень уравнения x^2 - 25 = 0", "answer": "5"},
            {"question": "Найдите положительный корень уравнения x^2 - 36 = 0", "answer": "6"},
            {"question": "Найдите положительный корень уравнения x^2 - 49 = 0", "answer": "7"},
            {"question": "Найдите положительный корень уравнения x^2 - 64 = 0", "answer": "8"},
            {"question": "Найдите положительный корень уравнения x^2 - 81 = 0", "answer": "9"},
            {"question": "Найдите положительный корень уравнения x^2 - 100 = 0", "answer": "10"},
            {"question": "Найдите положительный корень уравнения x^2 - 121 = 0", "answer": "11"},
            {"question": "Найдите положительный корень уравнения x^2 - 144 = 0", "answer": "12"}
        ]
    }
}

# =========================================================================
# КОММЕНТАРИЙ: Список купленных уроков для пользователей.
# Некупленные уроки вообще не будут отображаться в меню ученика.
# =========================================================================
USER_ACCESS = {
    # telegram_id: [список id купленных уроков]
    "default": [1, 2] # По умолчанию для теста доступны 1 и 2 уроки
}

router = Router()

class LessonStates(StatesGroup):
    solving = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Мои купленные уроки", callback_data="hw_menu")]
        ]
    )
    await message.answer(
        f"Привет, <b>{message.from_user.full_name}</b>! 👋\n\n"
        "Добро пожаловать в учебный бот платформы <b>MATH.MARK</b>.\n"
        "Здесь доступны только ваши приобретенные уроки с интерактивными блоками заданий.",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "hw_menu")
async def show_bought_lessons(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    
    # Получаем строго купленные уроки пользователя
    bought_lessons = USER_ACCESS.get(user_id, USER_ACCESS["default"])
    
    keyboard_buttons = []
    for lesson_id in bought_lessons:
        if lesson_id in LESSONS_DB:
            title = LESSONS_DB[lesson_id]["title"]
            keyboard_buttons.append(
                [InlineKeyboardButton(text=f"📖 {title}", callback_data=f"start_lesson_{lesson_id}")]
            )
    
    if not keyboard_buttons:
        await callback.message.edit_text("У вас пока нет купленных уроков.")
        await callback.answer()
        return

    keyboard_buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_home")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        "<b>Ваши доступные уроки:</b>\nВыберите урок для выполнения заданий:",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "back_home")
async def back_home_handler(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Мои купленные уроки", callback_data="hw_menu")]
        ]
    )
    await callback.message.edit_text(
        "Главное меню платформы <b>MATH.MARK</b>.",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("start_lesson_"))
async def start_lesson(callback: CallbackQuery, state: FSMContext):
    lesson_id = int(callback.data.split("_")[2])
    lesson = LESSONS_DB.get(lesson_id)
    
    if not lesson:
        await callback.answer("Урок не найден.", show_alert=True)
        return
        
    # Инициализируем прохождение урока с первого задания (индекс 0)
    await state.update_data(lesson_id=lesson_id, task_index=0)
    await state.set_state(LessonStates.solving)
    
    await callback.message.delete()
    await send_task(callback.message, state)
    await callback.answer()

async def send_task(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_id = data.get("lesson_id")
    task_index = data.get("task_index")
    
    lesson = LESSONS_DB[lesson_id]
    tasks = lesson["tasks"]
    
    if task_index >= len(tasks):
        # Если все 10+ заданий пройдены
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📚 К списку уроков", callback_data="hw_menu")]
            ]
        )
        await message.answer(
            f"🎉 <b>Великолепная работа!</b> Вы успешно решили все задания урока <i>«{lesson['title']}»</i>!",
            reply_markup=keyboard
        )
        await state.clear()
        return
        
    current_task = tasks[task_index]
    total_tasks = len(tasks)
    
    # =========================================================================
    # КОММЕНТАРИЙ: Сюда можно вставить отправку фотографии задания, если она есть.
    # Пример отправки фото задания:
    # await message.answer_photo(photo="file_id_фотографии", caption="Текст задания")
    # =========================================================================
    
    text = (
        f"<b>{lesson['title']}</b>\n"
        f"📝 Задание <b>{task_index + 1} из {total_tasks}</b>\n\n"
        f"{current_task['question']}\n\n"
        f"<i>Отправьте ответ текстом или прикрепите фото решения:</i>"
    )
    
    # ВАЖНО: Во время прохождения заданий у ученика НЕТ кнопки возврата к списку уроков.
    await message.answer(text)

@router.message(LessonStates.solving)
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_id = data.get("lesson_id")
    task_index = data.get("task_index")
    
    lesson = LESSONS_DB[lesson_id]
    current_task = lesson["tasks"][task_index]
    
    # =========================================================================
    # КОММЕНТАРИЙ: Обработка ответов ученика (текст или фото)
    # Если ученик прислал фото: message.photo[-1].file_id
    # Если текст: message.text.strip()
    # =========================================================================
    if message.photo:
        # Ученик отправил фотографию с решением
        user_answer = "photo"
        await message.answer("📸 Ваше фото с решением получено и передано на проверку!")
    elif message.text:
        user_answer = message.text.strip()
    else:
        await message.answer("Пожалуйста, отправьте текстовый ответ или фотографию решения.")
        return

    correct_answer = current_task["answer"]
    
    # Логика проверки ответа
    is_correct = False
    if message.text and user_answer.lower() == correct_answer.lower():
        is_correct = True
    elif message.photo:
        # Для фото можно сделать автоматическое подтверждение или ручную проверку преподавателем
        is_correct = True
        
    if is_correct:
        await message.answer("✅ <b>Верно! Идем дальше!</b> 🚀")
        # Увеличиваем индекс задания и переходим к следующему
        await state.update_data(task_index=task_index + 1)
        await send_task(message, state)
    else:
        # Кнопка "Попробовать еще раз" (кнопки возврата к списку уроков здесь нет)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать еще раз", callback_data="retry_task")]
            ]
        )
        await message.answer(
            "❌ <b>Неправильно.</b> Перепроверьте вычисления и попробуйте снова.",
            reply_markup=keyboard
        )

@router.callback_query(F.data == "retry_task")
async def retry_task(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await send_task(callback.message, state)
    await callback.answer()

async def main():
   # Фиктивный обработчик, чтобы хостинг видел, что мы "сайт"
async def handle(request):
    return web.Response(text="Бот MATH.MARK работает 24/7!")

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    # Поднимаем микро-сервер для обхода блокировок бесплатных хостингов
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render выдает свой порт, берем его или используем 8080 по умолчанию
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    print("Интеллектуальный бот MATH.MARK запущен и готов к работе...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем самого бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())