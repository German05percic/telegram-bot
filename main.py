import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import json
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt
import io
import csv
import logging

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Часовий пояс Києва
KYIV_TZ = pytz.timezone('Europe/Kyiv')

# Токен бота
TOKEN = '7616087734:AAFW_N5etPdTGQdim8PWEkRP7Tp58P61GcA'  # Заміни на свій токен

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

# Завантаження даних
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'spends': {}, 'profits': {}}

# Збереження даних
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Головне меню
async def start(update, context):
    if not check_access(update):
        return
    keyboard = [
        [InlineKeyboardButton("📉 Додати витрату", callback_data='add_spend'),
         InlineKeyboardButton("📈 Додати прибуток", callback_data='add_profit')],
        [InlineKeyboardButton("🏠 Додати витрати на життя", callback_data='add_living_expense')],
        [InlineKeyboardButton("📊 Переглянути статистику", callback_data='stats'),
         InlineKeyboardButton("📋 Викачати дані", callback_data='export')],
        [InlineKeyboardButton("📊 Графік за день", callback_data='graph_day'),
         InlineKeyboardButton("📊 Графік за місяць", callback_data='graph_month')],
        [InlineKeyboardButton("❌ Скасувати останню дію", callback_data='cancel_last')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Обери дію:', reply_markup=reply_markup)
    logger.info("Отримано команду /start")

# Обробка кнопок
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
    elif query.data == 'add_living_expense':
        await query.edit_message_text('Введи суму витрат на життя (наприклад, 200):')
        context.user_data['action'] = 'add_living_expense'
    elif query.data == 'stats':
        await show_stats(query, context, user_id)
    elif query.data == 'export':
        await export_data(query, context, user_id)
    elif query.data == 'graph_day':
        await send_graph(query, context, user_id, period='day')
    elif query.data == 'graph_month':
        await send_graph(query, context, user_id, period='month')
    elif query.data == 'cancel_last':
        await cancel_last_action(query, context, user_id)

# Обробка текстових повідомлень
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
            data['spends'][user_id][date].append({'amount': -amount, 'time': now, 'type': 'spend'})
            save_data(data)
            await update.message.reply_text(f'📉 Додано витрату: ${amount} о {now.split(" ")[1]}')
        elif action == 'add_profit':
            if user_id not in data['profits']:
                data['profits'][user_id] = {}
            if date not in data['profits'][user_id]:
                data['profits'][user_id][date] = []
            data['profits'][user_id][date].append({'amount': amount, 'time': now, 'type': 'profit'})
            save_data(data)
            await update.message.reply_text(f'📈 Додано прибуток: ${amount} о {now.split(" ")[1]}')
        elif action == 'add_living_expense':
            if user_id not in data['spends']:
                data['spends'][user_id] = {}
            if date not in data['spends'][user_id]:
                data['spends'][user_id][date] = []
            data['spends'][user_id][date].append({'amount': -amount, 'time': now, 'type': 'living'})
            save_data(data)
            await update.message.reply_text(f'🏠 Додано витрати на життя: ${amount} о {now.split(" ")[1]}')

        context.user_data['action'] = None
        await start(update, context)
    except ValueError:
        await update.message.reply_text('Введи коректну суму (наприклад, 50).')

# Показ статистики за день
async def show_stats(query, context, user_id):
    data = load_data()
    date = datetime.now(KYIV_TZ).strftime('%Y-%m-%d')
    total_spend = sum(item['amount'] for item in data['spends'].get(user_id, {}).get(date, []))
    total_profit = sum(item['amount'] for item in data['profits'].get(user_id, {}).get(date, []))
    response = f'📊 Статистика за {date}:\nСумарно за день: {total_spend:.2f} / +{total_profit:.2f}'
    await query.edit_message_text(response)

# Експорт даних у CSV
async def export_data(query, context, user_id):
    data = load_data()
    filename = f'finance_{user_id}.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Тип', 'Сума', 'Час', 'Дата'])
        for date, spends in data.get('spends', {}).get(user_id, {}).items():
            for item in spends:
                writer.writerow([item['type'], item['amount'], item['time'].split(' ')[1], date])
        for date, profits in data.get('profits', {}).get(user_id, {}).items():
            for item in profits:
                writer.writerow([item['type'], item['amount'], item['time'].split(' ')[1], date])
    with open(filename, 'rb') as f:
        await query.message.reply_document(document=f, filename=filename)
    await query.edit_message_text('📋 Дані викачано у файлі CSV!')

