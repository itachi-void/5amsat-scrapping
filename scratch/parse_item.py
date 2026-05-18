import cloudscraper
from bs4 import BeautifulSoup
import os

url = "https://khamsat.com/community/requests/788933-%D9%85%D8%B7%D9%84%D9%88%D8%A8-%D8%AA%D8%B5%D9%85%D9%8A%D9%85-presentation-%D8%A7%D8%AD%D8%AA%D8%B1%D8%A7%D9%81%D9%8A-%D9%84%D8%AA%D8%B7%D8%A8%D9%8A%D9%82-flutter"

proxy_user = "uzib0z5w4fzr"
proxy_pass = "f22ime6g7zlasj1"
proxies_list = []
if os.path.exists("../proxyscrape_premium_http_proxies.txt"):
    with open("../proxyscrape_premium_http_proxies.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                proxies_list.append(line)

print("Fetching item page...")
success = False
for idx, p_addr in enumerate(proxies_list[:10]):
    p_url = f"http://{proxy_user}:{proxy_pass}@{p_addr}"
    proxy = {"http": p_url, "https": p_url}
    print(f"Trying proxy {idx+1}: {p_addr}...")
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        resp = scraper.get(url, proxies=proxy, timeout=10)
        print(f"  Status Code: {resp.status_code}")
        if resp.status_code == 200:
            with open("item.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print("  SUCCESS! Item page saved.")
            success = True
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Let's search for divs or tags that contain the main post body.
            # In Khamsat/Hsoub community, the post body is usually inside a div with class "post__content" or "article__content" or inside a class containing "post".
            # Let's search for tags containing relevant classes or test selectors.
            content_divs = soup.select(".post_content, .post-content, .article-content, .post_body, .post__body, .forum_post, .post_message, .message")
            print(f"  Found {len(content_divs)} divs with common content classes")
            for i, d in enumerate(content_divs[:5]):
                print(f"  Div {i+1}: tag={d.name}, classes={d.get('class')}, text preview={d.get_text(strip=True)[:200]}")
                
            # If nothing, let's search broadly for tags inside a forum post table or article
            # Let's inspect the entire text length and look for specific paragraphs
            all_tds = soup.find_all("td")
            print(f"  Found {len(all_tds)} td elements")
            for i, td in enumerate(all_tds[:15]):
                txt = td.get_text(strip=True)
                if len(txt) > 20:
                    print(f"  TD {i+1}: class={td.get('class')}, text={txt[:150]}")
            
            break
    except Exception as e:
        print(f"  Error: {e}")

if not success:
    print("Failed to fetch.")
