from curl_cffi import requests as cffi_requests
import json
import os
import time
import random
import requests
import logging
import threading
from logging.handlers import RotatingFileHandler
from bs4 import BeautifulSoup

# Sync Locks and Shared Objects
subscribers_lock = threading.Lock()
                elif cmd == "/help":
                    # Dynamic help generator: build sections from cmd_roles and a short descriptions map
                    command_descriptions = {
                        "/add_admin": "إضافة أدمن جديد للبوت (Owner only)",
                        "/remove_admin": "إزالة أدمن من القائمة (Owner only)",
                        "/backup": "أخذ نسخة احتياطية يدوياً",
                        "/restore": "استعادة البيانات من ملف باك أب (Admins)",
                        "/freeze_backup": "تجميد الباك أب التلقائي مؤقتاً",
                        "/backup_freeze": "بديل لأمر تجميد الباك أب",
                        "/backup_stop": "إيقاف الباك أب التلقائي",
                        "/backup_end": "انتهاء الباك أب (تجميد نهائي)",
                        "/resume_backup": "تشغيل الباك أب التلقائي",
                        "/backup_resume": "بديل لأمر تشغيل الباك أب",
                        "/backup_play": "تشغيل الباك أب التلقائي (بديل)",
                        "/backup_menu": "فتح لوحة إعدادات الباك أب",
                        "/telegraph_freeze": "تجميد مزامنة Telegraph مؤقتاً",
                        "/telegraph_stop": "إيقاف مزامنة Telegraph",
                        "/telegraph_end": "إيقاف مزامنة Telegraph نهائياً",
                        "/telegraph_resume": "استئناف مزامنة Telegraph",
                        "/telegraph_play": "بديل لأمر تشغيل مزامنة Telegraph",
                        "/menu": "فتح لوحة تحكم الأدمن التفاعلية",
                        "/ids": "عرض معرفات المشتركين المسجلين",
                        "/broadcast": "بث رسالة إلى جميع المشتركين (Admins)",
                        "/send_last": "جلب وإرسال أحدث الطلبات يدوياً (Admins)",
                        "/block": "حظر مستخدم من استخدام البوت (Admins)",
                        "/unblock": "إلغاء حظر مستخدم (Admins)",
                        "/mute": "كتم إشعارات مستخدم معين",
                        "/unmute": "إلغاء كتم مستخدم",
                        "/muteall": "كتم إشعارات جميع المشتركين",
                        "/unmuteall": "إلغاء كتم الكل",
                        "/approve": "قبول طلب اشتراك معلق",
                        "/reject": "رفض طلب اشتراك معلق",
                        "/pending": "عرض قائمة الطلبات المعلقة",
                        "/status": "عرض حالة البوت والإحصائيات",
                        "/dashboard": "فتح لوحة تقارير بصرية",
                        "/vstatus": "بديل لأمر لوحة التقارير",
                        "/start": "الاشتراك في إشعارات البوت",
                        "/subscribe": "الاشتراك في إشعارات البوت",
                        "/unsubscribe": "إلغاء الاشتراك من البوت",
                        "/mymute": "كتم إشعارات الطلبات لحسابك",
                        "/pause": "كتم مؤقت لإشعاراتك",
                        "/myunmute": "إلغاء كتم حسابك",
                        "/resume": "إلغاء كتم واستئناف الإشعارات",
                        "/ping": "فحص استجابة البوت",
                        "/help": "عرض هذه القائمة المساعدة",
                        "/filter": "تصفية الطلبات حسب كلمات مفتاحية",
                        "/myfilters": "عرض كلماتك المفتاحية الحالية",
                        "/filter_clear": "مسح فلاتر المستخدم",
                        "/filter_off": "إيقاف الفلترة واستلام كل الطلبات",
                    }

                    # Group commands by required role using the existing cmd_roles mapping
                    owner_cmds = []
                    admin_cmds = []
                    user_cmds = []
                    for c, r in cmd_roles.items():
                        if r >= 3:
                            owner_cmds.append(c)
                        elif r == 2:
                            admin_cmds.append(c)
                        else:
                            user_cmds.append(c)

                    def fmt_list(cmds):
                        lines = []
                        for c in sorted(cmds):
                            desc = command_descriptions.get(c, "شرح غير متوفر")
                            lines.append(f"  {c} — {desc}")
                        return "\n".join(lines)

                    if role >= 3:
                        help_text = (
                            "🤖 **دليل أوامر البوت الكامل:**\n\n"
                            "👑 أوامر المالك (Owner Only):\n"
                            + fmt_list(owner_cmds)
                            + "\n\n👮 أوامر الأدمنز والأشراف (Admins & Owner):\n"
                            + fmt_list(admin_cmds)
                            + "\n\n👤 أوامر المشتركين (Users):\n"
                            + fmt_list(user_cmds)
                        )
                    elif role >= 2:
                        help_text = (
                            "🤖 **دليل أوامر الأدمن:**\n\n"
                            "👮 أوامر الأدمنز (Admin):\n"
                            + fmt_list(admin_cmds)
                            + "\n\n👤 أوامر المشتركين (Users):\n"
                            + fmt_list(user_cmds)
                        )
                    else:
                        help_text = (
                            "🤖 **دليل أوامر المشتركين:**\n\n"
                            + fmt_list(user_cmds)
                        )

                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": help_text, "parse_mode": "Markdown"})
        return False
    return time.time() < _proxy_cooldowns.get(proxy_addr, 0)


def _register_proxy_result(proxy_addr, ok=False, blocked=False):
    """Track proxy health and assign exponential cooldown on failures."""
    if not proxy_addr:
        return 0.0, 0

    if ok:
        _proxy_fail_streak[proxy_addr] = 0
        _proxy_cooldowns[proxy_addr] = 0
        return 0.0, 0

    streak = _proxy_fail_streak.get(proxy_addr, 0) + 1
    _proxy_fail_streak[proxy_addr] = streak

    base = PROXY_BLOCK_BASE_SECONDS if blocked else PROXY_BACKOFF_BASE_SECONDS
    exp_power = min(streak - 1, 6)
    delay = min(PROXY_MAX_BACKOFF_SECONDS, base * (2 ** exp_power))
    delay *= random.uniform(0.85, 1.25)  # jitter to avoid synchronized retries

    _proxy_cooldowns[proxy_addr] = time.time() + delay
    return delay, streak

scraper = _new_scraper()

# ==============================================================================
# ENVIRONMENT AND CONFIG DYNAMIC LOADER
# ==============================================================================
def load_all_configs():
    """Dynamically load configs from environment or local .env file."""
    global KHAMSAT_BOT_TOKEN, PROXY_USER, PROXY_PASS, TELEGRAPH_TOKEN_KHAMSAT, TELEGRAPH_PATH_KHAMSAT
    
    KHAMSAT_BOT_TOKEN = os.getenv("BOT_TOKEN")
    PROXY_USER = os.getenv("PROXY_USER", "")
    PROXY_PASS = os.getenv("PROXY_PASS", "")
    TELEGRAPH_TOKEN_KHAMSAT = os.getenv("TELEGRAPH_TOKEN", TELEGRAPH_TOKEN_KHAMSAT)
    TELEGRAPH_PATH_KHAMSAT = os.getenv("TELEGRAPH_PATH", TELEGRAPH_PATH_KHAMSAT)

    # Local .env path
    khamsat_env = "C:\\Users\\itachi\\Downloads\\5amsat-scrapping\\.env"
    if not os.path.exists(khamsat_env):
        khamsat_env = ".env"
        
    if os.path.exists(khamsat_env):
        with open(khamsat_env, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k == "BOT_TOKEN":
                        KHAMSAT_BOT_TOKEN = v
                    elif k == "PROXY_USER":
                        PROXY_USER = v
                    elif k == "PROXY_PASS":
                        PROXY_PASS = v
                    elif k == "TELEGRAPH_TOKEN":
                        TELEGRAPH_TOKEN_KHAMSAT = v
                    elif k == "TELEGRAPH_PATH":
                        TELEGRAPH_PATH_KHAMSAT = v

    logger.info(f"Config loaded: Khamsat Token={'Loaded' if KHAMSAT_BOT_TOKEN else 'Missing'}")

# ==============================================================================
# PROXY CONSOLIDATION POOL LOADER
# ==============================================================================
def load_proxies():
    """Consolidate proxy files from both workspaces into a single resilient pool."""
    global premium_proxies, free_proxies
    premium_proxies = []
    free_proxies = []
    
    paths = [
        "C:\\Users\\itachi\\Downloads\\mostaql scrapping",
        "C:\\Users\\itachi\\Downloads\\5amsat-scrapping"
    ]
    
    for p in paths:
        # Premium proxies file
        p_file = os.path.join(p, "proxyscrape_premium_http_proxies.txt")
        if PROXY_USER and PROXY_PASS and os.path.exists(p_file):
            try:
                with open(p_file, 'r') as f:
                    loaded = [("http", l.strip()) for l in f if ":" in l]
                premium_proxies.extend(loaded)
                logger.info(f"Loaded {len(loaded)} premium proxies from {p_file}")
            except Exception as e:
                logger.error(f"Failed premium proxy load: {e}")
        
        # Free proxies file
        f_file = os.path.join(p, "free_proxies.txt")
        if os.path.exists(f_file):
            try:
                loaded_free = []
                with open(f_file, 'r') as f:
                    for l in f:
                        l = l.strip()
                        if ":" in l:
                            if "://" in l:
                                parts = l.split("://", 1)
                                loaded_free.append((parts[0].lower(), parts[1]))
                            else:
                                loaded_free.append(("http", l))
                free_proxies.extend(loaded_free)
                logger.info(f"Loaded {len(loaded_free)} free proxies from {f_file}")
            except Exception as e:
                logger.error(f"Failed free proxy load: {e}")
                
    # Deduplicate lists
    premium_proxies = list(set(premium_proxies))
    free_proxies = list(set(free_proxies))
    logger.info(f"Consolidated Proxy Pool: {len(premium_proxies)} premium, {len(free_proxies)} free proxies.")

# ==============================================================================
# PARAMETERIZED DATA STORAGE ACCESS LAYER
# ==============================================================================
def _get_file_path(file_key):
    """Retrieve isolated path prefixing 'khamsat_' to keep existing databases intact."""
    names = {
        "subscribers": "subscribers.json",
        "pending": "pending_subscribers.json",
        "blocked": "blocked_users.json",
        "roles": "roles.json",
        "state": "bot_state.json",
        "seen": "max_id.json",
        "muted": "muted_users.json",
        "stats": "bot_stats.json",
        "last_broadcast": "last_broadcast_msgs.json",
        "keywords": "keywords.json"
    }
    return os.path.join(DATA_DIR, f"khamsat_{names[file_key]}")

def _load_notifications_state():
    global notifications_active, backup_active, backup_freeze_until, telegraph_active, telegraph_freeze_until
    file_path = _get_file_path("state")
    if not os.path.exists(file_path):
        notifications_active = True
        backup_active = True
        backup_freeze_until = 0
        telegraph_active = False
        telegraph_freeze_until = 0
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        notifications_active = data.get("notifications_active", True)
        backup_active = data.get("backup_active", True)
        backup_freeze_until = data.get("backup_freeze_until", 0)
        telegraph_active = data.get("telegraph_active", False)
        telegraph_freeze_until = data.get("telegraph_freeze_until", 0)
    except Exception:
        notifications_active = True
        backup_active = True
        backup_freeze_until = 0
        telegraph_active = False
        telegraph_freeze_until = 0

def _save_notifications_state():
    file_path = _get_file_path("state")
    tmp_path = file_path + ".tmp"
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump({
                "notifications_active": notifications_active,
                "backup_active": backup_active,
                "backup_freeze_until": backup_freeze_until,
                "telegraph_active": telegraph_active,
                "telegraph_freeze_until": telegraph_freeze_until
            }, f, indent=4)
        os.replace(tmp_path, file_path)
    except Exception as e:
        logger.error(f"Failed to save bot state: {e}")

def _send_backup_menu(chat_id, callback=None):
    if not KHAMSAT_BOT_TOKEN:
        return
    base_url = f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}"
    
    now = time.time()
    if not backup_active:
        status_text = "🔴 **مجمد نهائياً (موقوف تماماً)**"
    elif now < backup_freeze_until:
        remaining_sec = int(backup_freeze_until - now)
        m, s = divmod(remaining_sec, 60)
        h, m = divmod(m, 60)
        time_str = f"{h} ساعة و {m} دقيقة" if h > 0 else f"{m} دقيقة"
        status_text = f"❄️ **مجمد مؤقتاً** (متبقي: `{time_str}`)"
    else:
        status_text = "🟢 **نشط ويعمل تلقائياً كل 3 دقائق**"
        
    menu_text = (
        "💾 **إعدادات النسخ الاحتياطي التلقائي لبوت خمسات (Backup Settings):**\n\n"
        f"الحالة الحالية: {status_text}\n\n"
        "ℹ️ **الفرق بين الباك أب التلقائي ومزامنة Telegraph:**\n"
        "• 💾 **الباك أب التلقائي (هذا القسم):** يقوم بإنشاء ملف نسخة احتياطية (.json) وإرساله لك مباشرةً في شات التليجرام كل 3 دقائق. تكمن أهميته في إمكانية عمل رد (Reply) عليه وكتابة أمر `/restore` لاستعادة البيانات يدوياً في أي وقت.\n"
        "• ☁️ **مزامنة Telegraph:** هي مزامنة سحابية صامتة تحدث كل دقيقتين، حيث يتم حفظ نسخة مشفرة من قاعدة البيانات على خوادم Telegraph سحابياً. فائدتها أنها تُمكّن البوت من استرجاع كافة البيانات تلقائياً دون تدخل منك عند إعادة تشغيل البوت أو نقله لسيرفر جديد.\n\n"
        "💡 يمكنك التحكم في تشغيل أو تجميد الباك أب التلقائي واختيار مدة التجميد المناسبة من الخيارات أدناه:"
    )
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🟢 تشغيل / إلغاء التجميد", "callback_data": "backup_op:resume"}
            ],
            [
                {"text": "❄️ تجميد 30 دقيقة", "callback_data": "backup_op:freeze_30m"},
                {"text": "❄️ تجميد ساعتين", "callback_data": "backup_op:freeze_2h"}
            ],
            [
                {"text": "❄️ تجميد 6 ساعات", "callback_data": "backup_op:freeze_6h"},
                {"text": "❄️ تجميد 12 ساعة", "callback_data": "backup_op:freeze_12h"}
            ],
            [
                {"text": "❄️ تجميد 24 ساعة", "callback_data": "backup_op:freeze_24h"},
                {"text": "🔴 تجميد نهائي (للأبد)", "callback_data": "backup_op:freeze_forever"}
            ],
            [
                {"text": "🔙 العودة للوحة التحكم", "callback_data": "backup_op:back_to_menu"}
            ]
        ]
    }
    
    if callback and "message" in callback:
        msg_id = callback["message"]["message_id"]
        requests.post(f"{base_url}/editMessageText", json={
            "chat_id": chat_id,
            "message_id": msg_id,
            "text": menu_text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        })
        requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback["id"]})
    else:
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": chat_id,
            "text": menu_text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        })

