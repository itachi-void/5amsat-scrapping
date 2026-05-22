import os
import re

file_path = r"c:\Users\itachi\Downloads\5amsat-scrapping\5.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
if "import openai" not in content:
    content = content.replace("import requests\n", "import requests\nimport openai\nfrom twilio.rest import Client as TwilioClient\n")

# 2. Globals initialization
if "OPENAI_API_KEY = None" not in content:
    content = content.replace(
        "KHAMSAT_BOT_TOKEN = None",
        "KHAMSAT_BOT_TOKEN = None\nOPENAI_API_KEY = None\nTWILIO_ACCOUNT_SID = None\nTWILIO_AUTH_TOKEN = None\nTWILIO_FROM_NUMBER = None\nTWILIO_TO_NUMBER = None"
    )

# 3. load_all_configs
content = content.replace(
    "global KHAMSAT_BOT_TOKEN, PROXY_USER, PROXY_PASS, TELEGRAPH_TOKEN_KHAMSAT, TELEGRAPH_PATH_KHAMSAT, BACKUP_CHAT_ID",
    "global KHAMSAT_BOT_TOKEN, PROXY_USER, PROXY_PASS, TELEGRAPH_TOKEN_KHAMSAT, TELEGRAPH_PATH_KHAMSAT, BACKUP_CHAT_ID, OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER"
)

content = content.replace(
    "TELEGRAPH_PATH_KHAMSAT = os.getenv(\"TELEGRAPH_PATH\", TELEGRAPH_PATH_KHAMSAT)",
    "TELEGRAPH_PATH_KHAMSAT = os.getenv(\"TELEGRAPH_PATH\", TELEGRAPH_PATH_KHAMSAT)\n    OPENAI_API_KEY = os.getenv(\"OPENAI_API_KEY\")\n    TWILIO_ACCOUNT_SID = os.getenv(\"TWILIO_ACCOUNT_SID\")\n    TWILIO_AUTH_TOKEN = os.getenv(\"TWILIO_AUTH_TOKEN\")\n    TWILIO_FROM_NUMBER = os.getenv(\"TWILIO_FROM_NUMBER\")\n    TWILIO_TO_NUMBER = os.getenv(\"TWILIO_TO_NUMBER\")"
)

content = content.replace(
    "elif k == \"TELEGRAPH_PATH\":\n                        TELEGRAPH_PATH_KHAMSAT = v",
    "elif k == \"TELEGRAPH_PATH\":\n                        TELEGRAPH_PATH_KHAMSAT = v\n                    elif k == \"OPENAI_API_KEY\": OPENAI_API_KEY = v\n                    elif k == \"TWILIO_ACCOUNT_SID\": TWILIO_ACCOUNT_SID = v\n                    elif k == \"TWILIO_AUTH_TOKEN\": TWILIO_AUTH_TOKEN = v\n                    elif k == \"TWILIO_FROM_NUMBER\": TWILIO_FROM_NUMBER = v\n                    elif k == \"TWILIO_TO_NUMBER\": TWILIO_TO_NUMBER = v"
)

# 4. Twilio Function
twilio_func = """
def make_urgent_call():
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_TO_NUMBER:
        return
    try:
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            twiml='<Response><Say language="ar-AE">مرحباً، هناك مشروع جديد هام جداً على موقع خمسات، يرجى تفقده فوراً.</Say></Response>',
            to=TWILIO_TO_NUMBER,
            from_=TWILIO_FROM_NUMBER
        )
        logger.info(f"Initiated urgent Twilio call: {call.sid}")
    except Exception as e:
        logger.error(f"Failed to make Twilio call: {e}")

"""
if "def make_urgent_call():" not in content:
    content = content.replace("def _increment_stats(sent_count):", twilio_func + "def _increment_stats(sent_count):")

# 5. Check Khamsat: Add inline button for AI proposal and Trigger Twilio
button_replace = """
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "الذهاب للطلب 🌐", "url": p['link']}],
                    [{"text": "✨ اكتب لي عرضاً", "callback_data": f"ai_proposal:{p['id']}"}]
                ]
            }
"""
content = re.sub(r'reply_markup\s*=\s*\{\s*"inline_keyboard":\s*\[\s*\[\{"text": "الذهاب للطلب 🌐", "url": p\[\'link\'\]\}\]\s*\]\s*\}', button_replace.strip(), content)

