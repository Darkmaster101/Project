import tkinter as tk
from tkinter import messagebox
import requests
import math
import os
import socket
import getpass
import threading

API_KEY = "d1ade3237608df2da9a67645e41c04c7"
DJANGO_BASE = "http://127.0.0.1:8000/api"
_session_id = None

def _session_open():
    global _session_id
    try:
        resp = requests.post(
            f"{DJANGO_BASE}/session/open/",
            json={
                "username": getpass.getuser(),
                "hostname": socket.gethostname(),
            },
            timeout=3,
        )
        if resp.status_code == 200:
            _session_id = resp.json().get("session_id")
            print(f"[Tracker] Session opened: id={_session_id}")
    except Exception as e:
        print(f"[Tracker] Could not open session: {e}")

def _session_close():
    if _session_id is None:
        return
    try:
        requests.post(f"{DJANGO_BASE}/session/close/{_session_id}/", timeout=3)
        print(f"[Tracker] Session closed: id={_session_id}")
    except Exception as e:
        print(f"[Tracker] Could not close session: {e}")

def on_quit():
    _session_close()
    root.destroy()

# ── Weather icons / gradients ────────────────────────────────────────────────

WEATHER_ICONS = {
    "clear sky": "☀️", "few clouds": "🌤", "scattered clouds": "⛅",
    "broken clouds": "☁️", "shower rain": "🌧", "rain": "🌧",
    "light rain": "🌦", "thunderstorm": "⛈", "snow": "❄️",
    "mist": "🌫", "fog": "🌫", "overcast clouds": "☁️",
    "moderate rain": "🌧", "heavy rain": "🌧", "drizzle": "🌦",
}

WEATHER_GRADIENTS = {
    "clear":   ("#FF6B35", "#c94b0a"),
    "cloud":   ("#3a6fa8", "#1e3a5f"),
    "rain":    ("#2a5298", "#1a2a6c"),
    "snow":    ("#6b8dd6", "#8e9eab"),
    "thunder": ("#1c1c2e", "#2a2a4a"),
    "mist":    ("#4a5568", "#2d3748"),
    "default": ("#1a1a2e", "#16213e"),
}

def get_icon(description):
    for key, icon in WEATHER_ICONS.items():
        if key in description:
            return icon
    return "🌡"

def get_bg_colors(description):
    desc = description.lower()
    if "clear" in desc:      return WEATHER_GRADIENTS["clear"]
    elif "thunder" in desc:  return WEATHER_GRADIENTS["thunder"]
    elif "snow" in desc:     return WEATHER_GRADIENTS["snow"]
    elif "rain" in desc or "drizzle" in desc: return WEATHER_GRADIENTS["rain"]
    elif "mist" in desc or "fog" in desc:     return WEATHER_GRADIENTS["mist"]
    elif "cloud" in desc:    return WEATHER_GRADIENTS["cloud"]
    return WEATHER_GRADIENTS["default"]

def interpolate_color(c1, c2, t):
    r1,g1,b1 = int(c1[1:3],16),int(c1[3:5],16),int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16),int(c2[3:5],16),int(c2[5:7],16)
    r,g,b = int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)
    return f"#{r:02x}{g:02x}{b:02x}"

old_c1,old_c2 = "#1a1a2e","#16213e"
target_c1,target_c2 = "#1a1a2e","#16213e"
anim_progress = 1.0

def animate_background(c1,c2):
    global target_c1,target_c2,old_c1,old_c2,anim_progress
    old_c1,old_c2 = target_c1,target_c2
    target_c1,target_c2 = c1,c2
    anim_progress = 0.0
    _bg_step()

def _bg_step():
    global anim_progress
    if anim_progress >= 1.0:
        draw_gradient(target_c1,target_c2); return
    anim_progress = min(1.0, anim_progress+0.04)
    draw_gradient(interpolate_color(old_c1,target_c1,anim_progress),
                  interpolate_color(old_c2,target_c2,anim_progress))
    root.after(16, _bg_step)

def draw_gradient(c1,c2):
    canvas.delete("all")
    for i in range(520):
        canvas.create_line(0,i,400,i, fill=interpolate_color(c1,c2,i/520))
    canvas.create_oval(-80,-80,180,180, outline="#ffffff", width=1, fill="")
    canvas.create_oval(240,300,500,560, outline="#ffffff", width=1, fill="")

pulse_angle = 5
is_animating = False

def start_pulse():
    global pulse_angle,is_animating
    is_animating = True; _pulse_step()

def _pulse_step():
    global pulse_angle
    if not is_animating: return
    pulse_angle += 0.30
    icon_label.config(font=("Segoe UI Emoji", int(52+4*math.sin(pulse_angle))))
    root.after(40, _pulse_step)

def stop_pulse():
    global is_animating
    is_animating = False
    icon_label.config(font=("Segoe UI Emoji", 52))

