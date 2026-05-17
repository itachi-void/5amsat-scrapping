from curl_cffi import requests as cffi_requests
import json
import os
import time
import random
import requests
import logging
import importlib.util
import importlib
from bs4 import BeautifulSoup
import threading
from logging.handlers import RotatingFileHandler

subscribers_lock = threading.Lock()
MAX_SUBSCRIBERS = 50

def load_env_file(env_path=".env"):
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


if importlib.util.find_spec("dotenv") is not None:
    importlib.import_module("dotenv").load_dotenv()

# تحميل متغيرات البيئة
load_env_file()

# إعداد Logging (console + rotating file)
_log_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_log_formatter)
_file_handler = RotatingFileHandler('khamsat_bot.log', maxBytes=2*1024*1024, backupCount=3, encoding='utf-8')
_file_handler.setFormatter(_log_formatter)
logger.addHandler(_console_handler)
logger.addHandler(_file_handler)
logging.getLogger().addHandler(_console_handler)

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = "8785131188:AAGMhnlUTmrWkblRdmKmVN-UM0dhSwo1pO4"
OWNER_ID = 1622676655
URL = "https://khamsat.com/community/requests"

# Premium Proxy Data (مع يوزر وباسورد)
PROXY_USER = os.getenv("PROXY_USER", "")
PROXY_PASS = os.getenv("PROXY_PASS", "")
PREMIUM_PROXY_FILE = "proxyscrape_premium_http_proxies.txt"
FREE_PROXY_FILES = [
    "HTTP - 2.txt",
    "SOCKS4 - 2.txt",
    "SOCKS5 - 2.txt",
]  # بروكسيات مجانية بدون يوزر وباسورد

CHECK_INTERVAL = 45 
SEEN_FILE        = "khamsat_max_id.json"
SUBSCRIBERS_FILE = "subscribers.json"
PENDING_FILE     = "pending_subscribers.json"
BLOCKED_FILE     = "blocked_users.json"
STATE_FILE       = "bot_state.json"
LAST_BROADCAST_FILE = "last_broadcast_msgs.json"
ADMINS_FILE      = "admins.json"
MUTED_USERS_FILE = "muted_users.json"   # كتم شخصي لكل مشترك
STATS_FILE       = "bot_stats.json"     # إحصائيات تراكمية
premium_proxies = []
free_proxies    = []

# Rate limiting: chat_id -> last command timestamp
_rate_limit: dict = {}
RATE_LIMIT_SECONDS = 3   # حد أدنى بين أوامر المستخدم

# Project cache
_projects_cache: list = []
_projects_cache_ts: float = 0
PROJECTS_CACHE_TTL = 30   # ثانية

# وقت تشغيل البوت
bot_start_time = time.time()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]

IMPERSONATE_TARGETS = ["chrome110", "chrome116", "chrome120", "chrome123", "chrome124"]

def _new_scraper():
    """Create a fresh scraper session with random browser fingerprint."""
    target = random.choice(IMPERSONATE_TARGETS)
    return cffi_requests.Session(impersonate=target)

scraper = _new_scraper()

# =========================
# FUNCTIONS
# =========================

def send_telegram(text):
    """Send a Telegram message to all admins + subscribers (no duplicates)."""
    def _send(chat_id, payload_text, retries=3):
        tele_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for attempt in range(retries):
            try:
                response = requests.post(
                    tele_url,
                    json={"chat_id": chat_id, "text": payload_text},
                    timeout=10,
                )
                if response.status_code == 200:
                    return True
                elif response.status_code == 401:
                    logger.error("Telegram auth failed")
                    return False
                elif response.status_code == 403:
                    logger.warning(f"Chat {chat_id} blocked bot")
                    return False
                elif response.status_code == 429:
                    retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                    time.sleep(retry_after)
                else:
                    logger.error(f"Telegram error: {response.status_code}")
            except Exception as e:
                logger.error(f"Send attempt {attempt+1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(1 + attempt)
        return False

    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN is missing - Telegram messages are disabled")
        return False

    # Collect all unique recipient IDs: admins
    all_recipients = set(_get_all_admins())

    if not _is_muted():
        with subscribers_lock:
            subs = _load_subscribers()
        muted_users = _load_muted_users()
        all_recipients.update(subs - muted_users)
    else:
        logger.info("Bot is muted globally. Sending to admins only.")

    if not all_recipients:
        logger.warning("No CHAT_ID and no subscribers: message not sent")
        return False

    ok = True
    sent_count = 0
    for cid in all_recipients:
        if _send(cid, text):
            sent_count += 1
        else:
            ok = False
    _increment_stats(sent_count)
    return ok


def _load_subscribers():
    """Load subscriber IDs from file. Returns a set of ints."""
    if not os.path.exists(SUBSCRIBERS_FILE):
        return set()
    try:
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {int(x) for x in data}
    except Exception:
        pass
    return set()


def _save_subscribers(subs_set):
    """Atomically save subscribers to disk."""
    tmp_path = SUBSCRIBERS_FILE + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(subs_set), f)
    os.replace(tmp_path, SUBSCRIBERS_FILE)


def _load_admins():
    """Load admins from file. Returns a set of ints."""
    if not os.path.exists(ADMINS_FILE):
        return set()
    try:
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {int(x) for x in data}
    except Exception:
        pass
    return set()

def _save_admins(admins_set):
    """Atomically save admins to disk."""
    tmp_path = ADMINS_FILE + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(admins_set), f)
    os.replace(tmp_path, ADMINS_FILE)

