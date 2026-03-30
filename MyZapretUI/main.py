import os
import sys
import subprocess
import json
import hashlib
import customtkinter as ctk
import requests

# --- ЛОГИКА СЕКРЕТНОЙ СОЛИ ---
try:
    from config import SECRET_SALT
except ImportError:
    SECRET_SALT = "LocalDevelopmentManualSalt"

APP_DIR_NAME = "Dostup_YT_DS_RBLX"

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_hwid():
    try:
        hwid = subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()
        return hwid
    except Exception:
        import uuid
        return str(uuid.getnode())

def generate_valid_key(hwid):
    return hashlib.sha256((hwid + SECRET_SALT).encode()).hexdigest()

def get_license_path():
    appdata = os.getenv('APPDATA')
    target_dir = os.path.join(appdata, APP_DIR_NAME)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    return os.path.join(target_dir, "license.json")

# --- ИНТЕРФЕЙС ---

class DostupApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_DIR_NAME}")
        self.geometry("550x550")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.hwid = get_hwid()
        self.process = None
        
        # Сканируем доступные стратегии (батники)
        self.scan_strategies()

        if self.check_license():
            self.build_main_ui()
        else:
            self.build_auth_ui()

    def scan_strategies(self):
        """Автоматически находит все .bat файлы в папке proxy_bin"""
        self.strategies = {}
        proxy_dir = get_resource_path("proxy_bin")
        
        if os.path.exists(proxy_dir):
            files = [f for f in os.listdir(proxy_dir) if f.endswith('.bat')]
            for f in files:
                # Красивое имя для списка (убираем .bat и заменяем подчеркивания)
                pretty_name = f.replace(".bat", "").replace("_", " ").title()
                self.strategies[pretty_name] = f
        
        if not self.strategies:
            self.strategies = {"Файлы не найдены": "none"}

    def check_license(self):
        path = get_license_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("key") == generate_valid_key(self.hwid)
            except: return False
        return False

    def handle_activation(self):
        entered_key = self.key_entry.get().strip()
        if entered_key == generate_valid_key(self.hwid):
            self.save_license(entered_key)
            self.auth_frame.destroy()
            self.build_main_ui()
        else:
            self.error_label.configure(text="Неверный ключ!", text_color="#ff5555")

    def save_license(self, key):
        path = get_license_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"key": key}, f)

    def copy_hwid(self):
        self.clipboard_clear()
        self.clipboard_append(self.hwid)
        self.btn_hwid.configure(text="Скопировано!")

    # --- UI АВТОРИЗАЦИИ ---
    def build_auth_ui(self):
        self.auth_frame = ctk.CTkFrame(self, corner_radius=15)
        self.auth_frame.pack(fill="both", expand=True, padx=30, pady=30)
        ctk.CTkLabel(self.auth_frame, text="Активация доступа", font=("Arial", 24, "bold")).pack(pady=20)
        ctk.CTkLabel(self.auth_frame, text=f"HWID: {self.hwid}", font=("Arial", 10)).pack()
        self.btn_hwid = ctk.CTkButton(self.auth_frame, text="Копировать HWID", command=self.copy_hwid)
        self.btn_hwid.pack(pady=10)
        self.key_entry = ctk.CTkEntry(self.auth_frame, placeholder_text="Введите ключ", width=300)
        self.key_entry.pack(pady=20)
        ctk.CTkButton(self.auth_frame, text="Войти", fg_color="#2ecc71", command=self.handle_activation).pack()
        self.error_label = ctk.CTkLabel(self.auth_frame, text="")
        self.error_label.pack()

    # --- ГЛАВНЫЙ UI ---
    def build_main_ui(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.main_frame, text=APP_DIR_NAME, font=("Arial", 22, "bold")).pack(pady=20)

        # Выпадающий список со ВСЕМИ генералами
        ctk.CTkLabel(self.main_frame, text="Выберите стратегию (из папки bin):").pack()
        self.strat_var = ctk.StringVar(value=list(self.strategies.keys())[0])
        self.menu = ctk.CTkOptionMenu(self.main_frame, values=list(self.strategies.keys()), variable=self.strat_var, width=350)
        self.menu.pack(pady=10)

        self.btn_start = ctk.CTkButton(self.main_frame, text="ЗАПУСТИТЬ", fg_color="#2ecc71", font=("Arial", 16, "bold"), height=45, command=self.start_proxy)
        self.btn_start.pack(pady=10)

        self.btn_stop = ctk.CTkButton(self.main_frame, text="ОСТАНОВИТЬ", fg_color="#e74c3c", font=("Arial", 16, "bold"), height=45, command=self.stop_proxy, state="disabled")
        self.btn_stop.pack(pady=5)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Статус: Остановлен 🔴", font=("Arial", 14, "bold"), text_color="#e74c3c")
        self.status_label.pack(pady=20)

        ctk.CTkButton(self.main_frame, text="Проверить YouTube / Discord / Roblox", command=self.check_net).pack(pady=10)
        self.health_label = ctk.CTkLabel(self.main_frame, text="")
        self.health_label.pack()

    def start_proxy(self):
        self.stop_proxy()
        bat_file = self.strategies[self.strat_var.get()]
        bat_path = get_resource_path(os.path.join("proxy_bin", bat_file))

        if not os.path.exists(bat_path): return

        try:
            self.process = subprocess.Popen(bat_path, creationflags=0x08000000, shell=True)
            self.status_label.configure(text="Статус: Работает 🟢", text_color="#2ecc71")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
        except: pass

    def stop_proxy(self):
        subprocess.call("taskkill /F /IM winws.exe", shell=True, creationflags=0x08000000)
        if self.process: self.process.terminate(); self.process = None
        self.status_label.configure(text="Статус: Остановлен 🔴", text_color="#e74c3c")
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def check_net(self):
        self.health_label.configure(text="Проверка...")
        self.update()
        res = []
        urls = {"YT": "https://www.youtube.com", "DS": "https://discord.com", "RB": "https://www.roblox.com"}
        for k, v in urls.items():
            try:
                r = requests.get(v, timeout=3)
                res.append(f"{k}:✅" if r.status_code == 200 else f"{k}:⚠️")
            except: res.append(f"{k}:❌")
        self.health_label.configure(text=" | ".join(res))

if __name__ == "__main__":
    app = DostupApp()
    app.mainloop()
