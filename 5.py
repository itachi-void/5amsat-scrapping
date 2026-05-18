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

# Sync Locks and Shared Objects
subscribers_lock = threading.Lock()
seen_ids_lock = threading.Lock()
max_seen_id_lock = threading.Lock()

MAX_SUBSCRIBERS = 50

# Rate limiting map: {(bot_type, chat_id): last_msg_timestamp}
_rate_limit_map = {}
_RATE_LIMIT_SECONDS = 3

# Project caches
_mostaql_project_cache = {"data": [], "ts": 0}
_khamsat_project_cache = {"data": [], "ts": 0}
MOSTAQL_CACHE_TTL = 30
KHAMSAT_CACHE_TTL = 20

# Backoff states
backoff_until_mostaql = 0
backoff_until_khamsat = 0
deep_scan_counter_mostaql = 0
deep_scan_counter_khamsat = 0

# Uptime baseline
bot_start_time = time.time()

# Configurations & Tokens (Auto-loaded from .env files)
MOSTAQL_BOT_TOKEN = None
KHAMSAT_BOT_TOKEN = None

TELEGRAPH_TOKEN_MOSTAQL = "c8bb576ff4e83bab9ecf8711741738ffab9e8a428145ca0a69c6fbc69004"
TELEGRAPH_PATH_MOSTAQL = "DB-05-17-2"

TELEGRAPH_TOKEN_KHAMSAT = "2182ffe6168f99027ca825ef33d364abc37cede07f0286aef1b9f993d791"
TELEGRAPH_PATH_KHAMSAT = "DB-05-17"

PROXY_USER = ""
PROXY_PASS = ""

CHECK_INTERVAL_MOSTAQL = 45
DATA_DIR = os.getenv("DATA_DIR", ".")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# Logger Setup (Console + rotating file)
_log_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_log_formatter)
try:
    log_file_path = os.path.join(DATA_DIR, 'unified_bot.log')
    _fh = RotatingFileHandler(log_file_path, maxBytes=2*1024*1024, backupCount=3, encoding='utf-8')
    _fh.setFormatter(_log_formatter)
    logger.addHandler(_fh)
except Exception:
    pass
logger.addHandler(_console_handler)
logging.getLogger().addHandler(_console_handler)

premium_proxies = []  # [(scheme, addr)]
free_proxies = []     # [(scheme, addr)]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
]

IMPERSONATE_TARGETS = ["chrome110", "chrome116", "chrome120", "chrome123", "chrome124", "safari15_3", "safari17_0", "edge101"]

def _new_scraper():
    """Create a fresh scraper session with random browser fingerprint."""
    target = random.choice(IMPERSONATE_TARGETS)
    return cffi_requests.Session(impersonate=target)

scraper = _new_scraper()

# ==============================================================================
# ENVIRONMENT AND CONFIG DYNAMIC LOADER
# ==============================================================================
def load_all_configs():
    """Dynamically load configs from both workspace .env files."""
    global MOSTAQL_BOT_TOKEN, KHAMSAT_BOT_TOKEN, PROXY_USER, PROXY_PASS, DATA_DIR
    
    # Check current env vars first
    MOSTAQL_BOT_TOKEN = os.getenv("MOSTAQL_BOT_TOKEN")
    KHAMSAT_BOT_TOKEN = os.getenv("KHAMSAT_BOT_TOKEN")
    PROXY_USER = os.getenv("PROXY_USER", "")
    PROXY_PASS = os.getenv("PROXY_PASS", "")

    # Mostaql .env path
    mostaql_env = "C:\\Users\\itachi\\Downloads\\mostaql scrapping\\.env"
    if os.path.exists(mostaql_env):
        with open(mostaql_env, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k == "BOT_TOKEN" and not MOSTAQL_BOT_TOKEN:
                        MOSTAQL_BOT_TOKEN = v
                    elif k == "PROXY_USER" and not PROXY_USER:
                        PROXY_USER = v
                    elif k == "PROXY_PASS" and not PROXY_PASS:
                        PROXY_PASS = v

    # Khamsat .env path
    khamsat_env = "C:\\Users\\itachi\\Downloads\\5amsat-scrapping\\.env"
    if os.path.exists(khamsat_env):
        with open(khamsat_env, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k == "BOT_TOKEN" and not KHAMSAT_BOT_TOKEN:
                        KHAMSAT_BOT_TOKEN = v

    # Fallback to local .env if any token is still empty
    if not MOSTAQL_BOT_TOKEN:
        MOSTAQL_BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not KHAMSAT_BOT_TOKEN:
        KHAMSAT_BOT_TOKEN = os.getenv("BOT_TOKEN")

    logger.info(f"Config loaded: Mostaql Token={'Loaded' if MOSTAQL_BOT_TOKEN else 'Missing'}, Khamsat Token={'Loaded' if KHAMSAT_BOT_TOKEN else 'Missing'}")

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
def _get_file_path(bot_type, file_key):
    """Retrieve isolated path prefixing bot_type to prevent database collisions."""
    names = {
        "subscribers": "subscribers.json",
        "pending": "pending_subscribers.json",
        "blocked": "blocked_users.json",
        "roles": "roles.json",
        "state": "bot_state.json",
        "seen": "seen_ids.json" if bot_type == "mostaql" else "max_id.json",
        "muted": "muted_users.json",
        "stats": "bot_stats.json",
        "last_broadcast": "last_broadcast_msgs.json"
    }
    return os.path.join(DATA_DIR, f"{bot_type}_{names[file_key]}")

def _load_subscribers(bot_type):
    file_path = _get_file_path(bot_type, "subscribers")
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

def _save_subscribers(bot_type, subs_set):
    file_path = _get_file_path(bot_type, "subscribers")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(subs_set), f)
    os.replace(tmp_path, file_path)

def _load_roles(bot_type):
    file_path = _get_file_path(bot_type, "roles")
    if not os.path.exists(file_path):
        default_roles = {"owner": 1622676655, "admins": [8064837651]}
        _save_roles(bot_type, default_roles)
        return default_roles
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"owner": 1622676655, "admins": [8064837651]}

def _save_roles(bot_type, roles_data):
    file_path = _get_file_path(bot_type, "roles")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(roles_data, f, indent=4)
    os.replace(tmp_path, file_path)

def get_owner_id(bot_type):
    return int(_load_roles(bot_type).get("owner", 1622676655))

def _load_admins(bot_type):
    roles = _load_roles(bot_type)
    admins_list = roles.get("admins", [])
    if not isinstance(admins_list, list):
        admins_list = []
    return {int(x) for x in admins_list}

def _save_admins(bot_type, admins_set):
    roles = _load_roles(bot_type)
    roles["admins"] = sorted(admins_set)
    _save_roles(bot_type, roles)

