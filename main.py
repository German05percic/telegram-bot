import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import json
from datetime import datetime, timedelta
import pytz
import logging
import matplotlib.pyplot as plt
import io
import csv

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Налаштування часового поясу Києва
KYIV_TZ = pytz.timezone('Europe/Kyiv')

# Токен твого бота від BotFather (ЗАМІНИ НА СВІЙ ТОКЕН!)
TOKEN = '7616087734:AAFW_N5etPdTGQdim8PWEkRP7Tp58P61GcA'  # Встав сюди токен від BotFather

# Файл для зберігання даних
DATA_FILE = 'finance_data.json'

# Твій Telegram ID
ALLOWED_USER_ID = 997763291

# Перевірка доступу
def check_access(update):
    user_id = update.effective_chat.id
    if user_id != ALLOWED_USER_ID:
        update.message.reply_text('Доступ заборонено. Цей бот лише для приватного використання.')
        return False
    return True

# Завантаження даних з файлу
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'spends': {}, 'profits': {}}

# Збереження даних у файл
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Головне меню з кнопками
async def start(update, context):
    if not check_access(update):
        return
    keyboard = [
        [InlineKeyboardButton("📉 Додати витрату", callback_data='add_spend'),
         InlineKeyboardButton("📈 Додати прибуток", callback_data='add_profit')],
        [InlineKeyboardButton("📊 Переглянути статистику", callback_data='stats'),
         InlineKeyboardButton("📋 Викачати дані", callback_data='export')],
        [InlineKeyboardButton("📊 Графік за день", callback_data='graph_day')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Обери дію:', reply_markup=reply_markup)
    logger.info("Отримано команду /start")

# Обробка натискання кнопок
async def button(update, context):
    query = update.callback_query
    await query.answer()
    user_id = str(query.message.chat_id)

    if query.data == 'add_spend':
        await query.edit_message_text('Введи суму витрати (наприклад, 50):')
        context.user_data['action'] = 'add_spend'
    elif query.data == 'add_profit':
        await query.edit_message_text('Введи суму прибутку (наприклад, 100):')
        context.user_data['action'] = 'add_profit'
    elif query.data == 'stats':
        await show_stats(query, context, user_id)
    elif query.data == 'export':
        await export_data(query, context, user_id)
    elif query.data == 'graph_day':
        await send_graph(query, context, user_id)

# Обробка текстових повідомлень після вибору дії
async def handle_message(update, context):
    if not check_access(update):
        return
    user_id = str(update.message.chat_id)
    action = context.user_data.get('action')
    if not action:
        await update.message.reply_text('Спочатку обери дію через /start.')
        return

    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError
        data = load_data()
        now = datetime.now(KYIV_TZ).strftime('%Y-%m-%d %H:%M')
        date = datetime.now(KYIV_TZ).strftime('%Y-%m-%d')

        if action == 'add_spend':
            if user_id not in data['spends']:
                data['spends'][user_id] = {}
            if date not in data['spends'][user_id]:
                data['spends'][user_id][date] = []
            data['spends'][user_id][date].append({'amount': -amount, 'time': now})
            save_data(data)
            await update.message.reply_text(f'📉 Додано витрату: ${amount} о {now.split(" ")[1]}')
            logger.info(f"Додано витрату: ${amount}")
        elif action == 'add_profit':
            if user_id not in data['profits']:
                data['profits'][user_id] = {}
            if date not in data['profits'][user_id]:
                data['profits'][user_id][date] = []
            data['profits'][user_id][date].append({'amount': amount, 'time': now})
            save_data(data)
            await update.message.reply_text(f'📈 Додано прибуток: ${amount} о {now.split(" ")[1]}')
            logger.info(f"Додано прибуток: ${amount}")

        context.user_data['action'] = None  # Скидаємо дію
        await start(update, context)  # Повертаємо меню
    except ValueError:
        await update.message.reply_text('Введи коректну суму (наприклад, 50).')

# Показ статистики
async def show_stats(query, context, user_id):
    data = load_data()
    date = datetime.now(KYIV_TZ).strftime('%Y-%m-%d')
    
    total_spend = sum(item['amount'] for item in data['spends'].get(user_id, {}).get(date, []))
    total_profit = sum(item['amount'] for item in data['profits'].get(user_id, {}).get(date, []))
    response = f'📊 Статистика за {date}:\nСумарно за день: {total_spend:.2f} / +{total_profit:.2f}'
    await query.edit_message_text(response)
    logger.info(f"Переглянуто статистику за {date}")

# Експорт даних у CSV
async def export_data(query, context, user_id):
    data = load_data()
    filename = f'finance_{user_id}.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Тип', 'Сума', 'Час', 'Дата'])
        
        # Витрати
        for date, spends in data.get('spends', {}).get(user_id, {}).items():
            for item in spends:
                writer.writerow(['Витрата', item['amount'], item['time'].split(' ')[1], date])
        
        # Прибутки
        for date, profits in data.get('profits', {}).get(user_id, {}).items():
            for item in profits:
                writer.writerow(['Прибуток', item['amount'], item['time'].split(' ')[1], date])

    with open(filename, 'rb') as f:
        await query.message.reply_document(document=f, filename=filename)
    await query.edit_message_text('📋 Дані викачано у файлі CSV!')
    logger.info("Дані експортовано у CSV")

# Генерація графіка за день
async def send_graph(query, context, user_id):
    data = load_data()
    date = datetime.now(KYIV_TZ).strftime('%Y-%m-%d')
    
    spends = data.get('spends', {}).get(user_id, {}).get(date, [])
    profits = data.get('profits', {}).get(user_id, {}).get(date, [])
    
    times = [item['time'].split(' ')[1] for item in spends + profits]
    amounts = [item['amount'] for item in spends + profits]
    
    if not times:  # Якщо немає даних
        await query.edit_message_text('📊 Немає даних для графіка за цей день.')
        return
    
    plt.figure(figsize=(10, 5))
    plt.plot(times, amounts, marker='o', linestyle='-', color='b')
    plt.title(f'Графік за {date}')
    plt.xlabel('Час')
    plt.ylabel('Сума ($)')
    plt.xticks(rotation=45)
    plt.grid(True)
    
    # Збереження графіка у пам’ять
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    await query.message.reply_photo(photo=buf, caption=f'📊 Графік за {date}')
    buf.close()
    plt.close()
    await query.edit_message_text('Графік надіслано!')
    logger.info(f"Надіслано графік за {date}")

# Основна функція запуску бота
def main():
    logger.info("Запуск бота...")
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Обробка тексту без команд
    
    logger.info("Бот запущений!")
    application.run_polling()

if __name__ == '__main__':
    main()
