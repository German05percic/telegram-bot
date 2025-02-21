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

# Мови
LANGUAGES = {
    'ua': {
        'start': 'Обери дію:',
        'add_spend': '📉 Додати витрату',
        'add_profit': '📈 Додати прибуток',
        'add_living': '🏠 Додати витрати на життя',
        'stats_day': '📊 За день',
        'stats_week': '📊 За тиждень',
        'stats_month': '📊 За місяць',
        'balance': '💰 Баланс',
        'export': '📋 Викачати дані',
        'graph_day': '📊 Графік за день',
        'graph_month': '📊 Графік за місяць',
        'cancel': '❌ Скасувати останні дії',
        'choose_category': 'Обери категорію витрат:',
        'food': '🍔 Їжа',
        'transport': '🚗 Транспорт',
        'entertainment': '🎉 Розваги',
        'living': '🏠 Життя',
        'other': 'Інше',
        'enter_spend': 'Введи суму витрати для "{category}" (наприклад, 50):',
        'enter_profit': 'Введи суму прибутку (наприклад, 100):',
        'enter_living': 'Введи суму витрат на життя (наприклад, 200):',
        'added_spend': '📉 Додано витрату ({category}): ${amount} о {time}',
        'added_profit': '📈 Додано прибуток: ${amount} о {time}',
        'added_living': '🏠 Додано витрати на життя: ${amount} о {time}',
        'stats_format': '{title}:\nСумарно: {spend:.2f} / +{profit:.2f}\nСередній дохід за день: {avg_day:.2f}\nСередній дохід за місяць: {avg_month:.2f}',
        'stats_day_title': '📊 Статистика за {date}',
        'stats_week_title': '📊 Статистика за тиждень з {week_start}',
        'stats_month_title': '📊 Статистика за {month}',
        'balance_format': '💰 Поточний баланс: ${balance:.2f}\nЗагальні прибутки: +{profit:.2f}\nЗагальні витрати: {spend:.2f}',
        'exported': '📋 Дані викачано у файлі CSV!',
        'no_data_graph': '📊 Немає даних для графіка за {period}.',
        'graph_sent': 'Графік надіслано!',
        'cancel_choose': 'Скільки останніх дій скасувати?',
        'cancel_1': '1 дія',
        'cancel_2': '2 дії',
        'cancel_3': '3 дії',
        'canceled_spend': '❌ Скасовано витрату ({category}): ${amount} о {time}',
        'canceled_profit': '❌ Скасовано прибуток: ${amount} о {time}',
        'no_actions': '❌ Немає дій для скасування сьогодні.',
        'invalid_amount': 'Введи коректну суму (наприклад, 50).'
    },
    'ru': {
        'start': 'Выбери действие:',
        'add_spend': '📉 Добавить расход',
        'add_profit': '📈 Добавить доход',
        'add_living': '🏠 Добавить расходы на жизнь',
        'stats_day': '📊 За день',
        'stats_week': '📊 За неделю',
        'stats_month': '📊 За месяц',
        'balance': '💰 Баланс',
        'export': '📋 Скачать данные',
        'graph_day': '📊 График за день',
        'graph_month': '📊 График за месяц',
        'cancel': '❌ Отменить последние действия',
        'choose_category': 'Выбери категорию расходов:',
        'food': '🍔 Еда',
        'transport': '🚗 Транспорт',
        'entertainment': '🎉 Развлечения',
        'living': '🏠 Жизнь',
        'other': 'Другое',
        'enter_spend': 'Введи сумму расхода для "{category}" (например, 50):',
        'enter_profit': 'Введи сумму дохода (например, 100):',
        'enter_living': 'Введи сумму расходов на жизнь (например, 200):',
        'added_spend': '📉 Добавлен расход ({category}): ${amount} в {time}',
        'added_profit': '📈 Добавлен доход: ${amount} в {time}',
        'added_living': '🏠 Добавлены расходы на жизнь: ${amount} в {time}',
        'stats_format': '{title}:\nИтого: {spend:.2f} / +{profit:.2f}\nСредний доход за день: {avg_day:.2f}\nСредний доход за месяц: {avg_month:.2f}',
        'stats_day_title': '📊 Статистика за {date}',
        'stats_week_title': '📊 Статистика за неделю с {week_start}',
        'stats_month_title': '📊 Статистика за {month}',
        'balance_format': '💰 Текущий баланс: ${balance:.2f}\nОбщие доходы: +{profit:.2f}\nОбщие расходы: {spend:.2f}',
        'exported': '📋 Данные скачаны в файле CSV!',
        'no_data_graph': '📊 Нет данных для графика за {period}.',
        'graph_sent': 'График отправлен!',
        'cancel_choose': 'Сколько последних действий отменить?',
        'cancel_1': '1 действие',
        'cancel_2': '2 действия',
        'cancel_3': '3 действия',
        'canceled_spend': '❌ Отменен расход ({category}): ${amount} в {time}',
        'canceled_profit': '❌ Отменен доход: ${amount} в {time}',
        'no_actions': '❌ Нет действий для отмены сегодня.',
        'invalid_amount': 'Введи корректную сумму (например, 50).'
    },
    'en': {
        'start': 'Choose an action:',
        'add_spend': '📉 Add expense',
        'add_profit': '📈 Add income',
        'add_living': '🏠 Add living expenses',
        'stats_day': '📊 Daily',
        'stats_week': '📊 Weekly',
        'stats_month': '📊 Monthly',
        'balance': '💰 Balance',
        'export': '📋 Download data',
        'graph_day': '📊 Daily graph',
        'graph_month': '📊 Monthly graph',
        'cancel': '❌ Cancel last actions',
        'choose_category': 'Choose expense category:',
        'food': '🍔 Food',
        'transport': '🚗 Transport',
        'entertainment': '🎉 Entertainment',
        'living': '🏠 Living',
        'other': 'Other',
        'enter_spend': 'Enter expense amount for "{category}" (e.g., 50):',
        'enter_profit': 'Enter income amount (e.g., 100):',
        'enter_living': 'Enter living expense amount (e.g., 200):',
        'added_spend': '📉 Added expense ({category}): ${amount} at {time}',
        'added_profit': '📈 Added income: ${amount} at {time}',
        'added_living': '🏠 Added living expenses: ${amount} at {time}',
        'stats_format': '{title}:\nTotal: {spend:.2f} / +{profit:.2f}\nAverage daily income: {avg_day:.2f}\nAverage monthly income: {avg_month:.2f}',
        'stats_day_title': '📊 Stats for {date}',
        'stats_week_title': '📊 Stats for week starting {week_start}',
        'stats_month_title': '📊 Stats for {month}',
        'balance_format': '💰 Current balance: ${balance:.2f}\nTotal income: +{profit:.2f}\nTotal expenses: {spend:.2f}',
        'exported': '📋 Data downloaded in CSV file!',
        'no_data_graph': '📊 No data for graph for {period}.',
        'graph_sent': 'Graph sent!',
        'cancel_choose': 'How many recent actions to cancel?',
        'cancel_1': '1 action',
        'cancel_2': '2 actions',
        'cancel_3': '3 actions',
        'canceled_spend': '❌ Canceled expense ({category}): ${amount} at {time}',
        'canceled_profit': '❌ Canceled income: ${amount} at {time}',
        'no_actions': '❌ No actions to cancel today.',
        'invalid_amount': 'Enter a valid amount (e.g., 50).'
    }
}

