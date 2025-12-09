import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------------- CONFIG ----------------
TOKEN = "8361065068:AAFKiPSwK81BHw6dL9U2T6GF6iAccBzNy8Q"
OPENWEATHER_API_KEY = "b81471a787d41482f688297818e8e8b8"

logging.basicConfig(level=logging.INFO)

# ================= STATES (ALL US STATES) =================

STATES = {
    "AL": {"name": "Alabama", "city": "Montgomery"},
    "AK": {"name": "Alaska", "city": "Anchorage"},
    "AZ": {"name": "Arizona", "city": "Phoenix"},
    "AR": {"name": "Arkansas", "city": "Little Rock"},
    "CA": {"name": "California", "city": "Los Angeles"},
    "CO": {"name": "Colorado", "city": "Denver"},
    "CT": {"name": "Connecticut", "city": "Hartford"},
    "DE": {"name": "Delaware", "city": "Dover"},
    "FL": {"name": "Florida", "city": "Miami"},
    "GA": {"name": "Georgia", "city": "Atlanta"},
    "HI": {"name": "Hawaii", "city": "Honolulu"},
    "ID": {"name": "Idaho", "city": "Boise"},
    "IL": {"name": "Illinois", "city": "Chicago"},
    "IN": {"name": "Indiana", "city": "Indianapolis"},
    "IA": {"name": "Iowa", "city": "Des Moines"},
    "KS": {"name": "Kansas", "city": "Topeka"},
    "KY": {"name": "Kentucky", "city": "Frankfort"},
    "LA": {"name": "Louisiana", "city": "Baton Rouge"},
    "ME": {"name": "Maine", "city": "Augusta"},
    "MD": {"name": "Maryland", "city": "Annapolis"},
    "MA": {"name": "Massachusetts", "city": "Boston"},
    "MI": {"name": "Michigan", "city": "Lansing"},
    "MN": {"name": "Minnesota", "city": "Saint Paul"},
    "MS": {"name": "Mississippi", "city": "Jackson"},
    "MO": {"name": "Missouri", "city": "Jefferson City"},
    "MT": {"name": "Montana", "city": "Helena"},
    "NE": {"name": "Nebraska", "city": "Lincoln"},
    "NV": {"name": "Nevada", "city": "Las Vegas"},
    "NH": {"name": "New Hampshire", "city": "Concord"},
    "NJ": {"name": "New Jersey", "city": "Trenton"},
    "NM": {"name": "New Mexico", "city": "Santa Fe"},
    "NY": {"name": "New York", "city": "New York"},
    "NC": {"name": "North Carolina", "city": "Raleigh"},
    "ND": {"name": "North Dakota", "city": "Bismarck"},
    "OH": {"name": "Ohio", "city": "Columbus"},
    "OK": {"name": "Oklahoma", "city": "Oklahoma City"},
    "OR": {"name": "Oregon", "city": "Salem"},
    "PA": {"name": "Pennsylvania", "city": "Harrisburg"},
    "RI": {"name": "Rhode Island", "city": "Providence"},
    "SC": {"name": "South Carolina", "city": "Columbia"},
    "SD": {"name": "South Dakota", "city": "Pierre"},
    "TN": {"name": "Tennessee", "city": "Nashville"},
    "TX": {"name": "Texas", "city": "Austin"},
    "UT": {"name": "Utah", "city": "Salt Lake City"},
    "VT": {"name": "Vermont", "city": "Montpelier"},
    "VA": {"name": "Virginia", "city": "Richmond"},
    "WA": {"name": "Washington", "city": "Olympia"},
    "WV": {"name": "West Virginia", "city": "Charleston"},
    "WI": {"name": "Wisconsin", "city": "Madison"},
    "WY": {"name": "Wyoming", "city": "Cheyenne"}
}


# ---------------- STORAGE ----------------
USER_LANG = {}
USER_STATES = {}
USER_NEWS = {}

# ---------------- ICONS ----------------
def weather_icon(desc: str) -> str:
    d = desc.lower()
    if "clear" in d: return "☀️"
    if "cloud" in d: return "☁️"
    if "rain" in d: return "🌧"
    if "snow" in d: return "❄️"
    if "storm" in d: return "⛈"
    if "fog" in d or "mist" in d: return "🌫"
    return "🌡"