def _load_subscribers():
    file_path = _get_file_path("subscribers")
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {int(x) for x in data}
    except Exception:
        pass
    return set()

def _save_subscribers(subs_set):
    file_path = _get_file_path("subscribers")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(subs_set), f)
    os.replace(tmp_path, file_path)

def _load_roles():
    file_path = _get_file_path("roles")
    if not os.path.exists(file_path):
        default_roles = {"owner": 1622676655, "admins": [8064837651]}
        _save_roles(default_roles)
        return default_roles
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"owner": 1622676655, "admins": [8064837651]}

def _save_roles(roles_data):
    file_path = _get_file_path("roles")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(roles_data, f, indent=4)
    os.replace(tmp_path, file_path)

def get_owner_id():
    return int(_load_roles().get("owner", 1622676655))

def _load_admins():
    roles = _load_roles()
    admins_list = roles.get("admins", [])
    if not isinstance(admins_list, list):
        admins_list = []
    return {int(x) for x in admins_list}

def _save_admins(admins_set):
    roles = _load_roles()
    roles["admins"] = sorted(admins_set)
    _save_roles(roles)

def _get_all_admins():
    return _load_admins() | {get_owner_id()}

def _load_pending():
    file_path = _get_file_path("pending")
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {int(x) for x in data}
    except Exception:
        pass
    return set()

def _save_pending(pending_set):
    file_path = _get_file_path("pending")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(pending_set), f)
    os.replace(tmp_path, file_path)

def _load_blocked():
    file_path = _get_file_path("blocked")
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {int(x) for x in data}
    except Exception:
        pass
    return set()

def _save_blocked(blocked_set):
    file_path = _get_file_path("blocked")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(blocked_set), f)
    os.replace(tmp_path, file_path)

def _load_muted_users():
    file_path = _get_file_path("muted")
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {int(x) for x in data}
    except Exception:
        pass
    return set()

def _save_muted_users(muted_set):
    file_path = _get_file_path("muted")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(muted_set), f)
    os.replace(tmp_path, file_path)

def _get_stats():
    file_path = _get_file_path("stats")
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_stats(stats_data):
    file_path = _get_file_path("stats")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=4)
    os.replace(tmp_path, file_path)

def _increment_stats(sent_count):
    if sent_count <= 0:
        return
    with subscribers_lock:
        s = _get_stats()
        s["total_sent"] = s.get("total_sent", 0) + sent_count
        _save_stats(s)

def _load_broadcast_msgs():
    file_path = _get_file_path("last_broadcast")
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        pass
    return {}

def _save_broadcast_msgs(msg_map):
    file_path = _get_file_path("last_broadcast")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(msg_map, f, indent=4)
    os.replace(tmp_path, file_path)

def _load_keywords():
    file_path = _get_file_path("keywords")
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_keywords(keywords_dict):
    file_path = _get_file_path("keywords")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(keywords_dict, f, indent=4, ensure_ascii=False)
    os.replace(tmp_path, file_path)

# ==============================================================================
# SUBSCRIBER MUTATION ENGINE
# ==============================================================================
def add_subscriber(chat_id):
    """Add user to subscribers list (max limit of 50 enforced)."""
    with subscribers_lock:
        subs = _load_subscribers()
        pending = _load_pending()
        blocked = _load_blocked()
        
        if chat_id in blocked:
            return False
            
        if chat_id in subs:
            return True
            
        if len(subs) >= MAX_SUBSCRIBERS:
            pending.add(chat_id)
            _save_pending(pending)
            return False
            
        subs.add(chat_id)
        _save_subscribers(subs)
        pending.discard(chat_id)
        _save_pending(pending)
        return True

def remove_subscriber(chat_id):
    with subscribers_lock:
        subs = _load_subscribers()
        subs.discard(chat_id)
        _save_subscribers(subs)
        
        pending = _load_pending()
        pending.discard(chat_id)
        _save_pending(pending)

def reject_subscriber(chat_id):
    with subscribers_lock:
        pending = _load_pending()
        pending.discard(chat_id)
        _save_pending(pending)
        
        subs = _load_subscribers()
        subs.discard(chat_id)
        _save_subscribers(subs)

def is_owner(chat_id):
    try:
        return int(chat_id) == get_owner_id()
    except (ValueError, TypeError):
        return False

def is_admin(chat_id):
    try:
        cid = int(chat_id)
        return cid in _load_admins() or cid == get_owner_id()
    except (ValueError, TypeError):
        return False

def _notify_admins(text):
    """Alert all administrative endpoints of events."""
    if not KHAMSAT_BOT_TOKEN or not _get_all_admins():
        return
    for cid in _get_all_admins():
        try:
            requests.post(f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}/sendMessage", json={"chat_id": cid, "text": text}, timeout=10)
        except Exception:
            pass

def _is_rate_limited(chat_id):
    now = time.time()
    key = chat_id
    last = _rate_limit_map.get(key, 0)
    if now - last < _RATE_LIMIT_SECONDS:
        return True
    _rate_limit_map[key] = now
    return False

# ==============================================================================
# TELEGRAM BASE TRANSMITTER
# ==============================================================================
def _send_one(chat_id, text, reply_markup=None, retries=3, parse_mode=None):
    """Send message to user with auto-removal if bot blocked."""
    if not KHAMSAT_BOT_TOKEN:
        return False, None
    tele_url = f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode

    for attempt in range(retries):
        try:
            r = requests.post(tele_url, json=payload, timeout=10)
            if r.status_code == 200:
                return True, r.json().get("result", {}).get("message_id")
            elif r.status_code == 403:
                remove_subscriber(chat_id)
                logger.warning(f"Removed user {chat_id} from Khamsat subscribers (blocked the bot).")
                return False, None
        except Exception:
            pass
        time.sleep(1)
    return False, None

# ==============================================================================
# TELEGRAPH DATA CLOUD BACKUP INTEGRATION
# ==============================================================================
last_uploaded_db_hash_khamsat = None

def generate_full_backup():
    backup_data = {}
    files_to_backup = {
        "subscribers": _get_file_path("subscribers"),
        "pending": _get_file_path("pending"),
        "blocked": _get_file_path("blocked"),
        "roles": _get_file_path("roles"),
        "state": _get_file_path("state"),
        "seen": _get_file_path("seen"),
        "muted": _get_file_path("muted"),
        "stats": _get_file_path("stats"),
        "keywords": _get_file_path("keywords"),
    }
    for key, fpath in files_to_backup.items():
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    backup_data[key] = json.load(f)
            except Exception:
                backup_data[key] = None
        else:
            backup_data[key] = None
    return backup_data

def restore_full_backup(backup_data):
    files_to_backup = {
        "subscribers": _get_file_path("subscribers"),
        "pending": _get_file_path("pending"),
        "blocked": _get_file_path("blocked"),
        "roles": _get_file_path("roles"),
        "state": _get_file_path("state"),
        "seen": _get_file_path("seen"),
        "muted": _get_file_path("muted"),
        "stats": _get_file_path("stats"),
        "keywords": _get_file_path("keywords"),
    }
    for key, fpath in files_to_backup.items():
        if key in backup_data and backup_data[key] is not None:
            tmp = fpath + ".tmp"
            try:
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(backup_data[key], f, indent=4)
                os.replace(tmp, fpath)
            except Exception as e:
                logger.error(f"Failed to restore {key} for Khamsat: {e}")

def generate_system_backup():
    """Generate a single unified backup for Khamsat data."""
    return {
        "khamsat": generate_full_backup(),
        "timestamp": time.time()
    }

def restore_system_backup(backup_data):
    """Restore a backup containing Khamsat data."""
    if "khamsat" in backup_data and backup_data["khamsat"] is not None:
        restore_full_backup(backup_data["khamsat"])
    else:
        # Fallback if restore data is directly the inner backup dictionary
        restore_full_backup(backup_data)

def download_telegraph_db():
    try:
        r = requests.get(f'https://api.telegra.ph/getPage/{TELEGRAPH_PATH_KHAMSAT}?return_content=true').json()
        if not r.get("ok"):
            return
        content = r['result']['content'][0]['children'][0]
        if content and content.startswith("{"):
            backup_data = json.loads(content)
            restore_full_backup(backup_data)
            logger.info("Successfully restored Khamsat state from Telegraph DB cloud!")
    except Exception as e:
        logger.error(f"Failed to download Telegraph DB: {e}")

def download_railway_backup():
    """If configured, fetch the latest backup from the external Railway backup URL and restore it."""
    try:
        railway_url = os.getenv("RAILWAY_BACKUP_URL", "").strip()
        railway_token = os.getenv("RAILWAY_BACKUP_TOKEN", "").strip()
        if not railway_url:
            return

        headers = {}
        if railway_token:
            headers["Authorization"] = f"Bearer {railway_token}"

        # Expect the endpoint to return raw backup JSON (the same shape as generate_system_backup())
        r = requests.get(railway_url, headers=headers, timeout=20)
        if r.status_code != 200:
            logger.warning(f"Failed to download Railway backup: HTTP {r.status_code}")
            return

        try:
            backup_data = r.json()
        except Exception:
            backup_data = json.loads(r.content.decode("utf-8"))

        if backup_data:
            restore_system_backup(backup_data)
            logger.info("Successfully restored Khamsat state from Railway backup!")
    except Exception as e:
        logger.error(f"Failed to download Railway backup: {e}")

def telegraph_sync_thread():
    global last_uploaded_db_hash_khamsat
    
    while True:
        try:
            now = time.time()
            if telegraph_active and (telegraph_freeze_until == 0 or now >= telegraph_freeze_until):
                backup_data = generate_full_backup()
                db_str = json.dumps(backup_data)
                db_hash = hash(db_str)
                
                if db_hash != last_uploaded_db_hash_khamsat:
                    content = [{"tag":"p", "children":[db_str]}]
                    r = requests.post(f'https://api.telegra.ph/editPage/{TELEGRAPH_PATH_KHAMSAT}', json={
                        'access_token': TELEGRAPH_TOKEN_KHAMSAT,
                        'title': 'DB_khamsat',
                        'content': json.dumps(content)
                    }).json()
                    if r.get("ok"):
                        last_uploaded_db_hash_khamsat = db_hash
                        logger.info("Successfully synced Khamsat state to Telegraph DB!")
                        # Optional: push the same backup to an external backup endpoint (e.g., a Railway service)
                        try:
                            railway_url = os.getenv("RAILWAY_BACKUP_URL", "").strip()
                            railway_token = os.getenv("RAILWAY_BACKUP_TOKEN", "").strip()
                            if railway_url:
                                headers = {"Content-Type": "application/json"}
                                if railway_token:
                                    headers["Authorization"] = f"Bearer {railway_token}"
                                requests.post(railway_url, json=backup_data, headers=headers, timeout=15)
                                logger.info("Pushed Khamsat backup to external Railway URL.")
                        except Exception as _rexb:
                            logger.warning(f"Failed to push backup to external Railway URL: {_rexb}")
        except Exception:
            pass
        time.sleep(120)