# Графік за день або місяць
async def send_graph(query, context, user_id, period='day'):
    data = load_data()
    now = datetime.now(KYIV_TZ)
    if period == 'day':
        date = now.strftime('%Y-%m-%d')
        spends = data.get('spends', {}).get(user_id, {}).get(date, [])
        profits = data.get('profits', {}).get(user_id, {}).get(date, [])
        title = f'Графік за {date}'
    else:  # month
        month_start = now.replace(day=1).strftime('%Y-%m-%d')
        spends = []
        profits = []
        for date in data.get('spends', {}).get(user_id, {}).keys():
            if date.startswith(now.strftime('%Y-%m')):
                spends.extend(data['spends'][user_id][date])
        for date in data.get('profits', {}).get(user_id, {}).keys():
            if date.startswith(now.strftime('%Y-%m')):
                profits.extend(data['profits'][user_id][date])
        title = f'Графік за {now.strftime("%B %Y")}'

    times = [item['time'].split(' ')[1] for item in spends + profits]
    amounts = [item['amount'] for item in spends + profits]
    
    if not times:
        await query.edit_message_text(f'📊 Немає даних для графіка за {period}.')
        return
    
    plt.figure(figsize=(10, 5))
    plt.plot(times, amounts, marker='o', linestyle='-', color='b')
    plt.title(title)
    plt.xlabel('Час')
    plt.ylabel('Сума ($)')
    plt.xticks(rotation=45)
    plt.grid(True)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    await query.message.reply_photo(photo=buf, caption=title)
    buf.close()
    plt.close()
    await query.edit_message_text('Графік надіслано!')

# Скасування останньої дії
async def cancel_last_action(query, context, user_id):
    data = load_data()
    date = datetime.now(KYIV_TZ).strftime('%Y-%m-%d')
    spends = data.get('spends', {}).get(user_id, {}).get(date, [])
    profits = data.get('profits', {}).get(user_id, {}).get(date, [])

    if spends and profits:
        last_spend = spends[-1] if spends else {'time': '00:00'}
        last_profit = profits[-1] if profits else {'time': '00:00'}
        if last_spend['time'] > last_profit['time']:
            removed = spends.pop()
            data['spends'][user_id][date] = spends
            save_data(data)
            await query.edit_message_text(f'❌ Скасовано останню витрату: ${-removed["amount"]} о {removed["time"].split(" ")[1]}')
        else:
            removed = profits.pop()
            data['profits'][user_id][date] = profits
            save_data(data)
            await query.edit_message_text(f'❌ Скасовано останній прибуток: ${removed["amount"]} о {removed["time"].split(" ")[1]}')
    elif spends:
        removed = spends.pop()
        data['spends'][user_id][date] = spends
        save_data(data)
        await query.edit_message_text(f'❌ Скасовано останню витрату: ${-removed["amount"]} о {removed["time"].split(" ")[1]}')
    elif profits:
        removed = profits.pop()
        data['profits'][user_id][date] = profits
        save_data(data)
        await query.edit_message_text(f'❌ Скасовано останній прибуток: ${removed["amount"]} о {removed["time"].split(" ")[1]}')
    else:
        await query.edit_message_text('❌ Немає дій для скасування сьогодні.')
    await start(query, context)

# Основна функція запуску бота
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()