import threading
import time
import tkinter as tk

import pyautogui
import win32con
import win32gui


def get_windows():
    windows = []
    def enum_handler(hwnd, result):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            result.append(hwnd)
    win32gui.EnumWindows(enum_handler, windows)
    return windows

class RadExShots:
    def __init__(self, status_label, counter_label):
        self.running = False
        self.known_windows = set()
        self.initialized = False
        self.status_label = status_label
        self.counter_label = counter_label
        self.screenshot_count = 0

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.loop, daemon=True).start()
            print("Старт! Ждём новые окна...")
            self.update_status("Waiting for next section...")
            self.update_counter()

    def stop(self):
        self.running = False
        print("Стоп!")
        self.update_status("Stopped")

    def update_status(self, text):
        # Обновляем текст состояния
        self.status_label.config(text=text)

    def update_counter(self):
        # Обновляем счётчик скриншотов
        self.counter_label.config(text=f"Screenshots: {self.screenshot_count}")

    def loop(self):
        while self.running:
            current_windows = set(get_windows())

            if not self.initialized:
                self.known_windows = current_windows
                self.initialized = True

            new_windows = current_windows - self.known_windows

            if new_windows:
                hwnd = list(new_windows)[0]
                print("Новое окно найдено!")
                try:
                    # Активируем окно
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.5)

                    # Скриншот (Ctrl + I)
                    pyautogui.hotkey("ctrl", "i")
                    self.screenshot_count += 1
                    self.update_status(f"Screenshot saved! ({self.screenshot_count})")
                    self.update_counter()
                    time.sleep(1)

                    # Закрываем окно
                    pyautogui.hotkey("alt", "f4")
                    print("Окно обработано")

                    # Обновляем список известных окон
                    self.known_windows.add(hwnd)

                    # Готовимся к следующему окну
                    self.update_status("Waiting for next section...")

                except Exception as e:
                    print("Ошибка при обработке окна:", e)

            time.sleep(1)

# --- GUI ---
root = tk.Tk()
root.title("RadExShots")
root.geometry("300x150")

# Статус сверху
status_label = tk.Label(root, text="Waiting for next section...", wraplength=280)
status_label.pack(pady=10)

# Кнопки
start_btn = tk.Button(root, text="Старт", width=10)
start_btn.pack(pady=5)

stop_btn = tk.Button(root, text="Стоп", width=10, state=tk.DISABLED)
stop_btn.pack(pady=5)

# Счётчик в нижнем правом углу
counter_label = tk.Label(root, text="Screenshots: 0")
counter_label.pack(side=tk.BOTTOM, anchor="e", padx=10, pady=5)

# Создаём объект скрипта
radex = RadExShots(status_label, counter_label)

# Привязываем кнопки
start_btn.config(command=lambda: [radex.start(), start_btn.config(state=tk.DISABLED), stop_btn.config(state=tk.NORMAL)])
stop_btn.config(command=lambda: [radex.stop(), start_btn.config(state=tk.NORMAL), stop_btn.config(state=tk.DISABLED)])

root.mainloop()
