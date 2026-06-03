# 智能断点续传助手 (Smart Breakpoint Resumer)

轻量级 Windows 本地工具，一键记录工作断点，智能兜底提醒。

## 功能

- 一键抓取当前活跃窗口标题 + 剪贴板内容
- 10 分钟后台静默监听键鼠操作，自动判断是否已回归
- 未回归时弹出系统 Toast 通知提醒
- 可通过桌面快捷方式或全局快捷键 `Ctrl + Alt + B` 触发

## 环境搭建

### 1. 安装 Python 3

从 https://www.python.org/downloads/ 下载安装，安装时勾选 **"Add Python to PATH"**。

### 2. 安装依赖

在项目目录下打开终端，执行：

```batch
pip install -r requirements.txt
```

或使用虚拟环境（推荐）：

```batch
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 使用方式

### 双击运行

双击 `启动断点助手.bat` 即可运行。

### 设置全局快捷键 (Ctrl + Alt + B)

1. 右键点击 `启动断点助手.bat` → **发送到 → 桌面快捷方式**
2. 右键桌面新生成的快捷方式 → **属性**
3. 在 **快捷键** 输入框中按下 `Ctrl + Alt + B`
4. 点击确定

之后在任何时候按下 `Ctrl + Alt + B` 即可触发记录。

### 开机自启

1. 按 `Win + R`，输入 `shell:startup`，回车
2. 将 `启动断点助手.bat` 的快捷方式复制到打开的文件夹中

## 测试方法

1. 打开任意窗口（如记事本、浏览器）
2. 按下 `Ctrl + Alt + B` 或双击快捷方式
3. 观察命令行输出：应显示当前窗口标题
4. 保持 10 分钟不动（或按 Ctrl+C 提前退出测试）
5. 若 10 分钟内无操作，右下角会弹出系统通知

## 文件结构

```
SmartBreakpointResumer/
├── breakpoint_resumer.py    # 主程序
├── requirements.txt         # 依赖清单
├── 启动断点助手.bat          # 一键启动脚本
└── README.md                # 本说明文件
```

## 日志

运行日志保存在同目录下的 `breakpoint_resumer.log` 文件中。
