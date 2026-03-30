import os
import sys
import subprocess
import json
import hashlib
import customtkinter as ctk
import requests

# --- НАСТРОЙКИ ПРИЛОЖЕНИЯ ---
APP_DIR_NAME = "ZapretUI"
SECRET_SALT = "YourSecretSaltHere" # Эта же соль должна быть в твоем скрипте-кейгене

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_resource_path(relative_path):
    """Возвращает правильный путь к файлам при компиляции в один exe через PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_hwid():
    """Получает уникальный идентификатор оборудования (HWID) через WMIC."""
    try:
        hwid = subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()
        return hwid
    except Exception:
        return "UNKNOWN_HWID"

def generate_valid_key(hwid):
    """Генерирует правильный ключ на основе HWID и секретной соли."""
    return hashlib.sha256((hwid + SECRET_SALT).encode()).hexdigest()

def get_license_path():
    """Возвращает скрытый статичный путь к файлу license.json."""
    appdata = os.getenv('APPDATA')
    target_dir = os.path.join(appdata, APP_DIR_NAME)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    return os.path.join(target_dir, "license.json")

# --- ГЛАВНОЕ ПРИЛОЖЕНИЕ ---

class ZapretApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Zapret Control Panel")
        self.geometry("450x450")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.hwid = get_hwid()
        self.process = None

        # Проверяем лицензию при запуске
        if self.check_license():
            self.build_main_ui()
        else:
            self.build_auth_ui()

    # --- ЛОГИКА АВТОРИЗАЦИИ ---

    def check_license(self):
        """Проверяет наличие и валидность ключа в license.json."""
        lic_path = get_license_path()
        if os.path.exists(lic_path):
            try:
                with open(lic_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved_key = data.get("key", "")
                    if saved_key == generate_valid_key(self.hwid):
                        return True
            except Exception:
                pass
        return False

    def save_license(self, key):
        """Сохраняет валидный ключ в license.json."""
        lic_path = get_license_path()
        with open(lic_path, "w", encoding="utf-8") as f:
            json.dump({"key": key}, f)

    def activate(self):
        """Обработчик кнопки активации."""
        entered_key = self.key_entry.get().strip()
        if entered_key == generate_valid_key(self.hwid):
            self.save_license(entered_key)
            self.auth_frame.destroy()
            self.build_main_ui()
        else:
            self.auth_error_label.configure(text="Неверный ключ!", text_color="red")

    def copy_hwid(self):
        """Копирует
