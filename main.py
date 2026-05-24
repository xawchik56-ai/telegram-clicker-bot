import telebot
import json
import os
import threading
import time
from random import choice

import os
TOKEN = os.environ.get("BOT_TOKEN", "8867899616:AAFQMAW5CxHTxrTNH55M_yPgR4deI4PVj_4")
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

DEFAULT_USER = {"coins": 0, "power": 1, "auto": 0, "lvl": 1, "xp": 0, "clicks": 0, "autolvl": 0, "ups": {}, "coll": [], "daily": 0, "msgid": None}

def get_user(user_id):
    data = load_data()
    uid = str(user_id)
    if uid not in data or "power" not in data[uid]:
        data[uid] = dict(DEFAULT_USER)
        save_data(data)
    return data[uid]

def save_user(user_id, d):
    data = load_data()
    data[str(user_id)] = d
    save_data(data)

UPGRADES = [
    ("better", "Усилитель", 50, 2),
    ("ultra", "Ультра", 200, 5),
    ("mega", "Мега", 1000, 15),
    ("god", "Божественный", 10000, 100),
]
AUTOS = [
    (1, "Авто I", 100, 1),
    (2, "Авто II", 500, 5),
    (3, "Авто III", 2500, 25),
    (4, "Авто IV", 12000, 120),
    (5, "Авто V", 50000, 500),
]
COLLS = [
    ("coin", "Монетка", 500, "🪙"),
    ("gem", "Камень", 1500, "💎"),
    ("ring", "Кольцо", 3000, "💍"),
    ("trophy", "Трофей", 6000, "🏆"),
    ("crown", "Корона", 15000, "👑"),
    ("star", "Звезда", 30000, "⭐"),
    ("moon", "Луна", 60000, "🌙"),
]