PLACEHOLDER = "Enter city..."

def on_focus_in(e):
    if entry.get()==PLACEHOLDER:
        entry.delete(0,"end"); entry.config(fg="white")

def on_focus_out(e):
    if not entry.get().strip():
        entry.insert(0,PLACEHOLDER); entry.config(fg="#888888")

def shake_entry():
    def _shake(n,dx):
        if n<=0:
            entry_frame.place(x=20,y=82,width=360,height=46); return
        entry_frame.place(x=20+dx,y=82,width=360,height=46)
        root.after(40, lambda: _shake(n-1,-dx))
    _shake(6,8)

def get_weather(event=None):
    city = entry.get().strip()
    if not city or city==PLACEHOLDER:
        shake_entry(); return
    weather_btn.config(text="  Loading...", state="disabled")
    root.update()
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q":city,"appid":API_KEY,"units":"metric","lang":"ru"},
            timeout=5)
        data = resp.json()
    except Exception:
        weather_btn.config(text="🚀  Find out the weather", state="normal")
        messagebox.showerror("Error","No Internet Connection."); return
    weather_btn.config(text="🚀  Find out the weather", state="normal")
    if data.get("cod")==200:
        temp=data["main"]["temp"]; feels=data["main"]["feels_like"]
        desc=data["weather"][0]["description"]
        hum=data["main"]["humidity"]; wind=data["wind"]["speed"]
        c1,c2 = get_bg_colors(desc)
        animate_background(c1,c2); start_pulse()
        icon_label.config(text=get_icon(desc))
        city_label.config(text=city.upper())
        temp_label.config(text=f"{temp:.0f}°")
        unit_label.config(text="C")
        desc_label.config(text=desc.capitalize())
        feels_label.config(text=f"Feels like {feels:.0f}°C")
        detail_humid.config(text=f"{hum}%")
        detail_wind.config(text=f"{wind:.1f} м/с")
        result_frame.place(x=20,y=200,width=360,height=295)
        root.after(3000, stop_pulse)
    else:
        messagebox.showerror("Not found","City not found.\nPlease try again(in English).")

#История (Django)

def show_sessions():
    try:
        resp = requests.get(f"{DJANGO_BASE}/sessions/", timeout=3)
        sessions = resp.json().get("sessions", [])
    except Exception:
        messagebox.showerror("Error", "Django server не запущен.\nЗапустите run.py")
        return

    win = tk.Toplevel(root)
    win.title("История сессий")
    win.geometry("620x420")
    win.configure(bg="#1a1a2e")
    win.resizable(False, False)

    tk.Label(win, text="History",
             font=("Helvetica", 13, "bold"),
             bg="#252545", fg="#ccccff").pack(fill="x", ipady=10)

    frame = tk.Frame(win, bg="#1a1a2e")
    frame.pack(fill="both", expand=True, padx=12, pady=10)

    headers = ["#", "Пользователь", "Хост", "Открыто", "Закрыто", "Длит.(с)"]
    widths   = [30, 110, 110, 145, 145, 70]
    for col, (h, w) in enumerate(zip(headers, widths)):
        tk.Label(frame, text=h, font=("Helvetica", 9, "bold"),
                 bg="#252545", fg="#aaaacc", width=w//7, anchor="w"
                 ).grid(row=0, column=col, padx=2, pady=(0,4), sticky="w")

    scrollbar = tk.Scrollbar(frame)
    scrollbar.grid(row=1, column=len(headers), sticky="ns")

    listbox = tk.Listbox(frame, bg="#1a1a2e", fg="#ddddff",
                         font=("Courier", 9), selectbackground="#3a5acc",
                         highlightthickness=0, bd=0,
                         yscrollcommand=scrollbar.set,
                         height=18)
    listbox.grid(row=1, column=0, columnspan=len(headers), sticky="nsew")
    scrollbar.config(command=listbox.yview)

    if not sessions:
        listbox.insert("end", "  Нет записей")
    for s in sessions:
        dur = str(s["duration_seconds"]) + "с" if s["duration_seconds"] is not None else "—"
        closed = s["closed_at"] or "активна"
        line = (f"  {s['id']:<4} {s['username']:<14} {s['hostname']:<14} "
                f"{s['opened_at']:<20} {closed:<20} {dur}")
        listbox.insert("end", line)

    tk.Button(win, text="Закрыть", font=("Helvetica",10),
              bg="#3a5acc", fg="white", bd=0, relief="flat",
              command=win.destroy).pack(pady=8)


def show_help():
    messagebox.showinfo("Instruction",
        "How to use Weather Bot:\n\n"
        "1. Enter the name of the city\n"
        "2. Click on «Find out the weather» or Enter\n"
        "3. Enjoy the result!\n\n"
        "Examples: Almaty, Moscow, London, Tokyo")

