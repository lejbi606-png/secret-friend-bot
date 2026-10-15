import requests
import time
import json
import os
import random
import threading

TOKEN = "8918941174:AAE6VYeW4cPTsGInySM0W_4J1Dq6XmpPO4M"
API = "https://api.telegram.org/bot" + TOKEN
SAVE_FILE = "secret_friend.json"
offset = 0

ADMIN_PASSWORD = "12345"

чаты = {}
BOT_USERNAME = ""

КОМПЛИМЕНТЫ = [
    "Ты сегодня просто огонь", "С тобой всегда весело", "Ты очень умный, не забывай об этом",
    "Твоя улыбка делает день лучше", "Ты классный друг, спасибо что ты есть",
    "Твоя энергия заражает всех вокруг", "Ты умеешь поддержать в нужный момент",
    "С тобой не страшно ничего", "Ты очень талантливый", "Твоё чувство юмора — топ",
    "Ты делаешь этот мир лучше", "С тобой время летит незаметно", "Ты настоящий друг",
    "Твоя доброта бесценна", "Ты вдохновляешь меня", "С тобой любое дело по плечу",
    "Ты очень отзывчивый", "Твоя поддержка много значит", "Ты классно выглядишь сегодня",
    "Ты всегда найдёшь нужные слова", "С тобой интересно болтать", "Ты очень честный",
    "Твоя искренность подкупает", "Ты заслуживаешь всего лучшего", "Ты очень стильный",
    "С тобой весело даже в дождь", "Ты настоящий лидер", "Твоя настойчивость впечатляет",
    "Ты умеешь мечтать", "Ты очень внимательный", "С тобой уютно молчать",
    "Ты умеешь слушать", "Твои идеи — огонь", "Ты творческая личность",
    "У тебя отличный вкус", "Ты очень терпеливый", "С тобой хочется дружить",
    "Ты надёжный, как скала", "Твоя улыбка заразительна", "Ты умеешь радовать",
    "Ты невероятно крутой", "С тобой любая компания — праздник", "Ты очень мудрый",
    "Твоё мнение важно", "Ты заботишься о других", "Ты умеешь признавать ошибки",
    "Ты растёшь и становишься лучше", "Ты достоин восхищения",
    "С тобой я чувствую себя собой", "Ты — лучший!",
]

ЗНАЧКИ = {"👑": "Главный админ", "🛡": "Помощник", "⭐": "Проверенный", "🧪": "Тестировщик"}

# ============ TELEGRAM ============
def api(method, payload):
    try:
        r = requests.post(API + "/" + method, json=payload, timeout=(10, 40))
        return r.json()
    except Exception as e:
        print(method, "error:", e)
        return {}

def send(chat_id, text, keyboard=None):
    p = {"chat_id": chat_id, "text": text}
    if keyboard: p["reply_markup"] = keyboard
    r = api("sendMessage", p)
    if not r.get("ok"): print("send FAIL:", r)
    return r

def answer_cb(cb_id, text="", alert=False):
    api("answerCallbackQuery", {"callback_query_id": cb_id, "text": text, "show_alert": alert})

def kb(rows):
    return {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in rows]}

# ============ ЗАГРУЗКА ============
def load():
    global чаты
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                чаты = {int(k): v for k, v in json.load(f).items()}
        except: чаты = {}

def save():
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in чаты.items()}, f, ensure_ascii=False, indent=2)
    except: pass

def новый_чат():
    return {"игроки": {}, "ожидание": {}, "история": {},
            "список_msg_id": None, "дуэли": [], "значки": {}}

def получить_чат(cid):
    c = чаты.get(cid)
    if not c:
        c = новый_чат(); чаты[cid] = c
    if "значки" not in c: c["значки"] = {}
    if "дуэли" not in c: c["дуэли"] = []
    if "история" not in c: c["история"] = {}
    return c

def звание(очки):
    if очки >= 100: return "Хранитель тайн"
    if очки >= 61:  return "Легенда чата"
    if очки >= 31:  return "Душа компании"
    if очки >= 11:  return "Друг"
    return "Новичок"