# ---------------- WEATHER ----------------
async def fetch_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

# ---------------- UI ----------------
def build_main_menu(lang):
    if lang == "ru":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🌎 Выбрать штаты", callback_data="menu_states")],
            [InlineKeyboardButton("📰 Новости погоды", callback_data="menu_news")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌎 Select states", callback_data="menu_states")],
        [InlineKeyboardButton("📰 Weather news", callback_data="menu_news")]
    ])

def build_states_keyboard(user_id):
    selected = set(USER_STATES.get(user_id, []))
    buttons, row = [], []

    for code, st in STATES.items():
        mark = " ✅" if code in selected else ""
        row.append(InlineKeyboardButton(f"{st['name']} ({code}){mark}", callback_data=f"state_{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    back = "⬅ Назад" if USER_LANG.get(user_id) == "ru" else "⬅ Back"
    done = "✅ Готово" if USER_LANG.get(user_id) == "ru" else "✅ Done"

    buttons.append([
        InlineKeyboardButton(back, callback_data="menu_back"),
        InlineKeyboardButton(done, callback_data="done")
    ])

    return InlineKeyboardMarkup(buttons)

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_LANG.setdefault(user_id, "ru")
    await update.message.reply_text("Главное меню:", reply_markup=build_main_menu(USER_LANG[user_id]))

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id
    lang = USER_LANG.get(user_id, "ru")

    if q.data == "menu_states":
        await q.edit_message_text(
            "Выберите штаты:" if lang == "ru" else "Select states:",
            reply_markup=build_states_keyboard(user_id)
        )

    elif q.data == "menu_news":
        USER_NEWS[user_id] = True
        await q.edit_message_text(
            "✅ Новости включены" if lang == "ru" else "✅ News enabled",
            reply_markup=build_main_menu(lang)
        )

    elif q.data == "menu_back":
        await q.edit_message_text("Главное меню:", reply_markup=build_main_menu(lang))

async def state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id
    code = q.data.replace("state_", "")

    USER_STATES.setdefault(user_id, [])
    if code in USER_STATES[user_id]:
        USER_STATES[user_id].remove(code)
    else:
        USER_STATES[user_id].append(code)

    await q.edit_message_text(
        "Выберите штаты:" if USER_LANG[user_id] == "ru" else "Select states:",
        reply_markup=build_states_keyboard(user_id)
    )

async def done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id
    lang = USER_LANG.get(user_id, "ru")

    selected = USER_STATES.get(user_id, [])
    if not selected:
        await q.edit_message_text("Штаты не выбраны" if lang == "ru" else "No states selected")
        return

    lines = []
    for code in selected:
        st = STATES[code]
        data = await fetch_weather(st["city"])
        if not data:
            continue

        desc = data["weather"][0]["description"]
        temp = round(data["main"]["temp"])
        hum = data["main"]["humidity"]
        wind = data["wind"]["speed"]

        icon = weather_icon(desc)

        lines.append(
            f"🏙 {st['name']} ({code})\n"
            f"{icon} {desc}\n"
            f"🌡 {temp}°C\n"
            f"💧 {hum}%\n"
            f"🌬 {wind} m/s"
        )

    await q.edit_message_text("\n\n".join(lines))

# ---------------- AUTO NEWS ----------------
async def weather_news_job(context: ContextTypes.DEFAULT_TYPE):
    for user_id in USER_NEWS:
        if not USER_NEWS[user_id]:
            continue

        states = USER_STATES.get(user_id, [])
        if not states:
            continue

        for code in states:
            st = STATES[code]
            data = await fetch_weather(st["city"])
            if not data:
                continue

            desc = data["weather"][0]["description"]
            temp = round(data["main"]["temp"])
            icon = weather_icon(desc)

            await context.bot.send_message(
                chat_id=user_id,
                text=f"📰 {st['name']} — {icon} {desc}, {temp}°C"
            )

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(state_handler, pattern="^state_"))
    app.add_handler(CallbackQueryHandler(done_handler, pattern="^done$"))

    app.job_queue.run_repeating(weather_news_job, interval=1800, first=10)

    app.run_polling()

if __name__ == "__main__":
    main()
