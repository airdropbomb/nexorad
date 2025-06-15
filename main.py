import os
import time
import requests, random, string, time, re
from fake_useragent import UserAgent
from dotenv import load_dotenv
from datetime import datetime
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

init(autoreset=True)

# ─── NEW BANNER ───────────────────────
def show_banner():
    banner = """
       █████╗ ██████╗ ██████╗     ███╗   ██╗ ██████╗ ██████╗ ███████╗
      ██╔══██╗██╔══██╗██╔══██╗    ████╗  ██║██╔═══██╗██╔══██╗██╔════╝
      ███████║██║  ██║██████╔╝    ██╔██╗ ██║██║   ██║██║  ██║█████╗  
      ██╔══██║██║  ██║██╔══██╗    ██║╚██╗██║██║   ██║██║  ██║██╔══╝  
      ██║  ██║██████╔╝██████╔     ██║ ╚████║╚██████╔╝██████╔╝███████╗
      ╚═╝  ╚═╝╚═════╝ ╚═════╝     ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝  
        By : ADB NODE
    """
    print(banner)

show_banner()

ua = UserAgent()
load_dotenv()

INVITER_CODE = os.getenv("INVITER_CODE")

def log_message(account_num=None, total=None, message="", message_type="info"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    account_status = f"{account_num}/{total}" if account_num and total else ""
    colors = {
        "info": Fore.LIGHTWHITE_EX,
        "success": Fore.LIGHTGREEN_EX,
        "error": Fore.LIGHTRED_EX,
        "warning": Fore.LIGHTYELLOW_EX,
        "process": Fore.LIGHTCYAN_EX,
        "debug": Fore.LIGHTMAGENTA_EX
    }
    log_color = colors.get(message_type, Fore.LIGHTWHITE_EX)
    print(f"{Fore.WHITE}[{Style.DIM}{timestamp}{Style.RESET_ALL}{Fore.WHITE}] "
          f"{Fore.WHITE}[{Fore.LIGHTYELLOW_EX}{account_status}{Fore.WHITE}] "
          f"{log_color}{message}")

def load_proxies():
    if not os.path.exists("proxy.txt"):
        return []
    with open("proxy.txt") as f:
        return [line.strip() for line in f if line.strip()]

class MailTMClient:
    def __init__(self, proxy=None):
        self.session = requests.Session()
        self.proxy_raw = proxy
        self.proxies = self.format_proxy(proxy) if proxy else None
        self.base = "https://api.mail.tm"
        self.account = {}
        self.token = ""
        self.max_mail_retries = 3
        self.retry_delay_base = 5

    def log(self, msg, level="info", account_num=None, total=None):
        log_message(account_num=account_num, total=total, message=msg, message_type=level)

    def format_proxy(self, p):
        if "://" in p:
            return {"http": p, "https": p}
        return {"http": f"http://{p}", "https": f"http://{p}"}

    def request(self, method, url, **kwargs):
        headers = kwargs.get("headers", {})
        headers["User-Agent"] = ua.random
        kwargs["headers"] = headers
        if self.proxies:
            kwargs["proxies"] = self.proxies
            kwargs["timeout"] = 60

        for attempt in range(self.max_mail_retries + 1):
            try:
                r = self.session.request(method, url, **kwargs)
                r.raise_for_status()
                time.sleep(1)
                return r
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    delay = self.retry_delay_base * (2 ** attempt) + random.uniform(0, 2)
                    self.log(f"Rate limited by Mail.TM (429). Retrying in {delay:.2f} seconds (Attempt {attempt+1}/{self.max_mail_retries+1})...",实
                    time.sleep(delay)
                else:
                    self.log(f"Request failed (HTTPError): {str(e)}", "error")
                    return None
            except Exception as e:
                self.log(f"Request failed: {str(e)}", "error")
                return None
        self.log(f"Request failed after {self.max_mail_retries+1} attempts due to persistent errors or rate limiting.", "error")
        return None

    def create_account(self):
        dom = self.request("GET", f"{self.base}/domains")
        if not dom:
            return None
        domain = dom.json()["hydra:member"][0]["domain"]
        name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"{name}@{domain}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        payload = {"address": email, "password": password}
        res = self.request("POST", f"{self.base}/accounts", json=payload)
        if not res:
            return None
        auth = self.request("POST", f"{self.base}/token", json=payload)
        if not auth:
            return None
        self.token = auth.json()["token"]
        self.account = {"email": email, "password": password}
        return self.account

    def get_otp(self, timeout=60, account_num=None, total=None):
        for i in range(timeout // 5):
            self.log(f"OTP Attempt {i+1}", "process", account_num, total)
            inbox = self.request("GET", f"{self.base}/messages", headers={"Authorization": f"Bearer {self.token}"})
            if inbox and inbox.json()["hydra:totalItems"] > 0:
                msg_id = inbox.json()["hydra:member"][0]["id"]
                msg = self.request("GET", f"{self.base}/messages/{msg_id}", headers={"Authorization": f"Bearer {self.token}"})
                if msg:
                    data = msg.json()
                    text = data.get("text", "")
                    html = data.get("html", [""])[0]
                    full = text + "\n" + html
                    match = re.search(r'(\d\s\d\s\d\s\d\s\d\s\d)', full)
                    if match:
                        digits = re.findall(r'\d', match.group(1))
                        code = ''.join(digits)
                        if len(code) == 6:
                            return code
                    match2 = re.search(r'\b(\d{6})\b', full)
                    if match2:
                        return match2.group(1)
            time.sleep(5)
        return None

class NexoradBot:
    def __init__(self, proxy=None, account_num=None, total_accounts=None):
        self.proxy_raw = proxy
        self.ua = ua
        self.proxies = self.format_proxy(proxy) if proxy else None
        self.session = requests.Session()
        self.email = None
        self.account_num = account_num
        self.total_accounts = total_accounts

    def log(self, msg, level="info"):
        log_message(account_num=self.account_num, total=self.total_accounts, message=msg, message_type=level)

    def format_proxy(self, p):
        if "://" in p:
            return {"http": p, "https": p}
        return {"http": f"http://{p}", "https": f"http://{p}"}

    def request(self, method, url, **kwargs):
        headers = kwargs.get("headers", {})
        headers["User-Agent"] = self.ua.random
        kwargs["headers"] = headers
        if self.proxies:
            kwargs["proxies"] = self.proxies
            kwargs["timeout"] = 60
        try:
            r = self.session.request(method, url, **kwargs)
            r.raise_for_status()
            return r
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "error")
            return None

    def send_otp(self, email):
        self.log("Sending OTP...", "process")
        url = "https://nexorad-backend.onrender.com/waitlist/auth"
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://waitlist.nexorad.io",
            "referer": "https://waitlist.nexorad.io/"
        }
        payload = {
            "email": email,
            "inviterCode": INVITER_CODE
        }
        res = self.request("POST", url, headers=headers, json=payload)
        return res and res.status_code == 200

    def clear_task(self, token):
        url = "https://nexorad-backend.onrender.com/waitlist/verify/task/x"
        headers = {
            "accept": "application/json, text/plain, */*",
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
            "origin": "https://waitlist.nexorad.io",
            "referer": "https://waitlist.nexorad.io/"
        }
        try:
            res = self.session.post(url, headers=headers, json={}, timeout=30)
            if res.status_code == 200:
                self.log("Task cleared successfully", "success")
            else:
                self.log(f"Failed to clear task - {res.status_code}", "error")
        except Exception as e:
            self.log(f"Exception in clear_task: {str(e)}", "error")

    def verify_otp(self, email, code):
        self.log(f"Verifying OTP {code}...", "process")
        url = "https://nexorad-backend.onrender.com/waitlist/auth/verify"
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://waitlist.nexorad.io",
            "referer": "https://waitlist.nexorad.io/"
        }
        payload = { "email": email, "code": code }
        res = self.request("POST", url, headers=headers, json=payload)

        if res:
            try:
                data = res.json()

                nested_data = data.get("data")
                token = None
                if nested_data and isinstance(nested_data, dict):
                    token = nested_data.get("accessToken")

                if token:
                    with open("token.txt", "a") as tf:
                        tf.write(token + "\n")
                    self.log("Access token saved to token.txt", "success")
                    self.clear_task(token)
                    self.log("Verification successful", "success")
                    return True
                else:
                    self.log("Access token not found in response or malformed.", "error")
                    return False

            except requests.exceptions.JSONDecodeError:
                self.log("OTP verified, but response is not valid JSON.", "warning")
                return True

            except Exception as e:
                self.log(f"Unexpected error during OTP verification: {str(e)}", "error")
                return False
        else:
            self.log("OTP verification failed: No response received.", "error")
            return False

    def run(self):
        mail = MailTMClient(self.proxy_raw)
        acct = mail.create_account()
        if not acct:
            self.log("Failed to create email", "error")
            return False
        self.email = acct["email"]
        self.log(f"Email: {self.email}", "info")
        if not self.send_otp(self.email):
            self.log("Failed to send OTP", "error")
            return False
        otp = mail.get_otp(account_num=self.account_num, total=self.total_accounts)
        if otp:
            verified = self.verify_otp(self.email, otp)
            if verified:
                with open("account.txt", "a") as af:
                    af.write(f"{self.email}|{mail.account['password']}\n")
                self.log("Account saved to account.txt", "success")
                return True
            else:
                return False
        else:
            self.log("OTP not received", "error")
            return False

