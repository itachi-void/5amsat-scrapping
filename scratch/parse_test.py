import cloudscraper
from bs4 import BeautifulSoup
import os

url = "https://khamsat.com/community/requests"

proxy_user = "uzib0z5w4fzr"
proxy_pass = "f22ime6g7zlasj1"
proxies_list = []
if os.path.exists("../proxyscrape_premium_http_proxies.txt"):
    with open("../proxyscrape_premium_http_proxies.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                proxies_list.append(line)
elif os.path.exists("proxyscrape_premium_http_proxies.txt"):
    with open("proxyscrape_premium_http_proxies.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                proxies_list.append(line)

print(f"Loaded {len(proxies_list)} proxies.")

success = False
for idx, p_addr in enumerate(proxies_list[:15]):
    p_url = f"http://{proxy_user}:{proxy_pass}@{p_addr}"
    proxy = {"http": p_url, "https": p_url}
    print(f"Trying proxy {idx+1}/{len(proxies_list)}: {p_addr} ...")
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        resp = scraper.get(url, proxies=proxy, timeout=8)
        print(f"  Status Code: {resp.status_code}")
        if resp.status_code == 200:
            with open("page.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print("  SUCCESS! Page saved to page.html.")
            success = True
            
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("a[href*='/community/requests/']")
            print(f"  Found {len(links)} links matching the selector")
            
            # Let's inspect the DOM elements that represent a request card/item.
            # In Khamsat, usually there is a table or a list. Let's find table rows or list items or cards.
            # Let's print out what elements surround the request links.
            for i, link in enumerate(links[:3]):
                print(f"\n  --- Link {i+1} ---")
                print(f"  Href: {link.get('href')}")
                print(f"  Text (Title): {link.get_text(strip=True)}")
                
                # Check parents and search for description
                # Let's print first 3 levels of parent tag names and text
                curr = link.parent
                print(f"  Parent 1: tag={curr.name}, classes={curr.get('class')}")
                # In Khamsat community requests page, a post usually contains the title (link) and the post body/text/description.
                # Let's print the parent's sibling texts or children's texts
                for sibling in curr.next_siblings:
                    if sibling.name:
                        print(f"    Sibling tag={sibling.name}, classes={sibling.get('class')}, text={sibling.get_text(strip=True)[:150]}")
                
                # Let's inspect parent 2
                if curr.parent:
                    curr2 = curr.parent
                    print(f"  Parent 2: tag={curr2.name}, classes={curr2.get('class')}")
                    for sibling in curr2.next_siblings:
                        if sibling.name:
                            print(f"    Sibling 2 tag={sibling.name}, classes={sibling.get('class')}, text={sibling.get_text(strip=True)[:150]}")
                            
                # Let's inspect parent 3
                if curr.parent and curr.parent.parent:
                    curr3 = curr.parent.parent
                    print(f"  Parent 3: tag={curr3.name}, classes={curr3.get('class')}")
                    for sibling in curr3.next_siblings:
                        if sibling.name:
                            print(f"    Sibling 3 tag={sibling.name}, classes={sibling.get('class')}, text={sibling.get_text(strip=True)[:150]}")
            break
    except Exception as e:
        print(f"  Error: {e}")

if not success:
    print("Could not fetch page using any of the tested proxies.")
