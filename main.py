import telebot
import json
import os
from datetime import datetime
import sys

# ТОКЕН - ЗАМЕНИ НА СВОЙ!
TOKEN = "8894106518:AAGt2sdDHxxd34pKeIvXOodDoPqKNrJt4no"

# Проверка токена
if TOKEN == "ТВОЙ_ТОКЕН_СЮДА":
    print("❌ ОШИБКА: Ты не заменил токен!")
    sys.exit(1)

try:
    bot = telebot.TeleBot(TOKEN)
    print("✅ Бот подключён")
except Exception as e:
    print(f"❌ Ошибка токена: {e}")
    sys.exit(1)

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

def analyze_history(history):
    if len(history) < 10:
        return "❌ Мало данных! Нужно минимум 10 игр."
    recent = history[-50:]
    coeffs = [h['coefficient'] for h in recent]
    early = sum(1 for c in coeffs if c < 1.5)
    medium = sum(1 for c in coeffs if 1.5 <= c < 3.0)
    late = sum(1 for c in coeffs if c >= 3.0)
    avg = sum(coeffs) / len(coeffs)
    early_pct = early / (early + medium + late) * 100
    late_pct = late / (early + medium + late) * 100
    if early_pct > 50:
        signal = "🔴 SHORT (ранний краш)"
        confidence = round(60 + early_pct * 0.3, 1)
        recommend = "ВЫВОДИ РАНО! Не жди выше x1.5"
    elif late_pct > 40:
        signal = "🟢 LONG (поздний краш)"
        confidence = round(60 + late_pct * 0.3, 1)
        recommend = "МОЖНО ПОДОЖДАТЬ! Есть шанс на x3+"
    else:
        signal = "🟡 NEUTRAL"
        confidence = round(50 + (medium / (early + medium + late)) * 20, 1)
        recommend = "ВЫВОДИ НА x1.5 или пропусти"
    result = f"""
✈️ HIGH FLYER - АНАЛИЗ
📊 Всего игр: {len(history)}
📊 Средний коэф: {avg:.2f}
📊 Ранние: {early} | Средние: {medium} | Поздние: {late}
🎯 СИГНАЛ: {signal}
   Уверенность: {confidence}%
   {recommend}
"""
    return result

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✈️ HIGH FLYER AI ПРЕДИКТОР\nВведи коэффициенты через запятую")

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

print("🤖 Бот запущен и готов к работе!")
try:
    bot.infinity_polling()
except Exception as e:
    print(f"❌ Ошибка при работе бота: {e}")
    sys.exit(1)
