import os
import subprocess
import customtkinter as ctk
import requests
import uuid

# --- 1. ЛОГИКА ЛИЦЕНЗИИ И HWID ---

def get_hwid():
    # Простой способ получить уникальный ID на базе MAC-адреса
    return str(uuid.getnode())

def check_license():
    # Прячем лицензию в AppData, чтобы её не было видно в папке с программой
    appdata_path = os.getenv('APPDATA')
    license_dir = os.path.join(appdata_path, "MyZapretApp")
    license_file = os.path.join(license_dir, "license.json") # Или .bin
    
    # Здесь логика проверки: если файл есть и ключ совпадает с HWID -> True
    # Для теста возвращаем True
    return True

# --- 2. ЛОГИКА РАБОТЫ ZAPRET ---

process = None

def start_zapret(strategy):
    global process
    if process is not None:
        stop_zapret()
    
    # Получаем путь к winws.exe внутри временной папки PyInstaller
    winws_path = resource_path(os.path.join("zapret_bin", "winws.exe"))
    list_path = resource_path(os.path.join("zapret_bin", "list-general.txt"))
    
    # Формируем аргументы в зависимости от выбранной стратегии (генерала)
    # Это пример аргументов, подставь те, что нужны для Discord/YouTube
    args = [
        winws_path,
        "--wf-tcp=80,443",
        "--wf-udp=443,50000-65535",
        f"--hostlist={list_path}",
        # ... остальные параметры стратегии
    ]
    
    # Запускаем скрытно (без окон консоли)
    creationflags = 0x08000000 # CREATE_NO_WINDOW
    process = subprocess.Popen(args, creationflags=creationflags)
    status_label.configure(text="Статус: Работает 🟢", text_color="green")

def stop_zapret():
    global process
    if process:
        process.terminate()
        process = None
    status_label.configure(text="Статус: Остановлен 🔴", text_color="red")

# --- 3. ПРОВЕРКА РАБОТОСПОСОБНОСТИ (HEALTH CHECK) ---

def check_connection():
    try:
        # Проверяем доступность дискорда
        response = requests.get("https://discord.com", timeout=3)
        if response.status_code == 200:
            health_label.configure(text="Discord доступен ✅", text_color="green")
        else:
            health_label.configure(text=f"Ошибка: {response.status_code} ⚠️", text_color="orange")
    except requests.ConnectionError:
        health_label.configure(text="Нет связи ❌", text_color="red")

# --- 4. ИНТЕРФЕЙС (CustomTkinter) ---

if not check_license():
    print("Лицензия не найдена! Тут должен быть вызов окна ввода ключа.")
    sys.exit()

app = ctk.CTk()
app.title("Zapret Control Panel")
app.geometry("400x350")

# Выбор стратегии
strategy_var = ctk.StringVar(value="general")
strategy_label = ctk.CTkLabel(app, text="Выберите профиль обхода:")
strategy_label.pack(pady=(20, 5))

strategy_menu = ctk.CTkOptionMenu(app, values=["General (Рекомендуемый)", "Only Discord", "Alternative"], variable=strategy_var)
strategy_menu.pack(pady=5)

# Кнопки управления
btn_start = ctk.CTkButton(app, text="Запустить", fg_color="green", hover_color="darkgreen", command=lambda: start_zapret(strategy_var.get()))
btn_start.pack(pady=10)

btn_stop = ctk.CTkButton(app, text="Остановить", fg_color="red", hover_color="darkred", command=stop_zapret)
btn_stop.pack(pady=5)

# Статус
status_label = ctk.CTkLabel(app, text="Статус: Остановлен 🔴", text_color="red")
status_label.pack(pady=10)

# Проверка соединения
btn_check = ctk.CTkButton(app, text="Проверить соединение", command=check_connection)
btn_check.pack(pady=(20, 5))

health_label = ctk.CTkLabel(app, text="")
health_label.pack()

app.mainloop()
