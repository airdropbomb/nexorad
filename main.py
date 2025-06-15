print("""
       █████╗ ██████╗ ██████╗     ███╗   ██╗ ██████╗ ██████╗ ███████╗
      ██╔══██╗██╔══██╗██╔══██╗    ████╗  ██║██╔═══██╗██╔══██╗██╔════╝
      ███████║██║  ██║██████╔╝    ██╔██╗ ██║██║   ██║██║  ██║█████╗  
      ██╔══██║██║  ██║██╔══██╗    ██║╚██╗██║██║   ██║██║  ██║██╔══╝  
      ██║  ██║██████╔╝██████╔     ██║ ╚████║╚██████╔╝██████╔╝███████╗
      ╚═╝  ╚═╝╚═════╝ ╚═════╝     ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝  
""")

import requests
import httpx
import random
import string
import time
import json
import asyncio
from bs4 import BeautifulSoup
from colorama import init, Fore, Style

init(autoreset=True)

API_BASE = "https://api.mail.tm"

class WaitlistBot:
    def __init__(self):
        self.base_url = "https://nexorad-backend.onrender.com"
        self.headers = {
            "content-type": "application/json",
            "origin": "https://waitlist.nexorad.io",
            "referer": "https://waitlist.nexorad.io/",
            "user-agent": "Mozilla/5.0 (Linux; Android 13)"
        }

    async def create_temp_email(self, client):
        r = await client.get(f"{API_BASE}/domains")
        domain = random.choice(r.json()["hydra:member"])["domain"]
        local = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{local}@{domain}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        await client.post(f"{API_BASE}/accounts", json={"address": email, "password": password})
        return email, password

    async def get_token(self, client, email, password):
        r = await client.post(f"{API_BASE}/token", json={"address": email, "password": password})
        return r.json().get("token")

    async def get_code(self, client, token, timeout=120):
        headers = {"Authorization": f"Bearer {token}"}
        start = time.time()
        while time.time() - start < timeout:
            r = await client.get(f"{API_BASE}/messages", headers=headers)
            for msg in r.json().get("hydra:member", []):
                if "nexorad" in msg["from"]["address"]:
                    mid = msg["id"]
                    r2 = await client.get(f"{API_BASE}/messages/{mid}", headers=headers)
                    html = r2.json().get("html", "")
                    soup = BeautifulSoup(" ".join(html), "html.parser")
                    boxes = soup.find_all("span", class_="code-box")
                    if boxes and len(boxes) == 6:
                        return ''.join(b.get_text().strip() for b in boxes)
            await asyncio.sleep(5)
        return None

    def join_waitlist(self, email, code):
        url = f"{self.base_url}/waitlist/auth"
        payload = {"email": email, "inviterCode": code}
        r = requests.post(url, headers=self.headers, json=payload)
        return r.status_code == 200

    def verify(self, email, code):
        url = f"{self.base_url}/waitlist/auth/verify"
        r = requests.post(url, headers=self.headers, json={"email": email, "code": code})
        return r.json().get("data", {}).get("accessToken")

    def complete_task(self, token):
        url = f"{self.base_url}/waitlist/verify/task/x"
        h = self.headers.copy()
        h["authorization"] = f"Bearer {token}"
        requests.post(url, headers=h, json={})

    def check_points(self, token):
        url = f"{self.base_url}/waitlist/user/stats/points"
        h = self.headers.copy()
        h["authorization"] = f"Bearer {token}"
        r = requests.get(url, headers=h)
        return r.json().get("data", {})

async def main():
    bot = WaitlistBot()
    ref = input("Enter inviter code (e.g. XZ50SAWJ): ").strip()
    count = int(input("How many accounts?: ").strip())
    log_file = open("nexorad_output.txt", "a")

    async with httpx.AsyncClient() as client:
        for i in range(count):
            print(f"{Fore.CYAN}--- Account {i+1} ---")
            email, password = await bot.create_temp_email(client)
            print(f"[+] Created: {email}")
            if not bot.join_waitlist(email, ref):
                print(f"{Fore.RED}[-] Join failed.")
                continue
            token = await bot.get_token(client, email, password)
            code = await bot.get_code(client, token)
            if not code:
                print(f"{Fore.RED}[-] Code not found.")
                continue
            print(f"[✓] Code: {code}")
            access = bot.verify(email, code)
            if not access:
                print(f"{Fore.RED}[-] Verify failed.")
                continue
            bot.complete_task(access)
            points = bot.check_points(access)
            print(f"{Fore.GREEN}[✓] Points: {points.get('totalPoints')} | Tasks: {points.get('taskPoints')} | Progress: {points.get('progressPercentage')}%")
            log_file.write(f"{email} | {password} | {code} | {points.get('totalPoints')} pts\n{'-'*40}\n")
            time.sleep(3)

    log_file.close()

if __name__ == "__main__":
    asyncio.run(main())
