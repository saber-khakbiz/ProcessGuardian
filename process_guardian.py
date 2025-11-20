import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font, scrolledtext
import subprocess
import psutil
import threading
import time
import os
import json
from pathlib import Path
import sys
import logging
import shlex # Added for security

# Setup logging system
logging.basicConfig(
    filename='guardian_events.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class FloatingWidget:
    """Class to create a small floating widget when the app is minimized"""
    def __init__(self, root, restore_callback):
        self.root = root
        self.restore_callback = restore_callback
        self.widget = tk.Toplevel(root)
        self.widget.overrideredirect(True) # Remove window border
        self.widget.attributes('-topmost', True)
        self.widget.geometry("60x60+50+50")
        self.widget.configure(bg="#1e1e2e")
        
        # Create round icon
        self.canvas = tk.Canvas(self.widget, width=60, height=60, bg="#1e1e2e", highlightthickness=0)
        self.canvas.pack()
        
        # Draw circle and text
        self.canvas.create_oval(5, 5, 55, 55, fill="#89b4fa", outline="#cdd6f4", width=2)
        self.canvas.create_text(30, 30, text="⚡", font=("Segoe UI", 24))
        
        # Enable widget dragging
        self.widget.bind("<Button-1>", self.start_move)
        self.widget.bind("<B1-Motion>", self.do_move)
        self.widget.bind("<Double-Button-1>", lambda e: self.restore())
        
        # Simple tooltip
        self.widget.bind("<Enter>", lambda e: self.widget.configure(cursor="hand2"))
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.widget.winfo_x() + deltax
        y = self.widget.winfo_y() + deltay
        self.widget.geometry(f"+{x}+{y}")

    def restore(self):
        self.widget.destroy()
        self.restore_callback()

class ModernProcessMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Process Guardian - Ultimate Edition")
        self.root.geometry("800x550") 
        self.root.resizable(True, False)
        
        # Keep window always on top
        self.root.attributes('-topmost', True)
        
        # Modern color scheme
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.success_color = "#a6e3a1"
        self.warning_color = "#f9e2af"
        self.error_color = "#f38ba8"
        self.save_color = "#cba6f7"
        self.info_color = "#f5c2e7"
        self.log_color = "#fab387"
        self.card_bg = "#313244"
        
        self.root.configure(bg=self.bg_color)
        
        # Application variables
        self.monitoring = False
        self.monitor_threads = {}
        self.processes = []
        self.config_file = "guardian_config.json"
        self.floating_widget = None
        
        # Load previous settings
        self.load_config()
        
        # Create GUI
        self.create_modern_widgets()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto-start monitoring if configured
        if self.processes:
            self.root.after(1000, self.auto_start_monitoring)
            logging.info("Application started with auto-monitoring.")

    def create_modern_widgets(self):
        # Custom fonts
        title_font = font.Font(family="Segoe UI", size=20, weight="bold")
        header_font = font.Font(family="Segoe UI", size=10, weight="bold")
        normal_font = font.Font(family="Segoe UI", size=9)
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 1. Title section
        title_frame = tk.Frame(main_container, bg=self.bg_color)
        title_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            title_frame, text="⚡ Process Guardian", font=title_font,
            bg=self.bg_color, fg=self.accent_color
        )
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(
            title_frame, text="Auto-Recovery & Smart Monitoring",
            font=("Segoe UI", 9), bg=self.bg_color, fg=self.fg_color
        )
        subtitle_label.pack(side=tk.LEFT, padx=10)
        
        # 2. Status bar
        status_bar = tk.Frame(main_container, bg=self.card_bg)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self.status_label = tk.Label(
            status_bar, text="Ready", font=normal_font,
            bg=self.card_bg, fg=self.fg_color, anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=15, pady=8)
        
        # 3. Control panel
        control_frame = tk.Frame(main_container, bg=self.card_bg, relief=tk.FLAT)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))
        
        inner_control = tk.Frame(control_frame, bg=self.card_bg)
        inner_control.pack(fill=tk.X, padx=10, pady=15)
        
        # Left Side Buttons
        self.create_btn(inner_control, "➕ Add", self.add_process_dialog, self.accent_color, header_font)
        self.create_btn(inner_control, "💾 Save", self.manual_save_config, self.save_color, header_font)
        self.create_btn(inner_control, "📋 Logs", self.show_logs_dialog, self.log_color, header_font)
        self.start_all_btn = self.create_btn(inner_control, "▶ Start All", self.start_all_monitoring, self.success_color, header_font)
        self.stop_all_btn = self.create_btn(inner_control, "⏸ Stop All", self.stop_all_monitoring, self.error_color, header_font, state=tk.DISABLED)
        
        # Right Side Buttons
        about_btn = tk.Button(
            inner_control, text="ℹ About", command=self.show_about_dialog,
            bg=self.info_color, fg="#000000", font=normal_font, relief=tk.FLAT,
            padx=10, pady=8, cursor="hand2"
        )
        about_btn.pack(side=tk.RIGHT, padx=2)
        
        startup_btn = tk.Button(
            inner_control, text="🚀 Startup", command=self.add_to_startup,
            bg=self.warning_color, fg="#000000", font=normal_font, relief=tk.FLAT,
            padx=10, pady=8, cursor="hand2"
        )
        startup_btn.pack(side=tk.RIGHT, padx=2)

        # 4. Process list
        list_container = tk.Frame(main_container, bg=self.bg_color)
        list_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(list_container, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.process_list_frame = tk.Frame(canvas, bg=self.bg_color)
        
        self.process_list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.process_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_process_list()

    def create_btn(self, parent, text, cmd, bg, font, state=tk.NORMAL):
        btn = tk.Button(parent, text=text, command=cmd, bg=bg, fg="#000000", font=font, relief=tk.FLAT, padx=12, pady=8, cursor="hand2", state=state)
        btn.pack(side=tk.LEFT, padx=3)
        return btn

    def show_logs_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Event Logs")
        dialog.geometry("600x400")
        dialog.configure(bg=self.bg_color)
        dialog.attributes('-topmost', True)
        
        log_area = scrolledtext.ScrolledText(dialog, width=70, height=20, font=("Consolas", 9), bg=self.card_bg, fg=self.fg_color)
        log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            if os.path.exists('guardian_events.log'):
                with open('guardian_events.log', 'r') as f:
                    log_area.insert(tk.END, f.read())
            else:
                log_area.insert(tk.END, "No logs found yet.")
        except Exception as e:
            log_area.insert(tk.END, f"Error reading logs: {e}")
            
        log_area.configure(state='disabled')

    def manual_save_config(self):
        self.save_config()
        messagebox.showinfo("Saved", "Configuration saved successfully!")

    def show_about_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("About")
        dialog.geometry("360x400") # Corrected Dimensions
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = tk.Frame(dialog, bg=self.bg_color)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(frame, text="⚡", font=("Segoe UI", 48), bg=self.bg_color, fg=self.accent_color).pack(pady=(5, 0))
        tk.Label(frame, text="Process Guardian", font=("Segoe UI", 16, "bold"), bg=self.bg_color, fg=self.fg_color).pack(pady=5)
        tk.Label(frame, text="Version 2.0 (Ultimate)", font=("Segoe UI", 10), bg=self.bg_color, fg=self.warning_color).pack()
        tk.Label(frame, text="Features:\n• Auto-Restart & Crash Detection\n• 'Not Responding' Check\n• Event Logging\n• Smart Widget Mode", font=("Segoe UI", 9), bg=self.bg_color, fg=self.fg_color, justify=tk.CENTER).pack(pady=15)
        
        # Developer info at bottom
        tk.Label(frame, text="Developed by: Saber Khakbiz", font=("Segoe UI", 9, "bold"), bg=self.bg_color, fg=self.info_color).pack(side=tk.BOTTOM, pady=5)
        tk.Button(frame, text="Close", command=dialog.destroy, bg=self.card_bg, fg=self.fg_color, relief=tk.FLAT, cursor="hand2").pack(side=tk.BOTTOM, pady=5)

    def add_process_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Process")
        dialog.geometry("550x400")
        dialog.configure(bg=self.bg_color)
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = tk.Frame(dialog, bg=self.bg_color)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        def create_row(label_text, row):
            tk.Label(frame, text=label_text, bg=self.bg_color, fg=self.fg_color).grid(row=row, column=0, sticky=tk.W, pady=5)
            var = tk.StringVar()
            entry = tk.Entry(frame, textvariable=var, width=40, bg=self.card_bg, fg=self.fg_color, insertbackground=self.fg_color)
            entry.grid(row=row, column=1, padx=5, pady=5)
            return var, entry
            
        path_var, path_entry = create_row("App Path:", 0)
        def browse():
            filename = filedialog.askopenfilename(title="Select Executable", filetypes=(("Exe files", "*.exe"), ("All files", "*.*")))
            if filename:
                path_var.set(filename)
                name_var.set(Path(filename).name)
        tk.Button(frame, text="Browse", command=browse, bg=self.accent_color, fg="#000000", relief=tk.FLAT, cursor="hand2").grid(row=0, column=2, padx=5)
        
        name_var, _ = create_row("Process Name:", 1)
        
        args_var, _ = create_row("Arguments (Optional):", 2)
        tk.Label(frame, text="(e.g. --server --port 8080)", font=("Segoe UI", 7), bg=self.bg_color, fg=self.warning_color).grid(row=3, column=1, sticky=tk.W)
        
        icon_var, _ = create_row("Icon (emoji):", 4)
        icon_var.set("🔵")
        
        tk.Label(frame, text="Check Interval (sec):", bg=self.bg_color, fg=self.fg_color).grid(row=5, column=0, sticky=tk.W, pady=5)
        interval_var = tk.IntVar(value=5)
        tk.Spinbox(frame, from_=1, to=60, textvariable=interval_var, width=38, bg=self.card_bg, fg=self.fg_color).grid(row=5, column=1, padx=5, pady=5)
        
        def save():
            path = path_var.get()
            name = name_var.get()
            if not path or not name:
                messagebox.showerror("Error", "Path and Name are required!")
                return
            if not os.path.exists(path):
                messagebox.showerror("Error", "File not found!")
                return
            
            process_info = {
                "path": path,
                "name": name,
                "args": args_var.get(),
                "icon": icon_var.get(),
                "interval": interval_var.get(),
                "enabled": True,
                "restart_count": 0
            }
            self.processes.append(process_info)
            self.save_config()
            self.refresh_process_list()
            logging.info(f"Added new process configuration: {name}")
            dialog.destroy()
        
        btn_frame = tk.Frame(frame, bg=self.bg_color)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=20)
        tk.Button(btn_frame, text="Add Process", command=save, bg=self.success_color, fg="#000000", relief=tk.FLAT, padx=20, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg=self.error_color, fg="#000000", relief=tk.FLAT, padx=20, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=5)

    def refresh_process_list(self):
        for widget in self.process_list_frame.winfo_children():
            widget.destroy()
        if not self.processes:
            tk.Label(self.process_list_frame, text="No processes. Click 'Add' to start.", font=("Segoe UI", 11), bg=self.bg_color, fg=self.fg_color).pack(pady=50)
            return
        for idx, proc in enumerate(self.processes):
            self.create_process_card(idx, proc)

    def create_process_card(self, idx, proc):
        card = tk.Frame(self.process_list_frame, bg=self.card_bg, relief=tk.FLAT)
        card.pack(fill=tk.X, pady=5, padx=5)
        
        inner = tk.Frame(card, bg=self.card_bg)
        inner.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(inner, text=proc.get("icon", "🔵"), font=("Segoe UI", 24), bg=self.card_bg).pack(side=tk.LEFT, padx=(0, 15))
        
        info_frame = tk.Frame(inner, bg=self.card_bg)
        info_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(info_frame, text=proc["name"], font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.fg_color, anchor=tk.W).pack(anchor=tk.W)
        
        args_display = f"Args: {proc.get('args')}" if proc.get('args') else ""
        tk.Label(info_frame, text=f"{proc['path']} {args_display}", font=("Segoe UI", 8), bg=self.card_bg, fg=self.fg_color, anchor=tk.W).pack(anchor=tk.W)
        
        stats_frame = tk.Frame(info_frame, bg=self.card_bg)
        stats_frame.pack(anchor=tk.W, pady=(5, 0))
        
        status_var = tk.StringVar(value="⚫ Not Running")
        tk.Label(stats_frame, textvariable=status_var, font=("Segoe UI", 9), bg=self.card_bg, fg=self.warning_color).pack(side=tk.LEFT, padx=(0, 10))
        
        cpu_var = tk.StringVar(value="CPU: 0%")
        tk.Label(stats_frame, textvariable=cpu_var, font=("Segoe UI", 9), bg=self.card_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=(0, 10))
        
        ram_var = tk.StringVar(value="RAM: 0 MB")
        tk.Label(stats_frame, textvariable=ram_var, font=("Segoe UI", 9), bg=self.card_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=(0, 10))
        
        restart_var = tk.StringVar(value=f"Restarts: {proc.get('restart_count', 0)}")
        tk.Label(stats_frame, textvariable=restart_var, font=("Segoe UI", 9), bg=self.card_bg, fg=self.accent_color).pack(side=tk.LEFT)
        
        proc["status_var"] = status_var
        proc["cpu_var"] = cpu_var
        proc["ram_var"] = ram_var
        proc["restart_var"] = restart_var
        
        right = tk.Frame(inner, bg=self.card_bg)
        right.pack(side=tk.RIGHT)
        
        def toggle():
            if idx in self.monitor_threads: self.stop_monitoring_process(idx)
            else: self.start_monitoring_process(idx)
            
        toggle_btn = tk.Button(right, text="▶ Start", command=toggle, bg=self.success_color, fg="#000000", relief=tk.FLAT, padx=15, pady=8, cursor="hand2")
        toggle_btn.pack(side=tk.LEFT, padx=5)
        proc["toggle_btn"] = toggle_btn
        
        def remove():
            if idx in self.monitor_threads: self.stop_monitoring_process(idx)
            self.processes.pop(idx)
            self.save_config()
            self.refresh_process_list()
            
        tk.Button(right, text="🗑", command=remove, bg=self.error_color, fg="#000000", relief=tk.FLAT, padx=12, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=5)

    def start_monitoring_process(self, idx):
        if idx >= len(self.processes): return
        proc = self.processes[idx]
        proc["monitoring"] = True
        thread = threading.Thread(target=self.monitor_process, args=(idx,), daemon=True)
        thread.start()
        self.monitor_threads[idx] = thread
        if "toggle_btn" in proc: proc["toggle_btn"].config(text="⏸ Stop", bg=self.error_color)
        self.update_status()
        logging.info(f"Started monitoring: {proc['name']}")

    def stop_monitoring_process(self, idx):
        if idx >= len(self.processes): return
        proc = self.processes[idx]
        proc["monitoring"] = False
        if idx in self.monitor_threads: del self.monitor_threads[idx]
        if "toggle_btn" in proc: proc["toggle_btn"].config(text="▶ Start", bg=self.success_color)
        
        if "status_var" in proc: proc["status_var"].set("⚫ Stopped")
        if "cpu_var" in proc: proc["cpu_var"].set("CPU: 0%")
        if "ram_var" in proc: proc["ram_var"].set("RAM: 0 MB")
            
        self.update_status()
        logging.info(f"Stopped monitoring: {proc['name']}")

    def monitor_process(self, idx):
        proc = self.processes[idx]
        
        while proc.get("monitoring", False):
            try:
                found_process = None
                for p in psutil.process_iter(['name', 'cpu_percent', 'memory_info', 'status']):
                    try:
                        if p.info['name'].lower() == proc["name"].lower():
                            found_process = p
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if found_process:
                    status = found_process.info['status']
                    cpu = found_process.cpu_percent(interval=0.1)
                    ram = found_process.memory_info().rss / 1024 / 1024
                    
                    if "cpu_var" in proc: proc["cpu_var"].set(f"CPU: {cpu:.1f}%")
                    if "ram_var" in proc: proc["ram_var"].set(f"RAM: {ram:.1f} MB")
                    
                    # Smart Crash Detection
                    if status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                        logging.warning(f"Process {proc['name']} is detected as {status}. Restarting...")
                        if "status_var" in proc: proc["status_var"].set(f"⚠️ {status.title()}")
                        try:
                            found_process.terminate()
                        except: pass
                        time.sleep(1)
                        self.start_process(idx)
                    else:
                         if "status_var" in proc: proc["status_var"].set("🟢 Running")
                else:
                    if "status_var" in proc: proc["status_var"].set("🔴 Crashed/Closed")
                    logging.warning(f"Process {proc['name']} not found. Restarting...")
                    self.start_process(idx)
                
                time.sleep(proc.get("interval", 5))
                
            except Exception as e:
                logging.error(f"Monitor Error {proc['name']}: {str(e)}")
                time.sleep(proc.get("interval", 5))

    def start_process(self, idx):
        proc = self.processes[idx]
        try:
            # --- Security Fix Here: No Shell=True ---
            cmd = [proc["path"]]
            if proc.get("args"):
                # Parse string args into list safely
                cmd.extend(shlex.split(proc["args"]))
            
            # Set cwd to the executable's folder to prevent path errors
            process_dir = os.path.dirname(proc["path"])
            
            subprocess.Popen(cmd, shell=False, cwd=process_dir)
            
            proc["restart_count"] = proc.get("restart_count", 0) + 1
            if "restart_var" in proc: proc["restart_var"].set(f"Restarts: {proc['restart_count']}")
            
            self.save_config()
            logging.info(f"Process restarted: {proc['name']} (Count: {proc['restart_count']})")
            
        except Exception as e:
            logging.error(f"Failed to start {proc['name']}: {str(e)}")

    def start_all_monitoring(self):
        for idx in range(len(self.processes)):
            if idx not in self.monitor_threads: self.start_monitoring_process(idx)
        self.start_all_btn.config(state=tk.DISABLED)
        self.stop_all_btn.config(state=tk.NORMAL)

    def stop_all_monitoring(self):
        for idx in list(self.monitor_threads.keys()): self.stop_monitoring_process(idx)
        self.start_all_btn.config(state=tk.NORMAL)
        self.stop_all_btn.config(state=tk.DISABLED)

    def auto_start_monitoring(self):
        self.start_all_monitoring()

    def update_status(self):
        active = len(self.monitor_threads)
        total = len(self.processes)
        self.status_label.config(text=f"Monitoring {active} of {total} processes")

    def add_to_startup(self):
        try:
            startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
            script_path = os.path.abspath(sys.argv[0])
            
            if script_path.endswith('.py'):
                pythonw_path = sys.executable.replace('python.exe', 'pythonw.exe')
                shortcut_target = f'"{pythonw_path}" "{script_path}"'
                batch_file = os.path.join(startup_folder, 'ProcessGuardian.bat')
                with open(batch_file, 'w') as f: f.write(f'@echo off\nstart "" {shortcut_target}')
                messagebox.showinfo("Success", f"Added to startup!\nFile: {batch_file}")
            else:
                import shutil
                dest = os.path.join(startup_folder, os.path.basename(script_path))
                shutil.copy2(script_path, dest)
                messagebox.showinfo("Success", f"Added to startup!\nFile: {dest}")
        except Exception as e: messagebox.showerror("Error", f"Failed: {str(e)}")

    def save_config(self):
        clean_processes = []
        for proc in self.processes:
            clean_proc = proc.copy()
            keys_to_remove = ['status_var', 'cpu_var', 'ram_var', 'restart_var', 'toggle_btn', 'monitoring']
            for key in keys_to_remove:
                if key in clean_proc: del clean_proc[key]
            clean_processes.append(clean_proc)
        
        config = {"processes": clean_processes}
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"Error saving config: {str(e)}")

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.processes = config.get("processes", [])
            except Exception as e:
                print(f"Error loading config: {str(e)}")
                self.processes = []

    def on_closing(self):
        msg_box = tk.Toplevel(self.root)
        msg_box.title("Exit or Minimize?")
        msg_box.geometry("350x150")
        msg_box.configure(bg=self.bg_color)
        msg_box.attributes('-topmost', True)
        
        msg_box.update_idletasks()
        x = (msg_box.winfo_screenwidth() // 2) - (msg_box.winfo_width() // 2)
        y = (msg_box.winfo_screenheight() // 2) - (msg_box.winfo_height() // 2)
        msg_box.geometry(f"+{x}+{y}")
        
        tk.Label(msg_box, text="Do you want to exit or run in background?", font=("Segoe UI", 10), bg=self.bg_color, fg=self.fg_color).pack(pady=20)
        
        btn_frame = tk.Frame(msg_box, bg=self.bg_color)
        btn_frame.pack(pady=10)
        
        def minimize():
            msg_box.destroy()
            self.root.withdraw() 
            self.floating_widget = FloatingWidget(self.root, self.restore_window)
            logging.info("Application minimized to widget.")

        def full_exit():
            msg_box.destroy()
            for idx in list(self.monitor_threads.keys()):
                self.stop_monitoring_process(idx)
            logging.info("Application exiting.")
            self.root.destroy()

        tk.Button(btn_frame, text="⏬ Background", command=minimize, bg=self.accent_color, fg="black", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Exit App", command=full_exit, bg=self.error_color, fg="black", width=12).pack(side=tk.LEFT, padx=5)

    def restore_window(self):
        self.root.deiconify()
        logging.info("Application restored from widget.")

def main():
    root = tk.Tk()
    app = ModernProcessMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()