def _get_all_admins(bot_type):
    return _load_admins(bot_type) | {get_owner_id(bot_type)}

def _load_pending(bot_type):
    file_path = _get_file_path(bot_type, "pending")
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

def _save_pending(bot_type, pending_set):
    file_path = _get_file_path(bot_type, "pending")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(pending_set), f)
    os.replace(tmp_path, file_path)

def _load_blocked(bot_type):
    file_path = _get_file_path(bot_type, "blocked")
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

def _save_blocked(bot_type, blocked_set):
    file_path = _get_file_path(bot_type, "blocked")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(blocked_set), f)
    os.replace(tmp_path, file_path)

def _load_muted_users(bot_type):
    file_path = _get_file_path(bot_type, "muted")
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

def _save_muted_users(bot_type, muted_set):
    file_path = _get_file_path(bot_type, "muted")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(muted_set), f)
    os.replace(tmp_path, file_path)

def _get_stats(bot_type):
    file_path = _get_file_path(bot_type, "stats")
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_stats(bot_type, stats_data):
    file_path = _get_file_path(bot_type, "stats")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=4)
    os.replace(tmp_path, file_path)

def _increment_stats(bot_type, sent_count):
    if sent_count <= 0:
        return
    with subscribers_lock:
        s = _get_stats(bot_type)
        s["total_sent"] = s.get("total_sent", 0) + sent_count
        _save_stats(bot_type, s)

def _load_broadcast_msgs(bot_type):
    file_path = _get_file_path(bot_type, "last_broadcast")
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        pass
    return {}

def _save_broadcast_msgs(bot_type, msg_map):
    file_path = _get_file_path(bot_type, "last_broadcast")
    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(msg_map, f, indent=4)
    os.replace(tmp_path, file_path)

# ==============================================================================
# SUBSCRIBER MUTATION ENGINE
# ==============================================================================
def add_subscriber(bot_type, chat_id):
    """Add user to subscribers list (max limit of 50 enforced)."""
    with subscribers_lock:
        subs = _load_subscribers(bot_type)
        pending = _load_pending(bot_type)
        blocked = _load_blocked(bot_type)
        
        if chat_id in blocked:
            return False
            
        if chat_id in subs:
            return True
            
        if len(subs) >= MAX_SUBSCRIBERS:
            pending.add(chat_id)
            _save_pending(bot_type, pending)
            return False
            
        subs.add(chat_id)
        _save_subscribers(bot_type, subs)
        pending.discard(chat_id)
        _save_pending(bot_type, pending)
        return True

def remove_subscriber(bot_type, chat_id):
    with subscribers_lock:
        subs = _load_subscribers(bot_type)
        subs.discard(chat_id)
        _save_subscribers(bot_type, subs)
        
        pending = _load_pending(bot_type)
        pending.discard(chat_id)
        _save_pending(bot_type, pending)

def reject_subscriber(bot_type, chat_id):
    with subscribers_lock:
        pending = _load_pending(bot_type)
        pending.discard(chat_id)
        _save_pending(bot_type, pending)
        
        subs = _load_subscribers(bot_type)
        subs.discard(chat_id)
        _save_subscribers(bot_type, subs)

def is_owner(bot_type, chat_id):
    try:
        return int(chat_id) == get_owner_id(bot_type)
    except (ValueError, TypeError):
        return False

def is_admin(bot_type, chat_id):
    try:
        cid = int(chat_id)
        return cid in _load_admins(bot_type) or cid == get_owner_id(bot_type)
    except (ValueError, TypeError):
        return False

def _notify_admins(bot_type, text):
    """Alert all administrative endpoints of events."""
    token = MOSTAQL_BOT_TOKEN if bot_type == "mostaql" else KHAMSAT_BOT_TOKEN
    if not token or not _get_all_admins(bot_type):
        return
    for cid in _get_all_admins(bot_type):
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": cid, "text": text}, timeout=10)
        except Exception:
            pass

def _is_rate_limited(bot_type, chat_id):
    now = time.time()
    key = (bot_type, chat_id)
    last = _rate_limit_map.get(key, 0)
    if now - last < _RATE_LIMIT_SECONDS:
        return True
    _rate_limit_map[key] = now
    return False

# ==============================================================================
# TELEGRAM BASE TRANSMITTER
# ==============================================================================
def _send_one(bot_type, chat_id, text, reply_markup=None, retries=3):
    """Send message to user with auto-removal if bot blocked."""
    token = MOSTAQL_BOT_TOKEN if bot_type == "mostaql" else KHAMSAT_BOT_TOKEN
    if not token:
        return False, None
    tele_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    for attempt in range(retries):
        try:
            r = requests.post(tele_url, json=payload, timeout=10)
            if r.status_code == 200:
                return True, r.json().get("result", {}).get("message_id")
            elif r.status_code == 403:
                remove_subscriber(bot_type, chat_id)
                logger.warning(f"Removed user {chat_id} from {bot_type} subscribers (blocked the bot).")
                return False, None
        except Exception:
            pass
        time.sleep(1)
    return False, None

# ==============================================================================
# TELEGRAPH DATA CLOUD BACKUP INTEGRATION
# ==============================================================================
last_uploaded_db_hash_mostaql = None
last_uploaded_db_hash_khamsat = None