def _get_all_admins():
    return _load_admins() | {OWNER_ID}


def _load_pending():
    """Load pending subscriber IDs. Returns a set of ints."""
    if not os.path.exists(PENDING_FILE):
        return set()
    try:
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {int(x) for x in data}
    except Exception:
        pass
    return set()


def _save_pending(pending_set):
    """Atomically save pending subscribers to disk."""
    tmp_path = PENDING_FILE + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(pending_set), f)
    os.replace(tmp_path, PENDING_FILE)


def _load_muted_users():
    """Load personally muted user IDs."""
    if not os.path.exists(MUTED_USERS_FILE):
        return set()
    try:
        with open(MUTED_USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {int(x) for x in data} if isinstance(data, list) else set()
    except Exception:
        return set()


def _save_muted_users(muted_set):
    tmp = MUTED_USERS_FILE + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(sorted(muted_set), f)
    os.replace(tmp, MUTED_USERS_FILE)


def _increment_stats(count):
    """Increment total messages sent counter."""
    try:
        data = {}
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data["total_sent"] = data.get("total_sent", 0) + count
        data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception:
        pass


def _get_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _check_rate_limit(chat_id):
    """Return True if allowed, False if too fast."""
    now = time.time()
    last = _rate_limit.get(chat_id, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return False
    _rate_limit[chat_id] = now
    return True


def _notify_admins(text):
    """Send a message only to admin IDs (not subscribers)."""
    if not BOT_TOKEN or not _get_all_admins():
        return
    tele_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for admin_id in _get_all_admins():
        try:
            requests.post(tele_url, json={"chat_id": admin_id, "text": text}, timeout=10)
        except Exception:
            pass


def _load_blocked():
    """Load blocked user IDs. Returns a set of ints."""
    if not os.path.exists(BLOCKED_FILE):
        return set()
    try:
        with open(BLOCKED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {int(x) for x in data}
    except Exception:
        pass
    return set()


def _save_blocked(blocked_set):
    """Atomically save blocked users to disk."""
    tmp_path = BLOCKED_FILE + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(blocked_set), f)
    os.replace(tmp_path, BLOCKED_FILE)


def _is_muted():
    """Check if the bot is globally muted for subscribers."""
    if not os.path.exists(STATE_FILE):
        return False
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("muted", False)
    except Exception:
        return False


def _set_muted(muted: bool):
    """Set the global mute state."""
    try:
        data = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data["muted"] = muted
        tmp_path = STATE_FILE + ".tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        os.replace(tmp_path, STATE_FILE)
        return True
    except Exception as e:
        logger.error(f"Failed to set muted state: {str(e)}")
        return False


def _save_broadcast_msgs(msg_map):
    """Save broadcast message IDs mapping."""
    tmp_path = LAST_BROADCAST_FILE + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(msg_map, f)
    os.replace(tmp_path, LAST_BROADCAST_FILE)


def _load_broadcast_msgs():
    """Load broadcast message IDs mapping."""
    if not os.path.exists(LAST_BROADCAST_FILE):
        return {}
    try:
        with open(LAST_BROADCAST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def is_owner(chat_id):
    """Check if a chat_id is the owner."""
    try:
        return int(chat_id) == OWNER_ID
    except (ValueError, TypeError):
        return False

def load_proxies():
    """تحميل البروكسيات من الملفات"""
    global premium_proxies, free_proxies
    
    # تحميل البروكسيات المدفوعة (مع يوزر وباسورد)
    if PROXY_USER and PROXY_PASS and os.path.exists(PREMIUM_PROXY_FILE):
        try:
            with open(PREMIUM_PROXY_FILE, 'r') as f:
                premium_proxies = [("http", l.strip()) for l in f if ":" in l]
            logger.info(f"Loaded {len(premium_proxies)} premium proxies with username/password")
        except Exception as e:
            logger.error(f"Failed to load premium proxies: {str(e)}")
    
    # تحميل البروكسيات المجانية (بدون يوزر وباسورد)
    free_proxies = []
    for proxy_file in FREE_PROXY_FILES:
        if not os.path.exists(proxy_file):
            continue

        if proxy_file.startswith("SOCKS4"):
            scheme = "socks4"
        elif proxy_file.startswith("SOCKS5"):
            scheme = "socks5"
        else:
            scheme = "http"

        try:
            with open(proxy_file, 'r') as f:
                loaded_proxies = [(scheme, l.strip()) for l in f if ":" in l]
                free_proxies.extend(loaded_proxies)
            logger.info(f"Loaded {len(loaded_proxies)} proxies from {proxy_file} without username/password")
        except Exception as e:
            logger.error(f"Failed to load free proxies from {proxy_file}: {str(e)}")
    
    if not premium_proxies and not free_proxies:
        logger.warning("No proxies were loaded")

def get_proxy_url(use_premium=True):
    """الحصول على رابط بروكسي عشوائي"""
    if use_premium and premium_proxies:
        scheme, p_addr = random.choice(premium_proxies)
        proxy_url = f"{scheme}://{PROXY_USER}:{PROXY_PASS}@{p_addr}"
    elif free_proxies:
        scheme, p_addr = random.choice(free_proxies)
        proxy_url = f"{scheme}://{p_addr}"
    else:
        return None, None
    
    return proxy_url, p_addr


def _fetch_one_page(page_url, headers, proxies=None, proxy_kind="direct", p_addr=None):
    """Fetch and extract requests from a single Khamsat page."""
    global scraper
    try:
        resp = scraper.get(page_url, headers=headers, proxies=proxies or {}, timeout=15)
        if resp.status_code == 200:
            return extract_projects(resp.text)
    except Exception as e:
        logger.warning(f"Fetch error ({proxy_kind} {p_addr}): {e}")
    return None


def fetch_mostaql_projects(max_pages=8, max_attempts=12):
    """Fetch up to max_pages of Khamsat requests (≈200 items), with short-lived cache."""
    global scraper, _projects_cache, _projects_cache_ts

    # Return cached result if still fresh
    if _projects_cache and (time.time() - _projects_cache_ts) < PROJECTS_CACHE_TTL:
        return _projects_cache, "cache", None

    headers = {"User-Agent": random.choice(USER_AGENTS)}

    # Pick a working proxy (or go direct)
    all_proxies = list(premium_proxies) + list(free_proxies)
    random.shuffle(all_proxies)

    chosen_proxies = None
    proxy_kind = "direct"
    p_addr = None

    for scheme, addr in all_proxies[:max_attempts]:
        if PROXY_USER and PROXY_PASS and (scheme, addr) in premium_proxies:
            pu = f"{scheme}://{PROXY_USER}:{PROXY_PASS}@{addr}"
            pk = "premium"
        else:
            pu = f"{scheme}://{addr}"
            pk = "free"
        pg1 = _fetch_one_page(URL, headers, {"http": pu, "https": pu}, pk, addr)
        if pg1 is not None:
            chosen_proxies = {"http": pu, "https": pu}
            proxy_kind = pk
            p_addr = addr
            break

    if chosen_proxies is None:
        scraper = _new_scraper()
        pg1 = _fetch_one_page(URL, headers)
        if pg1 is None:
            return [], None, None

    # Collect pages
    all_items: list = pg1 or []
    seen_in_fetch: set = {p["id"] for p in all_items}

    for page_num in range(2, max_pages + 1):
        if len(all_items) >= 200:
            break
        page_url = f"{URL}?page={page_num}"
        items = _fetch_one_page(page_url, headers, chosen_proxies, proxy_kind, p_addr)
        if not items:
            break
        for item in items:
            if item["id"] not in seen_in_fetch:
                seen_in_fetch.add(item["id"])
                all_items.append(item)
        time.sleep(0.5)  # polite pause between pages

    all_items = all_items[:200]
    logger.info(f"Fetched {len(all_items)} requests via {proxy_kind} ({p_addr})")

    _projects_cache = all_items
    _projects_cache_ts = time.time()
    return all_items, proxy_kind, p_addr


def extract_projects(html_text):
    """Extract project items from Khamsat HTML."""
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


def add_subscriber(chat_id):
    """Thread-safe add approved subscriber with max limit."""
    try:
        chat_id = int(chat_id)
        with subscribers_lock:
            subs = _load_subscribers()
            if len(subs) >= MAX_SUBSCRIBERS:
                logger.warning(f"Max subscribers ({MAX_SUBSCRIBERS}) reached, rejecting {chat_id}")
                return False
            subs.add(chat_id)
            _save_subscribers(subs)
            # Remove from pending if was there
            pending = _load_pending()
            pending.discard(chat_id)
            _save_pending(pending)
        logger.info(f"Subscriber approved: {chat_id} (total: {len(subs)})")
        return True
    except Exception as e:
        logger.error(f"Failed to add subscriber: {str(e)}")
        return False


def request_subscription(chat_id, username="", first_name=""):
    """Add user to pending list and notify admins."""
    try:
        chat_id = int(chat_id)

        # Check if blocked
        with subscribers_lock:
            blocked = _load_blocked()
        if chat_id in blocked:
            return "blocked"

        # If already approved, skip
        with subscribers_lock:
            subs = _load_subscribers()
        if chat_id in subs or chat_id in _get_all_admins():
            return "already_approved"

        # Add to pending
        with subscribers_lock:
            pending = _load_pending()
            if chat_id in pending:
                return "already_pending"
            pending.add(chat_id)
            _save_pending(pending)

        # Build user info for admin notification
        user_info = f"🆔 ID: {chat_id}"
        if username:
            user_info += f"\n👤 يوزرنيم: @{username}"
        if first_name:
            user_info += f"\n📛 الاسم: {first_name}"

        # Send notification with inline buttons to admins
        notify_text = f"🆕 طلب اشتراك جديد!\n\n{user_info}"
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ موافقة", "callback_data": f"approve:{chat_id}"},
                    {"text": "❌ رفض", "callback_data": f"reject:{chat_id}"},
                    {"text": "🚫 بلوك", "callback_data": f"block:{chat_id}"},
                ]
            ]
        }
        tele_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for admin_id in _get_all_admins():
            try:
                requests.post(tele_url, json={"chat_id": admin_id, "text": notify_text, "reply_markup": keyboard}, timeout=10)
            except Exception:
                pass
        logger.info(f"Subscription request from {chat_id}, admins notified")
        return "pending"
    except Exception as e:
        logger.error(f"Failed to request subscription: {str(e)}")
        return "error"


