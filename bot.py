import os
import openai
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import docx
from PyPDF2 import PdfReader

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")     
openai.api_key = os.getenv("OPENAI_API_KEY")   

SYSTEM_PROMPT = """\

# Идентичность

Вы — карьерный консультант, специализирующийся на помощи студентам в выборе подходящего направления в сфере IT. Вы анализируете резюме и интересы пользователя, рекомендуете подходящие профессии в IT и определяете, каких навыков или квалификаций ему не хватает. Также вы даёте конкретные советы, как восполнить эти пробелы.
**Никогда не начинайте ответ с приветствия или вводных фраз** – сразу переходите к анализу и рекомендациям.

# Инструкции

Если пользователь присылает резюме и описывает интересы, внимательно проанализируйте оба источника.
Рекомендуйте 3 конкретных профессии в IT (например, Разработчик фронтенда на React, Инженер DevOps с фокусом на AWS, Аналитик данных для финансового сектора).
Для каждой профессии кратко опишите:

Описание: чем занимается специалист, какие у него обязанности.
Плюсы: высокая востребованность, зарплата, гибкий график.
Минусы: сложность освоения, высокая конкуренция, дорогое обучение.

Честно указывайте, каких навыков или знаний не хватает пользователю.
Дайте чёткие и практические рекомендации: какие курсы пройти, какие сертификаты получить, какие проекты сделать.
Отвечайте на том языке, на котором пишет пользователь (если по-русски — отвечайте по-русски, если по-английски — на английском).

Используйте Markdown для жирного выделения заголовков и ключевых пунктов. Например:  
**Описание**, **Плюсы**, **Минусы**, **Не хватает**, **Что делать**.  

Пишите кратко, без воды, но не слишком сокращайте текст. Поддерживайте дружелюбный, но прямой стиль.

Пример запроса пользователя
Я учусь в университете, интересуюсь технологиями и люблю помогать людям. Вот моё резюме: [вставлен текст]. Какие IT-профессии мне подойдут?

Пример ответа
На основе вашего резюме и интересов подойдут следующие направления:

Специалист технической поддержки
Описание: помогает пользователям решать технические проблемы, работает с тикетами и документацией.

Плюсы: быстрое трудоустройство, стабильность.

Минусы: монотонная работа, ограниченный рост без переквалификации.

Не хватает: опыта с тикет-системами и базовых сертификатов.

Что делать: изучите CompTIA A+ и пройдите симуляции Help Desk-сценариев онлайн.

Фронтенд-разработчик
Описание: создаёт пользовательские интерфейсы для сайтов и приложений.

Плюсы: творческая работа, высокий спрос.

Минусы: быстро меняющиеся технологии, много конкурентов.

Не хватает: знаний JavaScript-фреймворков и адаптивной вёрстки.

Что делать: пройдите курс от freeCodeCamp и сделайте проекты с использованием React.

Аналитик данных
Описание: анализирует данные, строит отчёты, помогает бизнесу принимать решения.

Плюсы: высокая зарплата, логичная работа.

Минусы: нужно знание математики и SQL, конкуренция.

Не хватает: SQL и визуализации данных.

Что делать: начните с SQL на Khan Academy и курсов по Tableau.

чтобы отделить профессии друг от друга, используйте пустую строку. ТОЛЬКО ПУСТОТУ между профессиями.
ВООБЩЕ НИКОГДА НЕ ИСПОЛЬЗУЙ "---"

"""

def parse_file(path: str) -> str:
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif path.lower().endswith(".docx"):
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def process_document(path: str) -> str:
    text = parse_file(path)
    response = openai.ChatCompletion.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": text}
        ],
        max_tokens=1500
    )
    return response.choices[0].message.content.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Подобрать профессию"]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "Здравствуйте! Выберите действие:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # Подсказка про язык
    lang_code = update.effective_user.language_code or "en"
    lang_instruction = (
        "Отвечай на русском языке."
        if lang_code.startswith("ru")
        else "Respond in English."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "system",  "content": lang_instruction},
            {"role": "user",    "content": user_text},
        ],
        max_tokens=1500
    )
    answer = response.choices[0].message.content.strip()
    await update.message.reply_text(answer, parse_mode=ParseMode.MARKDOWN)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    tg_file = await doc.get_file()
    path = doc.file_name
    await tg_file.download_to_drive(path)
    await update.message.reply_text("Анализирую документ…")

    text = parse_file(path)
    lang_code = update.effective_user.language_code or "en"
    lang_instruction = (
        "Отвечай на русском языке."
        if lang_code.startswith("ru")
        else "Respond in English."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": lang_instruction},
            {"role": "user",   "content": text}
        ],
        max_tokens=1500
    )
    result = response.choices[0].message.content.strip()
    await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)

async def analyze_resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /analyze_resume
    Загрузка резюме для анализа. Бот оценивает навыки, опыт и предлагает подходящие IT-направления.
    """
    await update.message.reply_text(
        "Загрузка резюме для анализа. Бот оценит ваши навыки, опыт и предложит подходящие IT-направления."
    )

async def generate_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /contact <goal> | <full_name> | <position> | <company>
    Генерирует вежливое короткое обращение к нужному человеку для стажировки.
    """
    # Если пользователь не передал аргументы — даём подробную инструкцию
    if not context.args:
        await update.message.reply_text(
            "Перед генерацией сообщения:\n"
            "1. Выберите область IT, в которой хотите работать.\n"
            "2. Найдите в LinkedIn специалистов из этой области.\n"
            "3. Скопируйте их данные – Имя Фамилия, должность и компанию.\n\n"
            "Затем отправьте команду в формате:\n"
            "/contact <цель> | <Имя Фамилия> | <должность> | <компания>\n\n"
            "Пример:\n"
            "/contact Найти стажировку в Machine Learning | Иван Иванов | ML Engineer | Google"
        )
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split("|")]
    if len(parts) != 4:
        await update.message.reply_text(
            "Некорректный формат. Используйте:\n"
            "/contact <цель> | <Имя Фамилия> | <должность> | <компания>"
        )
        return

    goal, full_name, position, company = parts
    prompt = f"""Твоя задача — на основе цели студента и профиля человека, которому он хочет написать, \
                сгенерировать короткое, уважительное сообщение, которое студент может вставить в запрос на контакт или в первое сообщение.

                Контекст:
                Цель студента: {goal}
                Имя и фамилия человека: {full_name}
                Должность: {position}
                Место работы: {company}

                Сгенерируй короткое сообщение 200 СИМВОЛОВ МАКСИМУМ И НЕ БОЛЬШЕ, где студент представится, укажет интерес к теме, поблагодарит, \
                и вежливо попросит возможность пройти стажировку или узнать больше о работе в этой сфере. \
                Не используй формальный стиль «уважаемый» — пусть будет дружелюбно, но уважительно. \
                Начни с «Здравствуйте, {full_name.split()[0]}». \
                Выводи только текст сообщения, без лишних комментариев."""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user",   "content": prompt}],
        max_tokens=250
    )

    result = response.choices[0].message.content.strip()
    await update.message.reply_text(result)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze_resume", analyze_resume_command))
    app.add_handler(CommandHandler("contact", generate_contact))
    from telegram.ext import filters
    app.add_handler(MessageHandler(filters.Regex(r'^Подобрать профессию$'), analyze_resume_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()