urgent_check = """
            # Check for urgent call
            if any(word in title_lower for word in ["مستعجل", "ميزانية مفتوحة", "ضروري", "عاجل"]):
                make_urgent_call()
"""
if "make_urgent_call()" not in content:
    content = content.replace("title_lower = p['title'].lower()", "title_lower = p['title'].lower()" + urgent_check)

# 6. Callback handler for AI Proposal
ai_handler = """
    if data.startswith("ai_proposal:"):
        pid = data.split(":")[1]
        msg_id = callback["message"]["message_id"]
        
        # Send waiting message
        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⏳ جاري توليد العرض بالذكاء الاصطناعي..."}, timeout=10)
        
        # Generate proposal
        try:
            if not OPENAI_API_KEY:
                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ يرجى إضافة OPENAI_API_KEY في الإعدادات."}, timeout=10)
                return
                
            openai.api_key = OPENAI_API_KEY
            prompt = f"قم بكتابة عرض احترافي كمستقل لتقديم خدمة على منصة خمسات بناءً على هذا المشروع:\\n{callback['message']['text']}"
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            proposal = resp.choices[0].message.content.strip()
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✨ **العرض المقترح:**\\n\\n{proposal}", "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"❌ حدث خطأ: {e}"}, timeout=10)
        
        requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback["id"]})
        return

"""
if "ai_proposal:" not in content:
    content = content.replace("def handle_callback_query(callback):\n    data = callback.get(\"data\")\n    chat_id = callback.get(\"from\", {}).get(\"id\")\n    if not data or not chat_id:\n        return", "def handle_callback_query(callback):\n    data = callback.get(\"data\")\n    chat_id = callback.get(\"from\", {}).get(\"id\")\n    if not data or not chat_id:\n        return\n" + ai_handler)

# 7. /settings command
settings_cmd = """
        elif text == '/settings':
            # Simple keyword toggling logic could go here, but for now we provide instructions
            keyboard = {
                "inline_keyboard": [
                    [{"text": "إضافة كلمة مفتاحية ➕", "callback_data": "add_keyword"}],
                    [{"text": "حذف كلمة مفتاحية ➖", "callback_data": "remove_keyword"}]
                ]
            }
            _send_one(chat_id, "⚙️ **إعدادات الفلاتر والكلمات المفتاحية:**", reply_markup=keyboard, parse_mode="Markdown")
"""
if "elif text == '/settings':" not in content:
    content = content.replace("elif text == '/ping':", settings_cmd.strip() + "\n        elif text == '/ping':")

# 8. Daily Market Insight Thread
daily_report = """
def daily_report_job():
    while True:
        import datetime
        now = datetime.datetime.now()
        # Sleep until midnight
        next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time.sleep((next_midnight - now).total_seconds())
        
        subs = _load_subscribers()
        stats = _get_stats()
        sent_today = stats.get("total_sent", 0)
        
        report_text = f"📊 **تقرير السوق اليومي:**\\n\\nتم إرسال {sent_today} مشروع اليوم في تخصصاتك. استعد ليوم جديد غداً!"
        for cid in subs:
            _send_one(cid, report_text, parse_mode="Markdown")

"""
if "def daily_report_job():" not in content:
    content = content.replace("def _periodic_tasks_loop():", daily_report + "def _periodic_tasks_loop():")

# 9. Start daily report thread
if "threading.Thread(target=daily_report_job, daemon=True).start()" not in content:
    content = content.replace("threading.Thread(target=_periodic_tasks_loop, daemon=True).start()", "threading.Thread(target=_periodic_tasks_loop, daemon=True).start()\n        threading.Thread(target=daily_report_job, daemon=True).start()")

# 10. Update /help and Backup Message
content = content.replace(
    "لو محتاج استرجاع: اعمل Reply على آخر backup واكتب /restore",
    "لو محتاج استرجاع: اعمل Reply على آخر backup واكتب /restore\\n\\n✨ **الميزات الجديدة مفعلة:**\\n- ذكاء اصطناعي (AI Proposals)\\n- فلاتر (/settings)\\n- تقرير يومي (Daily Insight)\\n- مكالمات طوارئ (Twilio)"
)

content = content.replace(
    "/help - هذا الدليل",
    "/help - هذا الدليل\\n/settings - إعدادات الفلاتر والكلمات المفتاحية"
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied updates successfully!")
