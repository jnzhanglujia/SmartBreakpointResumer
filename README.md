# 智能断点续传助手 / Smart Breakpoint Resumer

> 一键记录工作断点，截屏保存现场，智能兜底持续提醒，直到你回来。
> One-key breakpoint recording, screenshot preservation, and persistent smart reminders until you return.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-brightgreen)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🇨🇳 中文说明

### 项目简介

工作中经常被电话、会议或突发事件打断，回来后却忘了刚才在做什么。**智能断点续传助手** 是一个轻量级 Windows 本地工具，帮你解决这个问题。

按下 `Ctrl + Alt + B`（或双击快捷方式），它会立即：

1. **抓取当前窗口标题** — 记录你在做什么
2. **读取剪贴板内容** — 保留关键信息
3. **截取全屏画面** — 保存完整的视觉现场

然后进入 10 分钟静默监听：

- **你回来了**（有键鼠操作）→ 自动静默取消，不打扰
- **你没回来** → 每 2 分钟弹一次 Toast 通知 + 自动打开当时截图，直到你回来为止

### 快速开始

#### 1️⃣ 安装 Python 3

从 [python.org](https://www.python.org/downloads/) 下载安装，安装时勾选 **"Add Python to PATH"**。

#### 2️⃣ 安装依赖

```batch
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

#### 3️⃣ 启动方式

**方式 A — 后台常驻（推荐）**

双击 `启动后台监听.bat`（一闪而过，无窗口残留），然后按 `Ctrl + Alt + B` 随时触发。

**方式 B — 单次触发**

双击 `启动断点助手.bat`，立即记录并开始监听。

### 验证是否生效

- 按 `Ctrl + Alt + B` → 右下角弹出「断点已记录」通知
- 查看 `screenshots/` 目录：有新的 `.png` 截图文件即成功

### 开机自启

1. `Win + R` → 输入 `shell:startup` → 回车
2. 将 `启动后台监听.bat` 的快捷方式拖入该文件夹

### 文件结构

```
SmartBreakpointResumer/
├── breakpoint_resumer.py    # 主程序
├── requirements.txt         # 依赖清单
├── daemon.ps1               # PowerShell 后台启动脚本
├── 启动后台监听.bat          # 后台常驻入口（推荐）
├── 启动断点助手.bat          # 单次触发入口
├── screenshots/             # 截图保存目录（自动创建）
└── README.md                # 本说明文件
```

### 日志

运行日志保存在 `breakpoint_resumer.log`（UTF-8 编码）。

---

## 🇬🇧 English Guide

### Overview

Ever been pulled away by a phone call or an urgent meeting, only to return and completely forget what you were working on? **Smart Breakpoint Resumer** is a lightweight Windows utility that solves this.

Press `Ctrl + Alt + B` (or double-click the launcher), and it instantly:

1. **Captures the active window title** — records your current task
2. **Reads clipboard content** — preserves key information
3. **Takes a full-screen screenshot** — saves the complete visual context

Then enters a 10-minute silent monitoring phase:

- **You return** (keyboard/mouse activity detected) → silently cancels, no interruption
- **You don't return** → fires a Toast notification every 2 minutes + opens the screenshot, until you're back

### Quick Start

#### 1️⃣ Install Python 3

Download from [python.org](https://www.python.org/downloads/), make sure to check **"Add Python to PATH"**.

#### 2️⃣ Install Dependencies

```batch
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

#### 3️⃣ Launch

**Option A — Background Mode (Recommended)**

Double-click `启动后台监听.bat` (flashes once, no window remains), then press `Ctrl + Alt + B` anytime.

**Option B — Single Shot**

Double-click `启动断点助手.bat` to capture and monitor immediately.

### Verification

- Press `Ctrl + Alt + B` → a "Breakpoint Recorded" Toast notification appears
- Check the `screenshots/` folder for a new `.png` file

### Auto-start on Boot

1. `Win + R` → type `shell:startup` → Enter
2. Drag a shortcut of `启动后台监听.bat` into the folder

### File Structure

```
SmartBreakpointResumer/
├── breakpoint_resumer.py    # Main program
├── requirements.txt         # Dependencies list
├── daemon.ps1               # PowerShell background launcher
├── 启动后台监听.bat          # Background mode entry (recommended)
├── 启动断点助手.bat          # Single-shot entry
├── screenshots/             # Screenshot storage (auto-created)
└── README.md                # This file
```

### Logs

Logs are written to `breakpoint_resumer.log` (UTF-8 encoding).