def generate_full_backup(bot_type):
    backup_data = {}
    files_to_backup = {
        "subscribers": _get_file_path(bot_type, "subscribers"),
        "pending": _get_file_path(bot_type, "pending"),
        "blocked": _get_file_path(bot_type, "blocked"),
        "roles": _get_file_path(bot_type, "roles"),
        "state": _get_file_path(bot_type, "state"),
        "seen": _get_file_path(bot_type, "seen"),
        "muted": _get_file_path(bot_type, "muted"),
        "stats": _get_file_path(bot_type, "stats"),
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

def restore_full_backup(bot_type, backup_data):
    files_to_backup = {
        "subscribers": _get_file_path(bot_type, "subscribers"),
        "pending": _get_file_path(bot_type, "pending"),
        "blocked": _get_file_path(bot_type, "blocked"),
        "roles": _get_file_path(bot_type, "roles"),
        "state": _get_file_path(bot_type, "state"),
        "seen": _get_file_path(bot_type, "seen"),
        "muted": _get_file_path(bot_type, "muted"),
        "stats": _get_file_path(bot_type, "stats"),
    }
    for key, fpath in files_to_backup.items():
        if key in backup_data and backup_data[key] is not None:
            tmp = fpath + ".tmp"
            try:
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(backup_data[key], f, indent=4)
                os.replace(tmp, fpath)
            except Exception as e:
                logger.error(f"Failed to restore {key} for {bot_type}: {e}")

def generate_system_backup():
    """Generate a single unified backup for both Mostaql and Khamsat data."""
    return {
        "mostaql": generate_full_backup("mostaql"),
        "khamsat": generate_full_backup("khamsat"),
        "timestamp": time.time()
    }

def restore_system_backup(backup_data):
    """Restore a single unified backup containing both Mostaql and Khamsat data."""
    if "mostaql" in backup_data and backup_data["mostaql"] is not None:
        restore_full_backup("mostaql", backup_data["mostaql"])
    if "khamsat" in backup_data and backup_data["khamsat"] is not None:
        restore_full_backup("khamsat", backup_data["khamsat"])

def download_telegraph_db(bot_type):
    token = TELEGRAPH_TOKEN_MOSTAQL if bot_type == "mostaql" else TELEGRAPH_TOKEN_KHAMSAT
    path = TELEGRAPH_PATH_MOSTAQL if bot_type == "mostaql" else TELEGRAPH_PATH_KHAMSAT
    try:
        r = requests.get(f'https://api.telegra.ph/getPage/{path}?return_content=true').json()
        if not r.get("ok"):
            return
        content = r['result']['content'][0]['children'][0]
        if content and content.startswith("{"):
            backup_data = json.loads(content)
            restore_full_backup(bot_type, backup_data)
            logger.info(f"Successfully restored {bot_type} state from Telegraph DB cloud!")
    except Exception as e:
        logger.error(f"Failed to download Telegraph DB for {bot_type}: {e}")

def telegraph_sync_thread(bot_type):
    global last_uploaded_db_hash_mostaql, last_uploaded_db_hash_khamsat
    
    token = TELEGRAPH_TOKEN_MOSTAQL if bot_type == "mostaql" else TELEGRAPH_TOKEN_KHAMSAT
    path = TELEGRAPH_PATH_MOSTAQL if bot_type == "mostaql" else TELEGRAPH_PATH_KHAMSAT
    
    while True:
        try:
            backup_data = generate_full_backup(bot_type)
            db_str = json.dumps(backup_data)
            db_hash = hash(db_str)
            
            is_new = False
            if bot_type == "mostaql":
                if db_hash != last_uploaded_db_hash_mostaql:
                    is_new = True
            else:
                if db_hash != last_uploaded_db_hash_khamsat:
                    is_new = True
                    
            if is_new:
                content = [{"tag":"p", "children":[db_str]}]
                r = requests.post(f'https://api.telegra.ph/editPage/{path}', json={
                    'access_token': token,
                    'title': f'DB_{bot_type}',
                    'content': json.dumps(content)
                }).json()
                if r.get("ok"):
                    if bot_type == "mostaql":
                        last_uploaded_db_hash_mostaql = db_hash
                    else:
                        last_uploaded_db_hash_khamsat = db_hash
                    logger.info(f"Successfully synced {bot_type} state to Telegraph DB!")
        except Exception:
            pass
        time.sleep(120)

# ==============================================================================
# CORE SCRAPING ENGINES
# ==============================================================================
def fetch_mostaql_projects(max_pages=5, max_attempts=12):
    """Fetch up to max_pages of Mostaql projects, with short-lived cache."""
    global scraper, _mostaql_project_cache
    now = time.time()
    if _mostaql_project_cache["data"] and (now - _mostaql_project_cache["ts"]) < MOSTAQL_CACHE_TTL:
        return _mostaql_project_cache["data"], "cache", None

    headers = {"User-Agent": random.choice(USER_AGENTS)}
    all_proxies = list(premium_proxies) + list(free_proxies)
    random.shuffle(all_proxies)

    proxy_idx = 0
    def get_next_proxy():
        nonlocal proxy_idx
        while proxy_idx < len(all_proxies) and proxy_idx < max_attempts:
            scheme, addr = all_proxies[proxy_idx]
            proxy_idx += 1
            if PROXY_USER and PROXY_PASS and (scheme, addr) in premium_proxies:
                pu = f"{scheme}://{PROXY_USER}:{PROXY_PASS}@{addr}"
                pk = "premium"
            else:
                pu = f"{scheme}://{addr}"
                pk = "free"
            return {"http": pu, "https": pu}, pk, addr
        return None, "direct", None

    chosen_proxies, proxy_kind, p_addr = get_next_proxy()
    all_items = []
    seen_in_fetch = set()

    url_mostaql = "https://mostaql.com/projects"
    for page_num in range(1, max_pages + 1):
        if len(all_items) >= 200:
            break
        page_url = f"{url_mostaql}?page={page_num}" if page_num > 1 else url_mostaql
        
        items = None
        while items is None:
            if chosen_proxies is None:
                scraper = _new_scraper()
                items = _fetch_mostaql_page(page_url, headers)
                if items is None:
                    break
            else:
                items = _fetch_mostaql_page(page_url, headers, chosen_proxies, proxy_kind, p_addr)
                if items is None:
                    chosen_proxies, proxy_kind, p_addr = get_next_proxy()
                    if chosen_proxies is None:
                        break
                        
        if not items:
            break
            
        for item in items:
            if item["id"] not in seen_in_fetch:
                seen_in_fetch.add(item["id"])
                all_items.append(item)
                
        time.sleep(0.5)

    all_items = all_items[:200]
    if all_items:
        logger.info(f"Fetched {len(all_items)} Mostaql projects via {proxy_kind} ({p_addr})")
        _mostaql_project_cache["data"] = all_items
        _mostaql_project_cache["ts"] = time.time()
    return all_items, proxy_kind, p_addr

def _fetch_mostaql_page(page_url, headers, proxies=None, proxy_kind="direct", p_addr=None):
    global scraper, backoff_until_mostaql
    try:
        resp = scraper.get(page_url, headers=headers, proxies=proxies or {}, timeout=10)
        if resp.status_code == 200:
            return extract_mostaql_projects(resp.text)
        elif resp.status_code in (429, 403):
            logger.error(f"Mostaql returned {resp.status_code}. Backing off for 5 minutes.")
            backoff_until_mostaql = time.time() + 300
            _notify_admins("mostaql", f"⚠️ تحذير: موقع مستقل قام بحظر الطلبات مؤقتاً (Error {resp.status_code}). تم إيقاف الفحص لمدة 5 دقائق.")
    except Exception as e:
        logger.warning(f"Mostaql Fetch error ({proxy_kind} {p_addr}): {e}")
    return None

def extract_mostaql_projects(html_text):
    if not html_text or not isinstance(html_text, str):
        return []
    soup = BeautifulSoup(html_text, "html.parser")
    project_elements = soup.select("a[href*='/project/']")
    projects = []

    for el in project_elements:
        full_link = el.get("href")
        if not full_link:
            continue

        if full_link.startswith("/"):
            full_link = f"https://mostaql.com{full_link}"

        if "/project/" not in full_link:
            continue

        try:
            project_id = full_link.split('/project/')[-1].split('-')[0]
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
        while proxy_idx < len(all_proxies) and proxy_idx < max_attempts:
            scheme, addr = all_proxies[proxy_idx]
            proxy_idx += 1
            if PROXY_USER and PROXY_PASS and (scheme, addr) in premium_proxies:
                pu = f"{scheme}://{PROXY_USER}:{PROXY_PASS}@{addr}"
                pk = "premium"
            else:
                pu = f"{scheme}://{addr}"
                pk = "free"
            return {"http": pu, "https": pu}, pk, addr
        return None, "direct", None

    chosen_proxies, proxy_kind, p_addr = get_next_proxy()
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
                    if chosen_proxies is None:
                        break
                        
        if not items:
            break
            
        for item in items:
            if item["id"] not in seen_in_fetch:
                seen_in_fetch.add(item["id"])
                all_items.append(item)
                
        time.sleep(0.5)

    all_items = all_items[:200]
    if all_items:
        logger.info(f"Fetched {len(all_items)} Khamsat requests via {proxy_kind} ({p_addr})")
        _khamsat_project_cache["data"] = all_items
        _khamsat_project_cache["ts"] = time.time()
    return all_items, proxy_kind, p_addr

def _fetch_khamsat_page(page_url, headers, proxies=None, proxy_kind="direct", p_addr=None):
    global scraper, backoff_until_khamsat
    try:
        resp = scraper.get(page_url, headers=headers, proxies=proxies or {}, timeout=15)
        if resp.status_code == 200:
            return extract_khamsat_projects(resp.text)
        elif resp.status_code in (429, 403):
            logger.error(f"Khamsat returned {resp.status_code}. Backing off for 5 minutes.")
            backoff_until_khamsat = time.time() + 300
            _notify_admins("khamsat", f"⚠️ تحذير: موقع خمسات قام بحظر الطلبات مؤقتاً (Error {resp.status_code}). تم إيقاف الفحص لمدة 5 دقائق.")
    except Exception as e:
        logger.warning(f"Khamsat Fetch error ({proxy_kind} {p_addr}): {e}")
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

# ==============================================================================
# MONITORING ENGINE & REAL-TIME EMITTERS
# ==============================================================================
seen_ids = set()
max_seen_id = 0

def check_mostaql():
    global seen_ids, backoff_until_mostaql, deep_scan_counter_mostaql
    
    if time.time() < backoff_until_mostaql:
        return

    deep_scan_counter_mostaql += 1
    pages_to_fetch = 5 if deep_scan_counter_mostaql % 20 == 0 else 1
    if deep_scan_counter_mostaql % 20 == 0:
        global _mostaql_project_cache
        _mostaql_project_cache["ts"] = 0

    projects, proxy_type, p_addr = fetch_mostaql_projects(max_pages=pages_to_fetch)
    if not projects:
        return

    new_projects = []
    with seen_ids_lock:
        for p in projects:
            p_id = p["id"]
            if p_id not in seen_ids:
                seen_ids.add(p_id)
                new_projects.append(p)
        
        if new_projects:
            try:
                seen_file = _get_file_path("mostaql", "seen")
                tmp_path = seen_file + ".tmp"
                with open(tmp_path, "w") as f:
                    json.dump(list(seen_ids), f)
                os.replace(tmp_path, seen_file)
            except Exception as e:
                logger.error(f"Failed to save Mostaql seen IDs: {e}")

    if new_projects:
        subs = _load_subscribers("mostaql")
        muted = _load_muted_users("mostaql")
        targets = (subs | _get_all_admins("mostaql")) - muted
        
        for p in reversed(new_projects):
            msg_text = f"🚀 مشروع جديد على مستقل:\n\n📝 {p['title']}"
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "عرض المشروع ↗️", "url": p['link']}]
                ]
            }
            sent_count = 0
            for cid in targets:
                success, _ = _send_one("mostaql", cid, msg_text, reply_markup=reply_markup)
                if success:
                    sent_count += 1
            _increment_stats("mostaql", sent_count)

