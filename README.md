# ⚡ Process Guardian - Ultimate Edition

**Process Guardian** is a lightweight, robust, and modern process monitoring tool written in Python. It ensures your critical applications (servers, scripts, games) stay running 24/7 by automatically detecting crashes, closures, or "Not Responding" states.

## ✨ Features

* **🔄 Auto-Restart:** Immediately restarts applications if they crash or close.
* **🧠 Smart Monitoring:** Detects "Not Responding" (hanging) and Zombie processes.
* **⏬ Widget Mode:** Minimizes to a floating desktop widget (System Tray alternative).
* **📋 Event Logging:** Keeps a detailed history of all crashes and restarts.
* **🚀 Launch Arguments:** Supports passing custom arguments to executables.
* **💾 Persistence:** Saves your configuration automatically.
* **🔝 Always on Top:** Keeps the monitoring dashboard visible.
* **⚡ Lightweight:** Built with `tkinter` and `psutil` for minimal resource usage.

## 📥 Installation

### Option 1: Download Executable (Recommended for Users)
Go to the [Releases](../../releases) page and download the latest `ProcessGuardian.exe`. No Python installation required!

### Option 2: Run from Source (For Developers)

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/Process-Guardian.git](https://github.com/YOUR_USERNAME/Process-Guardian.git)
    cd Process-Guardian
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    python process_guardian.py
    ```

## 🛠 How to Use

1.  Click **"➕ Add"** to select an `.exe` file you want to monitor.
2.  (Optional) Add launch arguments (e.g., `--server --port 8080`).
3.  Set the check interval (default is 5 seconds).
4.  Click **"▶ Start All"** to begin monitoring.
5.  If you close the main window, you can choose to minimize it to a **Floating Widget** to keep it running in the background.

## 📦 Building the Exe

If you want to build the executable yourself:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name="ProcessGuardian" process_guardian.py