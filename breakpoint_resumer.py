import sys
import os
import time
import threading
import logging
import re
import subprocess
import argparse
import json
import uuid
from datetime import datetime

import win32gui
import win32con
import win32clipboard
from pynput import keyboard, mouse
from plyer import notification
from PIL import ImageGrab

try:
    import tkinter as tk
    from tkinter import font as tkfont
    _HAS_TK = True
except ImportError:
    _HAS_TK = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("breakpoint_resumer.log", encoding="utf-8"), logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

SILENT_TIMEOUT = 600
REMINDER_INTERVAL = 120
POLL_INTERVAL = 0.5
STARTUP_GRACE = 3

is_active = False
stop_listener = False
window_title = ""
clipboard_text = ""
screenshot_path = ""
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
RECORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.json")
_last_screenshot_proc = threading.local()
dismiss_event = threading.Event()

def safe_print(*args, **kwargs):
    text = " ".join(str(a) for a in args)
    text = re.sub(r'[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', text)
    try:
        print(text, **kwargs, flush=True)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("gbk", errors="replace"), **kwargs, flush=True)

def load_records():
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                item.setdefault("completed", False)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_records(records):
    os.makedirs(os.path.dirname(RECORDS_FILE), exist_ok=True)
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def add_record(window_title, clipboard_text, screenshot_path):
    records = load_records()
    record = {
        "id": str(uuid.uuid4()),
        "window_title": window_title,
        "clipboard": clipboard_text or "",
        "screenshot_path": screenshot_path or "",
        "timestamp": datetime.now().strftime("%m-%d %H:%M"),
        "completed": False,
    }
    records.insert(0, record)
    save_records(records)
    logger.info(f"断点已保存: {window_title}")
    return record

def get_active_window_title():
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        return title.strip() or "未知窗口"
    except Exception as e:
        logger.warning(f"获取窗口标题失败: {e}")
        return "未知窗口"

def take_screenshot():
    global screenshot_path
    try:
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"breakpoint_{ts}.png"
        path = os.path.join(SCREENSHOTS_DIR, filename)
        img = ImageGrab.grab(all_screens=True)
        img.save(path, "PNG")
        screenshot_path = path
        logger.info(f"截图已保存: {path}")
        return path
    except Exception as e:
        logger.warning(f"截图失败: {e}")
        return None

def get_clipboard_text():
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            return data.strip() if data else None
        return None
    except Exception as e:
        logger.debug(f"读取剪贴板失败: {e}")
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass

def on_activity():
    global is_active, stop_listener
    if not is_active:
        is_active = True
        logger.info("检测到用户操作，任务将自动取消")
        stop_listener = True
    return False

def on_key_press(key):
    return on_activity()

def on_mouse_click(x, y, button, pressed):
    return on_activity()

def on_mouse_scroll(x, y, dx, dy):
    return on_activity()

def monitor_user_activity():
    global stop_listener
    keyboard_listener = keyboard.Listener(on_press=on_key_press)
    mouse_listener = mouse.Listener(on_click=on_mouse_click, on_scroll=on_mouse_scroll)

    keyboard_listener.start()
    mouse_listener.start()

    keyboard_listener.wait()
    mouse_listener.wait()

    keyboard_listener.stop()
    mouse_listener.stop()

def show_toast_notification(window_title, clipboard_text=None, n=1):
    try:
        msgs = [f"刚才你正在处理【{window_title}】时被中断了"]
        if clipboard_text:
            msgs.append(f"剪贴板: {clipboard_text[:50]}……")
        msgs.append("建议现在回去看看哦。")
        msg = "\n".join(msgs)
        notification.notify(
            title="断点恢复提醒" if n == 1 else f"断点恢复提醒 (第{n}次)",
            message=msg,
            timeout=20,
        )
        logger.info(f"已发送第{n}次提醒：{msg}")
        open_screenshot()
    except Exception as e:
        logger.warning(f"Toast 弹窗失败: {e}，使用命令行提醒")
        safe_print("\n" + "=" * 60)
        safe_print(f"断点恢复提醒 (第{n}次)")
        safe_print(f"刚才你正在处理【{window_title}】时被中断了，建议现在回去看看哦。")
        safe_print("=" * 60)
        open_screenshot()

def wait_silent_phase():
    for remaining in range(SILENT_TIMEOUT, 0, -1):
        if stop_listener:
            return
        if remaining % 60 == 0 or remaining <= 10:
            mins, secs = divmod(remaining, 60)
            logger.info(f"静默倒计时: {mins:02d}:{secs:02d}")
        time.sleep(1)