def game_kb():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("👆 КЛИК!", callback_data="click"))
    kb.row(telebot.types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"), telebot.types.InlineKeyboardButton("🎁 Коллекция", callback_data="coll"))
    kb.row(telebot.types.InlineKeyboardButton("📊 Профиль", callback_data="prof"), telebot.types.InlineKeyboardButton("🎲 Казино", callback_data="cas"))
    kb.add(telebot.types.InlineKeyboardButton("📅 Бонус", callback_data="daily"))
    return kb

def game_text(d):
    return (
        f"🎮 КЛИКЕР\n\n"
        f"💰 {d['coins']} монет\n"
        f"👆 Сила: {d['power']} | ⚡ Авто: {d['auto']}/5с\n"
        f"🎖 Уровень {d['lvl']} | 🔄 {d['clicks']} кликов\n\n"
        f"ЖМИ КНОПКУ ВНИЗУ!"
    )

def show_game(chat_id, uid):
    d = get_user(uid)
    txt = game_text(d)
    if d["msgid"]:
        try:
            bot.edit_message_text(txt, chat_id, d["msgid"], reply_markup=game_kb())
            return
        except Exception as e:
            print(f"edit err: {e}")
    msg = bot.send_message(chat_id, txt, reply_markup=game_kb())
    d["msgid"] = msg.message_id
    save_user(uid, d)

@bot.message_handler(commands=["start"])
def start(m):
    get_user(m.from_user.id)
    show_game(m.chat.id, m.from_user.id)

@bot.callback_query_handler(func=lambda c: True)
def all_cb(c):
    uid = c.from_user.id
    d = get_user(uid)
    data = c.data
    print(f"CALLBACK: {data} from user {uid}")

    if data == "click":
        earned = d["power"]
        d["coins"] += earned
        d["clicks"] += 1
        d["xp"] += 1
        if d["xp"] >= d["lvl"] * 50:
            d["lvl"] += 1
            d["coins"] += d["lvl"] * 10
        save_user(uid, d)
        try:
            bot.edit_message_text(game_text(d), c.message.chat.id, c.message.message_id, reply_markup=game_kb())
        except:
            show_game(c.message.chat.id, uid)
        bot.answer_callback_query(c.id, f"+{earned}")
        return

    if data == "shop":
        kb = telebot.types.InlineKeyboardMarkup(row_width=1)
        kb.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
        for id_, name, cost, pow_ in UPGRADES:
            label = f"{'✅' if id_ in d['ups'] else '🔹'} {name} x{pow_} — {cost}"
            kb.add(telebot.types.InlineKeyboardButton(label, callback_data=f"buyup_{id_}"))
        for lvl, name, cost, pow_ in AUTOS:
            label = f"{'✅' if d['autolvl'] >= lvl else '🔹'} {name} +{pow_}/5с — {cost}"
            kb.add(telebot.types.InlineKeyboardButton(label, callback_data=f"buyauto_{lvl}"))
        bot.edit_message_text(f"🛒 МАГАЗИН | Баланс: {d['coins']}", c.message.chat.id, c.message.message_id, reply_markup=kb)
        return

    if data == "coll":
        kb = telebot.types.InlineKeyboardMarkup(row_width=1)
        kb.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
        for id_, name, cost, emoji in COLLS:
            label = f"{'✅' if id_ in d['coll'] else emoji} {name} — {cost}"
            kb.add(telebot.types.InlineKeyboardButton(label, callback_data=f"buycoll_{id_}"))
        lst = "\n".join(f"{emoji} {name}" for id_, name, cost, emoji in COLLS if id_ in d["coll"]) or "Пусто"
        bot.edit_message_text(f"🎁 КОЛЛЕКЦИЯ {len(d['coll'])}/{len(COLLS)}\n\n{lst}", c.message.chat.id, c.message.message_id, reply_markup=kb)
        return

    if data == "prof":
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
        bot.edit_message_text(
            f"📊 ПРОФИЛЬ\n\n🎖 Уровень: {d['lvl']}\n⭐ XP: {d['xp']}/{d['lvl']*50}\n💰 Монет: {d['coins']}\n👆 Сила: {d['power']}\n⚡ Авто: {d['auto']}/5с\n🔄 Кликов: {d['clicks']}\n📦 Апгрейдов: {len(d['ups'])}\n🎁 Коллекция: {len(d['coll'])}/{len(COLLS)}",
            c.message.chat.id, c.message.message_id, reply_markup=kb)
        return

    if data == "cas":
        kb = telebot.types.InlineKeyboardMarkup(row_width=2)
        kb.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
        for bet in [10, 50, 100, 500]:
            kb.add(telebot.types.InlineKeyboardButton(f"Ставка {bet}", callback_data=f"casino_{bet}"))
        bot.edit_message_text(f"🎲 КАЗИНО | {d['coins']} монет\nОрёл или решка — x2!", c.message.chat.id, c.message.message_id, reply_markup=kb)
        return

    if data == "daily":
        now = time.time()
        if now - d["daily"] < 86400:
            rem = int(86400 - (now - d["daily"]))
            bot.answer_callback_query(c.id, f"Жди {rem//3600}ч {(rem%3600)//60}м")
            return
        bonus = 100 + d["lvl"] * 20
        d["coins"] += bonus
        d["daily"] = now
        save_user(uid, d)
        bot.answer_callback_query(c.id, f"Бонус +{bonus}!", show_alert=True)
        show_game(c.message.chat.id, uid)
        return

    if data == "back":
        show_game(c.message.chat.id, uid)
        return

    if data.startswith("buyup_"):
        id_ = data.split("_", 1)[1]
        item = next((x for x in UPGRADES if x[0] == id_), None)
        if not item: return
        if id_ in d["ups"]:
            bot.answer_callback_query(c.id, "Уже куплено!")
            return
        if d["coins"] < item[2]:
            bot.answer_callback_query(c.id, "Не хватает монет!")
            return
        d["coins"] -= item[2]
        d["power"] *= item[3]
        d["ups"][id_] = True
        save_user(uid, d)
        bot.answer_callback_query(c.id, f"{item[1]} куплен!")
        show_game(c.message.chat.id, uid)
        return

    if data.startswith("buyauto_"):
        lvl = int(data.split("_", 1)[1])
        item = next((x for x in AUTOS if x[0] == lvl), None)
        if not item: return
        if d["autolvl"] >= lvl:
            bot.answer_callback_query(c.id, "Уже куплено!")
            return
        if d["autolvl"] != lvl - 1:
            bot.answer_callback_query(c.id, "Купи предыдущий!")
            return
        if d["coins"] < item[2]:
            bot.answer_callback_query(c.id, "Не хватает монет!")
            return
        d["coins"] -= item[2]
        d["auto"] += item[3]
        d["autolvl"] = lvl
        save_user(uid, d)
        bot.answer_callback_query(c.id, f"{item[1]} куплен!")
        show_game(c.message.chat.id, uid)
        return

    if data.startswith("buycoll_"):
        id_ = data.split("_", 1)[1]
        item = next((x for x in COLLS if x[0] == id_), None)
        if not item: return
        if id_ in d["coll"]:
            bot.answer_callback_query(c.id, "Уже есть!")
            return
        if d["coins"] < item[2]:
            bot.answer_callback_query(c.id, "Не хватает монет!")
            return
        d["coins"] -= item[2]
        d["coll"].append(id_)
        d["xp"] += 10
        if d["xp"] >= d["lvl"] * 50:
            d["lvl"] += 1
        save_user(uid, d)
        if len(d["coll"]) == len(COLLS):
            d["coins"] += 5000
            save_user(uid, d)
            bot.answer_callback_query(c.id, "ВСЯ КОЛЛЕКЦИЯ! +5000!", show_alert=True)
        else:
            bot.answer_callback_query(c.id, f"{item[3]} {item[1]} получен!")
        show_game(c.message.chat.id, uid)
        return

    if data.startswith("casino_"):
        bet = int(data.split("_", 1)[1])
        if d["coins"] < bet:
            bot.answer_callback_query(c.id, "Не хватает монет!")
            return
        d["coins"] -= bet
        coin = choice(["Орёл 🦅", "Решка 🪙"])
        pick = choice(["Орёл 🦅", "Решка 🪙"])
        win = coin == pick
        if win:
            d["coins"] += bet * 2
            d["xp"] += 5
            save_user(uid, d)
            bot.answer_callback_query(c.id, f"{coin}! Ты выбрал {pick}! +{bet*2}!", show_alert=True)
        else:
            d["xp"] += 1
            save_user(uid, d)
            bot.answer_callback_query(c.id, f"{coin}! Ты выбрал {pick}! -{bet}!", show_alert=True)
        show_game(c.message.chat.id, uid)
        return

def auto_loop():
    while True:
        try:
            data = load_data()
            for uid, d in data.items():
                if d.get("auto", 0) > 0:
                    d["coins"] += d["auto"]
                    d["xp"] += 1
                    if d["xp"] >= d["lvl"] * 50:
                        d["lvl"] += 1
                    save_user(uid, d)
        except:
            pass
        time.sleep(5)

threading.Thread(target=auto_loop, daemon=True).start()

if __name__ == "__main__":
    print("Бот запущен. Смотри консоль на логи нажатий...")
    bot.infinity_polling()
