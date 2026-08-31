import os
import time

import keyboard
import pyautogui
import pyperclip

stop_flag = False

def stop_script():
    global stop_flag
    stop_flag = True
    print("\nStopped by user!")

keyboard.add_hotkey("f12", stop_script)

def smart_sleep(seconds):
    for _ in range(int(seconds * 10)):
        if stop_flag:
            return
        time.sleep(0.1)

# 1) Создаем список для хранения названия пикировок и счетчик

picks_names = []
counter = 0

# 2) Создаем папку output на рабочем столе

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
output_folder = os.path.join(desktop_path, "output")
os.makedirs(output_folder, exist_ok=True)

# 2) Поток автоматизации

print("\nSelect first pick in Database Navigation window. Starting in 5 seconds...")
smart_sleep(5)
print("\nScript started! To stop it press F12 button")
print("")
smart_sleep(1)

while not stop_flag:

    # 1) открываем меню
    keyboard.send("shift+f10")
    smart_sleep(0.15)

    # 2) находим Rename
    for _ in range(2):
        keyboard.send("down")
        smart_sleep(0.15)

    # 3) открываем Rename
    keyboard.send("enter")
    smart_sleep(0.15)

    # 4) Копируем название пикировки
    pyperclip.copy("")
    smart_sleep(0.1)

    if stop_flag:
        break

    pyautogui.press("left")
    smart_sleep(0.1)

    pyautogui.hotkey("ctrl", "a")
    smart_sleep(0.1)

    pyautogui.hotkey("ctrl", "c")
    smart_sleep(0.25)

    # 5) Копируем название в переменную
    pick_name = pyperclip.paste()
    file_name = pick_name + ".txt"

    # 6) Проверка на дубликат имени - выход из потока!
    if pick_name in picks_names:
        print(f"Last pick {pick_name} found. Script stopped!")
        smart_sleep(0.2)
        break

    # 7) Добавляем переменную в список
    picks_names.append(pick_name)

    if stop_flag:
        break

    # 8) # закрываем Edit окно Edit
    keyboard.send("esc")
    smart_sleep(0.15)

    # 9) открываем меню
    keyboard.send("shift+f10")
    smart_sleep(0.15)

    # 10) переходим в Export
    for _ in range(4):
        keyboard.send("down")
        smart_sleep(0.15)

    # 11) Выбираем Export
    keyboard.send("enter")
    smart_sleep(0.2)

    if stop_flag:
        break

    # 12) Вставляем текущее название файла
    pyperclip.copy(file_name)
    keyboard.send("ctrl+v")
    smart_sleep(0.2)

    # 13) Перейти в нужную папку через Ctrl+L
    keyboard.send("ctrl+l")
    smart_sleep(0.2)

    # 14) Вставляем путь к output
    keyboard.write(output_folder)
    smart_sleep(0.2)

    # 15) Переходим в папку
    keyboard.send("enter")
    smart_sleep(0.3)

    # 16) Сохраняем файл
    keyboard.send("enter")
    smart_sleep(2)

    if stop_flag:
        break

    # 17) Ждем окно "Done". Закрываем окно
    keyboard.send("enter")
    smart_sleep(0.2)
    counter += 1
    print(f"Pick {file_name[:-4]} saved [{counter}]! Continuing... (to stop press F12)")

    # 18) Переходим к следующему файлу
    keyboard.send("down")
    smart_sleep(0.2)

    if stop_flag:
        break

# pyinstaller --onefile --name "AutoPickExporter" dev/AutoPickExporter.py