# ==============================================================================
# CORE SCRAPING ENGINES
# ==============================================================================
def fetch_khamsat_projects(max_pages=8, max_attempts=12):
    """Fetch up to max_pages of Khamsat requests, with short-lived cache."""
    global scraper, _khamsat_project_cache
    now = time.time()
    if _khamsat_project_cache["data"] and (now - _khamsat_project_cache["ts"]) < KHAMSAT_CACHE_TTL:
        return _khamsat_project_cache["data"], "cache", None

    headers = {"User-Agent": random.choice(USER_AGENTS)}
    all_proxies = list(premium_proxies) + list(free_proxies)
    random.shuffle(all_proxies)

    proxy_idx = 0
    def get_next_proxy():
        nonlocal proxy_idx
        tries = 0
        while proxy_idx < len(all_proxies) and tries < max_attempts:
            scheme, addr = all_proxies[proxy_idx]
            proxy_idx += 1
            tries += 1

            if _is_proxy_cooled(addr):
                continue

            if PROXY_USER and PROXY_PASS and (scheme, addr) in premium_proxies:
                pu = f"{scheme}://{PROXY_USER}:{PROXY_PASS}@{addr}"
                pk = "premium"
            else:
                pu = f"{scheme}://{addr}"
                pk = "free"
            return {"http": pu, "https": pu}, pk, addr
        return None, "direct", None

    chosen_proxies, proxy_kind, p_addr = get_next_proxy()
    active_proxies = chosen_proxies
    all_items = []
    seen_in_fetch = set()

    url_khamsat = "https://khamsat.com/community/requests"
    for page_num in range(1, max_pages + 1):
        if len(all_items) >= 200:
            break
        page_url = f"{url_khamsat}?page={page_num}" if page_num > 1 else url_khamsat
        
        items = None
        while items is None:
            if chosen_proxies is None:
                scraper = _new_scraper()
                items = _fetch_khamsat_page(page_url, headers)
                if items is None:
                    break
            else:
                items = _fetch_khamsat_page(page_url, headers, chosen_proxies, proxy_kind, p_addr)
                if items is None:
                    chosen_proxies, proxy_kind, p_addr = get_next_proxy()
                    active_proxies = chosen_proxies
                    if chosen_proxies is None:
                        break
                        
        if not items:
            break
            
        for item in items:
            if item["id"] not in seen_in_fetch:
                seen_in_fetch.add(item["id"])
                all_items.append(item)
                
        time.sleep(random.uniform(0.25, 0.9))

    all_items = all_items[:200]
    if all_items:
        logger.info(f"Fetched {len(all_items)} Khamsat requests via {proxy_kind} ({p_addr})")
        _khamsat_project_cache["data"] = all_items
        _khamsat_project_cache["ts"] = time.time()
    return all_items, proxy_kind, p_addr, active_proxies

def _fetch_khamsat_page(page_url, headers, proxies=None, proxy_kind="direct", p_addr=None):
    global scraper, _last_block_alert_ts
    for attempt in range(REQUEST_RETRY_ATTEMPTS):
        try:
            resp = scraper.get(page_url, headers=headers, proxies=proxies or {}, timeout=15)
            if resp.status_code == 200:
                _register_proxy_result(p_addr, ok=True)
                return extract_khamsat_projects(resp.text)

            if resp.status_code in (403, 429):
                is_block = resp.status_code == 403
                delay, streak = _register_proxy_result(p_addr, ok=False, blocked=is_block)
                if is_block:
                    now = time.time()
                    if now - _last_block_alert_ts > 120:
                        _last_block_alert_ts = now
                        _notify_admins(
                            f"⚠️ Khamsat {resp.status_code} على proxy `{p_addr}`. "
                            f"تم تهدئة هذا البروكسي فقط لمدة ~{int(delay)} ثانية (streak={streak})."
                        )
                logger.warning(
                    f"Khamsat returned {resp.status_code} on {proxy_kind} {p_addr}. "
                    f"proxy cooldown ~{delay:.1f}s (attempt {attempt + 1}/{REQUEST_RETRY_ATTEMPTS})"
                )
                scraper = _new_scraper()
                if attempt < REQUEST_RETRY_ATTEMPTS - 1:
                    time.sleep(min(delay, 4.0))
                continue

            # Any other non-200 response gets a small proxy-level cooldown
            delay, streak = _register_proxy_result(p_addr, ok=False, blocked=False)
            logger.warning(
                f"Khamsat HTTP {resp.status_code} on {proxy_kind} {p_addr}. "
                f"proxy cooldown ~{delay:.1f}s (streak={streak})"
            )
            if attempt < REQUEST_RETRY_ATTEMPTS - 1:
                time.sleep(min(delay, 2.0))
        except Exception as e:
            delay, streak = _register_proxy_result(p_addr, ok=False, blocked=False)
            logger.warning(
                f"Khamsat Fetch error ({proxy_kind} {p_addr}): {e} | "
                f"proxy cooldown ~{delay:.1f}s (streak={streak}, attempt {attempt + 1}/{REQUEST_RETRY_ATTEMPTS})"
            )
            if attempt < REQUEST_RETRY_ATTEMPTS - 1:
                time.sleep(min(delay, 2.0))
    return None

def extract_khamsat_projects(html_text):
    if not html_text or not isinstance(html_text, str):
        return []
    soup = BeautifulSoup(html_text, "html.parser")
    project_elements = soup.select("a[href*='/community/requests/']")
    projects = []

    for el in project_elements:
        full_link = el.get("href")
        if not full_link:
            continue

        if full_link.startswith("/"):
            full_link = f"https://khamsat.com{full_link}"

        if "/community/requests/" not in full_link:
            continue

        try:
            project_id = full_link.split('/community/requests/')[-1].split('-')[0]
        except (IndexError, AttributeError):
            continue

        if not project_id.isdigit():
            continue

        title = el.get_text(strip=True)
        if not title:
            continue

        projects.append({
            "id": project_id,
            "title": title,
            "link": full_link,
        })

    return projects

def parse_duration(arg):
    """Parse duration string like 30, 2h, 1d into minutes."""
    arg = arg.strip().lower()
    if not arg:
        return None
    if arg.isdigit():
        return int(arg) # default is minutes
    
    # Check suffixes
    unit = arg[-1]
    num_part = arg[:-1]
    if not num_part.isdigit():
        return None
    
    val = int(num_part)
    if unit == 'm':
        return val
    elif unit == 'h':
        return val * 60
    elif unit == 'd':
        return val * 1440
    else:
        return None

def fetch_khamsat_project_description(link, scraper_session, proxies, proxy_kind="direct", p_addr=None):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        resp = scraper_session.get(link, headers=headers, proxies=proxies or {}, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            td = soup.find("td", class_="details-td")
            if td:
                import copy
                td_copy = copy.copy(td)
                h3 = td_copy.find("h3")
                if h3: h3.decompose()
                ul = td_copy.find("ul", class_="details-list")
                if ul: ul.decompose()
                
                desc = td_copy.get_text("\n", strip=True)
                if desc:
                    return desc
            
            for selector in [".post_content", ".post-content", ".article-content", ".post_body", ".post__body", ".post_message", ".message"]:
                d_el = soup.select_one(selector)
                if d_el:
                    desc = d_el.get_text("\n", strip=True)
                    if desc: return desc
        else:
            logger.warning(f"Failed to fetch Khamsat description: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching Khamsat description: {e}")
    return ""

def truncate_description(desc, max_words=25):
    if not desc:
        return ""
    words = desc.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + " ..."
    return desc


# ==============================================================================
# MONITORING ENGINE & REAL-TIME EMITTERS
# ==============================================================================
max_seen_id = 0

def check_khamsat():
    global max_seen_id, deep_scan_counter_khamsat

    deep_scan_counter_khamsat += 1
    pages_to_fetch = 5 if deep_scan_counter_khamsat % 20 == 0 else 1
    if deep_scan_counter_khamsat % 20 == 0:
        global _khamsat_project_cache
        _khamsat_project_cache["ts"] = 0

    projects, proxy_type, p_addr, chosen_proxies = fetch_khamsat_projects(max_pages=pages_to_fetch)
    if not projects:
        return

    new_projects = []
    with max_seen_id_lock:
        current_max = max_seen_id
        for p in projects:
            try:
                p_id = int(p["id"])
            except ValueError:
                continue
            if p_id > current_max:
                new_projects.append(p)
                if p_id > max_seen_id:
                    max_seen_id = p_id
        
        if max_seen_id > current_max:
            try:
                seen_file = _get_file_path("seen")
                tmp_path = seen_file + ".tmp"
                with open(tmp_path, "w") as f:
                    json.dump(max_seen_id, f)
                os.replace(tmp_path, seen_file)
            except Exception as e:
                logger.error(f"Failed to save Khamsat max seen ID: {e}")

    if new_projects:
        subs = _load_subscribers()
        muted = _load_muted_users()
        targets = (subs | _get_all_admins()) - muted
        keywords_map = _load_keywords()
        
        new_projects.sort(key=lambda x: int(x["id"]))
        
        for p in new_projects:
            desc = fetch_khamsat_project_description(p['link'], scraper, chosen_proxies, proxy_type, p_addr)
            truncated_desc = truncate_description(desc, max_words=25)
            
            msg_text = f"🚀 طلب جديد على خمسات:\n\n📝 *{p['title']}*"
            if truncated_desc:
                msg_text += f"\n\n📄 {truncated_desc}"
                
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "الذهاب للطلب 🌐", "url": p['link']}]
                ]
            }
            title_lower = p['title'].lower()
            sent_count = 0
            for cid in targets:
                cid_str = str(cid)
                user_kws = keywords_map.get(cid_str, [])
                if user_kws:
                    matched = False
                    for kw in user_kws:
                        if kw in title_lower:
                            matched = True
                            break
                    if not matched:
                        continue
                
                success, _ = _send_one(cid, msg_text, reply_markup=reply_markup, parse_mode="Markdown")
                if success:
                    sent_count += 1
            _increment_stats(sent_count)

def seed_max_id(projects):
    global max_seen_id
    ids = []
    for p in projects:
        try:
            ids.append(int(p["id"]))
        except ValueError:
            pass
    if ids:
        with max_seen_id_lock:
            max_seen_id = max(ids)
            try:
                seen_file = _get_file_path("seen")
                tmp_path = seen_file + ".tmp"
                with open(tmp_path, "w") as f:
                    json.dump(max_seen_id, f)
                os.replace(tmp_path, seen_file)
            except Exception as e:
                logger.error(f"Failed to seed Khamsat max seen ID: {e}")

def send_startup_snapshot(projects):
    admins = _get_all_admins()
    if not admins:
        return
    
    lines = [f"📸 لقطة تشغيلية لأحدث طلبات خمسات المتوفرة حالياً:\n"]
    for i, p in enumerate(projects[:5], 1):
        lines.append(f"{i}. {p['title']}\n🔗 {p['link']}\n")
    
    msg_text = "\n".join(lines)
    for cid in admins:
        _send_one(cid, msg_text)

# ==============================================================================
# TELEGRAM BOT CONTROLLERS (ADMIN INTERFACES)
# ==============================================================================
def generate_visual_dashboard():
    """Generate a premium-designed PNG infographic dashboard of the bot's stats."""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        import numpy as np
        
        subs = _load_subscribers()
        pending = _load_pending()
        blocked = _load_blocked()
        muted = _load_muted_users()
        stats = _get_stats()
        total_sent = stats.get('total_sent', 0)
        
        uptime_sec = int(time.time() - bot_start_time)
        h, m = divmod(uptime_sec // 60, 60)
        uptime_str = f"{h}h {m}m"
        
        fig = plt.figure(figsize=(10, 6), facecolor='#121214')
        fig.text(0.05, 0.90, "📊 Khamsat Scraper Bot Dashboard", fontsize=18, fontweight='bold', color='#FFFFFF')
        fig.text(0.05, 0.84, f"⏱ Uptime: {uptime_str}  |  📨 Total Sent: {total_sent}", fontsize=11, color='#A0A0A5')
        
        ax1 = fig.add_axes([0.08, 0.15, 0.42, 0.58], facecolor='#1E1E22')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_color('#3E3E42')
        ax1.spines['bottom'].set_color('#3E3E42')
        ax1.tick_params(colors='#A0A0A5')
        
        labels = ['Active\nSubs', 'Pending\nQueue', 'Muted\nUsers', 'Blocked\nUsers']
        values = [len(subs), len(pending), len(muted), len(blocked)]
        colors = ['#00E676', '#FFD600', '#29B6F6', '#FF1744']
        
        bars = ax1.barh(labels, values, color=colors, height=0.55, edgecolor='none')
        ax1.set_xlabel('Count', color='#A0A0A5', fontsize=10)
        ax1.set_title('User Database Metrics', color='#FFFFFF', fontsize=12, fontweight='bold', pad=15)
        
        for bar in bars:
            width = bar.get_width()
            ax1.text(width + 0.3, bar.get_y() + bar.get_height()/2, f"{int(width)}", 
                     va='center', ha='left', color='#FFFFFF', fontweight='bold', fontsize=10)
                     
        ax2 = fig.add_axes([0.58, 0.15, 0.35, 0.58], facecolor='#1E1E22')
        ax2.axis('off')
        
        rect = plt.Rectangle((0, 0), 1, 1, fill=True, color='#1E1E22', transform=ax2.transAxes, zorder=-1)
        ax2.add_patch(rect)
        
        ax2.text(0.1, 0.85, "⚙ SYSTEM STATUS", fontsize=11, fontweight='bold', color='#FF4B4B')
        ax2.text(0.1, 0.70, "• Site: Khamsat Community", fontsize=10, color='#FFFFFF')
        ax2.text(0.1, 0.58, f"• Active Proxy Pool: {len(premium_proxies) + len(free_proxies)} IPs", fontsize=10, color='#FFFFFF')
        ax2.text(0.1, 0.46, f"• Limit: {len(subs)} / {MAX_SUBSCRIBERS} Subs", fontsize=10, color='#FFFFFF')
        
        now = time.time()
        cooled_count = sum(1 for v in _proxy_cooldowns.values() if v > now)
        total_proxy_pool = max(1, len(premium_proxies) + len(free_proxies))
        status_indicator = "HEALTHY" if cooled_count < max(3, int(total_proxy_pool * 0.15)) else "DEGRADED"
        indicator_color = "#00E676" if status_indicator == "HEALTHY" else "#FFB300"
        ax2.text(0.1, 0.30, f"• Scraper Status: {status_indicator}", fontsize=10, color='#FFFFFF')
        ax2.plot(0.85, 0.85, marker='o', markersize=12, color=indicator_color)
        
        fig.text(0.05, 0.05, "Generated dynamically by Advanced Agentic Bot Engine", fontsize=8, color='#505055', fontstyle='italic')
        
        import io
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='#121214')
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception as e:
        logger.error(f"Error generating visual dashboard: {e}")
        return None

