import os
import sys
import subprocess
import json
import hashlib
import customtkinter as ctk
import requests

APP_DIR_NAME = "Dostup_YT_DS_RBLX"

def get_resource_path(relative_path):
    """Путь к файлам внутри скомпилированного exe."""
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
        return "UNKNOWN_HWID"

def generate_valid_key(hwid):
    """Динамическая генерация соли без хранения секрета в открытом виде."""
    dynamic_salt = hwid[::-1] + APP_DIR_NAME
    return hashlib.sha256((hwid + dynamic_salt).encode()).hexdigest()

def get_license_path():
    """Статичное место хранения лицензии."""
    appdata = os.getenv('APPDATA')
    target_dir = os.path.join(appdata, APP_DIR_NAME)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    return os.path.join(target_dir, "license.json")

class DostupApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_DIR_NAME} Control Panel")
        self.geometry("480x480")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.hwid = get_hwid()
        self.process = None

        if self.check_license():
            self.build_main_ui()
        else:
            self.build_auth_ui()

    def check_license(self):
        lic_path = get_license_path()
        if os.path.exists(lic_path):
            try:
                with open(lic_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("key", "") == generate_valid_key(self.hwid):
                        return True
            except Exception:
                pass
        return False

    def save_license(self, key):
        lic_path = get_license_path()
        with open(lic_path, "w", encoding="utf-8") as f:
            json.dump({"key": key}, f)

    def activate(self):
        entered_key = self.key_entry.get().strip()
        if entered_key == generate_valid_key(self.hwid):
            self.save_license(entered_key)
            self.auth_frame.destroy()
            self.build_main_ui()
        else:
            self.auth_error_label.configure(text="Неверный ключ!", text_color="red")

    def copy_hwid(self):
        self.clipboard_clear()
        self.clipboard_append(self.hwid)
        self.hwid_label.configure(text="HWID скопирован!")

    def build_auth_ui(self):
        self.auth_frame = ctk.CTkFrame(self)
        self.auth_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.auth_frame, text="Активация Доступа", font=("Arial", 20, "bold")).pack(pady=(20, 10))
        
        ctk.CTkLabel(self.auth_frame, text="Ваш HWID:").pack(pady=(10, 0))
        self.hwid_label = ctk.CTkLabel(self.auth_frame, text=self.hwid, font=("Arial", 12, "bold"), text_color="gray")
        self.hwid_label.pack(pady=5)
        
        ctk.CTkButton(self.auth_frame, text="Копировать HWID", command=self.copy_hwid, width=150).pack(pady=5)

        self.key_entry = ctk.CTkEntry(self.auth_frame, placeholder_text="Введите ключ лицензии", width=300)
        self.key_entry.pack(pady=20)

        ctk.CTkButton(self.auth_frame, text="Активировать", command=self.activate, fg_color="green", hover_color="darkgreen").pack()

        self.auth_error_label = ctk.CTkLabel(self.auth_frame, text="")
        self.auth_error_label.pack(pady=10)

    def build_main_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.main_frame, text=f"{APP_DIR_NAME}", font=("Arial", 20, "bold")).pack(pady=(10, 20))

        ctk.CTkLabel(self.main_frame, text="Выберите профиль:").pack()
        
        # Названия файлов должны совпадать с теми, что лежат в корне репозитория
        self.strategies = {
            "General (Рекомендуемый)": "general.bat",
            "Discord Only": "discord.bat",
            "YouTube + Roblox": "youtube_rblx.bat"
        }
        self.strategy_var = ctk.StringVar(value="General (Рекомендуемый)")
        self.strategy_menu = ctk.CTkOptionMenu(self.main_frame, values=list(self.strategies.keys()), variable=self.strategy_var, width=250)
        self.strategy_menu.pack(pady=10)

        self.btn_start = ctk.CTkButton(self.main_frame, text="Запустить", fg_color="green", hover_color="darkgreen", command=self.start_proxy)
        self.btn_start.pack(pady=10)

        self.btn_stop = ctk.CTkButton(self.main_frame, text="Остановить", fg_color="red", hover_color="darkred", command=self.stop_proxy, state="disabled")
        self.btn_stop.pack(pady=5)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Статус: Остановлен 🔴", text_color="red", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=15)

        self.btn_check = ctk.CTkButton(self.main_frame, text="Проверить сервисы", command=self.check_health, fg_color="gray", hover_color="dimgray")
        self.btn_check.pack(pady=(15, 5))

        self.health_label = ctk.CTkLabel(self.main_frame, text="")
        self.health_label.pack(pady=5)

    def start_proxy(self):
        if self.process is not None:
            self.stop_proxy()

        selected_profile = self.strategy_var.get()
        bat_filename = self.strategies[selected_profile]
        
        # Обращаемся к папке proxy_bin внутри собранного exe
        bat_path = get_resource_path(os.path.join("proxy_bin", bat_filename))

        if not os.path.exists(bat_path):
            self.status_label.configure(text=f"Файл {bat_filename} не найден! 🔴", text_color="orange")
            return

        try:
            creationflags = 0x08000000 
            # Запускаем скрипт в скрытом режиме
            self.process = subprocess.Popen(bat_path, creationflags=creationflags, shell=True)
            self.status_label.configure(text=f"Статус: Работает 🟢", text_color="green")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
        except Exception:
            self.status_label.configure(text=f"Ошибка запуска 🔴", text_color="red")

    def stop_proxy(self):
        if self.process:
            # Убиваем winws.exe, так как он запускается из батника
            subprocess.call("taskkill /F /IM winws.exe", shell=True, creationflags=0x08000000)
            self.process.terminate()
            self.process = None
            
        self.status_label.configure(text="Статус: Остановлен 🔴", text_color="red")
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def check_health(self):
        self.health_label.configure(text="Проверка...", text_color="white")
        self.update()

        results = []
        services = {
            "DS": "https://discord.com",
            "YT": "https://www.youtube.com",
            "RBLX": "https://www.roblox.com"
        }

        for name, url in services.items():
            try:
                requests.get(url, timeout=3)
                results.append(f"{name}: ✅")
            except requests.ConnectionError:
                results.append(f"{name}: ❌")

        self.health_label.configure(text=" | ".join(results), text_color="white")

if __name__ == "__main__":
    app = DostupApp()
    app.mainloop()

health_label = ctk.CTkLabel(app, text="")
health_label.pack()

app.mainloop()