def значок_игрока(c, uid):
    return c.get("значки", {}).get(str(uid), "")

def место_в_рейтинге(c, uid):
    sp = sorted(c["игроки"].items(), key=lambda x: -x[1].get("очки", 0))
    for i, (u, p) in enumerate(sp):
        if u == str(uid):
            return i + 1, len(sp)
    return len(sp), len(sp)

# ============ СПИСОК ============
def кнопки_списка(chat_id):
    url = f"https://t.me/{BOT_USERNAME}?start=reg_{chat_id}"
    return kb([
        [("📝 Зарегистрироваться", url)],
        [("👥 Список участников", "refresh")],
        [("🏆 Топ недели", "top")],
        [("🌍 Топ за всё время", "top_all")],
        [("👤 Мой профиль", "profile")],
        [("⚔ Дуэль", "duel")],
        [("🤝 Реферальная ссылка", "ref")],
        [("❓ Помощь", "help")]
    ])

def текст_списка(chat_id):
    c = получить_чат(chat_id)
    if not c["игроки"]:
        return "👥 Участники\n\nПока никто не зарегистрирован.\n\n📝 Жми «Зарегистрироваться»!"
    sp = sorted(c["игроки"].items(), key=lambda x: -x[1].get("очки", 0))
    s = f"👥 Участники ({len(sp)}):\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, p) in enumerate(sp):
        знак = значок_игрока(c, uid)
        префикс = f"{знак} " if знак else ""
        m = medals[i] if i < 3 else f"{i+1}."
        s += f"{m} {префикс}{p['имя']} — {p.get('очки', 0)} очк.\n"
    s += "\n📝 /send_comp — комплимент\n⚔ /duel Имя — дуэль"
    return s

def топ_текст(chat_id):
    c = получить_чат(chat_id)
    if not c["игроки"]: return "🏆 Топ недели\n\nПока никого."
    sp = sorted(c["игроки"].items(), key=lambda x: -x[1].get("очки", 0))[:10]
    s = "🏆 Топ недели:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, p) in enumerate(sp):
        знак = значок_игрока(c, uid)
        префикс = f"{знак} " if знак else ""
        m = medals[i] if i < 3 else f"{i+1}."
        s += f"{m} {префикс}{p['имя']} — {p.get('очки', 0)} очк. [{звание(p.get('очки', 0))}]\n"
    return s

def топ_всё_время(chat_id):
    c = получить_чат(chat_id)
    if not c["игроки"]: return "🌍 Топ за всё время\n\nПока никого."
    sp = sorted(c["игроки"].items(), key=lambda x: -x[1].get("очки_всего", 0))[:10]
    s = "🌍 Топ за всё время:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, p) in enumerate(sp):
        знак = значок_игрока(c, uid)
        префикс = f"{знак} " if знак else ""
        m = medals[i] if i < 3 else f"{i+1}."
        s += f"{m} {префикс}{p['имя']} — {p.get('очки_всего', 0)} очк.\n"
    return s

def профиль_текст(chat_id, uid):
    c = получить_чат(chat_id)
    p = c["игроки"].get(str(uid))
    if not p: return "❌ Ты не зарегистрирован. Напиши /start в чате."
    место, всего = место_в_рейтинге(c, uid)
    знак = значок_игрока(c, uid)
    имя_с_значком = f"{знак} {p['имя']}" if знак else p['имя']
    return (f"👤 Профиль: {имя_с_значком}\n\n"
            f"🏆 Очки (неделя): {p.get('очки', 0)}\n"
            f"🌍 Очки (всего): {p.get('очки_всего', 0)}\n"
            f"📊 Место: {место} из {всего}\n"
            f"🎖 Звание: {звание(p.get('очки_всего', 0))}\n\n"
            f"💌 Отправлено: {p.get('отправлено', 0)}\n"
            f"📥 Получено: {p.get('получено', 0)}\n"
            f"🎯 Угадали тебя: {p.get('угадали', 0)} раз")

