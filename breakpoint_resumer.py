import sys
import os
import time
import threading
import logging
import re
import subprocess
import argparse
from datetime import datetime

import win32gui
import win32con
import win32clipboard
from pynput import keyboard, mouse
from plyer import notification
from PIL import ImageGrab

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

def safe_print(*args, **kwargs):
    text = " ".join(str(a) for a in args)
    text = re.sub(r'[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', text)
    try:
        print(text, **kwargs, flush=True)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("gbk", errors="replace"), **kwargs, flush=True)

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
    while not stop_listener:
        n += 1
        show_toast_notification(window_title, clipboard_text, n)
        for _ in range(REMINDER_INTERVAL):
            if stop_listener:
                return
            time.sleep(1)

def open_screenshot():
    if screenshot_path and os.path.exists(screenshot_path):
        try:
            abs_path = os.path.abspath(screenshot_path)
            subprocess.Popen(['cmd.exe', '/c', 'start', '', abs_path], shell=False)
            logger.info(f"已打开截图: {abs_path}")
        except Exception as e:
            logger.warning(f"打开截图失败: {e}")

def capture_and_monitor():
    global is_active, stop_listener, window_title, clipboard_text, screenshot_path

    is_active = False
    stop_listener = False
    screenshot_path = ""

    window_title = get_active_window_title()

    take_screenshot()
    logger.info(f"当前窗口标题: {window_title}")

    clipboard_text = get_clipboard_text()
    if clipboard_text:
        logger.info(f"剪贴板内容: {clipboard_text[:100]}")

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

    if is_active:
        logger.info("用户已回归，任务自动取消，不发送提醒")
        safe_print("\n检测到您已回归，任务已自动取消。")
        return

    logger.info("用户未回归，进入持续提醒阶段")
    safe_print("\n静默期结束，将持续提醒直到检测到您回归...")
    safe_print("   按 Ctrl+C 可手动退出\n")

    wait_reminder_phase()

    open_screenshot()
    logger.info("用户已回归，提醒终止")
    safe_print("\n检测到您已回归，提醒已终止。")
    safe_print(f"   当时截图已打开: {screenshot_path}")

def run_single():
    capture_and_monitor()

def run_daemon():
    safe_print("后台监听模式启动中，按 Ctrl+Alt+B 触发断点记录...")
    safe_print("   按 Ctrl+C 可退出\n")
    logger.info("后台监听模式启动")

    hotkey = keyboard.GlobalHotKeys({
        '<ctrl>+<alt>+b': lambda: threading.Thread(target=capture_and_monitor, daemon=True).start()
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