def _send_photo(chat_id, photo_buf, caption=""):
    """Send generated PNG chart to user."""
    if not KHAMSAT_BOT_TOKEN:
        return False
    tele_url = f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}/sendPhoto"
    try:
        photo_buf.seek(0)
        files = {"photo": ("dashboard.png", photo_buf, "image/png")}
        r = requests.post(tele_url, data={"chat_id": chat_id, "caption": caption}, files=files, timeout=20)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")
        return False

def _send_telegraph_menu(chat_id, callback=None):
    if not KHAMSAT_BOT_TOKEN:
        return
    base_url = f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}"
    
    now = time.time()
    if not telegraph_active:
        status_text = "🔴 **مغلقة (موقوفة تماماً)**"
    elif now < telegraph_freeze_until:
        remaining_sec = int(telegraph_freeze_until - now)
        m, s = divmod(remaining_sec, 60)
        h, m = divmod(m, 60)
        time_str = f"{h} ساعة و {m} دقيقة" if h > 0 else f"{m} دقيقة"
        status_text = f"❄️ **مجمدة مؤقتاً** (متبقي: `{time_str}`)"
    else:
        status_text = "🟢 **نشطة وتعمل تلقائياً كل دقيقتين**"
        
    menu_text = (
        "☁️ **إعدادات النسخ الاحتياطي السحابي لبوت خمسات (Telegraph Backup Settings):**\n\n"
        f"الحالة الحالية: {status_text}\n\n"
        "ℹ️ **الفرق بين مزامنة Telegraph والباك أب التلقائي:**\n"
        "• ☁️ **مزامنة Telegraph (هذا القسم):** هي مزامنة سحابية صامتة تحدث كل دقيقتين، حيث يتم حفظ نسخة مشفرة من قاعدة البيانات على خوادم Telegraph سحابياً. فائدتها أنها تُمكّن البوت من استرجاع كافة البيانات تلقائياً دون تدخل منك عند إعادة تشغيل البوت أو نقله لسيرفر جديد.\n"
        "• 💾 **الباك أب التلقائي:** يقوم بإنشاء ملف نسخة احتياطية (.json) وإرساله لك مباشرةً في شات التليجرام كل 3 دقائق. تكمن أهميته في إمكانية عمل رد (Reply) عليه وكتابة أمر `/restore` لاستعادة البيانات يدوياً في أي وقت.\n\n"
        "💡 يمكنك التحكم في تشغيل أو إيقاف النسخ الاحتياطي السحابي التلقائي إلى Telegraph واختيار مدة التجميد المناسبة من الأزرار أدناه:"
    )
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🟢 تشغيل / إلغاء التجميد", "callback_data": "tele_op:resume"}
            ],
            [
                {"text": "❄️ تجميد 30 دقيقة", "callback_data": "tele_op:freeze_30m"},
                {"text": "❄️ تجميد ساعتين", "callback_data": "tele_op:freeze_2h"}
            ],
            [
                {"text": "❄️ تجميد 12 ساعة", "callback_data": "tele_op:freeze_12h"},
                {"text": "🔴 إيقاف كامل (للأبد)", "callback_data": "tele_op:freeze_forever"}
            ],
            [
                {"text": "🔙 العودة للوحة التحكم", "callback_data": "tele_op:back_to_menu"}
            ]
        ]
    }
    
    if callback and "message" in callback:
        msg_id = callback["message"]["message_id"]
        requests.post(f"{base_url}/editMessageText", json={
            "chat_id": chat_id,
            "message_id": msg_id,
            "text": menu_text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        })
        requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback["id"]})
    else:
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": chat_id,
            "text": menu_text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        })

def _send_admin_menu(chat_id):
    if not KHAMSAT_BOT_TOKEN:
        return
    base_url = f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}"
    
    site_label = "خمسات"
    
    # Check current state of notifications to toggle button label dynamically
    status_emoji = "🔔" if notifications_active else "🔕"
    status_text = "تشغيل الإشعارات" if not notifications_active else "إيقاف الإشعارات"
    
    # Check current state of local backup to show in the menu
    now = time.time()
    if not backup_active:
        backup_status = "🔴 الباك اب: مجمد نهائياً"
    elif now < backup_freeze_until:
        remaining_sec = int(backup_freeze_until - now)
        m, s = divmod(remaining_sec, 60)
        h, m = divmod(m, 60)
        time_str = f"{h}س {m}د" if h > 0 else f"{m}د"
        backup_status = f"❄️ الباك اب: مجمد (باقي {time_str})"
    else:
        backup_status = "🟢 الباك اب: يعمل تلقائياً"

    # Check current state of Telegraph backup
    if not telegraph_active:
        telegraph_status = "🔴 مزامنة Telegraph: مغلقة"
    elif now < telegraph_freeze_until:
        remaining_sec = int(telegraph_freeze_until - now)
        m, s = divmod(remaining_sec, 60)
        h, m = divmod(m, 60)
        time_str = f"{h}س {m}د" if h > 0 else f"{m}د"
        telegraph_status = f"❄️ مزامنة Telegraph: مجمدة (باقي {time_str})"
    else:
        telegraph_status = "🟢 مزامنة Telegraph: تعمل تلقائياً"

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "👨‍💻 إدارة الأدمنز", "callback_data": "cmd:manage_admins"}
            ],
            [
                {"text": "⏳ طلبات معلقة", "callback_data": "cmd:view_pending"},
                {"text": "👥 المشتركين", "callback_data": "cmd:view_subs"}
            ],
            [
                {"text": "🚫 المحظورين", "callback_data": "cmd:view_blocked"},
                {"text": "📊 حالة البوت", "callback_data": "cmd:view_stats"}
            ],
            [
                {"text": f"{status_emoji} {status_text}", "callback_data": "cmd:toggle_notifications"}
            ],
            [
                {"text": backup_status, "callback_data": "cmd:manage_backup"}
            ],
            [
                {"text": telegraph_status, "callback_data": "cmd:manage_telegraph"}
            ],
            [
                {"text": "🔄 الفرق بين الباك أب والمزامنة", "callback_data": "cmd:explain_diff"}
            ],
            [
                {"text": "❓ المساعدة", "callback_data": "cmd:admin_help"},
                {"text": "📢 بث رسالة", "callback_data": "cmd:admin_broadcast_info"}
            ],
            [
                {"text": "🚀 إرسال آخر الطلبات", "callback_data": "cmd:send_last_5"}
            ]
        ]
    }
    requests.post(f"{base_url}/sendMessage", json={
        "chat_id": chat_id,
        "text": f"👑 لوحة تحكم أدمن بوت {site_label}:",
        "reply_markup": keyboard
    })