def reject_subscriber(chat_id):
    """Remove user from pending list."""
    try:
        chat_id = int(chat_id)
        with subscribers_lock:
            pending = _load_pending()
            pending.discard(chat_id)
            _save_pending(pending)
            # Also remove from approved if exists
            subs = _load_subscribers()
            subs.discard(chat_id)
            _save_subscribers(subs)
        logger.info(f"Subscriber rejected/removed: {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to reject subscriber: {str(e)}")
        return False


def remove_subscriber(chat_id):
    """Thread-safe remove subscriber."""
    try:
        chat_id = int(chat_id)
        with subscribers_lock:
            subs = _load_subscribers()
            subs.discard(chat_id)
            _save_subscribers(subs)
        logger.info(f"Subscriber removed: {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to remove subscriber: {str(e)}")
        return False


def is_admin(chat_id):
    """Check if a chat_id is an admin (from CHAT_ID env var)."""
    try:
        return int(chat_id) in _get_all_admins()
    except (ValueError, TypeError):
        return False

def _send_admin_menu(base_url, chat_id):
    """Send the admin control panel with inline buttons."""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "👥 المشتركين", "callback_data": "cmd:ids"},
                {"text": "⏳ طلبات معلقة", "callback_data": "cmd:pending"},
            ],
            [
                {"text": "📊 حالة البوت", "callback_data": "cmd:status"},
                {"text": "🚫 المحظورين", "callback_data": "cmd:blocked"},
            ],
            [
                {"text": "🔕 إيقاف الإشعارات", "callback_data": "cmd:mute"} if not _is_muted() else {"text": "🔔 تشغيل الإشعارات", "callback_data": "cmd:unmute"},
            ],
            [
                {"text": "📢 بث رسالة", "callback_data": "cmd:broadcast_help"},
                {"text": "❓ المساعدة", "callback_data": "cmd:help"},
            ],
            [
                {"text": "🚀 إرسال آخر الطلبات", "callback_data": "cmd:send_last_help"},
            ],
        ]
    }
    if is_owner(chat_id):
        keyboard["inline_keyboard"].insert(0, [
            {"text": "👨‍💻 إدارة الأدمنز", "callback_data": "cmd:admins_list"}
        ])

    requests.post(f"{base_url}/sendMessage", json={
        "chat_id": chat_id,
        "text": "👑 لوحة تحكم الأدمن:",
        "reply_markup": keyboard,
    })


