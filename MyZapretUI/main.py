import os
import sys
import subprocess
import json
import hashlib
import customtkinter as ctk
import requests

# --- ЛОГИКА СЕКРЕТНОЙ СОЛИ ---
try:
    # Этот файл будет создан автоматически во время сборки на GitHub
    from config import SECRET_SALT
except ImportError:
    # Соль для локальных тестов (не будет работать с ключами от основной версии)
    SECRET_SALT = "LocalDevelopmentManualSalt"

APP_DIR_NAME = "Dostup_YT_DS_RBLX"

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_resource_path(relative_path):
    """Определяет путь к ресурсам внутри скомпилированного .exe (PyInstaller)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_hwid():
    """Получает уникальный ID оборудования (UUID) через WMIC"""
    try:
        hwid = subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()
        return hwid
    except Exception:
        # Резервный вариант, если WMIC недоступен
        import uuid
        return str(uuid.getnode())

def generate_valid_key(hwid):
    """Хэширует HWID вместе с секретной солью для проверки лицензии"""
    raw_str = hwid + SECRET_SALT
    return hashlib.sha256(raw_str.encode()).hexdigest()

def get_license_path():
    """Возвращает путь к файлу лицензии в AppData (статичное скрытое место)"""
    appdata = os.getenv('APPDATA')
    target_dir = os.path.join(appdata, APP_DIR_NAME)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    return os.path.join(target_dir, "license.json")

# --- ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ ---

class DostupApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_DIR_NAME} | UI Control")
        self.geometry("500x520")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.hwid = get_hwid()
        self.process = None

        # Инициализация интерфейса в зависимости от лицензии
        if self.check_license():
            self.build_main_ui()
        else:
            self.build_auth_ui()

    # --- СИСТЕМА ЛИЦЕНЗИРОВАНИЯ ---

    def check_license(self):
        path = get_license_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("key") == generate_valid_key(self.hwid)
            except:
                return False
        return False

    def save_license(self, key):
        path = get_license_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"key": key}, f)

    def handle_activation(self):
        entered_key = self.key_entry.get().strip()
        if entered_key == generate_valid_key(self.hwid):
            self.save_license(entered_key)
            self.auth_frame.destroy()
            self.build_main_ui()
        else:
            self.error_label.configure(text="Неверный ключ доступа!", text_color="#ff5555")

    def copy_hwid(self):
        self.clipboard_clear()
        self.clipboard_append(self.hwid)
        self.btn_hwid.configure(text="Скопировано!")
        self.after(2000, lambda: self.btn_hwid.configure(text="Копировать HWID"))

    # --- ИНТЕРФЕЙС АВТОРИЗАЦИИ ---

    def build_auth_ui(self):
        self.auth_frame = ctk.CTkFrame(self, corner_radius=15)
        self.auth_frame.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(self.auth_frame, text="Активация системы", font=("Segoe UI", 24, "bold")).pack(pady=(30, 20))
        
        ctk.CTkLabel(self.auth_frame, text="Ваш уникальный ID (HWID):", font=("Segoe UI", 12)).pack()
        self.hwid_display = ctk.CTkEntry(self.auth_frame, width=300, justify="center")
        self.hwid_display.insert(0, self.hwid)
        self.hwid_display.configure(state="readonly")
        self.hwid_display.pack(pady=10)

        self.btn_hwid = ctk.CTkButton(self.auth_frame, text="Копировать HWID", command=self.copy_hwid, fg_color="#444", hover_color="#555")
        self.btn_hwid.pack(pady=5)

        self.key_entry = ctk.CTkEntry(self.auth_frame, placeholder_text="Введите лицензионный ключ", width=320, height=40)
        self.key_entry.pack(pady=(30, 10))

        ctk.CTkButton(self.auth_frame, text="Активировать", font=("Segoe UI", 14, "bold"), 
                      fg_color="#2ecc71", hover_color="#27ae60", height=45, width=200,
                      command=self.handle_activation).pack(pady=10)

        self.error_label = ctk.CTkLabel(self.auth_frame, text="")
        self.error_label.pack()

    # --- ГЛАВНЫЙ ИНТЕРФЕЙС УПРАВЛЕНИЯ ---

    def build_main_ui(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.main_frame, text="Dostup YT DS RBLX", font=("Segoe UI", 26, "bold"), text_color="#3498db").pack(pady=(15, 20))

        # Выбор режима
        ctk.CTkLabel(self.main_frame, text="Выберите профиль обхода:", font=("Segoe UI", 13)).pack()
        
        self.profiles = {
            "Авто (YouTube + Discord + Roblox)": "general.bat",
            "Только Discord": "discord.bat",
            "YouTube + Roblox (Alt)": "youtube_rblx.bat"
        }
        
        self.profile_var = ctk.StringVar(value=list(self.profiles.keys())[0])
        self.menu = ctk.CTkOptionMenu(self.main_frame, values=list(self.profiles.keys()), variable=self.profile_var, width=320, height=35)
        self.menu.pack(pady=10)

        # Кнопки управления
        self.btn_start = ctk.CTkButton(self.main_frame, text="ЗАПУСТИТЬ", font=("Segoe UI", 16, "bold"), 
                                      fg_color="#2ecc71", hover_color="#27ae60", height=50, width=250,
                                      command=self.start_service)
        self.btn_start.pack(pady=(20, 10))

        self.btn_stop = ctk.CTkButton(self.main_frame, text="ОСТАНОВИТЬ", font=("Segoe UI", 16, "bold"), 
                                     fg_color="#e74c3c", hover_color="#c0392b", height=50, width=250,
                                     command=self.stop_service, state="disabled")
        self.btn_stop.pack(pady=5)

        # Индикаторы
        self.status_label = ctk.CTkLabel(self.main_frame, text="Статус: Остановлен 🔴", font=("Segoe UI", 14, "bold"), text_color="#e74c3c")
        self.status_label.pack(pady=20)

        # Секция проверки
        self.check_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.check_frame.pack(pady=10)

        ctk.CTkButton(self.check_frame, text="Проверить соединение", width=180, command=self.check_connection).pack(side="left", padx=5)
        self.health_info = ctk.CTkLabel(self.check_frame, text="", font=("Segoe UI", 12))
        self.health_info.pack(side="left", padx=5)

    # --- ЛОГИКА РАБОТЫ ---

    def start_service(self):
        self.stop_service() # На всякий случай гасим старые процессы

        selected_name = self.profile_var.get()
        bat_name = self.profiles[selected_name]
        
        # Путь к батнику внутри прокси-папки в exe
        bat_path = get_resource_path(os.path.join("proxy_bin", bat_name))

        if not os.path.exists(bat_path):
            self.status_label.configure(text=f"Ошибка: {bat_name} не найден!", text_color="#f39c12")
            return

        try:
            # CREATE_NO_WINDOW = 0x08000000
            self.process = subprocess.Popen(bat_path, creationflags=0x08000000, shell=True)
            self.status_label.configure(text="Статус: Работает 🟢", text_color="#2ecc71")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
        except Exception as e:
            self.status_label.configure(text="Ошибка запуска процесса", text_color="#e74c3c")

    def stop_service(self):
        # Очистка всех возможных процессов Zapret
        try:
            subprocess.call("taskkill /F /IM winws.exe", shell=True, creationflags=0x08000000)
            if self.process:
                self.process.terminate()
                self.process = None
        except:
            pass
            
        self.status_label.configure(text="Статус: Остановлен 🔴", text_color="#e74c3c")
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def check_connection(self):
        self.health_info.configure(text="⌛ Проверка...")
        self.update()
        
        targets = {"YT": "https://www.youtube.com", "DS": "https://discord.com", "RB": "https://www.roblox.com"}
        results = []
        
        for short, url in targets.items():
            try:
                r = requests.get(url, timeout=3)
                results.append(f"{short}:✅" if r.status_code == 200 else f"{short}:⚠️")
            except:
                results.append(f"{short}:❌")
        
        self.health_info.configure(text=" | ".join(results))

if __name__ == "__main__":
    # Запуск приложения
    app = DostupApp()
    app.mainloop()