# Завантаження даних
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'spends': {}, 'profits': {}, 'users': {}}

# Збереження даних
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Вибір мови користувача
def get_user_language(context, user_id):
    data = load_data()
    return data.get('users', {}).get(user_id, {}).get('language', 'ua')

def set_user_language(context, user_id, lang):
    data = load_data()
    if user_id not in data['users']:
        data['users'][user_id] = {}
    data['users'][user_id]['language'] = lang
    save_data(data)

# Головне меню
async def start(update, context):
    user_id = str(update.effective_chat.id)
    lang = get_user_language(context, user_id)
    keyboard = [
        [InlineKeyboardButton(LANGUAGES[lang]['add_spend'], callback_data='add_spend'),
         InlineKeyboardButton(LANGUAGES[lang]['add_profit'], callback_data='add_profit')],
        [InlineKeyboardButton(LANGUAGES[lang]['add_living'], callback_data='add_living_expense')],
        [InlineKeyboardButton(LANGUAGES[lang]['stats_day'], callback_data='stats_day'),
         InlineKeyboardButton(LANGUAGES[lang]['stats_week'], callback_data='stats_week'),
         InlineKeyboardButton(LANGUAGES[lang]['stats_month'], callback_data='stats_month')],
        [InlineKeyboardButton(LANGUAGES[lang]['balance'], callback_data='balance'),
         InlineKeyboardButton(LANGUAGES[lang]['export'], callback_data='export')],
        [InlineKeyboardButton(LANGUAGES[lang]['graph_day'], callback_data='graph_day'),
         InlineKeyboardButton(LANGUAGES[lang]['graph_month'], callback_data='graph_month')],
        [InlineKeyboardButton(LANGUAGES[lang]['cancel'], callback_data='cancel_last')],
        [InlineKeyboardButton("🇺🇦 UA", callback_data='lang_ua'),
         InlineKeyboardButton("🇷🇺 RU", callback_data='lang_ru'),
         InlineKeyboardButton("🇬🇧 EN", callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(LANGUAGES[lang]['start'], reply_markup=reply_markup)
    logger.info(f"User {user_id} started bot with language {lang}")

# Обробка кнопок
async def button(update, context):
    query = update.callback_query
    await query.answer()
    user_id = str(query.message.chat_id)
    lang = get_user_language(context, user_id)

    if query.data.startswith('lang_'):
        new_lang = query.data.split('_')[1]
        set_user_language(context, user_id, new_lang)
        await start(query, context)
    elif query.data == 'add_spend':
        keyboard = [
            [InlineKeyboardButton(LANGUAGES[lang]['food'], callback_data='category_food'),
             InlineKeyboardButton(LANGUAGES[lang]['transport'], callback_data='category_transport')],
            [InlineKeyboardButton(LANGUAGES[lang]['entertainment'], callback_data='category_entertainment'),
             InlineKeyboardButton(LANGUAGES[lang]['living'], callback_data='add_living_expense')],
            [InlineKeyboardButton(LANGUAGES[lang]['other'], callback_data='category_other')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(LANGUAGES[lang]['choose_category'], reply_markup=reply_markup)
    elif query.data.startswith('category_'):
        category = query.data.split('_')[1]
        context.user_data['category'] = category
        context.user_data['action'] = 'add_spend'
        await query.edit_message_text(LANGUAGES[lang]['enter_spend'].format(category=category))
    elif query.data == 'add_profit':
        await query.edit_message_text(LANGUAGES[lang]['enter_profit'])
        context.user_data['action'] = 'add_profit'
    elif query.data == 'add_living_expense':
        await query.edit_message_text(LANGUAGES[lang]['enter_living'])
        context.user_data['action'] = 'add_living_expense'
    elif query.data == 'stats_day':
        await show_stats(query, context, user_id, 'day')
    elif query.data == 'stats_week':
        await show_stats(query, context, user_id, 'week')
    elif query.data == 'stats_month':
        await show_stats(query, context, user_id, 'month')
    elif query.data == 'balance':
        await show_balance(query, context, user_id)
    elif query.data == 'export':
        await export_data(query, context, user_id)
    elif query.data == 'graph_day':
        await send_graph(query, context, user_id, 'day')
    elif query.data == 'graph_month':
        await send_graph(query, context, user_id, 'month')
    elif query.data == 'cancel_last':
        keyboard = [
            [InlineKeyboardButton(LANGUAGES[lang]['cancel_1'], callback_data='cancel_1'),
             InlineKeyboardButton(LANGUAGES[lang]['cancel_2'], callback_data='cancel_2'),
             InlineKeyboardButton(LANGUAGES[lang]['cancel_3'], callback_data='cancel_3')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(LANGUAGES[lang]['cancel_choose'], reply_markup=reply_markup)
    elif query.data.startswith('cancel_'):
        count = int(query.data.split('_')[1])
        await cancel_last_action(query, context, user_id, count)

# Обробка текстових повідомлень
async def handle_message(update, context):
    user_id = str(update.effective_chat.id)
    lang = get_user_language(context, user_id)
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
            category = context.user_data.get('category', 'other')
            data['spends'][user_id][date].append({'amount': -amount, 'time': now, 'type': 'spend', 'category': category})
            save_data(data)
            await update.message.reply_text(LANGUAGES[lang]['added_spend'].format(category=category, amount=amount, time=now.split(" ")[1]))
        elif action == 'add_profit':
            if user_id not in data['profits']:
                data['profits'][user_id] = {}
            if date not in data['profits'][user_id]:
                data['profits'][user_id][date] = []
            data['profits'][user_id][date].append({'amount': amount, 'time': now, 'type': 'profit'})
            save_data(data)
            await update.message.reply_text(LANGUAGES[lang]['added_profit'].format(amount=amount, time=now.split(" ")[1]))
        elif action == 'add_living_expense':
            if user_id not in data['spends']:
                data['spends'][user_id] = {}
            if date not in data['spends'][user_id]:
                data['spends'][user_id][date] = []
            data['spends'][user_id][date].append({'amount': -amount, 'time': now, 'type': 'living', 'category': 'living'})
            save_data(data)
            await update.message.reply_text(LANGUAGES[lang]['added_living'].format(amount=amount, time=now.split(" ")[1]))

        context.user_data['action'] = None
        context.user_data['category'] = None
        await show_stats(update, context, user_id, 'day')
    except ValueError:
        await update.message.reply_text(LANGUAGES[lang]['invalid_amount'])

# Показ статистики з середнім доходом
async def show_stats(update_or_query, context, user_id, period='day'):
    data = load_data()
    lang = get_user_language(context, user_id)
    now = datetime.now(KYIV_TZ)

    # Обчислення загальних витрат і прибутків
    if period == 'day':
        date = now.strftime('%Y-%m-%d')
        total_spend = sum(item['amount'] for item in data['spends'].get(user_id, {}).get(date, []))
        total_profit = sum(item['amount'] for item in data['profits'].get(user_id, {}).get(date, []))
        days = 1
        title = LANGUAGES[lang]['stats_day_title'].format(date=date)
    elif period == 'week':
        week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
        total_spend = 0
        total_profit = 0
        days = min((now - datetime.strptime(week_start, '%Y-%m-%d').replace(tzinfo=KYIV_TZ)).days + 1, 7)
        for date in data.get('spends', {}).get(user_id, {}).keys():
            if date >= week_start:
                total_spend += sum(item['amount'] for item in data['spends'][user_id][date])
        for date in data.get('profits', {}).get(user_id, {}).keys():
            if date >= week_start:
                total_profit += sum(item['amount'] for item in data['profits'][user_id][date])
        title = LANGUAGES[lang]['stats_week_title'].format(week_start=week_start)
    else:  # month
        month_start = now.replace(day=1).strftime('%Y-%m-%d')
        total_spend = 0
        total_profit = 0
        days = (now - now.replace(day=1)).days + 1
        for date in data.get('spends', {}).get(user_id, {}).keys():
            if date.startswith(now.strftime('%Y-%m')):
                total_spend += sum(item['amount'] for item in data['spends'][user_id][date])
        for date in data.get('profits', {}).get(user_id, {}).keys():
            if date.startswith(now.strftime('%Y-%m')):
                total_profit += sum(item['amount'] for item in data['profits'][user_id][date])
        title = LANGUAGES[lang]['stats_month_title'].format(month=now.strftime("%B %Y"))

    # Обчислення середнього доходу
    avg_day = (total_profit + total_spend) / days if days > 0 else 0
    avg_month = avg_day * 30  # Приблизно 30 днів у місяці

    keyboard = [
        [InlineKeyboardButton(LANGUAGES[lang]['add_spend'], callback_data='add_spend'),
         InlineKeyboardButton(LANGUAGES[lang]['add_profit'], callback_data='add_profit')],
        [InlineKeyboardButton(LANGUAGES[lang]['add_living'], callback_data='add_living_expense')],
        [InlineKeyboardButton(LANGUAGES[lang]['stats_day'], callback_data='stats_day'),
         InlineKeyboardButton(LANGUAGES[lang]['stats_week'], callback_data='stats_week'),
         InlineKeyboardButton(LANGUAGES[lang]['stats_month'], callback_data='stats_month')],
        [InlineKeyboardButton(LANGUAGES[lang]['balance'], callback_data='balance'),
         InlineKeyboardButton(LANGUAGES[lang]['export'], callback_data='export')],
        [InlineKeyboardButton(LANGUAGES[lang]['graph_day'], callback_data='graph_day'),
         InlineKeyboardButton(LANGUAGES[lang]['graph_month'], callback_data='graph_month')],
        [InlineKeyboardButton(LANGUAGES[lang]['cancel'], callback_data='cancel_last')],
        [InlineKeyboardButton("🇺🇦 UA", callback_data='lang_ua'),
         InlineKeyboardButton("🇷🇺 RU", callback_data='lang_ru'),
         InlineKeyboardButton("🇬🇧 EN", callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    response = LANGUAGES[lang]['stats_format'].format(
        title=title, 
        spend=total_spend, 
        profit=total_profit, 
        avg_day=avg_day, 
        avg_month=avg_month
    )
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(response, reply_markup=reply_markup)
    else:
        await update_or_query.edit_message_text(response, reply_markup=reply_markup)

# Показ балансу
async def show_balance(query, context, user_id):
    data = load_data()
    lang = get_user_language(context, user_id)
    total_spend = sum(sum(item['amount'] for item in dates.values()) for dates in data.get('spends', {}).get(user_id, {}).values())
    total_profit = sum(sum(item['amount'] for item in dates.values()) for dates in data.get('profits', {}).get(user_id, {}).values())
    balance = total_profit + total_spend
    response = LANGUAGES[lang]['balance_format'].format(balance=balance, profit=total_profit, spend=total_spend)
    await query.edit_message_text(response)

# Експорт даних у CSV
async def export_data(query, context, user_id):
    data = load_data()
    lang = get_user_language(context, user_id)
    filename = f'finance_{user_id}.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Type', 'Category', 'Amount', 'Time', 'Date'])
        for date, spends in data.get('spends', {}).get(user_id, {}).items():
            for item in spends:
                writer.writerow([item['type'], item.get('category', 'other'), item['amount'], item['time'].split(' ')[1], date])
        for date, profits in data.get('profits', {}).get(user_id, {}).items():
            for item in profits:
                writer.writerow([item['type'], 'profit', item['amount'], item['time'].split(' ')[1], date])
    with open(filename, 'rb') as f:
        await query.message.reply_document(document=f, filename=filename)
    await query.edit_message_text(LANGUAGES[lang]['exported'])

# Графік за день або місяць
async def send_graph(query, context, user_id, period='day'):
    data = load_data()
    lang = get_user_language(context, user_id)
    now = datetime.now(KYIV_TZ)
    if period == 'day':
        date = now.strftime('%Y-%m-%d')
        spends = data.get('spends', {}).get(user_id, {}).get(date, [])
        profits = data.get('profits', {}).get(user_id, {}).get(date, [])
        title = LANGUAGES[lang]['stats_day_title'].format(date=date)
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
        title = LANGUAGES[lang]['stats_month_title'].format(month=now.strftime("%B %Y"))

    times = [item['time'].split(' ')[1] for item in spends + profits]
    amounts = [item['amount'] for item in spends + profits]
    
    if not times:
        await query.edit_message_text(LANGUAGES[lang]['no_data_graph'].format(period=period))
        return
    
    plt.figure(figsize=(10, 5))
    plt.plot(times, amounts, marker='o', linestyle='-', color='b')
    plt.title(title)
    plt.xlabel('Time' if lang == 'en' else 'Час')
    plt.ylabel('Amount ($)' if lang == 'en' else 'Сумма ($)' if lang == 'ru' else 'Сума ($)')
    plt.xticks(rotation=45)
    plt.grid(True)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    await query.message.reply_photo(photo=buf, caption=title)
    buf.close()
    plt.close()
    await query.edit_message_text(LANGUAGES[lang]['graph_sent'])

# Скасування кількох дій
async def cancel_last_action(query, context, user_id, count=1):
    data = load_data()
    lang = get_user_language(context, user_id)
    date = datetime.now(KYIV_TZ).strftime('%Y-%m-%d')
    spends = data.get('spends', {}).get(user_id, {}).get(date, [])
    profits = data.get('profits', {}).get(user_id, {}).get(date, [])

    all_actions = sorted(spends + profits, key=lambda x: x['time'], reverse=True)
    if not all_actions:
        await query.edit_message_text(LANGUAGES[lang]['no_actions'])
        return

    canceled_count = min(count, len(all_actions))
    canceled_items = all_actions[:canceled_count]
    response = f"Скасовано {canceled_count} дій:\n" if lang == 'ua' else f"Отменено {canceled_count} действий:\n" if lang == 'ru' else f"Canceled {canceled_count} actions:\n"
    
    for item in canceled_items:
        if item in spends:
            spends.remove(item)
            response += LANGUAGES[lang]['canceled_spend'].format(category=item.get('category', 'other'), amount=-item['amount'], time=item['time'].split(" ")[1]) + '\n'
        elif item in profits:
            profits.remove(item)
            response += LANGUAGES[lang]['canceled_profit'].format(amount=item['amount'], time=item['time'].split(" ")[1]) + '\n'
    
    data['spends'][user_id][date] = spends
    data['profits'][user_id][date] = profits
    save_data(data)
    
    await query.edit_message_text(response.strip())
    await show_stats(query, context, user_id, 'day')

# Основна функція запуску бота
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()