def check_khamsat():
    global max_seen_id, backoff_until_khamsat, deep_scan_counter_khamsat
    
    if time.time() < backoff_until_khamsat:
        return

    deep_scan_counter_khamsat += 1
    pages_to_fetch = 5 if deep_scan_counter_khamsat % 20 == 0 else 1
    if deep_scan_counter_khamsat % 20 == 0:
        global _khamsat_project_cache
        _khamsat_project_cache["ts"] = 0

    projects, proxy_type, p_addr = fetch_khamsat_projects(max_pages=pages_to_fetch)
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
                seen_file = _get_file_path("khamsat", "seen")
                tmp_path = seen_file + ".tmp"
                with open(tmp_path, "w") as f:
                    json.dump(max_seen_id, f)
                os.replace(tmp_path, seen_file)
            except Exception as e:
                logger.error(f"Failed to save Khamsat max seen ID: {e}")

    if new_projects:
        subs = _load_subscribers("khamsat")
        muted = _load_muted_users("khamsat")
        targets = (subs | _get_all_admins("khamsat")) - muted
        
        new_projects.sort(key=lambda x: int(x["id"]))
        
        for p in new_projects:
            msg_text = f"🚀 طلب جديد على خمسات:\n\n📝 {p['title']}"
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "عرض الطلب ↗️", "url": p['link']}]
                ]
            }
            sent_count = 0
            for cid in targets:
                success, _ = _send_one("khamsat", cid, msg_text, reply_markup=reply_markup)
                if success:
                    sent_count += 1
            _increment_stats("khamsat", sent_count)

def seed_seen_projects(projects):
    global seen_ids
    with seen_ids_lock:
        for p in projects:
            seen_ids.add(p["id"])
        try:
            seen_file = _get_file_path("mostaql", "seen")
            tmp_path = seen_file + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(list(seen_ids), f)
            os.replace(tmp_path, seen_file)
        except Exception as e:
            logger.error(f"Failed to seed Mostaql seen projects: {e}")

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
                seen_file = _get_file_path("khamsat", "seen")
                tmp_path = seen_file + ".tmp"
                with open(tmp_path, "w") as f:
                    json.dump(max_seen_id, f)
                os.replace(tmp_path, seen_file)
            except Exception as e:
                logger.error(f"Failed to seed Khamsat max seen ID: {e}")

