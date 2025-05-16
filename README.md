Telegram‑бот для консультирования студентов и молодых специалистов в сфере IT.
Бот анализирует резюме и интересы, предлагает подходящие профессии, честно описывает плюсы и минусы, подсказывает, каких навыков не хватает, и генерирует шаблон вежливого сообщения для нетворкинга.

Установка
1.Склонируйте репозиторий: 
    git clone https://github.com/arystan01/career_guidance
    cd career_guidance
    
2.Создайте виртуальное окружение и установите зависимости:
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
3.Создайте файл .env в корне проекта со следующими переменными:
    TELEGRAM_BOT_TOKEN=<Ваш Telegram Bot Token>
    OPENAI_API_KEY=<Ваш OpenAI API Key>
    
Зависимости:
• python-telegram-bot
• openai
• python-dotenv
• PyPDF2
• python-docx
