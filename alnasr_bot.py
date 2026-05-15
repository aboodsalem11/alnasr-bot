import telebot
import google.generativeai as genai
import requests
import io
import os
from PIL import Image
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ── المفاتيح من Environment Variables ──
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
COMPANY_PHONE  = "+201005691340"

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN و GEMINI_API_KEY لازم يتحددوا في Environment Variables")

# ── إعداد Gemini ──
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ── إعداد البوت ──
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ── حالة المستخدمين ──
user_states = {}

# ── Prompts ──
SYSTEM_PROMPT = """انت مساعد ذكاء اصطناعي متخصص في اعمال التشطيبات والبناء والديكور، تابع لشركة النصر للتشطيبات الحديثة والديكور.

تخصصاتك:
- البلاط والسيراميك والبورسلين
- الدهانات وتحضير الاسطح
- الجبس والجبس بورد
- الارضيات بجميع انواعها
- السباكة والصرف
- الكهرباء والاضاءة
- الالومنيوم والزجاج
- الديكور الداخلي
- حسابات الكميات والمساحات
- حل مشاكل التنفيذ

قواعد:
- رد بالعربية دائما
- اذا سئلت خارج التشطيبات قل: انا متخصص في التشطيبات والديكور فقط
- كن عمليا مع ارقام وقياسات دقيقة"""

VISION_PROMPT = """انت خبير ديكور وتشطيبات تابع لشركة النصر للتشطيبات الحديثة والديكور.

العميل بعتلك صورة اوضته او شقته. حللها وقدم له:

1. تحليل المكان الحالي:
وصف مختصر لما تشوفه في الصورة

2. مقترحات التشطيب:
- الوان الدهان المناسبة
- نوع الارضية المقترحة
- السقف والاضاءة المناسبة

3. افكار الديكور:
- اسلوب الديكور المناسب
- اهم 3 تغييرات هتحول المكان

4. تكلفة تقريبية:
- نطاق سعري للتشطيب الاقتصادي والمتوسط

اكتب بالعربية بشكل واضح ومشوق."""

def company_footer():
    return f"\n\n---\nللتواصل مع شركة النصر:\n{COMPANY_PHONE}"

def make_main_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📸 شوف شقتك قبل التشطيب", callback_data="photo_mode"),
        InlineKeyboardButton("🔨 اسأل عن التشطيبات",    callback_data="chat_mode"),
        InlineKeyboardButton("📞 تواصل مع شركة النصر",  callback_data="contact"),
    )
    return kb

def make_back_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
    return kb

def ask_gemini_text(prompt):
    response = model.generate_content(prompt)
    return response.text

def ask_gemini_vision(prompt_text, pil_image):
    response = model.generate_content([prompt_text, pil_image])
    return response.text


# ── /start ──
@bot.message_handler(commands=["start"])
def start(message):
    user_states[message.chat.id] = "main"
    name = message.from_user.first_name or "صديقي"
    bot.send_message(
        message.chat.id,
        f"السلام عليكم {name}\n\n"
        f"اهلا بيك في مساعد شركة النصر الذكي\n"
        f"للتشطيبات الحديثة والديكور\n\n"
        f"اختار اللي تحتاجه:",
        reply_markup=make_main_keyboard()
    )