def send_startup_snapshot(bot_type, projects):
    admins = _get_all_admins(bot_type)
    if not admins:
        return
    
    site_name = "مستقل" if bot_type == "mostaql" else "خمسات"
    lines = [f"📸 لقطة تشغيلية لأحدث طلبات {site_name} المتوفرة حالياً:\n"]
    for i, p in enumerate(projects[:5], 1):
        lines.append(f"{i}. {p['title']}\n🔗 {p['link']}\n")
    
    msg_text = "\n".join(lines)
    for cid in admins:
        _send_one(bot_type, cid, msg_text)

# ==============================================================================
# TELEGRAM BOT CONTROLLERS (ADMIN INTERFACES)
# ==============================================================================
def _send_admin_menu(bot_type, chat_id):
    token = MOSTAQL_BOT_TOKEN if bot_type == "mostaql" else KHAMSAT_BOT_TOKEN
    base_url = f"https://api.telegram.org/bot{token}"
    
    site_label = "مستقل" if bot_type == "mostaql" else "خمسات"
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "⏳ الطلبات المعلقة", "callback_data": "cmd:view_pending"},
                {"text": "📊 حالة البوت", "callback_data": "cmd:view_stats"}
            ],
            [
                {"text": "🗑️ مسح آخر بث", "callback_data": "cmd:delete_broadcast"}
            ]
        ]
    }
    requests.post(f"{base_url}/sendMessage", json={
        "chat_id": chat_id,
        "text": f"👑 لوحة تحكم أدمن بوت {site_label}:",
        "reply_markup": keyboard
    })