def handle_callback_query(callback):
    global notifications_active, backup_active, backup_freeze_until, telegraph_active, telegraph_freeze_until
    if not KHAMSAT_BOT_TOKEN:
        return
    base_url = f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}"
    
    cb_id = callback["id"]
    from_user = callback["from"]
    chat_id = from_user["id"]
    data = callback.get("data", "")
    
    role = 1
    if is_owner(chat_id): role = 3
    elif is_admin(chat_id): role = 2
    
    # 1. Handle FAQ clicks (accessible by everyone, including subscribers)
    if data.startswith("faq:"):
        faq_key = data.split("faq:", 1)[1]
        
        if faq_key == "how_works":
            faq_text = (
                "🤖 **كيف يعمل البوت؟**\n\n"
                "يقوم البوت بمراقبة موقع خمسات على مدار 24 ساعة بدون توقف.\n"
                "بمجرد نشر أي طلب جديد على خمسات، يقوم البوت بجلبه فوراً وإرساله لك في الشات مع زر مباشر للانتقال إلى صفحة الطلب وتقديم عرضك قبل الجميع! ⚡"
            )
        elif faq_key == "how_filter":
            faq_text = (
                "🏷️ **كيف أقوم بتفعيل فلتر التخصص؟**\n\n"
                "يمكنك فلترة الطلبات واستقبل ما يهمك فقط باستخدام أمر `/filter`:\n\n"
                "✍️ **طريقة التفعيل:**\n"
                "أرسل أمر `/filter` متبوعاً بالكلمات المفتاحية التي تهمك مفصولة بفواصل.\n"
                "مثال: `/filter برمجة, تصميم, كول سنتر`\n\n"
                "🗑️ **لإلغاء الفلتر واستقبال كل الطلبات:**\n"
                "أرسل أمر: `/filter_clear`\n\n"
                "🔍 **لعرض فلاترك الحالية:**\n"
                "أرسل أمر `/myfilters`."
            )
        else:
            faq_text = "⚠️ خيار غير معروف."
            
        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": faq_text, "parse_mode": "Markdown"})
        requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})
        return

    # 2. Admin operations
    if data.startswith("backup_op:"):
        op = data.split("backup_op:", 1)[1]
        
        if role < 2:
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "هنهذر ولا اي", "show_alert": True})
            return
            
        alert_text = ""
        if op == "resume":
            backup_active = True
            backup_freeze_until = 0
            alert_text = "🟢 تم تشغيل الباك أب وإلغاء التجميد بنجاح!"
        elif op == "freeze_30m":
            backup_active = True
            backup_freeze_until = time.time() + 30 * 60
            alert_text = "❄️ تم تجميد الباك أب لمدة 30 دقيقة."
        elif op == "freeze_2h":
            backup_active = True
            backup_freeze_until = time.time() + 2 * 3600
            alert_text = "❄️ تم تجميد الباك أب لمدة ساعتين."
        elif op == "freeze_6h":
            backup_active = True
            backup_freeze_until = time.time() + 6 * 3600
            alert_text = "❄️ تم تجميد الباك أب لمدة 6 ساعات."
        elif op == "freeze_12h":
            backup_active = True
            backup_freeze_until = time.time() + 12 * 3600
            alert_text = "❄️ تم تجميد الباك أب لمدة 12 ساعة."
        elif op == "freeze_24h":
            backup_active = True
            backup_freeze_until = time.time() + 24 * 3600
            alert_text = "❄️ تم تجميد الباك أب لمدة 24 ساعة."
        elif op == "freeze_forever":
            backup_active = False
            backup_freeze_until = 0
            alert_text = "🔴 تم تجميد الباك أب نهائياً ولن يتم إرساله تلقائياً."
        elif op == "back_to_menu":
            status_emoji = "🔔" if notifications_active else "🔕"
            status_text = "تشغيل الإشعارات" if not notifications_active else "إيقاف الإشعارات"
            
            now = time.time()
            if not backup_active:
                backup_status = "🔴 الباك اب: مجمد نهائياً"
            elif now < backup_freeze_until:
                remaining_sec = int(backup_freeze_until - now)
                m, s = divmod(remaining_sec, 60)
                h, m = divmod(m, 60)
                time_str = f"{h}س {m}د" if h > 0 else f"{m}د"
                backup_status = f"❄️ الباك اب: مجمد (باقي {time_str})"
            else:
                backup_status = "🟢 الباك اب: يعمل تلقائياً"

            if not telegraph_active:
                telegraph_status = "🔴 مزامنة Telegraph: مغلقة"
            elif now < telegraph_freeze_until:
                remaining_sec = int(telegraph_freeze_until - now)
                m, s = divmod(remaining_sec, 60)
                h, m = divmod(m, 60)
                time_str = f"{h}س {m}د" if h > 0 else f"{m}د"
                telegraph_status = f"❄️ مزامنة Telegraph: مجمدة (باقي {time_str})"
            else:
                telegraph_status = "🟢 مزامنة Telegraph: تعمل تلقائياً"

            keyboard = {
                "inline_keyboard": [
                    [{"text": "👨‍💻 إدارة الأدمنز", "callback_data": "cmd:manage_admins"}],
                    [{"text": "⏳ طلبات معلقة", "callback_data": "cmd:view_pending"}, {"text": "👥 المشتركين", "callback_data": "cmd:view_subs"}],
                    [{"text": "🚫 المحظورين", "callback_data": "cmd:view_blocked"}, {"text": "📊 حالة البوت", "callback_data": "cmd:view_stats"}],
                    [{"text": f"{status_emoji} {status_text}", "callback_data": "cmd:toggle_notifications"}],
                    [{"text": backup_status, "callback_data": "cmd:manage_backup"}],
                    [{"text": telegraph_status, "callback_data": "cmd:manage_telegraph"}],
                    [{"text": "🔄 الفرق بين الباك أب والمزامنة", "callback_data": "cmd:explain_diff"}],
                    [{"text": "❓ المساعدة", "callback_data": "cmd:admin_help"}, {"text": "📢 بث رسالة", "callback_data": "cmd:admin_broadcast_info"}],
                    [{"text": "🚀 إرسال آخر الطلبات", "callback_data": "cmd:send_last_5"}]
                ]
            }
            if "message" in callback:
                msg_id = callback["message"]["message_id"]
                requests.post(f"{base_url}/editMessageText", json={
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "text": "👑 لوحة تحكم أدمن بوت خمسات:",
                    "reply_markup": keyboard
                })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})
            return
            
        _save_notifications_state()
        requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": alert_text, "show_alert": True})
        _send_backup_menu(chat_id, callback)
        return

    if data.startswith("tele_op:"):
        op = data.split("tele_op:", 1)[1]
        
        if role < 2:
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "هنهذر ولا اي", "show_alert": True})
            return
        
        alert_text = ""
        if op == "resume":
            telegraph_active = True
            telegraph_freeze_until = 0
            alert_text = "🟢 تم تشغيل مزامنة Telegraph وإلغاء التجميد بنجاح!"
        elif op == "freeze_30m":
            telegraph_active = True
            telegraph_freeze_until = time.time() + 30 * 60
            alert_text = "❄️ تم تجميد مزامنة Telegraph لمدة 30 دقيقة."
        elif op == "freeze_2h":
            telegraph_active = True
            telegraph_freeze_until = time.time() + 2 * 3600
            alert_text = "❄️ تم تجميد مزامنة Telegraph لمدة ساعتين."
        elif op == "freeze_12h":
            telegraph_active = True
            telegraph_freeze_until = time.time() + 12 * 3600
            alert_text = "❄️ تم تجميد مزامنة Telegraph لمدة 12 ساعة."
        elif op == "freeze_forever":
            telegraph_active = False
            telegraph_freeze_until = 0
            alert_text = "🔴 تم تعطيل مزامنة Telegraph نهائياً."
        elif op == "back_to_menu":
            status_emoji = "🔔" if notifications_active else "🔕"
            status_text = "تشغيل الإشعارات" if not notifications_active else "إيقاف الإشعارات"
            
            now = time.time()
            if not backup_active:
                backup_status = "🔴 الباك اب: مجمد نهائياً"
            elif now < backup_freeze_until:
                remaining_sec = int(backup_freeze_until - now)
                m, s = divmod(remaining_sec, 60)
                h, m = divmod(m, 60)
                time_str = f"{h}س {m}د" if h > 0 else f"{m}د"
                backup_status = f"❄️ الباك اب: مجمد (باقي {time_str})"
            else:
                backup_status = "🟢 الباك اب: يعمل تلقائياً"

            if not telegraph_active:
                telegraph_status = "🔴 مزامنة Telegraph: مغلقة"
            elif now < telegraph_freeze_until:
                remaining_sec = int(telegraph_freeze_until - now)
                m, s = divmod(remaining_sec, 60)
                h, m = divmod(m, 60)
                time_str = f"{h}س {m}د" if h > 0 else f"{m}د"
                telegraph_status = f"❄️ مزامنة Telegraph: مجمدة (باقي {time_str})"
            else:
                telegraph_status = "🟢 مزامنة Telegraph: تعمل تلقائياً"

            keyboard = {
                "inline_keyboard": [
                    [{"text": "👨‍💻 إدارة الأدمنز", "callback_data": "cmd:manage_admins"}],
                    [{"text": "⏳ طلبات معلقة", "callback_data": "cmd:view_pending"}, {"text": "👥 المشتركين", "callback_data": "cmd:view_subs"}],
                    [{"text": "🚫 المحظورين", "callback_data": "cmd:view_blocked"}, {"text": "📊 حالة البوت", "callback_data": "cmd:view_stats"}],
                    [{"text": f"{status_emoji} {status_text}", "callback_data": "cmd:toggle_notifications"}],
                    [{"text": backup_status, "callback_data": "cmd:manage_backup"}],
                    [{"text": telegraph_status, "callback_data": "cmd:manage_telegraph"}],
                    [{"text": "🔄 الفرق بين الباك أب والمزامنة", "callback_data": "cmd:explain_diff"}],
                    [{"text": "❓ المساعدة", "callback_data": "cmd:admin_help"}, {"text": "📢 بث رسالة", "callback_data": "cmd:admin_broadcast_info"}],
                    [{"text": "🚀 إرسال آخر الطلبات", "callback_data": "cmd:send_last_5"}]
                ]
            }
            if "message" in callback:
                msg_id = callback["message"]["message_id"]
                requests.post(f"{base_url}/editMessageText", json={
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "text": "👑 لوحة تحكم أدمن بوت خمسات:",
                    "reply_markup": keyboard
                })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})
            return
            
        _save_notifications_state()
        requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": alert_text, "show_alert": True})
        _send_telegraph_menu(chat_id, callback)
        return

    if data.startswith("cmd:"):
        cmd = data.split("cmd:", 1)[1]
        
        if role < 2:
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "هنهذر ولا اي", "show_alert": True})
            return
            
        if cmd == "manage_backup":
            _send_backup_menu(chat_id, callback)
            return
            
        elif cmd == "manage_telegraph":
            _send_telegraph_menu(chat_id, callback)
            return
            
        elif cmd == "explain_diff":
            diff_text = (
                "🔄 **الفرق التفصيلي بين الباك أب التلقائي ومزامنة Telegraph:**\n\n"
                "💾 **1. النسخ الاحتياطي التلقائي (Local Backup):**\n"
                "• **كيف يعمل؟** يقوم البوت بتجميع كافة البيانات (المشتركين، الفلاتر، المحظورين، إلخ) وإرسالها لك مباشرة في شات التليجرام كملف `.json` كل 3 دقائق.\n"
                "• **فائدته:** يمنحك تحكماً يدوياً كاملاً؛ حيث يمكنك عمل رد (Reply) على أي ملف باك أب أرسله البوت وكتابة أمر `/restore` لاستعادة البيانات فوراً.\n\n"
                "☁️ **2. مزامنة Telegraph السحابية (Telegraph Sync):**\n"
                "• **كيف تعمل؟** يقوم البوت تلقائياً ومحلياً بحفظ نسخة مشفرة من قاعدة البيانات ورفعها سحابياً وتحديثها على صفحة Telegraph سحابية خاصة كل دقيقتين بصمت وبدون إرسال ملفات تملأ الشات.\n"
                "• **فائدتها:** استرجاع البيانات تلقائياً بالكامل بدون أي تدخل بشري بمجرد تشغيل البوت أو نقله إلى سيرفر جديد كلياً في حال حدوث أي عطل أو حذف للملفات.\n\n"
                "💡 **الخلاصة:** الباك أب التلقائي هو وسيلة الاستعادة **اليدوية** المضمونة بملفات تليجرام، بينما مزامنة Telegraph هي الملاذ **التلقائي والسحابي الصامت** للتعافي الذاتي عند إعادة التشغيل."
            )
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": diff_text, "parse_mode": "Markdown"})
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})
            return
            
        elif cmd == "delete_broadcast":
            broadcast_msgs = _load_broadcast_msgs()
            if not broadcast_msgs:
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "⚠️ لا توجد رسالة بث مسجلة للمسح.", "show_alert": True})
                return
                
            deleted = 0
            for cid, mid in list(broadcast_msgs.items()):
                try:
                    requests.post(f"{base_url}/deleteMessage", json={"chat_id": int(cid), "message_id": int(mid)}, timeout=5)
                    deleted += 1
                except Exception:
                    pass
            _save_broadcast_msgs({})
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": f"✅ تم حذف البث لـ {deleted} مستخدم.", "show_alert": True})
            
        elif cmd == "view_pending":
            pending = _load_pending()
            if not pending:
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "✅ لا توجد طلبات معلقة حالياً.", "show_alert": True})
            else:
                lines = ["⏳ طلبات الاشتراك المعلقة:\n"]
                for pid in sorted(pending):
                    lines.append(f"🆔 {pid}  →  /approve {pid}")
                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines)})
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})
                
        elif cmd == "view_stats":
            subs = _load_subscribers()
            pending = _load_pending()
            blocked = _load_blocked()
            stats = _get_stats()
            uptime_sec = int(time.time() - bot_start_time)
            h, m = divmod(uptime_sec // 60, 60)
            muted_count = len(_load_muted_users())
            
            id_label = f"أعلى ID طلب شوفناه: {max_seen_id}"
                
            status_msg = (
                f"📊 حالة بوت خمسات:\n"
                f"⏱️ وقت التشغيل: {h}ساعة {m}دقيقة\n"
                f"👥 المشتركين: {len(subs)} / {MAX_SUBSCRIBERS}\n"
                f"🔕 كتموا إشعاراتهم: {muted_count}\n"
                f"⏳ طلبات معلقة: {len(pending)}\n"
                f"🚫 محظورين: {len(blocked)}\n"
                f"👑 أدمنز: {len(_get_all_admins())}\n"
                f"🔢 {id_label}\n"
                f"📨 إجمالي رسائل مرسلة: {stats.get('total_sent', 0)}"
            )
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": status_msg})
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})
            
            # Premium addition: automatically send visual status graph!
            photo_buf = generate_visual_dashboard()
            if photo_buf:
                _send_photo(chat_id, photo_buf, caption="📊 الرسم البياني لحالة الأداء والنشاط")
                
        elif cmd == "view_visual":
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "⏳ جاري توليد التقرير البصري..."})
            photo_buf = generate_visual_dashboard()
            if photo_buf:
                _send_photo(chat_id, photo_buf, caption="📊 لوحة التقارير البصرية الذكية لـ خمسات")
            else:
                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ فشل توليد التقرير البصري."})

        elif cmd == "manage_admins":
            if role < 3:
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "⚠️ عذراً، هذا القسم مخصص لمالك البوت فقط.", "show_alert": True})
                return
            admins = _get_all_admins()
            lines = ["👨‍💻 **إدارة الأدمنز الحاليين لبوت خمسات:**\n"]
            for idx, aid in enumerate(sorted(admins), 1):
                lines.append(f"{idx}. 🆔 `{aid}`")
            lines.append("\n💡 **التحكم بالصلاحيات:**")
            lines.append("➕ لإضافة أدمن: أرسل `/add_admin <id>`")
            lines.append("➖ لحذف أدمن: أرسل `/remove_admin <id>`")
            
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines), "parse_mode": "Markdown"})
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})

        elif cmd == "view_subs":
            subs = _load_subscribers()
            if not subs:
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "👥 لا يوجد أي مشتركين مسجلين حالياً.", "show_alert": True})
            else:
                lines = [f"👥 **المشتركين النشطين (العدد: {len(subs)}):**\n"]
                for sid in sorted(subs):
                    lines.append(f"🆔 `{sid}`  →  /block {sid}")
                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines), "parse_mode": "Markdown"})
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})

        elif cmd == "view_blocked":
            blocked = _load_blocked()
            if not blocked:
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "🚫 لا توجد حسابات محظورة حالياً.", "show_alert": True})
            else:
                lines = [f"🚫 **المستخدمين المحظورين (العدد: {len(blocked)}):**\n"]
                for bid in sorted(blocked):
                    lines.append(f"🆔 `{bid}`  →  /unblock {bid}")
                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines), "parse_mode": "Markdown"})
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})

        elif cmd == "toggle_notifications":
            notifications_active = not notifications_active
            _save_notifications_state()
            
            state_label = "✅ تم تشغيل الإشعارات وجاري الفحص المستمر لموقع خمسات!" if notifications_active else "🔕 تم إيقاف الإشعارات وتجميد الفحص لموقع خمسات مؤقتاً."
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": state_label, "show_alert": True})
            
            status_emoji = "🔔" if notifications_active else "🔕"
            status_text = "تشغيل الإشعارات" if not notifications_active else "إيقاف الإشعارات"
            
            now = time.time()
            if not backup_active:
                backup_status = "🔴 الباك اب: مجمد نهائياً"
            elif now < backup_freeze_until:
                remaining_sec = int(backup_freeze_until - now)
                m, s = divmod(remaining_sec, 60)
                h, m = divmod(m, 60)
                time_str = f"{h}س {m}د" if h > 0 else f"{m}د"
                backup_status = f"❄️ الباك اب: مجمد (باقي {time_str})"
            else:
                backup_status = "🟢 الباك اب: يعمل تلقائياً"

            if not telegraph_active:
                telegraph_status = "🔴 مزامنة Telegraph: مغلقة"
            elif now < telegraph_freeze_until:
                remaining_sec = int(telegraph_freeze_until - now)
                m, s = divmod(remaining_sec, 60)
                h, m = divmod(m, 60)
                time_str = f"{h}س {m}د" if h > 0 else f"{m}د"
                telegraph_status = f"❄️ مزامنة Telegraph: مجمدة (باقي {time_str})"
            else:
                telegraph_status = "🟢 مزامنة Telegraph: تعمل تلقائياً"

            keyboard = {
                "inline_keyboard": [
                    [{"text": "👨‍💻 إدارة الأدمنز", "callback_data": "cmd:manage_admins"}],
                    [{"text": "⏳ طلبات معلقة", "callback_data": "cmd:view_pending"}, {"text": "👥 المشتركين", "callback_data": "cmd:view_subs"}],
                    [{"text": "🚫 المحظورين", "callback_data": "cmd:view_blocked"}, {"text": "📊 حالة البوت", "callback_data": "cmd:view_stats"}],
                    [{"text": f"{status_emoji} {status_text}", "callback_data": "cmd:toggle_notifications"}],
                    [{"text": backup_status, "callback_data": "cmd:manage_backup"}],
                    [{"text": telegraph_status, "callback_data": "cmd:manage_telegraph"}],
                    [{"text": "🔄 الفرق بين الباك أب والمزامنة", "callback_data": "cmd:explain_diff"}],
                    [{"text": "❓ المساعدة", "callback_data": "cmd:admin_help"}, {"text": "📢 بث رسالة", "callback_data": "cmd:admin_broadcast_info"}],
                    [{"text": "🚀 إرسال آخر الطلبات", "callback_data": "cmd:send_last_5"}]
                ]
            }
            if "message" in callback:
                msg_id = callback["message"]["message_id"]
                requests.post(f"{base_url}/editMessageReplyMarkup", json={
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "reply_markup": keyboard
                })

        elif cmd == "admin_help":
            help_text = (
                "❓ **دليل أوامر الأدمن الكاملة لبوت خمسات (Admin & Owner Commands):**\n\n"
                "👑 **👑 أوامر المالك فقط (Owner Only):**\n"
                "➕ `/add_admin <id>` — إضافة أدمن جديد\n"
                "➖ `/remove_admin <id>` — إزالة أدمن\n"
                "💾 `/backup` — أخذ نسخة احتياطية للملفات يدوياً\n\n"
                "👮‍♂️ **👮‍♂️ أوامر الإشراف (Admins & Owners):**\n"
                "💻 `/menu` — فتح لوحة تحكم الأدمن التفاعلية\n"
                "🆔 `/ids` — عرض معرفات (IDs) المشتركين المسجلين\n"
                "✅ `/approve <id>` — قبول مشترك معلق\n"
                "❌ `/reject <id>` — رفض مشترك معلق\n"
                "⏳ `/pending` — عرض طلبات الاشتراك المعلقة\n"
                "🚫 `/block <id>` — حظر مستخدم نهائياً\n"
                "🔓 `/unblock <id>` — إلغاء حظر مستخدم\n"
                "🔕 `/mute <id>` — كتم إشعارات مستخدم معين بقوة\n"
                "🔔 `/unmute <id>` — إلغاء كتم إشعارات مستخدم معين\n"
                "🔇 `/muteall` — كتم إشعارات جميع المشتركين بقوة\n"
                "🔊 `/unmuteall` — إلغاء كتم إشعارات جميع المشتركين\n"
                "📢 `/broadcast <رسالة>` — إرسال بث عام للجميع مع ميزة المسح التفاعلي\n"
                "🚀 `/send_last <عدد>` — جلب وإرسال عدد من أحدث الطلبات\n"
                "📊 `/status` — عرض حالة البوت والإحصائيات الحالية للرسائل والباك أب\n"
                "💾 `/restore` — استعادة البيانات بالرد (Reply) على ملف الباك أب\n"
                "⚙️ `/backup_menu` — فتح لوحة التحكم التفاعلية في الباك أب\n"
                "❄️ `/freeze_backup` أو `/backup_freeze` أو `/backup_stop` أو `/backup_end` — تجميد الباك أب التلقائي (مثال: `/freeze_backup 30m` أو `2h` أو `1d`)\n"
                "🟢 `/resume_backup` أو `/backup_resume` أو `/backup_play` — تشغيل وإلغاء تجميد الباك أب التلقائي\n"
                "❄️ `/telegraph_freeze` أو `/telegraph_stop` أو `/telegraph_end` — تجميد المزامنة السحابية Telegraph (مثال: `/telegraph_freeze 2h`)\n"
                "🟢 `/telegraph_resume` أو `/telegraph_play` — تشغيل وإلغاء تجميد مزامنة Telegraph"
            )
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": help_text, "parse_mode": "Markdown"})
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})

        elif cmd == "admin_broadcast_info":
            info_text = (
                "📢 **كيفية إرسال بث رسالة للجميع:**\n\n"
                "أرسل الأمر متبوعاً بالرسالة التي ترغب في بثها لجميع المشتركين والأدمنز.\n\n"
                "✍️ **طريقة الإرسال:**\n"
                "`/broadcast أهلاً بكم، تم إجراء تحديثات جديدة لبوت خمسات!`\n\n"
                "🗑️ **مسح الرسالة للجميع:**\n"
                "بمجرد إرسال البث، سيظهر لك زر تفاعلي لحذف الرسالة فوراً من شات جميع من استلمها في حال حدوث خطأ!"
            )
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": info_text, "parse_mode": "Markdown"})
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})

        elif cmd == "send_last_5":
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "🚀 جاري جلب وإرسال آخر 5 طلبات..."})
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⏳ جاري جلب آخر 5 طلبات..."})
            
            projects, _, _, _ = fetch_khamsat_projects()
            if projects:
                to_send = projects[:5]
                msg_lines = ["🚀 إليك أحدث 5 طلبات تم طرحها على خمسات:\n"]
                for p in to_send:
                    msg_lines.append(f"📝 {p['title']}\n🔗 {p['link']}\n")
                
                broadcast_msg = "\n".join(msg_lines)
                
                with subscribers_lock:
                    subs = _load_subscribers()
                all_targets = subs | _get_all_admins()
                sent = 0
                msg_map = {}
                for target in all_targets:
                    try:
                        r = requests.post(f"{base_url}/sendMessage", json={"chat_id": target, "text": broadcast_msg}, timeout=10)
                        if r.status_code == 200:
                            sent += 1
                            data = r.json()
                            msg_map[str(target)] = data["result"]["message_id"]
                    except Exception:
                        pass
                if msg_map:
                    _save_broadcast_msgs(msg_map)
                    kb = {"inline_keyboard": [[{"text": "🗑️ مسح للجميع", "callback_data": "cmd:delete_broadcast"}]]}
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إرسال الطلبات لـ {sent}/{len(all_targets)} مستخدم.", "reply_markup": kb})
                else:
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لم يتم إرسال الرسالة لأي شخص."})
            else:
                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لم يتم العثور على أي طلبات حالياً."})

