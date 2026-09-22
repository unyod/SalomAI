# AI Telegram Bot 🤖

Professional, modular AI Telegram Bot built with Python 3.12+, Aiogram 3.x, SQLAlchemy, and multiple AI provider support.

## Features

- 💬 **AI Chat** — Multi-turn conversations with context memory
- 📚 **Chat History** — Save, browse, continue, pin, rename, delete chats
- 🧠 **Long-term Memory** — Persist key user information across sessions
- 📊 **Statistics** — Per-user usage analytics
- ⚙️ **Settings** — AI model, language, memory toggle
- 👨‍💼 **Admin Panel** — Broadcast, block users, manage channels, view stats
- 📢 **Force Subscription** — Require channel membership before using the bot

## Setup

### 1. Clone and install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram Bot token from @BotFather |
| `ADMIN_IDS` | Comma-separated admin Telegram IDs |
| `AI_PROVIDER` | `gemini` or `openai` |
| `GEMINI_API_KEY` | Google Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key (optional) |
| `DATABASE_URL` | SQLite (default) or PostgreSQL URL |

### 3. Run

```bash
python bot.py
```

The database is created automatically on first run.

## Project Structure

```
ai_telegram_bot/
├── bot.py                  # Entry point
├── config.py               # Pydantic settings
├── requirements.txt
├── .env.example
│
├── handlers/               # Aiogram message handlers
│   ├── start.py            # /start, subscription check
│   ├── chat.py             # Active AI chat (FSM)
│   ├── chats.py            # Chat list & management
│   ├── memory.py           # Memory management
│   ├── statistics.py       # User stats
│   ├── settings.py         # Bot settings
│   ├── admin.py            # Admin panel
│   └── help.py             # Help text
│
├── keyboards/              # Inline & reply keyboards
│   ├── main.py
│   ├── chats.py
│   ├── settings.py
│   ├── admin.py
│   └── subscription.py
│
├── database/               # SQLAlchemy ORM
│   ├── database.py         # Engine & session
│   ├── models.py           # ORM models
│   └── queries.py          # All DB queries
│
├── services/               # Business logic
│   ├── ai.py               # AI provider abstraction
│   ├── memory.py           # Memory context builder
│   ├── statistics.py       # Stats aggregation
│   └── subscription.py     # Subscription checks + cache
│
├── middlewares/
│   ├── db_session.py       # DB session injection
│   └── subscription.py     # Force subscription gate
│
└── utils/
    ├── logger.py
    └── helpers.py
```

## Admin Commands

- `/admin` — Open admin panel (admin IDs only)
- **Broadcast** — Send message to all users
- **Block User** — Block/unblock by Telegram ID
- **Force Subscription** — Add/remove required channels
- **Statistics** — Total users, chats, messages

## Adding New AI Providers

1. Subclass `BaseAIProvider` in `services/ai.py`
2. Implement `chat()` and `generate_title()` methods
3. Register in `_PROVIDERS` dict

## Production (PostgreSQL)

```
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

## Future Extensions Ready

The architecture supports adding:
- 🎤 Voice message processing
- 🖼 Image analysis
- 📄 File analysis
- 🌍 Full i18n
- 💳 Premium subscriptions
- ☁️ Cloud deployment (Railway, Fly.io, VPS)