def _handle_menu_action(base_url, chat_id, action):
    """Handle admin menu button presses."""
    if action == "ids":
        with subscribers_lock:
            subs = _load_subscribers()
        if subs:
            lines = ["👥 المشتركين المعتمدين:\n"]
            for i, sid in enumerate(sorted(subs), 1):
                marker = "👑" if sid in _get_all_admins() else "👤"
                lines.append(f"{i}. {marker} {sid}")
            # Add block buttons for each subscriber
            keyboard = {"inline_keyboard": []}
            for sid in sorted(subs):
                if sid != OWNER_ID:
                    keyboard["inline_keyboard"].append([
                        {"text": f"🚫 حظر {sid}", "callback_data": f"block:{sid}"}
                    ])
            keyboard["inline_keyboard"].append([{"text": "🔙 القائمة", "callback_data": "cmd:menu"}])
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines), "reply_markup": keyboard})
        else:
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "📭 لا يوجد مشتركين حالياً."})

    elif action == "pending":
        with subscribers_lock:
            pending = _load_pending()
        if pending:
            lines = ["⏳ طلبات الاشتراك المعلقة:\n"]
            keyboard = {"inline_keyboard": []}
            for pid in sorted(pending):
                lines.append(f"🆔 {pid}")
                keyboard["inline_keyboard"].append([
                    {"text": f"✅ قبول {pid}", "callback_data": f"approve:{pid}"},
                    {"text": f"❌ رفض {pid}", "callback_data": f"reject:{pid}"},
                ])
            keyboard["inline_keyboard"].append([{"text": "🔙 القائمة", "callback_data": "cmd:menu"}])
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines), "reply_markup": keyboard})
        else:
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "✅ لا توجد طلبات معلقة."})

    elif action == "admins_list" and is_owner(chat_id):
        admins = _load_admins()
        if admins:
            lines = ["👨‍💻 قائمة الأدمنز:\n"]
            keyboard = {"inline_keyboard": []}
            for i, aid in enumerate(sorted(admins), 1):
                lines.append(f"{i}. 👑 {aid}")
                keyboard["inline_keyboard"].append([
                    {"text": f"❌ إزالة أدمن {aid}", "callback_data": f"cmd:remove_admin_{aid}"}
                ])
            keyboard["inline_keyboard"].append([{"text": "🔙 القائمة", "callback_data": "cmd:menu"}])
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines), "reply_markup": keyboard})
        else:
            keyboard = {"inline_keyboard": [[{"text": "🔙 القائمة", "callback_data": "cmd:menu"}]]}
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "📭 لا يوجد أدمنز إضافيين.\n\nلإضافة أدمن أرسل:\n/add_admin <id>", "reply_markup": keyboard})

    elif action.startswith("remove_admin_") and is_owner(chat_id):
        try:
            target_id = int(action.split("_", 2)[2])
            with subscribers_lock:
                admins = _load_admins()
                admins.discard(target_id)
                _save_admins(admins)
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إزالة الأدمن {target_id}"})
        except Exception:
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ خطأ"})

    elif action == "status":
        with subscribers_lock:
            subs = _load_subscribers()
            pending = _load_pending()
            blocked = _load_blocked()
        status_msg = (
            f"📊 حالة البوت:\n"
            f"📢 الإشعارات للمشتركين: {'موقوفة 🔕' if _is_muted() else 'شغالة 🔔'}\n"
            f"👥 المشتركين المعتمدين: {len(subs)}\n"
            f"⏳ طلبات معلقة: {len(pending)}\n"
            f"🚫 محظورين: {len(blocked)}\n"
            f"👑 أدمنز: {len(_get_all_admins())}"
        )
        keyboard = {"inline_keyboard": [[{"text": "🔙 القائمة", "callback_data": "cmd:menu"}]]}
        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": status_msg, "reply_markup": keyboard})

    elif action == "blocked":
        with subscribers_lock:
            blocked = _load_blocked()
        if blocked:
            lines = ["🚫 المستخدمين المحظورين:\n"]
            keyboard = {"inline_keyboard": []}
            for bid in sorted(blocked):
                lines.append(f"🆔 {bid}")
                keyboard["inline_keyboard"].append([
                    {"text": f"✅ إلغاء حظر {bid}", "callback_data": f"cmd:unblock_{bid}"},
                ])
            keyboard["inline_keyboard"].append([{"text": "🔙 القائمة", "callback_data": "cmd:menu"}])
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines), "reply_markup": keyboard})
        else:
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "✅ لا يوجد محظورين."})

    elif action.startswith("unblock_"):
        try:
            target_id = int(action.split("_", 1)[1])
            with subscribers_lock:
                blocked = _load_blocked()
                blocked.discard(target_id)
                _save_blocked(blocked)
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إلغاء حظر {target_id}"})
        except Exception:
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ خطأ"})

    elif action == "mute":
        if _set_muted(True):
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔕 تم إيقاف إرسال الإشعارات للمشتركين.\n(الأدمنز فقط هيوصلهم التنبيهات)"})
            _send_admin_menu(base_url, chat_id)

    elif action == "unmute":
        if _set_muted(False):
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔔 تم إعادة تشغيل الإشعارات للمشتركين."})
            _send_admin_menu(base_url, chat_id)

    elif action == "delete_broadcast":
        msg_map = _load_broadcast_msgs()
        if not msg_map:
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لا توجد رسالة سابقة يمكن مسحها."})
            return
        
        deleted = 0
        for tid, mid in msg_map.items():
            try:
                r = requests.post(f"{base_url}/deleteMessage", json={"chat_id": tid, "message_id": mid}, timeout=5)
                if r.status_code == 200:
                    deleted += 1
            except Exception:
                pass
        
        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"🗑️ تم حذف الرسالة بنجاح من {deleted} مستخدم."})
        if os.path.exists(LAST_BROADCAST_FILE):
            os.remove(LAST_BROADCAST_FILE)

    elif action == "broadcast_help":
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": chat_id,
            "text": "📢 لبث رسالة لكل المشتركين:\n\nاكتب:\n/broadcast رسالتك هنا"
        })

    elif action == "send_last_help":
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": chat_id,
            "text": "🚀 لإرسال آخر طلبات للمشتركين، اكتب الأمر التالي متبوعاً بالعدد:\n\nمثال لإرسال آخر 5 طلبات:\n/send_last 5"
        })

    elif action == "help":
        help_text = (
            "🤖 أوامر البوت:\n\n"
            "👑 أوامر المالك:\n"
            "/menu - لوحة التحكم\n"
            "/ids - عرض كل المشتركين\n"
            "/add_admin <id> - إضافة أدمن\n"
            "/remove_admin <id> - إزالة أدمن\n"
            "/block <id> - حظر مستخدم\n"
            "/unblock <id> - إلغاء حظر\n"
            "/broadcast <رسالة> - إرسال رسالة للكل\n"
            "/send_last <رقم> - إرسال آخر الطلبات للكل\n\n"
            "⚙️ أوامر الأدمن:\n"
            "/approve <id> - قبول مشترك\n"
            "/reject <id> - رفض مشترك\n"
            "/pending - الطلبات المعلقة\n"
            "/status - حالة البوت\n\n"
            "👤 أوامر عامة:\n"
            "/start - طلب اشتراك\n"
            "/unsubscribe - إلغاء اشتراك\n"
            "/ping - فحص البوت"
        )
        keyboard = {"inline_keyboard": [[{"text": "🔙 القائمة", "callback_data": "cmd:menu"}]]}
        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": help_text, "reply_markup": keyboard})

    elif action == "menu":
        _send_admin_menu(base_url, chat_id)