# Интерфейс (UI)

root = tk.Tk()
root.title("Weather Bot")
root.geometry("400x520")
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", on_quit)

canvas = tk.Canvas(root, width=400, height=520, highlightthickness=0)
canvas.place(x=0, y=0)
draw_gradient("#1a1a2e","#16213e")

header = tk.Frame(root, bg="#252545")
header.place(x=0,y=0,width=400,height=58)
tk.Label(header, text="WEATHER BOT", font=("Helvetica",13,"bold"),
         bg="#252545", fg="#ccccff").place(x=0,y=0,width=240,height=58)

#кнопка для истории (Django)
tk.Button(header, text="📋", font=("Helvetica",12),
          bg="#3a3a6a", fg="white", bd=0, relief="flat", cursor="hand2",
          activebackground="#4a4a8a", activeforeground="white",
          command=show_sessions).place(x=310,y=14,width=36,height=30)

tk.Button(header, text="?", font=("Helvetica",12,"bold"),
          bg="#3a3a6a", fg="white", bd=0, relief="flat", cursor="hand2",
          activebackground="#4a4a8a", activeforeground="white",
          command=show_help).place(x=356,y=14,width=30,height=30)

entry_frame = tk.Frame(root, bg="#2a2a4a",
                       highlightthickness=1,
                       highlightbackground="#5555aa",
                       highlightcolor="#8888ff")
entry_frame.place(x=20,y=82,width=360,height=46)
tk.Label(entry_frame, text="🔍", font=("Segoe UI Emoji",13),
         bg="#2a2a4a", fg="#aaaacc").pack(side="left", padx=(12,0))
entry = tk.Entry(entry_frame, font=("Helvetica",13), bd=0, relief="flat",
                 bg="#2a2a4a", fg="#888888", insertbackground="white",
                 highlightthickness=0)
entry.pack(side="left", fill="both", expand=True, padx=10, ipady=6)
entry.insert(0, PLACEHOLDER)
entry.bind("<FocusIn>",  on_focus_in)
entry.bind("<FocusOut>", on_focus_out)
entry.bind("<Return>",   get_weather)

weather_btn = tk.Button(root, text="🚀  Find out the weather",
    font=("Helvetica",12,"bold"), bg="#3a5acc", fg="white",
    bd=0, relief="flat", cursor="hand2",
    activebackground="#2a4abb", activeforeground="white",
    command=get_weather)
weather_btn.place(x=20,y=144,width=270,height=42)

tk.Button(root, text="✕ Quit", font=("Helvetica",11),
          bg="#2a2a4a", fg="#aaaaaa", bd=0, relief="flat", cursor="hand2",
          activebackground="#4a2a2a", activeforeground="white",
          command=on_quit).place(x=300,y=144,width=80,height=42)

result_frame = tk.Frame(root, bg="#252545",
                        highlightthickness=1, highlightbackground="#5555aa")

icon_label = tk.Label(result_frame, text="", font=("Segoe UI Emoji",52),
                      bg="#252545")
icon_label.pack(pady=(16,2))

city_label = tk.Label(result_frame, text="", font=("Helvetica",10,"bold"),
                      bg="#252545", fg="#aaaacc")
city_label.pack()

temp_row = tk.Frame(result_frame, bg="#252545")
temp_row.pack()
temp_label = tk.Label(temp_row, text="", font=("Helvetica",56,"bold"),
                      bg="#252545", fg="white")
temp_label.pack(side="left")
unit_label = tk.Label(temp_row, text="", font=("Helvetica",22),
                      bg="#252545", fg="#aaaacc")
unit_label.pack(side="left", anchor="n", pady=10)

desc_label = tk.Label(result_frame, text="", font=("Helvetica",13),
                      bg="#252545", fg="#ddddff")
desc_label.pack()
feels_label = tk.Label(result_frame, text="", font=("Helvetica",10),
                       bg="#252545", fg="#888888")
feels_label.pack(pady=(2,10))

tk.Frame(result_frame, bg="#5555aa", height=1).pack(fill="x", padx=30)

details_row = tk.Frame(result_frame, bg="#252545")
details_row.pack(pady=12)

def make_detail(parent, icon, label_text):
    col = tk.Frame(parent, bg="#252545")
    col.pack(side="left", padx=24)
    tk.Label(col, text=icon, font=("Segoe UI Emoji",18), bg="#252545").pack()
    val = tk.Label(col, text="—", font=("Helvetica",13,"bold"),
                   bg="#252545", fg="white")
    val.pack()
    tk.Label(col, text=label_text, font=("Helvetica",9),
             bg="#252545", fg="#888888").pack()
    return val

detail_humid = make_detail(details_row, "💧", "humidity")
detail_wind  = make_detail(details_row, "🌬", "wind")

#старт
threading.Thread(target=_session_open, daemon=True).start()

root.mainloop()
