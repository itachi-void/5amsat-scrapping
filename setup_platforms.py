import os
import shutil

source_dir = r"c:\Users\itachi\Downloads\5amsat-scrapping"
platforms = [
    {"name": "kafiil", "arabic": "كفيل", "url": "https://kafiil.com"},
    {"name": "nqfezly", "arabic": "نفذلي", "url": "https://nafezly.com"}
]

for p in platforms:
    target_dir = os.path.join(r"c:\Users\itachi\Downloads", f"{p['name']}-scrapping")
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy requirements.txt
    if os.path.exists(os.path.join(source_dir, "requirements.txt")):
        shutil.copy(os.path.join(source_dir, "requirements.txt"), os.path.join(target_dir, "requirements.txt"))
        
    # Create empty .env
    with open(os.path.join(target_dir, ".env"), "w", encoding="utf-8") as f:
        f.write(f"# {p['name'].capitalize()} Bot Configuration\nBOT_TOKEN=\nCHAT_ID=1622676655\nOPENAI_API_KEY=\nTWILIO_ACCOUNT_SID=\nTWILIO_AUTH_TOKEN=\nTWILIO_FROM_NUMBER=\nTWILIO_TO_NUMBER=\n")
    
    # Read 5.py, replace khamsat/خمسات, and save
    try:
        with open(os.path.join(source_dir, "5.py"), "r", encoding="utf-8") as f:
            content = f.read()
            
        content = content.replace("khamsat", p['name'])
        content = content.replace("Khamsat", p['name'].capitalize())
        content = content.replace("KHAMSAT", p['name'].upper())
        content = content.replace("خمسات", p['arabic'])
        
        with open(os.path.join(target_dir, f"{p['name']}_bot.py"), "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Created {target_dir} successfully.")
    except Exception as e:
        print(f"Error processing {p['name']}: {e}")