def handle_updates_loop(poll_interval=1):
    """Poll Telegram getUpdates and handle /subscribe and /unsubscribe."""
    if not BOT_TOKEN:
        logger.info("Skipping updates handler: BOT_TOKEN missing")
        return

    offset = None
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    logger.info("Starting Telegram updates handler")
    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            resp = requests.get(f"{base_url}/getUpdates", params=params, timeout=40)
            data = resp.json() if resp.status_code == 200 else {}
            if not data.get("ok"):
                time.sleep(poll_interval)
                continue

            for upd in data.get("result", []):
                offset = upd["update_id"] + 1

                # Handle callback queries (inline button presses)
                cb = upd.get("callback_query")
                if cb:
                    cb_id = cb.get("id")
                    cb_data = cb.get("data", "")
                    cb_from = cb.get("from", {}).get("id")
                    cb_msg = cb.get("message", {})

                    if cb_from and is_admin(cb_from):
                        action, _, target_str = cb_data.partition(":")
                        try:
                            target_id = int(target_str)
                        except (ValueError, TypeError):
                            target_id = None

                        answer_text = ""
                        if action == "approve" and target_id:
                            if add_subscriber(target_id):
                                answer_text = f"✅ تم قبول {target_id}"
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "🎉 تم قبول اشتراكك! ستصلك تنبيهات الطلبات الجديدة."})
                            else:
                                answer_text = f"⚠️ فشل قبول {target_id}"
                        elif action == "reject" and target_id:
                            reject_subscriber(target_id)
                            answer_text = f"❌ تم رفض {target_id}"
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "❌ عذراً، تم رفض طلب اشتراكك."})
                        elif action == "block" and target_id:
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
                            answer_text = f"🚫 تم حظر {target_id}"
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "🚫 تم حظرك من هذا البوت."})
                        elif action == "menu":
                            _send_admin_menu(base_url, cb_from)
                            answer_text = ""
                        elif action == "cmd":
                            # Handle menu button presses
                            _handle_menu_action(base_url, cb_from, target_str)
                            answer_text = ""
                        else:
                            answer_text = "⚠️ إجراء غير معروف"

                        # Update the original message to show result
                        if answer_text and cb_msg.get("message_id"):
                            original_text = cb_msg.get("text", "")
                            requests.post(f"{base_url}/editMessageText", json={
                                "chat_id": cb_from,
                                "message_id": cb_msg["message_id"],
                                "text": f"{original_text}\n\n✔️ {answer_text}"
                            })

                        # Answer callback to remove loading state
                        requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": answer_text or "✅"})
                    else:
                        requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "⚠️ غير مصرح لك"})
                    continue

                msg = upd.get("message") or upd.get("edited_message")
                if not msg:
                    continue
                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                text = msg.get("text", "")
                if not text or not chat_id:
                    continue

                text = text.strip()

                # Rate limiting
                if not is_admin(chat_id) and not _check_rate_limit(chat_id):
                    continue

                if text.startswith("/start") or text.startswith("/subscribe"):
                    # Admins auto-approve themselves
                    if is_admin(chat_id):
                        add_subscriber(chat_id)
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "✅ تم تفعيل اشتراكك (أدمن)."})
                        if is_owner(chat_id):
                            _send_admin_menu(base_url, chat_id)
                    else:
                        from_user = msg.get("from", {})
                        username = from_user.get("username", "")
                        first_name = from_user.get("first_name", "") or "مستخدم"
                        result = request_subscription(chat_id, username, first_name)
                        if result == "pending":
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"مرحباً {first_name}! ⛳ تم إرسال طلب اشتراكك للأدمن. انتظر الموافقة."})
                        elif result == "already_approved":
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "✅ أنت مشترك بالفعل!"})
                        elif result == "already_pending":
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⏳ طلبك قيد المراجعة بالفعل. انتظر الموافقة."})
                        elif result == "blocked":
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🚫 تم حظرك من استخدام هذا البوت."})
                        else:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ حدث خطأ. حاول مرة أخرى."})

                elif text.startswith("/menu") and is_owner(chat_id):
                    _send_admin_menu(base_url, chat_id)

                elif text.startswith("/approve") and is_admin(chat_id):
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

                elif text.startswith("/reject") and is_admin(chat_id):
                    parts = text.split()
                    if len(parts) >= 2:
                        target_id = parts[1].strip()
                        try:
                            target_id = int(target_id)
                            reject_subscriber(target_id)
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"❌ تم رفض المستخدم {target_id}"})
                            # Notify the rejected user
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "❌ عذراً، تم رفض طلب اشتراكك."})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /reject <id>"})

                elif text.startswith("/ids") and is_owner(chat_id):
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

                elif text.startswith("/add_admin") and is_owner(chat_id):
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target_id = int(parts[1].strip())
                            if target_id == OWNER_ID:
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

                elif text.startswith("/remove_admin") and is_owner(chat_id):
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

                elif text.startswith("/block") and is_owner(chat_id):
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target_id = int(parts[1].strip())
                            if target_id == OWNER_ID:
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لا يمكنك حظر نفسك!"})
                            else:
                                with subscribers_lock:
                                    blocked = _load_blocked()
                                    blocked.add(target_id)
                                    _save_blocked(blocked)
                                    # Remove from subscribers and pending
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

                elif text.startswith("/unblock") and is_owner(chat_id):
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

                elif text.startswith("/broadcast ") and is_owner(chat_id):
                    broadcast_msg = text[len("/broadcast "):].strip()
                    if broadcast_msg:
                        with subscribers_lock:
                            subs = _load_subscribers()
                        all_targets = subs | _get_all_admins()
                        sent = 0
                        msg_map = {}
                        for target in all_targets:
                            try:
                                r = requests.post(f"{base_url}/sendMessage", json={"chat_id": target, "text": f"📢 السلام عليكم و رحمة اللة و بركاتة:\n\n{broadcast_msg}"}, timeout=10)
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

                elif text.startswith("/send_last") and is_owner(chat_id):
                    parts = text.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        count = int(parts[1])
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"⏳ جاري جلب آخر {count} طلبات..."})
                        
                        projects, _, _ = fetch_mostaql_projects()
                        if not projects:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ لم يتم العثور على طلبات حالياً."})
                        else:
                            to_send = projects[:count]
                            # Build message
                            msg_lines = [f"🚀 إليك آخر {len(to_send)} طلبات تم طرحها على خمسات:\n"]
                            for p in to_send:
                                msg_lines.append(f"📝 {p['title']}\n🔗 {p['link']}\n")
                            
                            broadcast_msg = "\n".join(msg_lines)
                            
                            # Broadcast
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

                elif text.startswith("/unsubscribe"):
                    remove_subscriber(chat_id)
                    mu = _load_muted_users()
                    mu.discard(chat_id)
                    _save_muted_users(mu)
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ تم إلغاء اشتراكك."})

                elif text.startswith("/mymute"):
                    with subscribers_lock:
                        subs = _load_subscribers()
                    if chat_id in subs or is_admin(chat_id):
                        mu = _load_muted_users()
                        mu.add(chat_id)
                        _save_muted_users(mu)
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔕 تم كتم الإشعارات لحسابك مؤقتاً.\nأرسل /myunmute لإعادة تفعيلها."})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ أنت لست مشتركاً."})

                elif text.startswith("/myunmute"):
                    mu = _load_muted_users()
                    mu.discard(chat_id)
                    _save_muted_users(mu)
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔔 تم إعادة تفعيل إشعاراتك!"})

                elif text.startswith("/backup") and is_owner(chat_id):
                    files_to_send = [
                        SUBSCRIBERS_FILE, ADMINS_FILE, BLOCKED_FILE,
                        PENDING_FILE, STATE_FILE, SEEN_FILE, STATS_FILE
                    ]
                    tele_url_doc = f"{base_url}/sendDocument"
                    sent_backup = 0
                    for fp in files_to_send:
                        if os.path.exists(fp):
                            try:
                                with open(fp, 'rb') as doc:
                                    requests.post(tele_url_doc, data={"chat_id": chat_id}, files={"document": doc}, timeout=15)
                                sent_backup += 1
                            except Exception:
                                pass
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إرسال {sent_backup} ملف باكاب."})

                elif text.startswith("/pending") and is_admin(chat_id):
                    with subscribers_lock:
                        pending = _load_pending()
                    if pending:
                        lines = ["⏳ طلبات الاشتراك المعلقة:\n"]
                        for pid in sorted(pending):
                            lines.append(f"🆔 {pid}  →  /approve {pid}")
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines)})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "✅ لا توجد طلبات معلقة."})

                elif text.startswith("/help"):
                    if is_owner(chat_id):
                        help_text = (
                            "🤖 أوامر البوت:\n\n"
                            "👑 أوامر المالك:\n"
                            "/ids - عرض كل المشتركين\n"
                            "/add_admin <id> - إضافة أدمن\n"
                            "/remove_admin <id> - إزالة أدمن\n"
                            "/block <id> - حظر مستخدم\n"
                            "/unblock <id> - إلغاء حظر\n"
                            "/broadcast <رسالة> - إرسال للكل\n"
                            "/backup - نسخة احتياطية\n\n"
                            "⚙️ أوامر الأدمن:\n"
                            "/approve <id> - قبول مشترك\n"
                            "/reject <id> - رفض مشترك\n"
                            "/pending - الطلبات المعلقة\n"
                            "/status - حالة البوت\n\n"
                            "👤 أوامر عامة:\n"
                            "/start - طلب اشتراك\n"
                            "/mymute - كتم إشعاراتك مؤقتاً\n"
                            "/myunmute - تفعيل إشعاراتك\n"
                            "/unsubscribe - إلغاء اشتراك\n"
                            "/ping - فحص البوت"
                        )
                    elif is_admin(chat_id):
                        help_text = (
                            "🤖 أوامر البوت:\n\n"
                            "⚙️ أوامر الأدمن:\n"
                            "/approve <id> - قبول مشترك\n"
                            "/reject <id> - رفض مشترك\n"
                            "/pending - الطلبات المعلقة\n"
                            "/status - حالة البوت\n\n"
                            "👤 أوامر عامة:\n"
                            "/mymute - كتم إشعاراتك\n"
                            "/myunmute - تفعيل إشعاراتك\n"
                            "/unsubscribe - إلغاء اشتراك\n"
                            "/ping - فحص البوت"
                        )
                    else:
                        help_text = (
                            "🤖 أوامر البوت:\n\n"
                            "/start - طلب اشتراك\n"
                            "/mymute - كتم إشعاراتك مؤقتاً\n"
                            "/myunmute - تفعيل إشعاراتك\n"
                            "/unsubscribe - إلغاء اشتراك\n"
                            "/ping - فحص البوت"
                        )
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": help_text})

                elif text.startswith("/status") and is_admin(chat_id):
                    with subscribers_lock:
                        subs = _load_subscribers()
                        pending = _load_pending()
                        blocked = _load_blocked()
                    stats = _get_stats()
                    uptime_sec = int(time.time() - bot_start_time)
                    h, m = divmod(uptime_sec // 60, 60)
                    muted_count = len(_load_muted_users())
                    status_msg = (
                        f"📊 حالة البوت:\n"
                        f"⏱️ وقت التشغيل: {h}ساعة {m}دقيقة\n"
                        f"👥 المشتركين: {len(subs)} / {MAX_SUBSCRIBERS}\n"
                        f"🔕 كتموا إشعاراتهم: {muted_count}\n"
                        f"⏳ طلبات معلقة: {len(pending)}\n"
                        f"🚫 محظورين: {len(blocked)}\n"
                        f"👑 أدمنز: {len(_get_all_admins())}\n"
                        f"🔢 أعلى ID طلب شوفناه: {max_seen_id}\n"
                        f"📨 إجمالي رسائل مرسلة: {stats.get('total_sent', 0)}"
                    )
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": status_msg})

                elif text.startswith("/ping"):
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "pong ✅"})

        except Exception as e:
            logger.debug(f"Updates loop error: {str(e)}")
            time.sleep(poll_interval)