def worker_task(proxy, account_num, total_accounts, max_retries):
    current_retries = 0
    while current_retries <= max_retries:
        if current_retries > 0:
            log_message(message=f"Retrying account {account_num}/{total_accounts} (Attempt {current_retries+1}/{max_retries+1})...", message_type="warning", account_num=account_num, total=total_accounts)
            time.sleep(5)

        bot = NexoradBot(proxy, account_num=account_num, total_accounts=total_accounts)
        if bot.run():
            return True
        else:
            current_retries += 1
    return False

def main():
    if INVITER_CODE is None:
        log_message(message="INVITER_CODE environment variable is not set. Please set it in your .env file.", message_type="error")
        return

    try:
        total = int(input(f"{Fore.CYAN}How many referral accounts do you want to create? {Style.RESET_ALL}"))
    except ValueError:
        log_message(message="Invalid number input.", message_type="error")
        return

    proxies = load_proxies()
    max_workers = min(os.cpu_count() * 2 if os.cpu_count() else 4, total)
    max_retries = 3

    successful_count = 0
    failed_count = 0

    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(total):
            print("\n")
            proxy = proxies[i % len(proxies)] if proxies else None
            log_message(message="Queueing account", message_type="process", account_num=i+1, total=total)
            future = executor.submit(worker_task, proxy, i+1, total, max_retries)
            futures.append(future)

        for i, future in enumerate(as_completed(futures)):
            if future.result():
                successful_count += 1
            else:
                failed_count += 1

    print(f"\n{'='*50}")
    print(f"F O R E S T A R M Y — N E X O R A D")
    print(f"🎉 AUTO REFF PROCESS COMPLETED!")
    print(f"{'='*50}")
    print(f"✅ Successful: {successful_count}")
    print(f"❌ Failed: {failed_count}")
    if successful_count + failed_count > 0:
        success_rate = (successful_count / (successful_count + failed_count) * 100)
        print(f"📊 Success rate: {success_rate:.1f}%")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