# ── Callbacks ──
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    cid = call.message.chat.id

    if call.data == "main_menu":
        user_states[cid] = "main"
        try:
            bot.edit_message_text(
                "اختار اللي تحتاجه:",
                cid, call.message.message_id,
                reply_markup=make_main_keyboard()
            )
        except Exception:
            bot.send_message(cid, "اختار اللي تحتاجه:", reply_markup=make_main_keyboard())

    elif call.data == "chat_mode":
        user_states[cid] = "chat"
        try:
            bot.edit_message_text(
                "وضع التشطيبات\n\naسألني عن اي حاجة في التشطيبات والديكور!\nمقاسات، كميات، مواد، حل مشاكل",
                cid, call.message.message_id,
                reply_markup=make_back_keyboard()
            )
        except Exception:
            bot.send_message(cid, "اسألني عن اي حاجة في التشطيبات:", reply_markup=make_back_keyboard())

    elif call.data == "photo_mode":
        user_states[cid] = "waiting_photo"
        try:
            bot.edit_message_text(
                "شوف شقتك قبل التشطيب\n\nابعتلي صورة لاي اوضة او مكان في شقتك\nوهحللهالك واقترحلك احسن تشطيب وديكور مناسب!",
                cid, call.message.message_id,
                reply_markup=make_back_keyboard()
            )
        except Exception:
            bot.send_message(cid, "ابعتلي صورة الاوضة:", reply_markup=make_back_keyboard())

    elif call.data == "contact":
        try:
            bot.edit_message_text(
                f"شركة النصر للتشطيبات الحديثة والديكور\n\nللتواصل:\n{COMPANY_PHONE}\n\nنسعد بخدمتك!",
                cid, call.message.message_id,
                reply_markup=make_back_keyboard()
            )
        except Exception:
            bot.send_message(cid, f"للتواصل: {COMPANY_PHONE}", reply_markup=make_back_keyboard())

    bot.answer_callback_query(call.id)


# ── رسائل نصية ──
@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(message):
    cid = message.chat.id
    state = user_states.get(cid, "main")

    if state == "waiting_photo":
        bot.send_message(cid, "ابعتلي صورة الاوضة عشان اقدر احللهالك!", reply_markup=make_back_keyboard())
        return

    if state == "main":
        start(message)
        return

    # وضع المحادثة
    bot.send_chat_action(cid, "typing")
    try:
        prompt = f"{SYSTEM_PROMPT}\n\nسؤال العميل: {message.text}\n\nالرد:"
        reply = ask_gemini_text(prompt)
        reply = reply + company_footer()
        bot.send_message(cid, reply, reply_markup=make_back_keyboard())
    except Exception as e:
        error_msg = str(e)
        print(f"[TEXT ERROR] {error_msg}")
        if "API_KEY" in error_msg or "invalid" in error_msg.lower():
            bot.send_message(cid, "مشكلة في مفتاح API. تواصل مع الادارة.", reply_markup=make_back_keyboard())
        elif "quota" in error_msg.lower():
            bot.send_message(cid, "تجاوزنا الحد المجاني لهذا الشهر. حاول بكره!", reply_markup=make_back_keyboard())
        else:
            bot.send_message(cid, f"حصل خطا: {error_msg[:100]}", reply_markup=make_back_keyboard())


# ── صور ──
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    cid = message.chat.id
    state = user_states.get(cid, "main")

    if state != "waiting_photo":
        bot.send_message(cid, "اضغط على شوف شقتك من القائمة الرئيسية الاول!", reply_markup=make_main_keyboard())
        return

    wait_msg = bot.send_message(cid, "جاري تحليل صورتك... لحظة!")
    bot.send_chat_action(cid, "typing")

    try:
        # تحميل الصورة
        file_id   = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url  = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"

        img_bytes = requests.get(file_url, timeout=30).content
        img = Image.open(io.BytesIO(img_bytes))
        img.thumbnail((1024, 1024), Image.LANCZOS)

        if img.mode not in ("RGB",):
            img = img.convert("RGB")

        reply = ask_gemini_vision(VISION_PROMPT, img)
        reply = reply + company_footer()

        bot.delete_message(cid, wait_msg.message_id)
        bot.send_message(cid, reply, reply_markup=make_back_keyboard())
        user_states[cid] = "waiting_photo"

    except Exception as e:
        error_msg = str(e)
        print(f"[PHOTO ERROR] {error_msg}")
        bot.delete_message(cid, wait_msg.message_id)
        if "quota" in error_msg.lower():
            bot.send_message(cid, "تجاوزنا الحد المجاني. حاول بكره!", reply_markup=make_back_keyboard())
        else:
            bot.send_message(cid, f"مش قادر احلل الصورة. السبب: {error_msg[:100]}", reply_markup=make_back_keyboard())


# ── تشغيل البوت ──
print("البوت شغال بنجاح!")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