def обновить_список(chat_id):
    c = получить_чат(chat_id)
    old = c.get("список_msg_id")
    if old:
        try: api("deleteMessage", {"chat_id": chat_id, "message_id": old})
        except: pass
    r = send(chat_id, текст_списка(chat_id), кнопки_списка(chat_id))
    msg_id = r.get("result", {}).get("message_id")
    if msg_id:
        c["список_msg_id"] = msg_id; save()
        try: api("pinChatMessage", {"chat_id": chat_id, "message_id": msg_id, "disable_notification": True})
        except: pass

def реф_ссылка(uid, chat_id):
    return f"https://t.me/{BOT_USERNAME}?start=ref_{chat_id}_{uid}"

# ============ ДУЭЛИ ============
def создать_дуэль(chat_id, uid1, uid2):
    c = получить_чат(chat_id)
    d = {"игрок1": str(uid1), "игрок2": str(uid2), "очки1": 0, "очки2": 0,
         "старт": time.time(), "завершена": False}
    c["дуэли"].append(d); idx = len(c["дуэли"]) - 1; save()
    threading.Thread(target=таймер_дуэли, args=(chat_id, idx), daemon=True).start()
    return d

def таймер_дуэли(chat_id, idx):
    time.sleep(24 * 60 * 60)
    try:
        c = получить_чат(chat_id)
        if idx >= len(c["дуэли"]): return
        d = c["дуэли"][idx]
        if d.get("завершена"): return
        d["завершена"] = True
        имя1 = c["игроки"].get(d["игрок1"], {}).get("имя", "???")
        имя2 = c["игроки"].get(d["игрок2"], {}).get("имя", "???")
        if d["очки1"] > d["очки2"]: поб = d["игрок1"]
        elif d["очки2"] > d["очки1"]: поб = d["игрок2"]
        else: поб = None
        if поб:
            c["игроки"][поб]["очки"] = c["игроки"][поб].get("очки", 0) + 20
            c["игроки"][поб]["очки_всего"] = c["игроки"][поб].get("очки_всего", 0) + 20
            send(chat_id, f"⚔ ДУЭЛЬ ЗАВЕРШЕНА!\n\n{имя1} vs {имя2}\n📊 {d['очки1']} : {d['очки2']}\n\n🏆 Победитель: {c['игроки'][поб]['имя']} — +20 очков!")
            send(int(поб), "🎉 Ты выиграл дуэль! +20 очков")
        else:
            send(chat_id, f"⚔ ДУЭЛЬ ЗАВЕРШЕНА!\n\n{имя1} vs {имя2}\n📊 {d['очки1']} : {d['очки2']}\n\n🤝 Ничья!")
        save()
    except Exception as e:
        print("Ошибка дуэли:", e)

def учесть_комплимент_в_дуэли(chat_id, кому_uid):
    c = получить_чат(chat_id)
    for d in c["дуэли"]:
        if d.get("завершена"): continue
        if str(кому_uid) == d["игрок1"]: d["очки1"] += 1
        elif str(кому_uid) == d["игрок2"]: d["очки2"] += 1
    save()

# ============ АДМИН ============
def админ_меню(uid, chat_id):
    send(uid, f"👑 Админ-меню\n\nЧат ID: {chat_id}\n\nВыбери действие:",
         kb([
             [("🎖 Выдать значок", f"admin_icon_{chat_id}")],
             [("📊 Статистика", f"admin_stats_{chat_id}")],
             [("❌ Закрыть", "admin_close")]
         ]))

def меню_значков(chat_id, target_uid):
    return kb([
        [("👑 Главный админ", f"seticon_👑_{chat_id}_{target_uid}")],
        [("🛡 Помощник", f"seticon_🛡_{chat_id}_{target_uid}")],
        [("⭐ Проверенный", f"seticon_⭐_{chat_id}_{target_uid}")],
        [("🧪 Тестировщик", f"seticon_🧪_{chat_id}_{target_uid}")],
        [("❌ Убрать значок", f"seticon_❌_{chat_id}_{target_uid}")],
        [("↩ Назад", f"admin_back_{chat_id}")]
    ])

