import os
import sys
import subprocess
import json
import hashlib
import customtkinter as ctk
import requests

# --- КОНФИГУРАЦИЯ (Видна в UI) ---
SECRET_SALT = "Dostup_Top_Secret_Salt_2026" 
MASTER_KEY = "ADMIN123" 
APP_DIR_NAME = "Dostup_YT_DS_RBLX"

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_hwid():
    try:
        # Получаем UUID оборудования
        hwid = subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()
        return hwid
    except:
        import uuid
        return str(uuid.getnode())

def generate_valid_key(hwid):
    """Метод генерации, который мы проверяем"""
    raw_str = hwid + SECRET_SALT
    return hashlib.sha256(raw_str.encode()).hexdigest()

def get_license_path():
    path = os.path.join(os.getenv('APPDATA'), APP_DIR_NAME)
    if not os.path.exists(path): os.makedirs(path)
    return os.path.join(path, "license.json")

# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---

class DostupApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Dostup_YT_DS_RBLX | Debug Version")
        self.geometry("600x750") # Увеличил высоту для новых полей
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        self.hwid = get_hwid()
        self.expected_key = generate_valid_key(self.hwid)
        self.is_test_mode = False
        self.process = None
        
        self.scan_strategies()

        if self.check_license():
            self.build_main_ui()
        else:
            self.build_auth_ui()

    def scan_strategies(self):
        self.strategies = {}
        proxy_dir = get_resource_path("proxy_bin")
        if os.path.exists(proxy_dir):
            for f in os.listdir(proxy_dir):
                if f.endswith('.bat'):
                    self.strategies[f.replace(".bat", "").upper()] = f
        if not self.strategies: 
            self.strategies = {"СТРАТЕГИИ НЕ НАЙДЕНЫ": "none"}

    def check_license(self):
        path = get_license_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    key = data.get("key")
                    if key == "TEST_USER": 
                        self.is_test_mode = True
                        return True
                    return key == self.expected_key or key == MASTER_KEY
            except: return False
        return False

    def handle_activation(self):
        key = self.key_entry.get().strip()
        if key == self.expected_key or key == MASTER_KEY:
            self.save_license(key)
            self.auth_frame.destroy()
            self.build_main_ui()
        else:
            self.error_label.configure(text="КЛЮЧ НЕ СОВПАДАЕТ С ОЖИДАЕМЫМ!", text_color="#ff5555")

    def save_license(self, key):
        with open(get_license_path(), "w") as f:
            json.dump({"key": key}, f)

    def copy_to_clip(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    # --- ИНТЕРФЕЙС АКТИВАЦИИ (DEBUG) ---

    def build_auth_ui(self):
        self.auth_frame = ctk.CTkFrame(self)
        self.auth_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(self.auth_frame, text="ПАНЕЛЬ ОТЛАДКИ КЛЮЧЕЙ", font=("Arial", 22, "bold"), text_color="#3498db").pack(pady=15)
        
        # Блок HWID
        ctk.CTkLabel(self.auth_frame, text="1. ВАШ HWID:").pack()
        h_ent = ctk.CTkEntry(self.auth_frame, width=450, justify="center")
        h_ent.insert(0, self.hwid); h_ent.configure(state="readonly"); h_ent.pack(pady=5)
        ctk.CTkButton(self.auth_frame, text="Скопировать HWID", height=25, command=lambda: self.copy_to_clip(self.hwid)).pack()

        # Блок SALT
        ctk.CTkLabel(self.auth_frame, text="2. ТЕКУЩАЯ СОЛЬ (SALT):", font=("Arial", 12, "bold")).pack(pady=(15, 0))
        s_ent = ctk.CTkEntry(self.auth_frame, width=450, justify="center", text_color="#e67e22")
        s_ent.insert(0, SECRET_SALT); s_ent.configure(state="readonly"); s_ent.pack(pady=5)

        # Блок EXPECTED KEY
        ctk.CTkLabel(self.auth_frame, text="3. ОЖИДАЕМЫЙ КЛЮЧ (РЕЗУЛЬТАТ):", font=("Arial", 12, "bold")).pack(pady=(15, 0))
        e_ent = ctk.CTkEntry(self.auth_frame, width=450, justify="center", text_color="#2ecc71")
        e_ent.insert(0, self.expected_key); e_ent.configure(state="readonly"); e_ent.pack(pady=5)
        ctk.CTkButton(self.auth_frame, text="Скопировать Ожидаемый Ключ", height=25, fg_color="#27ae60", command=lambda: self.copy_to_clip(self.expected_key)).pack()

        # Поле ввода
        ctk.CTkLabel(self.auth_frame, text="--- ВВЕДИТЕ КЛЮЧ ДЛЯ ВХОДА ---", font=("Arial", 14, "bold")).pack(pady=(30, 5))
        self.key_entry = ctk.CTkEntry(self.auth_frame, placeholder_text="Вставьте ключ сюда...", width=450, height=50)
        self.key_entry.pack(pady=10)

        ctk.CTkButton(self.auth_frame, text="АКТИВИРОВАТЬ", fg_color="#2ecc71", height=55, width=300, font=("Arial", 16, "bold"), command=self.handle_activation).pack(pady=10)
        
        ctk.CTkButton(self.auth_frame, text="ВОЙТИ БЕЗ КЛЮЧА (ТЕСТ)", fg_color="#34495e", command=lambda: [self.save_license("TEST_USER"), self.auth_frame.destroy(), self.build_main_ui()]).pack()

        self.error_label = ctk.CTkLabel(self.auth_frame, text="")
        self.error_label.pack(pady=10)

    # --- ГЛАВНЫЙ ИНТЕРФЕЙС ---

    def build_main_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.main_frame, text=APP_DIR_NAME, font=("Arial", 24, "bold"), text_color="#3498db").pack(pady=20)

        # Выбор батника
        self.strat_var = ctk.StringVar(value=list(self.strategies.keys())[0])
        self.menu = ctk.CTkOptionMenu(self.main_frame, values=list(self.strategies.keys()), variable=self.strat_var, width=400, height=40)
        self.menu.pack(pady=10)

        self.btn_start = ctk.CTkButton(self.main_frame, text="ЗАПУСТИТЬ ОБХОД", fg_color="#2ecc71", height=60, width=350, font=("Arial", 18, "bold"), command=self.start_p)
        self.btn_start.pack(pady=20)

        self.btn_stop = ctk.CTkButton(self.main_frame, text="ОСТАНОВИТЬ", fg_color="#e74c3c", height=60, width=350, font=("Arial", 18, "bold"), command=self.stop_p, state="disabled")
        self.btn_stop.pack(pady=5)

        self.status_l = ctk.CTkLabel(self.main_frame, text="СТАТУС: ГОТОВ К РАБОТЕ 🔴", font=("Arial", 15, "bold"))
        self.status_l.pack(pady=30)

        ctk.CTkButton(self.main_frame, text="ПРОВЕРИТЬ СОЕДИНЕНИЕ", command=self.check_net).pack()
        self.health_l = ctk.CTkLabel(self.main_frame, text="", font=("Arial", 13))
        self.health_l.pack(pady=10)

    # --- ЛОГИКА ПРОЦЕССОВ ---

    def start_p(self):
        self.stop_p()
        bat = self.strategies[self.strat_var.get()]
        path = get_resource_path(os.path.join("proxy_bin", bat))
        if not os.path.exists(path): return
        
        self.process = subprocess.Popen(path, creationflags=0x08000000, shell=True)
        self.status_l.configure(text="СТАТУС: РАБОТАЕТ 🟢", text_color="#2ecc71")
        self.btn_start.configure(state="disabled"); self.btn_stop.configure(state="normal")

    def stop_p(self):
        subprocess.call("taskkill /F /IM winws.exe", shell=True, creationflags=0x08000000)
        if self.process: self.process.terminate(); self.process = None
        self.status_l.configure(text="СТАТУС: ОСТАНОВЛЕН 🔴", text_color="#e74c3c")
        self.btn_start.configure(state="normal"); self.btn_stop.configure(state="disabled")

    def check_net(self):
        self.health_l.configure(text="Проверяем YouTube и Discord...")
        self.update()
        res = []
        for k, v in {"YouTube": "https://www.youtube.com", "Discord": "https://discord.com"}.items():
            try:
                r = requests.get(v, timeout=4)
                res.append(f"{k}: ✅" if r.status_code == 200 else f"{k}: ⚠️")
            except: res.append(f"{k}: ❌")
        self.health_l.configure(text=" | ".join(res))

if __name__ == "__main__":
    DostupApp().mainloop()