def handle_callback_query(bot_type, callback):
    token = MOSTAQL_BOT_TOKEN if bot_type == "mostaql" else KHAMSAT_BOT_TOKEN
    base_url = f"https://api.telegram.org/bot{token}"
    
    cb_id = callback["id"]
    from_user = callback["from"]
    chat_id = from_user["id"]
    data = callback.get("data", "")
    
    role = 1
    if is_owner(bot_type, chat_id): role = 3
    elif is_admin(bot_type, chat_id): role = 2
    
    if data.startswith("cmd:"):
        cmd = data.split("cmd:", 1)[1]
        
        if role < 2:
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "هنهذر ولا اي", "show_alert": True})
            return
            
        if cmd == "delete_broadcast":
            broadcast_msgs = _load_broadcast_msgs(bot_type)
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
            _save_broadcast_msgs(bot_type, {})
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": f"✅ تم حذف البث لـ {deleted} مستخدم.", "show_alert": True})
            
        elif cmd == "view_pending":
            pending = _load_pending(bot_type)
            if not pending:
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": "✅ لا توجد طلبات معلقة حالياً.", "show_alert": True})
            else:
                lines = ["⏳ طلبات الاشتراك المعلقة:\n"]
                for pid in sorted(pending):
                    lines.append(f"🆔 {pid}  →  /approve {pid}")
                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines)})
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})
                
        elif cmd == "view_stats":
            subs = _load_subscribers(bot_type)
            pending = _load_pending(bot_type)
            blocked = _load_blocked(bot_type)
            stats = _get_stats(bot_type)
            uptime_sec = int(time.time() - bot_start_time)
            h, m = divmod(uptime_sec // 60, 60)
            muted_count = len(_load_muted_users(bot_type))
            
            if bot_type == "mostaql":
                id_label = f"عدد IDs المسجلة: {len(seen_ids)}"
            else:
                id_label = f"أعلى ID طلب شوفناه: {max_seen_id}"
                
            status_msg = (
                f"📊 حالة بوت { 'مستقل' if bot_type == 'mostaql' else 'خمسات' }:\n"
                f"⏱️ وقت التشغيل: {h}ساعة {m}دقيقة\n"
                f"👥 المشتركين: {len(subs)} / {MAX_SUBSCRIBERS}\n"
                f"🔕 كتموا إشعاراتهم: {muted_count}\n"
                f"⏳ طلبات معلقة: {len(pending)}\n"
                f"🚫 محظورين: {len(blocked)}\n"
                f"👑 أدمنز: {len(_get_all_admins(bot_type))}\n"
                f"🔢 {id_label}\n"
                f"📨 إجمالي رسائل مرسلة: {stats.get('total_sent', 0)}"
            )
            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": status_msg})
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": cb_id})

# ==============================================================================
# PARAMETERIZED UPDATE HANDLER & COMMAND ROUTER
# ==============================================================================
def handle_updates_loop(bot_type, poll_interval=2):
    token = MOSTAQL_BOT_TOKEN if bot_type == "mostaql" else KHAMSAT_BOT_TOKEN
    if not token:
        logger.warning(f"Polling disabled for {bot_type} (token is missing)")
        return

    base_url = f"https://api.telegram.org/bot{token}"
    offset = 0
    _load_roles(bot_type)

    logger.info(f"Started polling updates for {bot_type}...")
    while True:
        try:
            r = requests.get(f"{base_url}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=25).json()
            if not r.get("ok"):
                time.sleep(poll_interval)
                continue

            for update in r.get("result", []):
                offset = update["update_id"] + 1
                
                if "callback_query" in update:
                    handle_callback_query(bot_type, update["callback_query"])
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
                if is_owner(bot_type, chat_id):
                    role = 3
                elif is_admin(bot_type, chat_id):
                    role = 2

                cmd_roles = {
                    "/add_admin":    3,
                    "/remove_admin": 3,
                    "/backup":       3,

                    "/restore":   2,
                    "/menu":      2,
                    "/ids":       2,
                    "/broadcast": 2,
                    "/send_last": 2,
                    "/block":     2,
                    "/unblock":   2,
                    "/approve":   2,
                    "/reject":    2,
                    "/pending":   2,
                    "/status":    2,

                    "/start":       1,
                    "/subscribe":   1,
                    "/unsubscribe": 1,
                    "/mymute":      1,
                    "/pause":       1,
                    "/myunmute":    1,
                    "/resume":      1,
                    "/ping":        1,
                    "/help":        1,
                }

                if cmd in cmd_roles:
                    if role < cmd_roles[cmd]:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "هنهذر ولا اي"})
                        continue
                else:
                    continue

                if role == 1 and _is_rate_limited(bot_type, chat_id):
                    continue

                if cmd in ("/start", "/subscribe"):
                    with subscribers_lock:
                        blocked = _load_blocked(bot_type)
                    if chat_id in blocked:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🚫 تم حظرك من استخدام هذا البوت."})
                        continue

                    if add_subscriber(bot_type, chat_id):
                        welcome_msg = "لا تنسي الدعاء لنا و لامواتنا و اموات المسلمين\nوصلي علي النبي يا جدع"
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": welcome_msg})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ عذراً، لا يمكن الاشتراك الآن (ربما وصل البوت للحد الأقصى)."})

                    if role >= 2:
                        _send_admin_menu(bot_type, chat_id)

                elif cmd == "/menu":
                    _send_admin_menu(bot_type, chat_id)

                elif cmd == "/approve":
                    parts = text.split()
                    if len(parts) >= 2:
                        target_id = parts[1].strip()
                        try:
                            target_id = int(target_id)
                            if add_subscriber(bot_type, target_id):
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم قبول المستخدم {target_id}"})
                                site_label = "مستقل" if bot_type == "mostaql" else "خمسات"
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": (
                                    f"🎉 مرحباً! تم قبول اشتراكك في بوت {site_label}.\n\n"
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
                            reject_subscriber(bot_type, target_id)
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"❌ تم رفض المستخدم {target_id}"})
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": target_id, "text": "❌ عذراً، تم رفض طلب اشتراكك."})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /reject <id>"})

                elif cmd == "/ids":
                    with subscribers_lock:
                        subs = _load_subscribers(bot_type)
                    if subs:
                        lines = ["👥 المشتركين المعتمدين:\n"]
                        for i, sid in enumerate(sorted(subs), 1):
                            marker = "👑" if sid in _get_all_admins(bot_type) else "👤"
                            lines.append(f"{i}. {marker} {sid}  →  /block {sid}")
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines)})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "📭 لا يوجد مشتركين حالياً."})

                elif cmd == "/add_admin":
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target_id = int(parts[1].strip())
                            if target_id == get_owner_id(bot_type):
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "أنت المالك بالفعل!"})
                            else:
                                with subscribers_lock:
                                    admins = _load_admins(bot_type)
                                    admins.add(target_id)
                                    _save_admins(bot_type, admins)
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
                                admins = _load_admins(bot_type)
                                admins.discard(target_id)
                                _save_admins(bot_type, admins)
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
                            if target_id == get_owner_id(bot_type):
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لا يمكنك حظر نفسك!"})
                            else:
                                with subscribers_lock:
                                    blocked = _load_blocked(bot_type)
                                    blocked.add(target_id)
                                    _save_blocked(bot_type, blocked)
                                    subs = _load_subscribers(bot_type)
                                    subs.discard(target_id)
                                    _save_subscribers(bot_type, subs)
                                    pending = _load_pending(bot_type)
                                    pending.discard(target_id)
                                    _save_pending(bot_type, pending)
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
                                blocked = _load_blocked(bot_type)
                                blocked.discard(target_id)
                                _save_blocked(bot_type, blocked)
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إلغاء حظر المستخدم {target_id}"})
                        except ValueError:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ ID غير صالح"})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /unblock <id>"})

                elif cmd == "/broadcast":
                    broadcast_msg = text[len("/broadcast"):].strip()
                    if broadcast_msg:
                        with subscribers_lock:
                            subs = _load_subscribers(bot_type)
                        all_targets = subs | _get_all_admins(bot_type)
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
                            _save_broadcast_msgs(bot_type, msg_map)
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
                        
                        if bot_type == "mostaql":
                            projects, _, _ = fetch_mostaql_projects()
                            site_label = "مستقل"
                        else:
                            projects, _, _ = fetch_khamsat_projects()
                            site_label = "خمسات"
                            
                        if not projects:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ لم يتم العثور على طلبات حالياً."})
                        else:
                            to_send = projects[:count]
                            msg_lines = [f"🚀 إليك آخر {len(to_send)} طلبات تم طرحها على {site_label}:\n"]
                            for p in to_send:
                                msg_lines.append(f"📝 {p['title']}\n🔗 {p['link']}\n")
                            
                            broadcast_msg = "\n".join(msg_lines)
                            
                            with subscribers_lock:
                                subs = _load_subscribers(bot_type)
                            all_targets = subs | _get_all_admins(bot_type)
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
                                _save_broadcast_msgs(bot_type, msg_map)
                                kb = {"inline_keyboard": [[{"text": "🗑️ مسح للجميع", "callback_data": "cmd:delete_broadcast"}]]}
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"✅ تم إرسال الطلبات لـ {sent}/{len(all_targets)} مستخدم.", "reply_markup": kb})
                            else:
                                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ لم يتم إرسال الرسالة لأي شخص."})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "استخدم: /send_last <رقم>\nمثال: /send_last 5"})

                elif cmd == "/unsubscribe":
                    remove_subscriber(bot_type, chat_id)
                    mu = _load_muted_users(bot_type)
                    mu.discard(chat_id)
                    _save_muted_users(bot_type, mu)
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "❌ تم إلغاء اشتراكك."})

                elif cmd in ("/mymute", "/pause"):
                    with subscribers_lock:
                        subs = _load_subscribers(bot_type)
                    if chat_id in subs or is_admin(bot_type, chat_id):
                        mu = _load_muted_users(bot_type)
                        mu.add(chat_id)
                        _save_muted_users(bot_type, mu)
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "🔕 تم كتم الإشعارات لحسابك مؤقتاً.\nأرسل /myunmute لإعادة تفعيلها."})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ أنت لست مشتركاً."})

                elif cmd in ("/myunmute", "/resume"):
                    mu = _load_muted_users(bot_type)
                    mu.discard(chat_id)
                    _save_muted_users(bot_type, mu)
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
                            data={"chat_id": chat_id, "caption": "💾 نسخة احتياطية كاملة وشاملة (مستقل + خمسات) — استخدم /restore بالرد على هذا الملف لاستعادة كافة البيانات دفعة واحدة."},
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
                            r_dl = requests.get(f"https://api.telegram.org/file/bot{token}/{tg_path}", timeout=20)
                            backup_data = json.loads(r_dl.content.decode("utf-8"))
                            
                            # Smart restore: check if it's a unified backup or old format
                            if "mostaql" in backup_data or "khamsat" in backup_data:
                                restore_system_backup(backup_data)
                            else:
                                restore_full_backup(bot_type, backup_data)
                                
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "✅ تم استعادة جميع البيانات بنجاح! 🎉"})
                            logger.info(f"Full restore triggered by {chat_id} on {bot_type}")
                        except Exception as _re:
                            requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": f"❌ فشل الاستعادة: {_re}"})

                elif cmd == "/pending":
                    with subscribers_lock:
                        pending = _load_pending(bot_type)
                    if pending:
                        lines = ["⏳ طلبات الاشتراك المعلقة:\n"]
                        for pid in sorted(pending):
                            lines.append(f"🆔 {pid}  →  /approve {pid}")
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(lines)})
                    else:
                        requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "✅ لا توجد طلبات معلقة."})

                elif cmd == "/help":
                    site_label = "مستقل" if bot_type == "mostaql" else "خمسات"
                    if role >= 3:
                        help_text = (
                            f"🤖 أوامر البوت — نظام الرولز ({site_label}):\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "👑 المالك (Owner) فقط:\n"
                            "  /menu — لوحة التحكم\n"
                            "  /ids — عرض المشتركين\n"
                            "  /add_admin <id> — إضافة أدمن\n"
                            "  /remove_admin <id> — إزالة أدمن\n"
                            "  /block <id> — حظر مستخدم\n"
                            "  /unblock <id> — إلغاء حظر\n"
                            "  /broadcast <رسالة> — بث رسالة للكل\n"
                            "  /send_last <رقم> — إرسال آخر الطلبات\n"
                            "  /backup — إنشاء نسخة احتياطية\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "⚙️ الأدمن (Admin) + المالك:\n"
                            "  /approve <id> — قبول مشترك\n"
                            "  /reject <id> — رفض مشترك\n"
                            "  /pending — الطلبات المعلقة\n"
                            "  /status — حالة البوت\n"
                            "  /restore — استعادة باك أب (رد على الملف)\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "👤 المشترك العادي:\n"
                            "  /start — طلب اشتراك\n"
                            "  /mymute — كتم إشعاراتك\n"
                            "  /myunmute — تفعيل إشعاراتك\n"
                            "  /unsubscribe — إلغاء الاشتراك\n"
                            "  /ping — فحص البوت"
                        )
                    elif role >= 2:
                        help_text = (
                            f"🤖 أوامر البوت — نظام الرولز ({site_label}):\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "⚙️ الأدمن (Admin):\n"
                            "  /approve <id> — قبول مشترك\n"
                            "  /reject <id> — رفض مشترك\n"
                            "  /pending — الطلبات المعلقة\n"
                            "  /status — حالة البوت\n"
                            "  /restore — استعادة باك أب (رد على الملف)\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "👤 المشترك العادي:\n"
                            "  /mymute — كتم إشعاراتك\n"
                            "  /myunmute — تفعيل إشعاراتك\n"
                            "  /unsubscribe — إلغاء الاشتراك\n"
                            "  /ping — فحص البوت"
                        )
                    else:
                        help_text = (
                            f"🤖 أوامر البوت ({site_label}):\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "👤 أوامر عامة:\n"
                            "  /start — طلب اشتراك\n"
                            "  /mymute — كتم إشعاراتك\n"
                            "  /myunmute — تفعيل إشعاراتك\n"
                            "  /unsubscribe — إلغاء الاشتراك\n"
                            "  /ping — فحص البوت"
                        )
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": help_text})

                elif cmd == "/status":
                    with subscribers_lock:
                        subs = _load_subscribers(bot_type)
                        pending = _load_pending(bot_type)
                        blocked = _load_blocked(bot_type)
                    stats = _get_stats(bot_type)
                    uptime_sec = int(time.time() - bot_start_time)
                    h, m = divmod(uptime_sec // 60, 60)
                    muted_count = len(_load_muted_users(bot_type))
                    
                    if bot_type == "mostaql":
                        id_label = f"عدد IDs المسجلة: {len(seen_ids)}"
                    else:
                        id_label = f"أعلى ID طلب شوفناه: {max_seen_id}"
                        
                    status_msg = (
                        f"📊 حالة بوت { 'مستقل' if bot_type == 'mostaql' else 'خمسات' }:\n"
                        f"⏱️ وقت التشغيل: {h}ساعة {m}دقيقة\n"
                        f"👥 المشتركين: {len(subs)} / {MAX_SUBSCRIBERS}\n"
                        f"🔕 كتموا إشعاراتهم: {muted_count}\n"
                        f"⏳ طلبات معلقة: {len(pending)}\n"
                        f"🚫 محظورين: {len(blocked)}\n"
                        f"👑 أدمنز: {len(_get_all_admins(bot_type))}\n"
                        f"🔢 {id_label}\n"
                        f"📨 إجمالي رسائل مرسلة: {stats.get('total_sent', 0)}"
                    )
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": status_msg})

                elif cmd == "/ping":
                    requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "pong ✅"})
                    
        except Exception as e:
            logger.debug(f"Updates loop error for {bot_type}: {str(e)}")
            time.sleep(poll_interval)