# ============ ЛИЧКА ============
def обработка_лички(uid, text, payload=None):
    low = text.strip().lower()

    # /admin без payload — просим прийти из чата
    if low == "/admin" and not payload:
        send(uid, "i️ Чтобы открыть админку, напиши /admin в группе, где хочешь управлять игроками.")
        return

    # payload admin_CHATID — открываем админку для конкретного чата
    if payload and payload.startswith("admin_"):
        chat_id = int(payload.replace("admin_", ""))
        c = получить_чат(chat_id)
        c["ожидание"][str(uid)] = f"admin_pass_{chat_id}"
        save()
        send(uid, "🔐 Введи пароль админа:")
        return

    # проверка пароля
    for cid, c in чаты.items():
        ожидание = c.get("ожидание", {}).get(str(uid))
        if ожидание and ожидание.startswith("admin_pass_"):
            chat_id = int(ожидание.replace("admin_pass_", ""))
            if text.strip() == ADMIN_PASSWORD:
                del c["ожидание"][str(uid)]; save()
                админ_меню(uid, chat_id)
            else:
                del c["ожидание"][str(uid)]; save()
                send(uid, "❌ Неверный пароль.")
            return

    # deep-link регистрация/комплимент/реферал
    if payload:
        if payload.startswith("reg_"):
            chat_id = int(payload.replace("reg_", ""))
            c = получить_чат(chat_id)
            c["ожидание"][str(uid)] = f"reg_{chat_id}"; save()
            send(uid, "📝 Напиши своё имя (только бот увидит):")
            return
        if payload.startswith("comp_"):
            chat_id = int(payload.replace("comp_", ""))
            c = получить_чат(chat_id)
            c["ожидание"][str(uid)] = f"comp_{chat_id}"; save()
            send(uid, "💌 Напиши имя того, кому хочешь отправить комплимент:")
            return
        if payload.startswith("ref_"):
            parts = payload.split("_")
            chat_id = int(parts[1]); реферер = int(parts[2])
            c = получить_чат(chat_id)
            c["ожидание"][str(uid)] = f"ref_{chat_id}_{реферер}"; save()
            send(uid, "📝 Ты пришёл по приглашению! Напиши своё имя:")
            return

    # /start
    if low == "/start" and not payload:
        keyboard = kb([[("➕ Добавить в чат", f"https://t.me/{BOT_USERNAME}?startgroup=true")]])
        send(uid,
             "👋 Привет! Я Тайный Друг 🎭\n\n"
             "🎯 Зачем: отправляй анонимные комплименты друзьям.\n"
             "🏆 Цель: стать «Душой компании».\n\n"
             "📋 Как играть:\n1️⃣ Добавь меня в чат\n2️⃣ Жми Старт\n3️⃣ Регистрируйся\n"
             "4️⃣ Отправляй комплименты\n5️⃣ Соревнуйся в топе\n\n"
             "⚔ Дуэли, рефералы, топы!\n🤝 Скоро: кланы!\n\n👇 Добавь меня:",
             keyboard)
        return

    if low == "/guess":
        for cid, c in чаты.items():
            история = c.get("история", {}).get(str(uid), [])
            last = None
            for h in reversed(история):
                if not h.get("угадано"): last = h; break
            if last:
                c["ожидание"][str(uid)] = f"guess_{cid}_{last['от']}"; save()
                варианты = [v["имя"] for k, v in c["игроки"].items() if int(k) != uid]
                send(uid, f"🤔 Кто отправил последний комплимент?\n\nВарианты: {', '.join(варианты)}\n\nНапиши имя.")
                return
        send(uid, "У тебя нет неразгаданных комплиментов.")
        return

    if low == "/help":
        send(uid, "📖 Команды:\n\nВ чате:\n• /send_comp\n• /duel Имя\n• /players\n• /admin\n\nВ личке:\n• /guess")
        return

    # ожидания
    for cid, c in чаты.items():
        ожидание = c.get("ожидание", {}).get(str(uid))
        if not ожидание: continue

        if ожидание.startswith("reg_"):
            имя = text.strip()[:20]
            if str(uid) not in c["игроки"]:
                c["игроки"][str(uid)] = {"имя": имя, "очки": 0, "очки_всего": 0,
                                          "получено": 0, "отправлено": 0, "угадали": 0}
            else:
                c["игроки"][str(uid)]["имя"] = имя
            del c["ожидание"][str(uid)]; save()
            send(uid, f"✅ Готово, {имя}!\n\nВернись в чат.")
            обновить_список(cid); return

        if ожидание.startswith("ref_"):
            parts = ожидание.split("_"); chat_id = int(parts[1]); реферер = int(parts[2])
            имя = text.strip()[:20]
            c["игроки"][str(uid)] = {"имя": имя, "очки": 0, "очки_всего": 0,
                                      "получено": 0, "отправлено": 0, "угадали": 0}
            if str(реферер) in c["игроки"]:
                c["игроки"][str(реферер)]["очки"] = c["игроки"][str(реферер)].get("очки", 0) + 5
                c["игроки"][str(реферер)]["очки_всего"] = c["игроки"][str(реферер)].get("очки_всего", 0) + 5
                send(реферер, "🎉 По твоей ссылке пришёл друг! +5 очков")
            del c["ожидание"][str(uid)]; save()
            send(uid, f"✅ Готово, {имя}!\n\nВернись в чат.")
            обновить_список(chat_id); return

        if ожидание.startswith("comp_"):
            target_uid = None
            for k, v in c["игроки"].items():
                if v["имя"].lower() == text.strip().lower():
                    target_uid = int(k); break
            if not target_uid:
                send(uid, f"❌ «{text.strip()}» не найден.")
                del c["ожидание"][str(uid)]; save(); return
            if target_uid == uid:
                send(uid, "😄 Себе комплимент не отправить!")
                del c["ожидание"][str(uid)]; save(); return
            c["ожидание"][str(uid)] = f"choose_{cid}_{target_uid}"; save()
            send(uid, f"Кому: {c['игроки'][str(target_uid)]['имя']}\n\nКак отправить?",
                 kb([
                     [("🎲 Случайный", f"rand_{cid}_{target_uid}")],
                     [("✍️ Написать свой", f"own_{cid}_{target_uid}")]
                 ]))
            return

        if ожидание.startswith("ownmsg_"):
            parts = ожидание.split("_")
            chat_id = int(parts[1]); target_uid = parts[2]
            текст_комплимента = text.strip()[:200]
            if not текст_комплимента:
                send(uid, "❌ Пустой комплимент."); return
            c["игроки"][str(uid)]["очки"] = c["игроки"][str(uid)].get("очки", 0) + 1
            c["игроки"][str(uid)]["очки_всего"] = c["игроки"][str(uid)].get("очки_всего", 0) + 1
            c["игроки"][str(uid)]["отправлено"] = c["игроки"][str(uid)].get("отправлено", 0) + 1
            c["игроки"][str(target_uid)]["получено"] = c["игроки"][str(target_uid)].get("получено", 0) + 1
            c["история"].setdefault(str(target_uid), [])
            c["история"][str(target_uid)].append({"от": uid, "текст": текст_комплимента, "угадано": False})
            учесть_комплимент_в_дуэли(chat_id, int(target_uid))
            del c["ожидание"][str(uid)]; save()
            send(uid, "✅ Комплимент отправлен! +1 очко")
            send(int(target_uid), f"💌 Тебе анонимный комплимент:\n\n«{текст_комплимента}»\n\nХочешь угадать? /guess")
            return

        if ожидание.startswith("guess_"):
            parts = ожидание.split("_"); автор = int(parts[2])
            имя_автора = c["игроки"].get(str(автор), {}).get("имя", "")
            история = c["история"].get(str(uid), [])
            if text.strip().lower() == имя_автора.lower():
                for h in reversed(история):
                    if not h.get("угадано"): h["угадано"] = True; break
                c["игроки"][str(uid)]["очки"] = c["игроки"][str(uid)].get("очки", 0) + 2
                c["игроки"][str(uid)]["очки_всего"] = c["игроки"][str(uid)].get("очки_всего", 0) + 2
                c["игроки"][str(автор)]["очки"] = c["игроки"][str(автор)].get("очки", 0) + 2
                c["игроки"][str(автор)]["очки_всего"] = c["игроки"][str(автор)].get("очки_всего", 0) + 2
                c["игроки"][str(автор)]["угадали"] = c["игроки"][str(автор)].get("угадали", 0) + 1
                del c["ожидание"][str(uid)]; save()
                send(uid, f"🎉 Точно! Это был(а) {имя_автора}! +2 очка")
                send(автор, f"👀 Тебя раскрыли! +2 очка")
            else:
                c["игроки"][str(автор)]["очки"] = c["игроки"][str(автор)].get("очки", 0) + 3
                c["игроки"][str(автор)]["очки_всего"] = c["игроки"][str(автор)].get("очки_всего", 0) + 3
                send(uid, "❌ Не угадал. Автор остался в тайне. +3 очка автору.")
                send(автор, "😎 Ты остался загадкой! +3 очка")
                del c["ожидание"][str(uid)]; save()
            return

    send(uid, "Не понял. /start")