def _load_max_id():
    """Load the maximum request ID seen so far."""
    if not os.path.exists(SEEN_FILE):
        return 0
    try:
        with open(SEEN_FILE, "r") as f:
            return int(json.load(f))
    except Exception:
        return 0


def _save_max_id(max_id):
    """Save the maximum request ID seen so far."""
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(max_id, f)
    except Exception as e:
        logger.error(f"Failed to save max ID: {str(e)}")


def check_khamsat():
    """فحص طلبات جديدة على موقع خمسات — يعتمد على أعلى ID رقمي شوفناه"""
    global max_seen_id, premium_proxies, free_proxies

    projects, proxy_type, p_addr = fetch_mostaql_projects()
    if not projects:
        return

    # استخرج IDs رقمية فقط، مرتبة تصاعدياً
    numeric_projects = []
    for p in projects:
        try:
            numeric_projects.append((int(p["id"]), p))
        except ValueError:
            pass

    numeric_projects.sort(key=lambda x: x[0])  # ترتيب من الأصغر للأكبر

    new_max = max_seen_id
    for pid_int, project in numeric_projects:
        if pid_int <= max_seen_id:
            continue  # طلب قديم أو مكرر — تجاهله حتى لو طلع فوق بسبب كومنت

        msg = f"🌟 طلب جديد على خمسات:\n\n📝 {project['title']}\n\n🔗 {project['link']}"
        send_telegram(msg)
        new_max = max(new_max, pid_int)

    if new_max > max_seen_id:
        max_seen_id = new_max
        _save_max_id(max_seen_id)
        logger.info(f"New max_seen_id saved: {max_seen_id}")

    if proxy_type and p_addr:
        logger.info(f"Khamsat scan succeeded via {proxy_type} proxy ({p_addr})")