# ==============================================================================
# PARAMETERIZED UPDATE HANDLER & COMMAND ROUTER
# ==============================================================================
def handle_updates_loop(poll_interval=2):
    if not KHAMSAT_BOT_TOKEN:
        logger.warning("Polling disabled for Khamsat (token is missing)")
        return

    base_url = f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}"
    offset = 0
    _load_roles()

    logger.info("Started polling updates for Khamsat...")
    while True:
        try:
            r = requests.get(f"{base_url}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=25).json()
            if not r.get("ok"):
                time.sleep(poll_interval)
                continue

            for update in r.get("result", []):
                offset = update["update_id"] + 1
                
                if "callback_query" in update:
                    handle_callback_query(update["callback_query"])
                    continue

                msg = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                if not chat_id or not text:
                    continue

                text = text.strip()
                if not text.startswith("/"):
                    continue

                cmd = text.split()[0].split("@")[0].lower() if text else ""

                role = 1
                if is_owner(chat_id):
                    role = 3
                elif is_admin(chat_id):
                    role = 2

                cmd_roles = {
                    "/add_admin":    3,
                    "/remove_admin": 3,
                    "/backup":       3,
                    "/restore":      2,
                    "/freeze_backup": 2,
                    "/backup_freeze": 2,
                    "/backup_stop":   2,
                    "/backup_end":    2,
                    "/resume_backup": 2,
                    "/backup_resume": 2,
                    "/backup_play":   2,
                    "/backup_menu":   2,
                    "/telegraph_freeze": 2,
                    "/telegraph_stop":   2,
                    "/telegraph_end":    2,
                    "/telegraph_resume": 2,
                    "/telegraph_play":   2,
                    "/menu":      2,
                    "/ids":       2,
                    "/broadcast": 2,
                    "/send_last": 2,
                    "/block":     2,
                    "/unblock":   2,
                    "/mute":      2,
                    "/unmute":    2,
                    "/muteall":   2,
                    "/unmuteall": 2,
                    "/approve":   2,
                    "/reject":    2,
                    "/pending":   2,
                    "/status":    2,
                    "/dashboard": 2,
                    "/vstatus":   2,

                    "/start":       1,
                    "/subscribe":   1,
                    "/unsubscribe": 1,
                    "/mymute":      1,
                    "/pause":       1,
                    "/myunmute":    1,
                    "/resume":      1,
                    "/ping":        1,
                    "/help":        1,
                    "/filter":       1,
                    "/myfilters":    1,
                    "/filter_clear": 1,
                    "/filter_off":   1,
                }

                if cmd in cmd_roles:
                    if role < cmd_roles[cmd]:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "هنهذر ولا اي"})
                        continue
                else:
                    continue

                if role == 1 and _is_rate_limited(chat_id):
                    continue

                if cmd in ("/start", "/subscribe"):
                    with subscribers_lock:
                        blocked = _load_blocked()
                    if chat_id in blocked:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🚫 تم حظرك من استخدام هذا البوت."})
                        continue

                    if add_subscriber(chat_id):
                        welcome_msg = "لا تنسي الدعاء لنا و لامواتنا و اموات المسلمين\nوصلي علي النبي يا جدع"
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": welcome_msg})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ عذراً، لا يمكن الاشتراك الآن (ربما وصل البوت للحد الأقصى)."})

                    if role >= 2:
                        _send_admin_menu(chat_id)

                elif cmd == "/menu":
                    _send_admin_menu(chat_id)

                elif cmd == "/approve":
                    parts = text.split()
                    if len(parts) >= 2:
                        target_id = parts[1].strip()
                        try:
                            target_id = int(target_id)
                            if add_subscriber(target_id):
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم قبول المستخدم {target_id}"})
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": (
                                    f"🎉 مرحباً! تم قبول اشتراكك في بوت خمسات.\n\n"
                                    "ستصلك إشعارات الطلبات الجديدة فور نشرها.\n\n"
                                    "💡 أوامر مفيدة:\n"
                                    "/mymute - إيقاف الإشعارات مؤقتاً\n"
                                    "/myunmute - إعادة تفعيل الإشعارات\n"
                                    "/unsubscribe - إلغاء الاشتراك"
                                )})
                            else:
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"⚠️ فشل قبول {target_id} (ربما وصل الحد الأقصى)"})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /approve <id>"})

                elif cmd == "/reject":
                    parts = text.split()
                    if len(parts) >= 2:
                        target_id = parts[1].strip()
                        try:
                            target_id = int(target_id)
                            reject_subscriber(target_id)
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"❌ تم رفض المستخدم {target_id}"})
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "❌ عذراً، تم رفض طلب اشتراكك."})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /reject <id>"})

                elif cmd == "/ids":
                    with subscribers_lock:
                        subs = _load_subscribers()
                    if subs:
                        lines = ["👥 المشتركين المعتمدين:\n"]
                        for i, sid in enumerate(sorted(subs), 1):
                            marker = "👑" if sid in _get_all_admins() else "👤"
                            lines.append(f"{i}. {marker} {sid}  →  /block {sid}")
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines)})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "📭 لا يوجد مشتركين حالياً."})

                elif cmd == "/add_admin":
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target_id = int(parts[1].strip())
                            if target_id == get_owner_id():
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "أنت المالك بالفعل!"})
                            else:
                                with subscribers_lock:
                                    admins = _load_admins()
                                    admins.add(target_id)
                                    _save_admins(admins)
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إضافة الأدمن {target_id}"})
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "👑 تم ترقيتك لتصبح أدمن في البوت!"})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /add_admin <id>"})

                elif cmd == "/remove_admin":
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target_id = int(parts[1].strip())
                            with subscribers_lock:
                                admins = _load_admins()
                                admins.discard(target_id)
                                _save_admins(admins)
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إزالة الأدمن {target_id}"})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /remove_admin <id>"})

                elif cmd == "/block":
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target_id = int(parts[1].strip())
                            if target_id == get_owner_id():
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لا يمكنك حظر نفسك!"})
                            else:
                                with subscribers_lock:
                                    blocked = _load_blocked()
                                    blocked.add(target_id)
                                    _save_blocked(blocked)
                                    subs = _load_subscribers()
                                    subs.discard(target_id)
                                    _save_subscribers(subs)
                                    pending = _load_pending()
                                    pending.discard(target_id)
                                    _save_pending(pending)
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"🚫 تم حظر المستخدم {target_id}"})
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "🚫 تم حظرك من هذا البوت."})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /block <id>"})

                elif cmd == "/unblock":
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target_id = int(parts[1].strip())
                            with subscribers_lock:
                                blocked = _load_blocked()
                                blocked.discard(target_id)
                                _save_blocked(blocked)
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إلغاء حظر المستخدم {target_id}"})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /unblock <id>"})

                elif cmd == "/mute":
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target_id = int(parts[1].strip())
                            if target_id == get_owner_id():
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لا يمكنك كتم إشعارات المالك!"})
                            else:
                                with subscribers_lock:
                                    mu = _load_muted_users()
                                    mu.add(target_id)
                                    _save_muted_users(mu)
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"🔕 تم كتم إشعارات المستخدم {target_id} بنجاح."})
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "🔕 لقد قام الأدمن بكتم إشعاراتك مؤقتاً."})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /mute <id>"})

                elif cmd == "/unmute":
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target_id = int(parts[1].strip())
                            with subscribers_lock:
                                mu = _load_muted_users()
                                mu.discard(target_id)
                                _save_muted_users(mu)
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"🔔 تم تفعيل إشعارات المستخدم {target_id} بنجاح."})
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "🔔 تم إعادة تفعيل إشعاراتك بواسطة الأدمن!"})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /unmute <id>"})

                elif cmd == "/muteall":
                    with subscribers_lock:
                        subs = _load_subscribers()
                        mu = _load_muted_users()
                        for s in subs:
                            mu.add(s)
                        _save_muted_users(mu)
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔕 تم كتم إشعارات جميع المشتركين بنجاح."})

                elif cmd == "/unmuteall":
                    with subscribers_lock:
                        mu = _load_muted_users()
                        mu.clear()
                        _save_muted_users(mu)
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔔 تم إعادة تفعيل الإشعارات لجميع المشتركين بنجاح."})

                elif cmd == "/broadcast":
                    broadcast_msg = text[len("/broadcast"):].strip()
                    if broadcast_msg:
                        with subscribers_lock:
                            subs = _load_subscribers()
                        all_targets = subs | _get_all_admins()
                        sent = 0
                        msg_map = {}
                        for target in all_targets:
                            try:
                                r = requests.post(f"{base_url}/sendMessage", json={"chat_id": target, "text": f"📢 السلام عليكم و رحمة الله و بركاته:\n\n{broadcast_msg}"}, timeout=10)
                                if r.status_code == 200:
                                    sent += 1
                                    data = r.json()
                                    msg_map[str(target)] = data["result"]["message_id"]
                            except Exception:
                                pass
                        
                        if msg_map:
                            _save_broadcast_msgs(msg_map)
                            kb = {"inline_keyboard": [[{"text": "🗑️ مسح الرسالة للجميع", "callback_data": "cmd:delete_broadcast"}]]}
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إرسال الرسالة لـ {sent}/{len(all_targets)} مستخدم.", "reply_markup": kb})
                        else:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لم يتم إرسال الرسالة لأي شخص."})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /broadcast <رسالتك>"})

                elif cmd == "/send_last":
                    parts = text.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        count = int(parts[1])
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"⏳ جاري جلب آخر {count} طلبات..."})
                        
                        projects, _, _, _ = fetch_khamsat_projects()
                            
                        if not projects:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ لم يتم العثور على طلبات حالياً."})
                        else:
                            to_send = projects[:count]
                            msg_lines = [f"🚀 إليك آخر {len(to_send)} طلبات تم طرحها على خمسات:\n"]
                            for p in to_send:
                                msg_lines.append(f"📝 {p['title']}\n🔗 {p['link']}\n")
                            
                            broadcast_msg = "\n".join(msg_lines)
                            
                            with subscribers_lock:
                                subs = _load_subscribers()
                            all_targets = subs | _get_all_admins()
                            sent = 0
                            msg_map = {}
                            for target in all_targets:
                                try:
                                    r = requests.post(f"{base_url}/sendMessage", json={"chat_id": target, "text": broadcast_msg}, timeout=10)
                                    if r.status_code == 200:
                                        sent += 1
                                        data = r.json()
                                        msg_map[str(target)] = data["result"]["message_id"]
                                except Exception:
                                    pass
                            
                            if msg_map:
                                _save_broadcast_msgs(msg_map)
                                kb = {"inline_keyboard": [[{"text": "🗑️ مسح للجميع", "callback_data": "cmd:delete_broadcast"}]]}
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إرسال الطلبات لـ {sent}/{len(all_targets)} مستخدم.", "reply_markup": kb})
                            else:
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لم يتم إرسال الرسالة لأي شخص."})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /send_last <رقم>\nمثال: /send_last 5"})

                elif cmd == "/unsubscribe":
                    remove_subscriber(chat_id)
                    mu = _load_muted_users()
                    mu.discard(chat_id)
                    _save_muted_users(mu)
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ تم إلغاء اشتراكك."})

                elif cmd in ("/mymute", "/pause"):
                    with subscribers_lock:
                        subs = _load_subscribers()
                    if chat_id in subs or is_admin(chat_id):
                        mu = _load_muted_users()
                        mu.add(chat_id)
                        _save_muted_users(mu)
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔕 تم كتم الإشعارات لحسابك مؤقتاً.\nأرسل /myunmute لإعادة تفعيلها."})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ أنت لست مشتركاً."})

                elif cmd in ("/myunmute", "/resume"):
                    mu = _load_muted_users()
                    mu.discard(chat_id)
                    _save_muted_users(mu)
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔔 تم إعادة تفعيل إشعاراتك!"})

                elif cmd == "/backup":
                    try:
                        backup_data = generate_system_backup()
                        backup_bytes = json.dumps(backup_data, ensure_ascii=False, indent=2).encode("utf-8")
                        import io
                        bio = io.BytesIO(backup_bytes)
                        bio.name = "system_backup_data.json"
                        requests.post(
                            f"{base_url}/sendDocument",
                            data={"chat_id": chat_id, "caption": "💾 نسخة احتياطية كاملة وشاملة لبوت خمسات — استخدم /restore بالرد على هذا الملف لاستعادة كافة البيانات دفعة واحدة."},
                            files={"document": ("system_backup_data.json", bio, "application/json")},
                            timeout=20
                        )
                    except Exception as _be:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"⚠️ فشل إنشاء الباك أب: {_be}"})

                elif cmd == "/restore":
                    replied = msg.get("reply_to_message", {})
                    doc = replied.get("document", {})
                    file_id = doc.get("file_id")
                    if not file_id:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ استخدم /restore بالرد (Reply) على ملف الباك أب الذي أرسله البوت."})
                    else:
                        try:
                            r_fp = requests.get(f"{base_url}/getFile", params={"file_id": file_id}, timeout=10).json()
                            if not r_fp.get("ok"):
                                raise Exception("getFile failed")
                            tg_path = r_fp["result"]["file_path"]
                            r_dl = requests.get(f"https://api.telegram.org/file/bot{KHAMSAT_BOT_TOKEN}/{tg_path}", timeout=20)
                            backup_data = json.loads(r_dl.content.decode("utf-8"))
                            
                            restore_system_backup(backup_data)
                                
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "✅ تم استعادة جميع البيانات بنجاح! 🎉"})
                            logger.info(f"Full restore triggered by {chat_id}")
                        except Exception as _re:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"❌ فشل الاستعادة: {_re}"})

                elif cmd in ("/freeze_backup", "/backup_freeze", "/backup_stop", "/backup_end"):
                    parts = text.split()
                    if len(parts) >= 2:
                        duration_str = parts[1].strip()
                        minutes = parse_duration(duration_str)
                        if minutes is not None:
                            backup_active = True
                            backup_freeze_until = time.time() + minutes * 60
                            _save_notifications_state()
                            
                            h, m = divmod(minutes, 60)
                            d, h = divmod(h, 24)
                            time_parts = []
                            if d > 0: time_parts.append(f"{d} يوم")
                            if h > 0: time_parts.append(f"{h} ساعة")
                            if m > 0: time_parts.append(f"{m} دقيقة")
                            time_desc = " و ".join(time_parts)
                            
                            response = f"❄️ تم تجميد النسخ الاحتياطي التلقائي بنجاح لمدة {time_desc}."
                        else:
                            response = f"⚠️ صيغة المدة غير صالحة! استخدم أرقاماً بالدقائق (مثال: `{cmd} 30`) أو بالساعات/الأيام (مثال: `2h` أو `1d`)."
                    else:
                        backup_active = False
                        backup_freeze_until = 0
                        _save_notifications_state()
                        response = "🔴 تم تجميد النسخ الاحتياطي التلقائي نهائياً (للأبد) حتى تقوم بتشغيله مجدداً."
                        
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": response, "parse_mode": "Markdown"})

                elif cmd in ("/resume_backup", "/backup_resume", "/backup_play"):
                    backup_active = True
                    backup_freeze_until = 0
                    _save_notifications_state()
                    response = "🟢 تم إلغاء التجميد وتشغيل النسخ الاحتياطي التلقائي بنجاح كل 3 دقائق!"
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": response})

                elif cmd == "/backup_menu":
                    _send_backup_menu(chat_id)

                elif cmd in ("/telegraph_freeze", "/telegraph_stop", "/telegraph_end"):
                    parts = text.split()
                    if len(parts) >= 2:
                        duration_str = parts[1].strip()
                        minutes = parse_duration(duration_str)
                        if minutes is not None:
                            telegraph_active = True
                            telegraph_freeze_until = time.time() + minutes * 60
                            _save_notifications_state()
                            
                            h, m = divmod(minutes, 60)
                            d, h = divmod(h, 24)
                            time_parts = []
                            if d > 0: time_parts.append(f"{d} يوم")
                            if h > 0: time_parts.append(f"{h} ساعة")
                            if m > 0: time_parts.append(f"{m} دقيقة")
                            time_desc = " و ".join(time_parts)
                            
                            response = f"❄️ تم تجميد مزامنة Telegraph بنجاح لمدة {time_desc}."
                        else:
                            response = f"⚠️ صيغة المدة غير صالحة! استخدم أرقاماً بالدقائق (مثال: `{cmd} 30`) أو بالساعات/الأيام (مثال: `2h` أو `1d`)."
                    else:
                        telegraph_active = False
                        telegraph_freeze_until = 0
                        _save_notifications_state()
                        response = "🔴 تم تجميد مزامنة Telegraph نهائياً (للأبد) حتى تقوم بتشغيلها مجدداً."
                        
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": response, "parse_mode": "Markdown"})

                elif cmd in ("/telegraph_resume", "/telegraph_play"):
                    telegraph_active = True
                    telegraph_freeze_until = 0
                    _save_notifications_state()
                    response = "🟢 تم إلغاء التجميد وتشغيل مزامنة Telegraph بنجاح كل دقيقتين!"
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": response})

                elif cmd == "/pending":
                    with subscribers_lock:
                        pending = _load_pending()
                    if pending:
                        lines = ["⏳ طلبات الاشتراك المعلقة:\n"]
                        for pid in sorted(pending):
                            lines.append(f"🆔 {pid}  →  /approve {pid}")
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines)})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "✅ لا توجد طلبات معلقة."})

                elif cmd == "/help":
                    if role >= 3:
                        help_text = (
                            f"🤖 **دليل أوامر البوت الكامل — رتبة المالك (Owner) (خمسات):**\n\n"
                            "👑 **👑 أوامر المالك فقط (Owner Only):**\n"
                            "  /add_admin <id> — إضافة أدمن جديد للبوت\n"
                            "  /remove_admin <id> — إزالة أدمن وسحب صلاحياته\n"
                            "  /backup — أخذ نسخة احتياطية فورية لبيانات البوت\n\n"
                            "👮‍♂️ **👮‍♂️ أوامر الإشراف (Allowed for Admins & Owners):**\n"
                            "  /menu — فتح لوحة تحكم الأدمن التفاعلية\n"
                            "  /backup_menu — فتح لوحة التحكم التفاعلية في الباك أب ⚙️\n"
                            "  /freeze_backup, /backup_freeze, /backup_stop, /backup_end — تجميد الباك أب التلقائي (مثال: `/freeze_backup 30m` أو `2h` أو `1d`)\n"
                            "  /resume_backup, /backup_resume, /backup_play — تشغيل وإلغاء تجميد الباك أب التلقائي 🟢\n"
                            "  /telegraph_freeze, /telegraph_stop, /telegraph_end — تجميد المزامنة السحابية Telegraph (مثال: `/telegraph_freeze 2h`)\n"
                            "  /telegraph_resume, /telegraph_play — تشغيل المزامنة السحابية Telegraph 🟢\n"
                            "  /ids — عرض معرفات (IDs) المشتركين المعتمدين\n"
                            "  /approve <id> — قبول طلب اشتراك معلق\n"
                            "  /reject <id> — رفض طلب اشتراك معلق\n"
                            "  /pending — عرض قائمة طلبات الاشتراك المعلقة\n"
                            "  /block <id> — حظر مستخدم من استخدام البوت\n"
                            "  /unblock <id> — إلغاء حظر مستخدم محظور\n"
                            "  /mute <id> — كتم إشعارات مستخدم معين بقوة\n"
                            "  /unmute <id> — إلغاء كتم إشعارات مستخدم معين\n"
                            "  /muteall — كتم إشعارات جميع المشتركين بقوة\n"
                            "  /unmuteall — إلغاء كتم إشعارات جميع المشتركين\n"
                            "  /broadcast <الرسالة> — بث رسالة لجميع المشتركين\n"
                            "  /send_last <العدد> — جلب وإرسال أحدث طلبات خمسات\n"
                            "  /status — عرض حالة البوت والإحصائيات والرسم البياني\n"
                            "  /dashboard أو /vstatus — لوحة التقارير البصرية الذكية 📊\n"
                            "  /restore — استعادة البيانات بالرد (Reply) على ملف الباك أب\n\n"
                            "👤 **👤 أوامر المشتركين (General User Commands):**\n"
                            "  /start أو /subscribe — طلب اشتراك في إشعارات البوت\n"
                            "  /mymute أو /pause — كتم إشعارات الطلبات لحسابك مؤقتاً\n"
                            "  /myunmute أو /resume — تشغيل إشعارات الطلبات لحسابك\n"
                            "  /filter <الكلمات> — تصفية الطلبات بكلمات مفتاحية (مثال: `/filter تصميم, برمجة`)\n"
                            "  /myfilters — عرض كلماتك المفتاحية النشطة\n"
                            "  /filter_clear أو /filter_off — إلغاء الفلاتر واستلام جميع الطلبات\n"
                            "  /unsubscribe — إلغاء الاشتراك من البوت بالكامل\n"
                            "  /ping — فحص سرعة واستجابة البوت"
                        )
                    elif role >= 2:
                        help_text = (
                            f"🤖 **دليل أوامر البوت الكامل — رتبة الأدمن (Admin) (خمسات):**\n\n"
                            "👮‍♂️ **👮‍♂️ أوامر الإشراف (Allowed for Admins):**\n"
                            "  /menu — فتح لوحة تحكم الأدمن التفاعلية\n"
                            "  /backup_menu — فتح لوحة التحكم التفاعلية في الباك أب ⚙️\n"
                            "  /freeze_backup, /backup_freeze, /backup_stop, /backup_end — تجميد الباك أب التلقائي (مثال: `/freeze_backup 30m` أو `2h` أو `1d`)\n"
                            "  /resume_backup, /backup_resume, /backup_play — تشغيل وإلغاء تجميد الباك أب التلقائي 🟢\n"
                            "  /telegraph_freeze, /telegraph_stop, /telegraph_end — تجميد المزامنة السحابية Telegraph (مثال: `/telegraph_freeze 2h`)\n"
                            "  /telegraph_resume, /telegraph_play — تشغيل المزامنة السحابية Telegraph 🟢\n"
                            "  /ids — عرض معرفات (IDs) المشتركين المعتمدين\n"
                            "  /approve <id> — قبول طلب اشتراك معلق\n"
                            "  /reject <id> — رفض طلب اشتراك معلق\n"
                            "  /pending — عرض قائمة طلبات الاشتراك المعلقة\n"
                            "  /block <id> — حظر مستخدم من استخدام البوت\n"
                            "  /unblock <id> — إلغاء حظر مستخدم محظور\n"
                            "  /mute <id> — كتم إشعارات مستخدم معين بقوة\n"
                            "  /unmute <id> — إلغاء كتم إشعارات مستخدم معين\n"
                            "  /muteall — كتم إشعارات جميع المشتركين بقوة\n"
                            "  /unmuteall — إلغاء كتم إشعارات جميع المشتركين\n"
                            "  /broadcast <الرسالة> — بث رسالة لجميع المشتركين\n"
                            "  /send_last <العدد> — جلب وإرسال أحدث طلبات خمسات\n"
                            "  /status — عرض حالة البوت والإحصائيات والرسم البياني\n"
                            "  /dashboard أو /vstatus — لوحة التقارير البصرية الذكية 📊\n"
                            "  /restore — استعادة البيانات بالرد (Reply) على ملف الباك أب\n\n"
                            "👤 **👤 أوامر المشتركين (General User Commands):**\n"
                            "  /start أو /subscribe — طلب اشتراك في إشعارات البوت\n"
                            "  /mymute أو /pause — كتم إشعارات الطلبات لحسابك مؤقتاً\n"
                            "  /myunmute أو /resume — تشغيل إشعارات الطلبات لحسابك\n"
                            "  /filter <الكلمات> — تصفية الطلبات بكلمات مفتاحية (مثال: `/filter تصميم, برمجة`)\n"
                            "  /myfilters — عرض كلماتك المفتاحية النشطة\n"
                            "  /filter_clear أو /filter_off — إلغاء الفلاتر واستلام جميع الطلبات\n"
                            "  /unsubscribe — إلغاء الاشتراك من البوت بالكامل\n"
                            "  /ping — فحص سرعة واستجابة البوت"
                        )
                    else:
                        help_text = (
                            f"🤖 **دليل أوامر بوت إشعارات خمسات:**\n\n"
                            "👤 **👤 أوامر المشتركين (General User Commands):**\n"
                            "  /start أو /subscribe — طلب اشتراك في إشعارات الطلبات الجديدة\n"
                            "  /mymute أو /pause — كتم إشعارات الطلبات لحسابك مؤقتاً\n"
                            "  /myunmute أو /resume — تشغيل إشعارات الطلبات وإلغاء الكتم\n"
                            "  /filter <الكلمات> — تصفية الطلبات بكلمات مفتاحية محددة فقط\n"
                            "      (مثال: `/filter تصميم, برمجة, ترجمة`)\n"
                            "  /myfilters — عرض كلماتك المفتاحية النشطة لحسابك\n"
                            "  /filter_clear أو /filter_off — إلغاء الفلترة واستلام جميع الطلبات دون استثناء\n"
                            "  /unsubscribe — إلغاء الاشتراك من البوت بالكامل وحذف حسابك\n"
                            "  /ping — فحص سرعة واستجابة البوت"
                        )
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": help_text, "parse_mode": "Markdown"})

                elif cmd == "/status":
                    with subscribers_lock:
                        subs = _load_subscribers()
                        pending = _load_pending()
                        blocked = _load_blocked()
                    stats = _get_stats()
                    uptime_sec = int(time.time() - bot_start_time)
                    h, m = divmod(uptime_sec // 60, 60)
                    muted_count = len(_load_muted_users())
                    
                    id_label = f"أعلى ID طلب شوفناه: {max_seen_id}"
                        
                    status_msg = (
                        f"📊 حالة بوت خمسات:\n"
                        f"⏱️ وقت التشغيل: {h}ساعة {m}دقيقة\n"
                        f"👥 المشتركين: {len(subs)} / {MAX_SUBSCRIBERS}\n"
                        f"🔕 كتموا إشعاراتهم: {muted_count}\n"
                        f"⏳ طلبات معلقة: {len(pending)}\n"
                        f"🚫 محظورين: {len(blocked)}\n"
                        f"👑 أدمنز: {len(_get_all_admins())}\n"
                        f"🔢 {id_label}\n"
                        f"📨 إجمالي رسائل مرسلة: {stats.get('total_sent', 0)}"
                    )
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": status_msg})
                    
                    # Premium addition: automatically send visual status graph!
                    photo_buf = generate_visual_dashboard()
                    if photo_buf:
                        _send_photo(chat_id, photo_buf, caption="📊 الرسم البياني للأداء")

                elif cmd in ("/dashboard", "/vstatus"):
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⏳ جاري توليد لوحة التقارير البصرية الذكية..."})
                    photo_buf = generate_visual_dashboard()
                    if photo_buf:
                        _send_photo(chat_id, photo_buf, caption="📊 لوحة تقارير الأداء البصرية لبوت خمسات")
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ فشل توليد التقرير البصري."})

                elif cmd == "/filter":
                    keywords_str = text[len("/filter"):].strip()
                    if not keywords_str:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": (
                            "⚠️ يرجى إدخال الكلمات المفتاحية مفصولة بفواصل.\n"
                            "مثال: `/filter تصميم, برمجة, ترجمة`"
                        )})
                    else:
                        # Split by comma or space, strip whitespace, and lower-case
                        kws = [k.strip().lower() for k in keywords_str.replace("،", ",").split(",") if k.strip()]
                        if not kws:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ يرجى كتابة كلمات صحيحة مفصولة بفواصل."})
                        else:
                            with subscribers_lock:
                                kws_map = _load_keywords()
                                kws_map[str(chat_id)] = kws
                                _save_keywords(kws_map)
                            
                            formatted_kws = ", ".join(kws)
                            success_msg = (
                                f"✅ تم تفعيل الفلترة الذكية لحسابك بنجاح!\n\n"
                                f"📋 الكلمات المفتاحية الحالية:\n"
                                f"🏷️ *{formatted_kws}*\n\n"
                                f"💡 ستصلك الآن فقط طلبات خمسات التي تحتوي على أي من هذه الكلمات في عنوانها.\n"
                                f"لإلغاء الفلترة واستلام كل الطلبات، أرسل: `/filter_clear`"
                            )
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": success_msg, "parse_mode": "Markdown"})

                elif cmd == "/myfilters":
                    kws_map = _load_keywords()
                    kws = kws_map.get(str(chat_id), [])
                    if not kws:
                        msg = (
                            "🔔 أنت تستقبل حالياً جميع طلبات خمسات دون فلترة.\n\n"
                            "💡 لتفعيل الفلترة الذكية، أرسل الكلمات المفتاحية مفصولة بفواصل:\n"
                            "مثال: `/filter تصميم, ترجمة, لوجو`"
                        )
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
                    else:
                        formatted_kws = ", ".join(kws)
                        msg = (
                            f"📋 الكلمات المفتاحية النشطة لحسابك:\n"
                            f"🏷️ *{formatted_kws}*\n\n"
                            f"💡 لتحديثها، أرسل أمراً جديداً بالكلمات التي تريدها.\n"
                            f"لإلغاء الفلترة بالكامل، أرسل: `/filter_clear`"
                        )
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})

                elif cmd in ("/filter_clear", "/filter_off"):
                    with subscribers_lock:
                        kws_map = _load_keywords()
                        if str(chat_id) in kws_map:
                            del kws_map[str(chat_id)]
                            _save_keywords(kws_map)
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔔 تم إلغاء الفلترة الذكية بنجاح. ستصلك الآن جميع طلبات خمسات دون استثناء."})

                elif cmd == "/ping":
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "pong ✅"})
                    
        except Exception as e:
            logger.debug(f"Updates loop error: {str(e)}")
            time.sleep(poll_interval)