# ==============================================================================
# PERIODIC TASKS LOOP (STATS & 3-MINUTE AUTO TELEGRAM BACKUPS)
# ==============================================================================
def _periodic_tasks_loop(bot_type):
    """Send weekly statistics and daily backups to owner."""
    time.sleep(10)
    last_stats_sent = time.time()
    last_backup_sent = time.time()
    
    site_label = "مستقل" if bot_type == "mostaql" else "خمسات"
    while True:
        time.sleep(30)  # Check every 30 seconds for hyper-responsiveness
        now = time.time()
        
        # 3-minute automatic backups (180 seconds)
        if now - last_backup_sent >= 180:
            should_send = False
            if bot_type == "mostaql":
                should_send = True
            elif bot_type == "khamsat" and not MOSTAQL_BOT_TOKEN:
                should_send = True
                
            if should_send:
                try:
                    backup_data = generate_system_backup()
                    backup_bytes = json.dumps(backup_data, ensure_ascii=False, indent=2).encode("utf-8")
                    import io
                    bio = io.BytesIO(backup_bytes)
                    bio.name = "system_backup_data.json"
                    
                    token = MOSTAQL_BOT_TOKEN if bot_type == "mostaql" else KHAMSAT_BOT_TOKEN
                    if token:
                        requests.post(
                            f"https://api.telegram.org/bot{token}/sendDocument",
                            data={"chat_id": get_owner_id(bot_type), "caption": "📦 نسخة احتياطية تلقائية شاملة (مستقل + خمسات).\nلو الداتا طارت، اعمل Reply على الملف واكتب /restore"},
                            files={"document": ("system_backup_data.json", bio, "application/json")},
                            timeout=20
                        )
                    last_backup_sent = now
                    logger.info(f"Unified 3-minute backup sent to owner via {bot_type} thread")
                except Exception as e:
                    logger.error(f"Unified 3-minute backup error: {e}")

        # Weekly statistics
        if now - last_stats_sent >= 7 * 24 * 3600:
            try:
                subs = _load_subscribers(bot_type)
                pending = _load_pending(bot_type)
                blocked = _load_blocked(bot_type)
                stats = _get_stats(bot_type)
                uptime_sec = int(time.time() - bot_start_time)
                h, m = divmod(uptime_sec // 60, 60)
                muted_count = len(_load_muted_users(bot_type))
                
                stats_msg = (
                    f"📊 إحصائيات الأسبوع لبوت {site_label}:\n"
                    f"⏱️ وقت التشغيل: {h}ساعة {m}دقيقة\n"
                    f"👥 المشتركين: {len(subs)} / {MAX_SUBSCRIBERS}\n"
                    f"🔕 كتموا إشعاراتهم: {muted_count}\n"
                    f"⏳ طلبات معلقة: {len(pending)}\n"
                    f"🚫 محظورين: {len(blocked)}\n"
                    f"👑 أدمنز: {len(_get_all_admins(bot_type))}\n"
                    f"📨 إجمالي رسائل مرسلة: {stats.get('total_sent', 0)}"
                )
                token = MOSTAQL_BOT_TOKEN if bot_type == "mostaql" else KHAMSAT_BOT_TOKEN
                if token:
                    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": get_owner_id(bot_type), "text": stats_msg}, timeout=10)
                last_stats_sent = now
                logger.info(f"Weekly stats sent to owner for {bot_type}")
            except Exception as e:
                logger.error(f"Weekly stats error for {bot_type}: {e}")

# ==============================================================================
# MAIN SYSTEM INITIALIZER
# ==============================================================================
def load_seen_data():
    global seen_ids, max_seen_id
    
    mostaql_seen_file = _get_file_path("mostaql", "seen")
    if os.path.exists(mostaql_seen_file):
        try:
            with open(mostaql_seen_file, "r") as f:
                seen_ids = set(json.load(f))
            logger.info(f"Loaded {len(seen_ids)} previously seen Mostaql projects")
        except Exception as e:
            logger.error(f"Failed to load Mostaql seen file: {e}")
            seen_ids = set()
    else:
        seen_ids = set()
        
    khamsat_seen_file = _get_file_path("khamsat", "seen")
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
    
    # Download Telegraph backups dynamically
    if MOSTAQL_BOT_TOKEN:
        download_telegraph_db("mostaql")
    if KHAMSAT_BOT_TOKEN:
        download_telegraph_db("khamsat")
        
    load_seen_data()
    load_proxies()
    
    logger.info("=" * 50)
    logger.info("Unified Mostaql & Khamsat Scraper Bot System Started")
    logger.info("=" * 50)

    # 1. Start threads for Mostaql Bot
    if MOSTAQL_BOT_TOKEN:
        threading.Thread(target=handle_updates_loop, args=("mostaql", 2), daemon=True).start()
        threading.Thread(target=_periodic_tasks_loop, args=("mostaql",), daemon=True).start()
        threading.Thread(target=telegraph_sync_thread, args=("mostaql",), daemon=True).start()
        
        startup_projects, startup_proxy_type, startup_proxy_addr = fetch_mostaql_projects()
        if startup_projects:
            if not seen_ids:
                seed_seen_projects(startup_projects)
            send_startup_snapshot("mostaql", startup_projects)
            logger.info(f"Mostaql startup snapshot sent via {startup_proxy_type} proxy ({startup_proxy_addr})")
        else:
            logger.warning("No Mostaql startup projects were found")
            
    # 2. Start threads for Khamsat Bot
    if KHAMSAT_BOT_TOKEN:
        threading.Thread(target=handle_updates_loop, args=("khamsat", 2), daemon=True).start()
        threading.Thread(target=_periodic_tasks_loop, args=("khamsat",), daemon=True).start()
        threading.Thread(target=telegraph_sync_thread, args=("khamsat",), daemon=True).start()
        
        startup_reqs, startup_proxy_type, startup_proxy_addr = fetch_khamsat_projects()
        if startup_reqs:
            if max_seen_id == 0:
                seed_max_id(startup_reqs)
            send_startup_snapshot("khamsat", startup_reqs)
            logger.info(f"Khamsat startup snapshot sent via {startup_proxy_type} proxy ({startup_proxy_addr})")
        else:
            logger.warning("No Khamsat startup requests were found")

    # 3. Concurrent Scraping Loops
    def mostaql_scraping_loop():
        if not MOSTAQL_BOT_TOKEN:
            return
        logger.info("Started Mostaql scraping loop...")
        while True:
            try:
                check_mostaql()
            except Exception as e:
                logger.error(f"Mostaql scraping loop error: {e}")
            
            wait = CHECK_INTERVAL_MOSTAQL + random.randint(5, 15)
            logger.info(f"Mostaql waiting {wait}s before next scan")
            time.sleep(wait)

    def khamsat_scraping_loop():
        if not KHAMSAT_BOT_TOKEN:
            return
        logger.info("Started Khamsat scraping loop...")
        while True:
            try:
                check_khamsat()
            except Exception as e:
                logger.error(f"Khamsat scraping loop error: {e}")
            
            wait = random.uniform(5.0, 15.0)
            logger.info(f"Khamsat waiting {wait:.1f}s before next scan")
            time.sleep(wait)

    if MOSTAQL_BOT_TOKEN:
        threading.Thread(target=mostaql_scraping_loop, daemon=True).start()
    if KHAMSAT_BOT_TOKEN:
        threading.Thread(target=khamsat_scraping_loop, daemon=True).start()
        
    # Send startup notifications
    if MOSTAQL_BOT_TOKEN:
        _notify_admins("mostaql", "🚀 بدأت مراقبة مشاريع 'مستقل' الآن..")
        owner_startup_msg = (
            "🚀 تم تشغيل بوت مستقل بنجاح!\n\n"
            "لو حسيت إن الداتا طارت بسبب ريستارت السيرفر، مفيش مشكلة.\n"
            "اعمل Reply على آخر ملف نسخ احتياطي أرسلتهولك، واكتب أمر:\n"
            "/restore\n\n"
            "والداتا كلها هترجع في ثانية واحدة."
        )
        try:
            requests.post(f"https://api.telegram.org/bot{MOSTAQL_BOT_TOKEN}/sendMessage", json={"chat_id": get_owner_id("mostaql"), "text": owner_startup_msg}, timeout=10)
        except Exception:
            pass

    if KHAMSAT_BOT_TOKEN:
        _notify_admins("khamsat", "🚀 بدأت مراقبة طلبات 'خمسات' الآن..")
        owner_startup_msg = (
            "🚀 تم تشغيل بوت خمسات بنجاح!\n\n"
            "لو حسيت إن الداتا طارت بسبب ريستارت السيرفر، مفيش مشكلة.\n"
            "اعمل Reply على آخر ملف نسخ احتياطي أرسلتهولك، واكتب أمر:\n"
            "/restore\n\n"
            "والداتا كلها هترجع في ثانية واحدة."
        )
        try:
            requests.post(f"https://api.telegram.org/bot{KHAMSAT_BOT_TOKEN}/sendMessage", json={"chat_id": get_owner_id("khamsat"), "text": owner_startup_msg}, timeout=10)
        except Exception:
            pass

    # Keep the main process alive
    logger.info("All loops and threads started successfully. Keeping main thread alive.")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Unified bot stopped by user.")
            break
