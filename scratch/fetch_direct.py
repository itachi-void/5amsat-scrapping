import sys
import os
import importlib.util

# Resolve paths relative to this script's directory
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(base_dir, ".."))
sys.path.append(parent_dir)

import time
import random
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load env variables from parent (resolved path)
load_dotenv(dotenv_path=os.path.join(parent_dir, ".env"))

# Dynamically import 5.py from parent directory
spec = importlib.util.spec_from_file_location("bot_module", os.path.join(parent_dir, "5.py"))
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)

bot.load_all_configs()
bot.load_proxies()

# Request URL to fetch
url = "https://khamsat.com/community/requests/788933-%D9%85%D8%B7%D9%84%D9%88%D8%A8-%D8%AA%D8%B5%D9%85%D9%8A%D9%85-presentation-%D8%A7%D8%AD%D8%AA%D8%B1%D8%A7%D9%81%D9%8A-%D9%84%D8%AA%D8%B7%D8%A8%D9%8A%D9%82-flutter"

print("Fetching page using bot's scraper and proxy configuration...")
headers = {"User-Agent": random.choice(bot.USER_AGENTS)}

# Try direct first
print("Trying Direct Access...")
try:
    scraper = bot._new_scraper()
    resp = scraper.get(url, headers=headers, timeout=10)
    print(f"Direct Status Code: {resp.status_code}")
    if resp.status_code == 200:
        with open("item.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("SUCCESS! Saved page.")
        sys.exit(0)
except Exception as e:
    print(f"Direct error: {e}")

# Try proxies
all_proxies = list(bot.premium_proxies) + list(bot.free_proxies)
random.shuffle(all_proxies)
print(f"Loaded {len(all_proxies)} total proxies from bot.")

for idx, (scheme, addr) in enumerate(all_proxies[:30]):
    if bot.PROXY_USER and bot.PROXY_PASS and (scheme, addr) in bot.premium_proxies:
        pu = f"{scheme}://{bot.PROXY_USER}:{bot.PROXY_PASS}@{addr}"
        pk = "premium"
    else:
        pu = f"{scheme}://{addr}"
        pk = "free"
    
    proxies = {"http": pu, "https": pu}
    print(f"Trying {pk} proxy {idx+1}: {addr}...")
    try:
        scraper = bot._new_scraper()
        resp = scraper.get(url, headers=headers, proxies=proxies, timeout=10)
        print(f"  Status Code: {resp.status_code}")
        if resp.status_code == 200:
            with open("item.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print("  SUCCESS! Saved page.")
            
            # Print parsed DOM elements
            soup = BeautifulSoup(resp.text, "html.parser")
            print("Parsed page. Searching for content divs...")
            # Common content container selectors
            content_divs = soup.select(".post_content, .post-content, .article-content, .post_body, .post__body, .forum_post, .post_message, .message")
            for i, d in enumerate(content_divs[:5]):
                print(f"  Div {i+1}: class={d.get('class')}, preview={d.get_text(strip=True)[:300]}")
            
            # Let's check td elements which usually hold post bodies in traditional Hsoub forums
            tds = soup.find_all("td", class_="details-td")
            print(f"  Found details-tds: {len(tds)}")
            for i, td in enumerate(tds):
                print(f"    TD {i+1}: {td.get_text(strip=True)[:300]}")
                
            # Or let's inspect the entire elements with larger text content
            for tag in soup.find_all(["div", "article", "section", "p"]):
                cl = tag.get("class")
                if cl and any(any(kwd in str(c).lower() for kwd in ["body", "content", "message", "desc", "text"]) for c in cl):
                    txt = tag.get_text(strip=True)
                    if len(txt) > 50:
                        print(f"    Possible container: tag={tag.name}, class={cl}, text preview={txt[:300]}")
                        
            sys.exit(0)
    except Exception as e:
        print(f"  Proxy error: {e}")