# ============ ГРУППА ============
def обработка_группы(chat_id, uid, text):
    print(f"[ГРУППА] chat={chat_id} uid={uid} text={text!r}")
    low = text.strip().lower()
    c = получить_чат(chat_id)

    if low == "/start":
        send(chat_id,
             "💌 Тайный Друг\n\n🎯 Зачем: анонимные комплименты друзьям.\n"
             "🏆 Цель: стать «Душой компании».\n\n"
             "⚔ Дуэли, рефералы, топы!\n🤝 Скоро: кланы!\n\n👇 Жми:",
             кнопки_списка(chat_id))
        return

    if low == "/admin":
        url = f"https://t.me/{BOT_USERNAME}?start=admin_{chat_id}"
        send(chat_id, "👑 Открой админку в личке:",
             kb([[("🎛 Открыть админку", url)]]))
        return

    if low == "/send_comp":
        url = f"https://t.me/{BOT_USERNAME}?start=comp_{chat_id}"
        send(chat_id, "💌 Жми кнопку:",
             kb([[("💌 Отправить комплимент", url)]]))
        return

    if low.startswith("/duel"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send(chat_id, "❌ Напиши: /duel Имя"); return
        имя = parts[1].strip().lower()
        target = None
        for k, v in c["игроки"].items():
            if v["имя"].lower() == имя: target = k; break
        if not target:
            send(chat_id, f"❌ «{имя}» не найден."); return
        if target == str(uid):
            send(chat_id, "😄 Себе вызов не бросить!"); return
        if str(uid) not in c["игроки"]:
            send(chat_id, "❌ Сначала /start"); return
        for d in c["дуэли"]:
            if d.get("завершена"): continue
            if str(uid) in (d["игрок1"], d["игрок2"]) or target in (d["игрок1"], d["игрок2"]):
                send(chat_id, "❌ Один из вас уже в дуэли."); return
        создать_дуэль(chat_id, int(uid), int(target))
        имя1 = c["игроки"][str(uid)]["имя"]; имя2 = c["игроки"][target]["имя"]
        send(chat_id, f"⚔ ДУЭЛЬ!\n\n{имя1} vs {имя2}\n\n📊 За 24 часа больше комплиментов.\n🏆 Победитель: +20 очков!")
        return

    if low == "/players":
        send(chat_id, текст_списка(chat_id), кнопки_списка(chat_id)); return

    if low == "/help":
        send(chat_id, "📖 Команды:\n/start — меню\n/send_comp — комплимент\n/duel Имя — дуэль\n/players — список\n/admin — админка")
        return

# ============ ЗАПУСК ============
load()
me = api("getMe", {})
BOT_USERNAME = me.get("result", {}).get("username", "")
print(f"Бот запущен: @{BOT_USERNAME}")

while True:
    try:
        r = requests.get(API + "/getUpdates",
                         params={"offset": offset, "timeout": 20,
                                 "allowed_updates": '["message","callback_query","my_chat_member"]'},
                         timeout=25)
        data = r.json()
        if not data.get("ok"):
            print("Err:", data); time.sleep(2); continue

        for upd in data["result"]:
            offset = upd["update_id"] + 1

            mcm = upd.get("my_chat_member")
            if mcm:
                chat = mcm["chat"]; new_status = mcm["new_chat_member"]["status"]; chat_id = chat["id"]
                if chat_id < 0 and new_status in ("member", "administrator"):
                    получить_чат(chat_id)
                    send(chat_id,
                         "👋 Привет, ребята!\n\nЯ — Тайный Друг 🎭\n"
                         "🎯 Цель: стать «Душой компании».\n\n"
                         "⚔ Дуэли, топы, рефералы!\n🤝 Скоро: кланы.\n\n👇 Жми:",
                         kb([[("🚀 Старт", "begin")]]))
                continue

            cb = upd.get("callback_query")
            if cb:
                uid = cb["from"]["id"]; chat_id = cb["message"]["chat"]["id"]; act = cb["data"]

                if act == "begin":
                    answer_cb(cb["id"], "🚀 Поехали!")
                    send(chat_id, "💌 Меню:", кнопки_списка(chat_id))
                elif act == "refresh":
                    answer_cb(cb["id"], "🔄 Обновляю...")
                    send(chat_id, "📋 Список участников:\n\n" + текст_списка(chat_id), кнопки_списка(chat_id))
                elif act == "top":
                    answer_cb(cb["id"]); send(chat_id, топ_текст(chat_id))
                elif act == "top_all":
                    answer_cb(cb["id"]); send(chat_id, топ_всё_время(chat_id))
                elif act == "profile":
                    answer_cb(cb["id"]); send(chat_id, профиль_текст(chat_id, uid))
                elif act == "duel":
                    answer_cb(cb["id"]); send(chat_id, "⚔ Напиши: /duel Имя")
                elif act == "ref":
                    answer_cb(cb["id"])
                    send(chat_id, f"🤝 Твоя реферальная ссылка:\n\n{реф_ссылка(uid, chat_id)}\n\nПригласи друга → +5 очков!")
                elif act == "help":
                    answer_cb(cb["id"])
                    send(chat_id, "📖 Как играть:\n1. /start — регистрация\n2. /send_comp — комплимент\n3. /guess — угадать автора\n4. /duel Имя — дуэль\n\n🏆 +1 отправил, +2 угадал, +3 не угадали, +20 дуэль")

                # ========== КОМПЛИМЕНТЫ: случайный / свой ==========
                elif act.startswith("rand_"):
                    answer_cb(cb["id"], "🎲")
                    parts = act.split("_")
                    cid = int(parts[1]); target_uid = int(parts[2])
                    c = получить_чат(cid)
                    if str(uid) not in c["игроки"] or str(target_uid) not in c["игроки"]:
                        send(uid, "❌ Ошибка. Попробуй ещё раз."); continue
                    комплимент = random.choice(КОМПЛИМЕНТЫ)
                    c["игроки"][str(uid)]["очки"] = c["игроки"][str(uid)].get("очки", 0) + 1
                    c["игроки"][str(uid)]["очки_всего"] = c["игроки"][str(uid)].get("очки_всего", 0) + 1
                    c["игроки"][str(uid)]["отправлено"] = c["игроки"][str(uid)].get("отправлено", 0) + 1
                    c["игроки"][str(target_uid)]["получено"] = c["игроки"][str(target_uid)].get("получено", 0) + 1
                    c["история"].setdefault(str(target_uid), [])
                    c["история"][str(target_uid)].append({"от": uid, "текст": комплимент, "угадано": False})
                    учесть_комплимент_в_дуэли(cid, target_uid)
                    c["ожидание"].pop(str(uid), None); save()
                    send(uid, "✅ Комплимент отправлен! +1 очко")
                    send(target_uid, f"💌 Тебе анонимный комплимент:\n\n«{комплимент}»\n\nХочешь угадать? /guess")

                elif act.startswith("own_"):
                    answer_cb(cb["id"])
                    parts = act.split("_")
                    cid = int(parts[1]); target_uid = parts[2]
                    c = получить_чат(cid)
                    c["ожидание"][str(uid)] = f"ownmsg_{cid}_{target_uid}"; save()
                    send(uid, f"✍️ Напиши свой комплимент для {c['игроки'].get(target_uid, {}).get('имя', '???')}:")

                # ========== АДМИН ==========
                elif act.startswith("admin_icon_"):
                    answer_cb(cb["id"])
                    cid = int(act.replace("admin_icon_", ""))
                    c = получить_чат(cid)
                    if not c["игроки"]:
                        send(uid, f"❌ В чате {cid} никто не зарегистрирован."); continue
                    rows = []
                    for u_id, p in c["игроки"].items():
                        rows.append([{"text": p["имя"], "callback_data": f"pickuser_{cid}_{u_id}"}])
                    send(uid, "Кому выдать значок?", {"inline_keyboard": rows})

                elif act.startswith("pickuser_"):
                    answer_cb(cb["id"])
                    parts = act.split("_")
                    cid = int(parts[1]); target_uid = parts[2]
                    c = получить_чат(cid)
                    имя = c["игроки"].get(target_uid, {}).get("имя", "???")
                    send(uid, f"Выбери значок для {имя}:", меню_значков(cid, target_uid))

                elif act.startswith("seticon_"):
                    parts = act.split("_")
                    значок = parts[1]; cid = int(parts[2]); target_uid = parts[3]
                    c = получить_чат(cid)
                    if значок == "❌":
                        c["значки"].pop(target_uid, None)
                        send(uid, "✅ Значок убран.")
                    else:
                        c["значки"][target_uid] = значок
                        имя = c["игроки"].get(target_uid, {}).get("имя", "???")
                        send(uid, f"✅ {значок} выдан {имя}!")
                    save()
                    обновить_список(cid)
                    админ_меню(uid, cid)

                elif act.startswith("admin_back_"):
                    answer_cb(cb["id"])
                    cid = int(act.replace("admin_back_", ""))
                    админ_меню(uid, cid)

                elif act.startswith("admin_stats_"):
                    answer_cb(cb["id"])
                    cid = int(act.replace("admin_stats_", ""))
                    c = получить_чат(cid)
                    send(uid, f"📊 Статистика чата {cid}\n\n"
                              f"👥 Игроков: {len(c['игроки'])}\n"
                              f"💌 Комплиментов: {sum(len(v) for v in c['история'].values())}\n"
                              f"⚔ Дуэлей: {len(c['дуэли'])}")
                    админ_меню(uid, cid)

                elif act == "admin_close":
                    answer_cb(cb["id"], "Закрыто")
                else:
                    answer_cb(cb["id"])
                continue

            msg = upd.get("message")
            if not msg: continue
            chat_id = msg["chat"]["id"]; uid = msg["from"]["id"]; text = msg.get("text") or ""

            payload = None
            if text.startswith("/start "):
                payload = text.split(maxsplit=1)[1]; text = "/start"

            if chat_id > 0:
                обработка_лички(uid, text, payload)
            else:
                if text:
                    обработка_группы(chat_id, uid, text)

    except Exception as e:
        print("Ошибка:", e); time.sleep(3)