def wait_reminder_phase():
    n = 0
    while not dismiss_event.is_set():
        n += 1
        show_toast_notification(window_title, clipboard_text, n)
        for _ in range(REMINDER_INTERVAL):
            if dismiss_event.is_set():
                return
            time.sleep(1)

def close_current_screenshot():
    proc = getattr(_last_screenshot_proc, 'handle', None)
    if proc is not None:
        try:
            proc.kill()
            logger.info("已关闭截图")
        except Exception:
            pass

def open_screenshot():
    global screenshot_path
    if screenshot_path and os.path.exists(screenshot_path):
        try:
            close_current_screenshot()
            abs_path = os.path.abspath(screenshot_path)
            proc = subprocess.Popen(['cmd.exe', '/c', 'start', '', abs_path], shell=False)
            _last_screenshot_proc.handle = proc
            logger.info(f"已打开截图: {abs_path}")
        except Exception as e:
            logger.warning(f"打开截图失败: {e}")

def capture_and_monitor():
    global is_active, stop_listener, window_title, clipboard_text, screenshot_path

    dismiss_event.clear()
    is_active = False
    stop_listener = False
    screenshot_path = ""

    window_title = get_active_window_title()

    take_screenshot()
    logger.info(f"当前窗口标题: {window_title}")

    clipboard_text = get_clipboard_text()
    if clipboard_text:
        logger.info(f"剪贴板内容: {clipboard_text[:100]}")

    add_record(window_title, clipboard_text, screenshot_path)

    safe_print(f"\n已记录断点")
    safe_print(f"   窗口: {window_title}")
    if clipboard_text:
        safe_print(f"   剪贴板: {clipboard_text[:50]}{'...' if len(clipboard_text) > 50 else ''}")
    if screenshot_path:
        safe_print(f"   截图: {screenshot_path}")

    try:
        notification.notify(
            title="断点已记录",
            message=f"正在处理：【{window_title[:30]}】\n已开始 10 分钟静默监听",
            timeout=3,
        )
    except Exception:
        pass

    safe_print(f"\n开始静默监听 {SILENT_TIMEOUT} 秒，检测到键鼠操作将自动取消...")
    safe_print(f"   按 Ctrl+C 可手动退出\n")

    monitor_thread = threading.Thread(target=monitor_user_activity, daemon=True)
    monitor_thread.start()

    time.sleep(STARTUP_GRACE)
    if is_active:
        logger.info("启动阶段检测到活动，可能为误触，重置状态")
        is_active = False
        stop_listener = False
        monitor_thread = threading.Thread(target=monitor_user_activity, daemon=True)
        monitor_thread.start()

    wait_silent_phase()

    if is_active or dismiss_event.is_set():
        logger.info("用户已回归，任务自动取消，不发送提醒")
        safe_print("\n检测到您已回归，任务已自动取消。")
        return

    logger.info("用户未回归，进入持续提醒阶段")
    safe_print(f"\n静默期结束，将持续提醒直到您确认回归（按 Ctrl+Alt+D 解除提醒）...")
    safe_print(f"   注意：提醒期间普通键鼠操作不会关闭提醒")
    safe_print(f"   按 Ctrl+C 可手动退出\n")

    wait_reminder_phase()

    close_current_screenshot()
    logger.info("用户已确认回归，提醒解除")
    safe_print("\n已解除提醒，您可以继续工作了。")

    try:
        notification.notify(
            title="提醒已解除",
            message="已确认您已回归，祝工作顺利！",
            timeout=3,
        )
    except Exception:
        pass

def open_task_list():
    if not _HAS_TK:
        logger.warning("Tkinter 不可用，无法打开任务清单界面")
        safe_print("错误：系统缺少 Tkinter 支持，无法打开任务清单")
        return
    t = threading.Thread(target=_task_list_ui, daemon=True)
    t.start()