def send_startup_snapshot(projects):
    """إرسال ملخص أولي للطلبات الحالية عند التشغيل"""
    if not BOT_TOKEN:
        return False

    if not projects:
        return send_telegram("🚀 تم التشغيل، لكن لم يتم العثور على طلبات حالياً.")

    sample_count = min(5, len(projects))
    lines = [f"🚀 تم التشغيل بنجاح.", f"📊 أعلى ID طلب موجود: {max_seen_id}", "", f"أحدث {sample_count} طلبات شوفناها:"]
    for project in sorted(projects, key=lambda p: int(p['id']) if p['id'].isdigit() else 0, reverse=True)[:sample_count]:
        lines.append(f"- {project['title']}\n  {project['link']}")

    return send_telegram("\n".join(lines))


def seed_max_id(projects):
    """تسجيل أعلى ID موجود حالياً عند بداية التشغيل لتجنب الإشعارات المكررة"""
    global max_seen_id

    ids = []
    for p in projects:
        try:
            ids.append(int(p["id"]))
        except ValueError:
            pass
    if ids:
        max_seen_id = max(ids)
        _save_max_id(max_seen_id)
        logger.info(f"Startup baseline set: max_seen_id = {max_seen_id}")


def _weekly_stats_thread():
    """Send weekly stats report to owner every 7 days."""
    WEEK = 7 * 24 * 3600
    while True:
        time.sleep(WEEK)
        try:
            with subscribers_lock:
                subs = _load_subscribers()
                pending = _load_pending()
                blocked = _load_blocked()
            stats = _get_stats()
            uptime_sec = int(time.time() - bot_start_time)
            h, m = divmod(uptime_sec // 60, 60)
            msg = (
                f"📅 التقرير الأسبوعي:\n"
                f"⏱️ وقت التشغيل: {h}س {m}د\n"
                f"👥 المشتركين: {len(subs)}/{MAX_SUBSCRIBERS}\n"
                f"⏳ طلبات معلقة: {len(pending)}\n"
                f"🚫 محظورين: {len(blocked)}\n"
                f"🔢 أعلى ID طلب: {max_seen_id}\n"
                f"📨 إجمالي رسائل مرسلة: {stats.get('total_sent', 0)}"
            )
            _notify_admins(msg)
        except Exception as e:
            logger.error(f"Weekly stats error: {e}")

# =========================
# START
# =========================
if __name__ == "__main__":
    # تحميل أعلى ID شوفناه من قبل
    max_seen_id = _load_max_id()
    logger.info(f"Loaded max_seen_id = {max_seen_id}")

    logger.info("=" * 50)
    logger.info("Khamsat bot started")
    logger.info("=" * 50)

    # تشغيل Telegram polling في الخلفية
    if BOT_TOKEN:
        t = threading.Thread(target=handle_updates_loop, kwargs={"poll_interval": 2}, daemon=True)
        t.start()
        tw = threading.Thread(target=_weekly_stats_thread, daemon=True)
        tw.start()

    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN is missing - Telegram sending is disabled")
    else:
        send_telegram("🚀 بدأت مراقبة طلبات 'خمسات' الآن..")

    # جلب الطلبات الحالية وتسجيل أعلى ID (بدون إرسال إشعارات عنها)
    startup_projects, startup_proxy_type, startup_proxy_addr = fetch_mostaql_projects()
    if startup_projects:
        if max_seen_id == 0:
            # أول تشغيل: سجّل الـ baseline بدون إشعارات
            seed_max_id(startup_projects)
        send_startup_snapshot(startup_projects)
        if startup_proxy_type and startup_proxy_addr:
            logger.info(f"Startup scan via {startup_proxy_type} proxy ({startup_proxy_addr})")
    else:
        logger.warning("No startup projects were found")

    # حلقة المراقبة الرئيسية
    while True:
        try:
            check_khamsat()
        except KeyboardInterrupt:
            logger.info("\nBot stopped by user")
            break
        except Exception as e:
            logger.error(f"Main loop error: {str(e)}")

        wait = CHECK_INTERVAL + random.randint(5, 15)
        logger.info(f"Waiting {wait}s before the next scan")
        time.sleep(wait)