# ==============================================================================
# PERIODIC TASKS LOOP (STATS & 3-MINUTE AUTO TELEGRAM BACKUPS)
# ==============================================================================
def _periodic_tasks_loop():
    """Send weekly statistics and 3-minute automatic backups to owner."""
    time.sleep(10)
    last_stats_sent = time.time()
    last_backup_sent = time.time()
    
    while True:
        time.sleep(30)  # Check every 30 seconds
        now = time.time()
        
        # Check freeze expiration
        global backup_active, backup_freeze_until
        if backup_freeze_until > 0 and now >= backup_freeze_until:
            backup_freeze_until = 0
            backup_active = True
            _save_notifications_state()
            _notify_admins("🟢 انتهت مدة تجميد النسخ الاحتياطي التلقائي وتم تفعيله تلقائياً كل 3 دقائق!")
        
        # Check telegraph freeze expiration
        global telegraph_active, telegraph_freeze_until
        if telegraph_freeze_until > 0 and now >= telegraph_freeze_until:
            telegraph_freeze_until = 0
            telegraph_active = True
            _save_notifications_state()
            _notify_admins("🟢 انتهت مدة تجميد مزامنة Telegraph وتم تفعيلها تلقائياً كل دقيقتين!")
        
        # 3-minute automatic backups (180 seconds)
        if backup_active and backup_freeze_until == 0:
            if now - last_backup_sent >= 180:
                try:
                    backup_data = generate_system_backup()
                    backup_bytes = json.dumps(backup_data, ensure_ascii=False, indent=2).encode("utf-8")
                    import io
                    bio = io.BytesIO(backup_bytes)
                    bio.name = "system_backup_data.json"
                    
                    if KHAMSAT_BOT_TOKEN:
                        requests.post(
                            f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}/sendDocument",
                            data={"chat_id": get_owner_id(), "caption": "📦 نسخة احتياطية تلقائية لبوت خمسات.\nلو الداتا طارت، اعمل Reply على الملف واكتب /restore"},
                            files={"document": ("system_backup_data.json", bio, "application/json")},
                            timeout=20
                        )
                    last_backup_sent = now
                    logger.info("3-minute backup sent to owner via Khamsat")
                except Exception as e:
                    logger.error(f"3-minute backup error: {e}")

        # Weekly statistics
        if now - last_stats_sent >= 7 * 24 * 3600:
            try:
                subs = _load_subscribers()
                pending = _load_pending()
                blocked = _load_blocked()
                stats = _get_stats()
                uptime_sec = int(time.time() - bot_start_time)
                h, m = divmod(uptime_sec // 60, 60)
                muted_count = len(_load_muted_users())
                
                stats_msg = (
                    f"📊 إحصائيات الأسبوع لبوت خمسات:\n"
                    f"⏱️ وقت التشغيل: {h}ساعة {m}دقيقة\n"
                    f"👥 المشتركين: {len(subs)} / {MAX_SUBSCRIBERS}\n"
                    f"🔕 كتموا إشعاراتهم: {muted_count}\n"
                    f"⏳ طلبات معلقة: {len(pending)}\n"
                    f"🚫 محظورين: {len(blocked)}\n"
                    f"👑 أدمنز: {len(_get_all_admins())}\n"
                    f"📨 إجمالي رسائل مرسلة: {stats.get('total_sent', 0)}"
                )
                if KHAMSAT_BOT_TOKEN:
                    requests.post(f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}/sendMessage", json={"chat_id": get_owner_id(), "text": stats_msg}, timeout=10)
                last_stats_sent = now
                logger.info("Weekly stats sent to owner")
            except Exception as e:
                logger.error(f"Weekly stats error: {e}")

# ==============================================================================
# MAIN SYSTEM INITIALIZER
# ==============================================================================
def load_seen_data():
    global max_seen_id
    
    khamsat_seen_file = _get_file_path("seen")
    if os.path.exists(khamsat_seen_file):
        try:
            with open(khamsat_seen_file, "r") as f:
                max_seen_id = int(json.load(f))
            logger.info(f"Loaded Khamsat max_seen_id = {max_seen_id}")
        except Exception as e:
            logger.error(f"Failed to load Khamsat max ID file: {e}")
            max_seen_id = 0
    else:
        max_seen_id = 0

if __name__ == "__main__":
    load_all_configs()
    _load_notifications_state()
    
    # Download Telegraph backups dynamically
    if KHAMSAT_BOT_TOKEN:
        download_telegraph_db()
    # Download Railway backups dynamically (if configured)
    download_railway_backup()
        
    load_seen_data()
    load_proxies()
    
    logger.info("=" * 50)
    logger.info("Khamsat Scraper Bot System Started")
    logger.info("=" * 50)

    # Start threads for Khamsat Bot
    if KHAMSAT_BOT_TOKEN:
        threading.Thread(target=handle_updates_loop, daemon=True).start()
        threading.Thread(target=_periodic_tasks_loop, daemon=True).start()
        threading.Thread(target=telegraph_sync_thread, daemon=True).start()
        
        startup_reqs, startup_proxy_type, startup_proxy_addr, _ = fetch_khamsat_projects()
        if startup_reqs:
            if max_seen_id == 0:
                seed_max_id(startup_reqs)
            send_startup_snapshot(startup_reqs)
            logger.info(f"Khamsat startup snapshot sent via {startup_proxy_type} proxy ({startup_proxy_addr})")
        else:
            logger.warning("No Khamsat startup requests were found")

    def khamsat_scraping_loop():
        if not KHAMSAT_BOT_TOKEN:
            return
        logger.info("Started Khamsat scraping loop...")
        while True:
            try:
                if notifications_active:
                    check_khamsat()
                else:
                    logger.info("Scraping is globally paused (notifications disabled)")
            except Exception as e:
                logger.error(f"Khamsat scraping loop error: {e}")
            
            wait = random.uniform(5.0, 15.0)
            logger.info(f"Khamsat waiting {wait:.1f}s before next scan")
            time.sleep(wait)

    if KHAMSAT_BOT_TOKEN:
        threading.Thread(target=khamsat_scraping_loop, daemon=True).start()
        
    # Send startup notifications
    if KHAMSAT_BOT_TOKEN:
        server_name = os.getenv("SERVER_NAME") or os.getenv("RAILWAY_SERVICE_NAME") or os.getenv("HOSTNAME") or "unknown"
        startup_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        try:
            requests.post(
                f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}/sendMessage",
                json={"chat_id": get_owner_id(), "text": "🚀 بدأت مراقبة طلبات 'خمسات' الآن.."},
                timeout=10,
            )
        except Exception:
            pass
        owner_startup_msg = (
            "🚀 تم تشغيل البوت بنجاح.\n"
            f"🖥️ السيرفر: {server_name}\n"
            f"🕒 الوقت: {startup_time}\n\n"
            "لو محتاج استرجاع: اعمل Reply على آخر backup واكتب /restore"
        )
        try:
            requests.post(f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}/sendMessage", json={"chat_id": get_owner_id(), "text": owner_startup_msg}, timeout=10)
        except Exception:
            pass

    # Keep the main process alive
    logger.info("All loops and threads started successfully. Keeping main thread alive.")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Khamsat bot stopped by user.")
            break