def _task_list_ui():
    root = tk.Tk()
    root.title("断点恢复清单")
    root.geometry("520x480")
    root.minsize(380, 300)

    BG = "#f3f3f3"
    CARD = "#ffffff"
    ACCENT = "#2564cf"
    BORDER = "#e0e0e0"
    root.configure(bg=BG)

    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    header = tk.Frame(root, bg=ACCENT, height=46)
    header.pack(fill=tk.X)

    tk.Label(header, text="  断点恢复清单", bg=ACCENT, fg="white",
             font=("Segoe UI", 15, "bold")).pack(side=tk.LEFT, padx=12, pady=8)

    c = tk.Frame(root, bg=BG)
    c.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(c, bg=BG, highlightthickness=0)
    scrollbar = tk.Scrollbar(c, orient=tk.VERTICAL, command=canvas.yview)
    scrollable = tk.Frame(canvas, bg=BG)

    scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * event.delta / 120), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def rebuild():
        for w in scrollable.winfo_children():
            w.destroy()

        records = load_records()
        if not records:
            tk.Label(scrollable, text="暂无断点记录\n按 Ctrl+Alt+B 记录工作断点",
                     bg=BG, fg="#888", font=("Segoe UI", 12)).pack(pady=40)
            return

        for i, rec in enumerate(records):
            pady_b = (0, 6) if i < len(records) - 1 else (0, 12)

            card = tk.Frame(scrollable, bg=CARD, highlightbackground=BORDER, highlightthickness=1, relief=tk.FLAT)
            card.pack(fill=tk.X, padx=12, pady=pady_b)

            done = rec.get("completed", False)

            ck = tk.Canvas(card, width=24, height=24, bg=CARD, highlightthickness=0)
            ck.pack(side=tk.LEFT, padx=(14, 8), pady=12)

            if done:
                ck.create_oval(2, 2, 22, 22, fill=ACCENT, outline=ACCENT, width=2)
                ck.create_text(12, 12, text="✓", fill="white", font=("Segoe UI", 11, "bold"))
            else:
                ck.create_oval(2, 2, 22, 22, fill="", outline="#bbb", width=2)

            body = tk.Frame(card, bg=CARD)
            body.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=10)

            title_font = ("Segoe UI", 12, "overstrike" if done else "normal")
            title_fg = "#aaa" if done else "#222"
            tk.Label(body, text=rec.get("window_title", ""), font=title_font,
                     fg=title_fg, bg=CARD, anchor="w", wraplength=340).pack(fill=tk.X)

            detail = rec.get("timestamp", "")
            clip = rec.get("clipboard", "")
            if clip:
                detail += f"  剪贴板: {clip[:40]}{'...' if len(clip) > 40 else ''}"
            tk.Label(body, text=detail, font=("Segoe UI", 9), fg="#888",
                     bg=CARD, anchor="w").pack(fill=tk.X)

            sp = rec.get("screenshot_path", "")
            if sp and os.path.exists(sp):
                btn = tk.Label(card, text="🖼", font=("Segoe UI", 16), bg=CARD, fg="#888", cursor="hand2")
                btn.pack(side=tk.RIGHT, padx=(0, 14))
                def open_shot(p=sp):
                    subprocess.Popen(['cmd.exe', '/c', 'start', '', os.path.abspath(p)], shell=False)
                btn.bind("<Button-1>", lambda e, p=sp: open_shot(p))
                btn.bind("<Enter>", lambda e: btn.configure(fg=ACCENT))
                btn.bind("<Leave>", lambda e: btn.configure(fg="#888"))

            def toggle(r=rec):
                records2 = load_records()
                for rr in records2:
                    if rr["id"] == r["id"]:
                        rr["completed"] = not rr.get("completed", False)
                        break
                save_records(records2)
                rebuild()

            ck.bind("<Button-1>", lambda e, r=rec: toggle(r))
            card.bind("<Button-1>", lambda e, r=rec: toggle(r))
            body.bind("<Button-1>", lambda e, r=rec: toggle(r))

    rebuild()
    root.mainloop()

def run_single():
    capture_and_monitor()

def on_dismiss():
    logger.info("用户按下 Ctrl+Alt+D，解除提醒")
    dismiss_event.set()

def run_daemon():
    safe_print("后台监听模式启动中...")
    safe_print("   Ctrl+Alt+B  记录断点")
    safe_print("   Ctrl+Alt+D  解除当前提醒")
    safe_print("   Ctrl+Alt+T  打开断点待办清单")
    safe_print("   按 Ctrl+C 可退出\n")
    logger.info("后台监听模式启动")

    hotkey = keyboard.GlobalHotKeys({
        '<ctrl>+<alt>+b': lambda: threading.Thread(target=capture_and_monitor, daemon=True).start(),
        '<ctrl>+<alt>+d': on_dismiss,
        '<ctrl>+<alt>+t': open_task_list,
    })
    hotkey.start()
    hotkey.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="智能断点续传助手")
    parser.add_argument("--listen", action="store_true", help="后台监听模式，注册全局快捷键 Ctrl+Alt+B")
    args = parser.parse_args()

    try:
        if args.listen:
            run_daemon()
        else:
            run_single()
    except KeyboardInterrupt:
        safe_print("\n\n已手动退出。")
        logger.info("用户手动退出")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"程序异常: {e}")
        sys.exit(1)
