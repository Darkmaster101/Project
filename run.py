"""
run.py — точка входа.
Запускает Django-сервер в фоне, затем открывает приложение.
При выходе из приложения сервер останавливается автоматически.
"""

import subprocess
import sys
import os
import time
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def start_django():
    """Запускает Django runserver в фоновом процессе."""
    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "--noreload", "127.0.0.1:8000"],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"[run.py] Django запущен (PID={proc.pid}) на http://127.0.0.1:8000")
    return proc


def wait_for_django(timeout=10):
    """Ждём, пока Django поднимется."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/api/sessions/", timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def run_app():
    """Запускает Tkinter-приложение в основном потоке."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("weather_app",
                                                   os.path.join(BASE_DIR, "weather_app.py"))
    mod = importlib.util.load_module_from_spec(spec) if hasattr(importlib.util, "load_module_from_spec") else None
    # Просто выполняем файл — проще и надёжнее
    exec(open(os.path.join(BASE_DIR, "weather_app.py"), encoding="utf-8").read(), {"__name__": "__main__"})


if __name__ == "__main__":
    django_proc = start_django()

    print("[run.py] Ожидаю готовности Django...")
    if not wait_for_django():
        print("[run.py] ⚠️  Django не ответил за 10 с — продолжаю без трекера.")
    else:
        print("[run.py] Django готов ✓")

    try:
        run_app()
    finally:
        print("[run.py] Завершаю Django...")
        django_proc.terminate()
        django_proc.wait()
        print("[run.py] Готово.")
