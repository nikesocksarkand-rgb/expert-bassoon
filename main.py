import telebot
import json
import os
from datetime import datetime

# ========== ВСТАВЬ СВОЙ ТОКЕН ==========
TOKEN = "8764351452:AAEjnki4TqSb4hWZcFVshLOeCnrFNIsIDD8"
# ======================================

bot = telebot.TeleBot(TOKEN)
HISTORY_FILE = "user_history.json"

def load_history(user_id):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            all_data = json.load(f)
            return all_data.get(str(user_id), [])
    return []

def save_history(user_id, history):
    all_data = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            all_data = json.load(f)
    all_data[str(user_id)] = history[-500:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(all_data, f, indent=2)

def calculate_optimal_coeff(coeffs):
    """Вычисляет оптимальный коэффициент для вывода"""
    if not coeffs:
        return 1.5
    
    # Сортируем для вычисления медианы
    sorted_coeffs = sorted(coeffs)
    
    # Среднее
    avg = sum(coeffs) / len(coeffs)
    
    # Медиана
    if len(sorted_coeffs) % 2 == 0:
        median = (sorted_coeffs[len(sorted_coeffs)//2 - 1] + sorted_coeffs[len(sorted_coeffs)//2]) / 2
    else:
        median = sorted_coeffs[len(sorted_coeffs)//2]
    
    # Находим самый частый диапазон
    early = sum(1 for c in coeffs if c < 1.5)
    medium = sum(1 for c in coeffs if 1.5 <= c < 3.0)
    late = sum(1 for c in coeffs if c >= 3.0)
    
    total = len(coeffs)
    early_pct = early / total * 100
    medium_pct = medium / total * 100
    late_pct = late / total * 100
    
    # Рекомендуемый кэф на основе статистики
    if early_pct > 50:
        # Если много ранних крашей — рекомендуем низкий кэф
        recommended = round(median * 0.6, 2)
        if recommended < 1.2:
            recommended = 1.2
        strategy = "🔴 Осторожный (много ранних крашей)"
    elif late_pct > 40:
        # Если много поздних крашей — можно рискнуть
        recommended = round(median * 0.85, 2)
        strategy = "🟢 Рискованный (много поздних крашей)"
    else:
        # Смешанный режим
        recommended = round(median * 0.7, 2)
        strategy = "🟡 Умеренный (смешанный режим)"
    
    # Корректируем, чтобы не выходить за разумные пределы
    if recommended < 1.1:
        recommended = 1.1
    if recommended > 5.0:
        recommended = 5.0
    
    return {
        'recommended': recommended,
        'avg': round(avg, 2),
        'median': round(median, 2),
        'strategy': strategy,
        'early_pct': round(early_pct, 1),
        'medium_pct': round(medium_pct, 1),
        'late_pct': round(late_pct, 1)
    }

def analyze_history(history):
    if len(history) < 10:
        return "❌ Мало данных! Нужно минимум 10 игр."

    recent = history[-50:]
    coeffs = [h['coefficient'] for h in recent]
    
    early = sum(1 for c in coeffs if c < 1.5)
    medium = sum(1 for c in coeffs if 1.5 <= c < 3.0)
    late = sum(1 for c in coeffs if c >= 3.0)
    avg = sum(coeffs) / len(coeffs)

    # Тренд
    if len(coeffs) > 20:
        first = sum(coeffs[:len(coeffs)//2]) / len(coeffs[:len(coeffs)//2])
        second = sum(coeffs[len(coeffs)//2:]) / len(coeffs[len(coeffs)//2:])
        if second > first * 1.1:
            trend = "📈 краши ПОЗЖЕ (можно рискнуть)"
        elif second < first * 0.9:
            trend = "📉 краши РАНЬШЕ (выводи рано)"
        else:
            trend = "➡️ стабильно"
    else:
        trend = "➡️ мало данных"

    # Вычисляем оптимальный кэф
    opt = calculate_optimal_coeff(coeffs)

    early_pct = early / (early + medium + late) * 100
    late_pct = late / (early + medium + late) * 100

    if early_pct > 50:
        signal = "🔴 SHORT (ранний краш)"
        confidence = round(60 + early_pct * 0.3, 1)
        recommend = "ВЫВОДИ РАНО!"
    elif late_pct > 40:
        signal = "🟢 LONG (поздний краш)"
        confidence = round(60 + late_pct * 0.3, 1)
        recommend = "МОЖНО ПОДОЖДАТЬ!"
    else:
        signal = "🟡 NEUTRAL"
        confidence = round(50 + (medium / (early + medium + late)) * 20, 1)
        recommend = "БУДЬ ОСТОРОЖЕН!"

    # ФОРМИРУЕМ ОТВЕТ
    result = f"""
✈️ HIGH FLYER - АНАЛИЗ И ОПТИМАЛЬНЫЙ КЭФ

📊 СТАТИСТИКА:
• Всего игр: {len(history)}
• Средний кэф: {avg:.2f}
• Медиана: {opt['median']}
• Ранние (<1.5): {early} ({opt['early_pct']}%)
• Средние (1.5-3.0): {medium} ({opt['medium_pct']}%)
• Поздние (>3.0): {late} ({opt['late_pct']}%)
• Тренд: {trend}

🎯 СИГНАЛ: {signal}
• Уверенность: {confidence}%
• Стратегия: {opt['strategy']}

🔥 ОПТИМАЛЬНЫЙ КЭФ ДЛЯ ВЫВОДА: x{opt['recommended']}

📌 Рекомендация: {recommend}
"""
    
    if confidence > 75:
        result += "\n⚡ СИЛЬНЫЙ СИГНАЛ! Действуй по оптимальному кэфу!"
    elif confidence > 60:
        result += "\n⚠️ СРЕДНИЙ СИГНАЛ. Следуй оптимальному кэфу, но будь осторожен."
    else:
        result += "\n❌ СЛАБЫЙ СИГНАЛ. Лучше пропустить или выводить на минимальный кэф."
    
    return result

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """
✈️ HIGH FLYER AI ПРЕДИКТОР

📌 Введи коэффициенты через запятую
Пример: 1.35,2.78,3.42,1.12,4.56

🤖 AI сам выберет оптимальный кэф для вывода!
Чем больше данных, тем точнее прогноз.

📊 Команды:
/start - это сообщение
/stats - текущая статистика
/clear - очистить историю
""")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    user_id = message.from_user.id
    history = load_history(user_id)
    if len(history) < 10:
        bot.reply_to(message, f"📊 В истории {len(history)} игр. Нужно минимум 10.")
        return
    bot.reply_to(message, analyze_history(history))

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_id = message.from_user.id
    save_history(user_id, [])
    bot.reply_to(message, "🗑️ История очищена!")

@bot.message_handler(func=lambda message: True)
def handle_coefficients(message):
    user_id = message.from_user.id
    text = message.text.replace(' ', '')
    
    coeffs = []
    for p in text.split(','):
        try:
            c = float(p)
            if 1.0 <= c <= 1000:
                coeffs.append(c)
        except:
            continue
    
    if not coeffs:
        bot.reply_to(message, "❌ Введи числа через запятую")
        return
    
    history = load_history(user_id)
    for c in coeffs:
        history.append({'coefficient': c, 'timestamp': datetime.now().isoformat()})
    save_history(user_id, history)
    
    bot.reply_to(message, f"✅ Добавлено {len(coeffs)} игр!\n\n" + analyze_history(history))

print("🤖 Бот запущен! Он сам выбирает оптимальный кэф!")
bot.infinity_polling()