# BAT Launcher Dashboard
# Author: Atul Kumar Dubey
# GitHub: atuldubey1200
#
# Window-adjustable version:
# - Columns automatically resize with the window.
# - Description box expands/shrinks based on available window width.
# - Entries stretch to the full visible window.
# - No forced huge left-right table width.
# - Horizontal scrollbar appears only when the window becomes too small.
# - Based on your working JSON-load version.
# - Adds visible right-side up/down scroll buttons and a wider vertical scrollbar.
# - Description and Developer fields now autosave while typing.
# - Keeps the same BAT launch method:
#       subprocess.Popen(f'start "" "{path}"', shell=True)

import json
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from datetime import datetime


APP_TITLE = "BAT Launcher Dashboard"
AUTHOR = "Atul Kumar Dubey"
GITHUB = "atuldubey1200"


class BATLauncherDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1550x820")
        self.minsize(1050, 620)

        self.items = []
        self.selected_bat = ""

        self.settings_file = os.path.join(os.getcwd(), "bat_launcher_settings.json")
        self.autosave_file = os.path.join(os.getcwd(), "bat_launcher_list.json")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_list())

        self.load_settings()
        self.build_ui()
        self.load_items()
        self.refresh_list()

    # -----------------------------
    # UI
    # -----------------------------
    def build_ui(self):
        title = tk.Label(self, text=APP_TITLE, font=("Arial", 20, "bold"))
        title.pack(pady=(10, 2))

        author = tk.Label(
            self,
            text=f"Author: {AUTHOR}   |   GitHub: {GITHUB}",
            font=("Arial", 10)
        )
        author.pack(pady=(0, 10))

        top = tk.Frame(self)
        top.pack(fill="x", padx=12, pady=5)

        tk.Button(
            top,
            text="Add BAT File",
            width=18,
            height=2,
            command=self.add_bat_file
        ).pack(side="left", padx=5)

        tk.Button(
            top,
            text="Set Autosave Location",
            width=22,
            height=2,
            command=self.set_autosave_location
        ).pack(side="left", padx=5)

        tk.Button(
            top,
            text="Load Autosave JSON",
            width=22,
            height=2,
            command=self.load_autosave_json
        ).pack(side="left", padx=5)

        tk.Label(top, text="Search:").pack(side="left", padx=(25, 5))

        tk.Entry(
            top,
            textvariable=self.search_var,
            width=55
        ).pack(side="left", padx=5, fill="x", expand=True)

        # Main table area
        table_outer = tk.Frame(self)
        table_outer.pack(fill="both", expand=True, padx=12, pady=(10, 5))

        self.canvas = tk.Canvas(table_outer, borderwidth=0, highlightthickness=0)
        self.table_frame = tk.Frame(self.canvas)

        # Right-side scroll control panel:
        # Up button + visible scrollbar + Down button.
        scroll_panel = tk.Frame(table_outer)
        scroll_panel.pack(side="right", fill="y")

        self.scroll_up_btn = tk.Button(
            scroll_panel,
            text="▲",
            width=3,
            command=lambda: self.canvas.yview_scroll(-3, "units")
        )
        self.scroll_up_btn.pack(side="top", fill="x")

        self.v_scrollbar = tk.Scrollbar(
            scroll_panel,
            orient="vertical",
            command=self.canvas.yview,
            width=22
        )
        self.v_scrollbar.pack(side="top", fill="y", expand=True)

        self.scroll_down_btn = tk.Button(
            scroll_panel,
            text="▼",
            width=3,
            command=lambda: self.canvas.yview_scroll(3, "units")
        )
        self.scroll_down_btn.pack(side="bottom", fill="x")

        self.h_scrollbar = tk.Scrollbar(table_outer, orient="horizontal", command=self.canvas.xview)

        self.canvas.configure(
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )

        self.h_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")

        self.table_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.bind("<Configure>", self.on_canvas_configure)
        # Up/down scrolling for many GUI rows.
        # Mouse wheel works when cursor is anywhere over the launcher window.
        self.bind_all("<MouseWheel>", self.on_mousewheel)

        # Keyboard scrolling support.
        # Useful when no mouse is available.
        self.bind_all("<Up>", self.on_key_scroll_up)
        self.bind_all("<Down>", self.on_key_scroll_down)
        self.bind_all("<Prior>", self.on_key_page_up)     # Page Up
        self.bind_all("<Next>", self.on_key_page_down)    # Page Down
        self.bind_all("<Home>", self.on_key_home)
        self.bind_all("<End>", self.on_key_end)

        # Header
        self.header = tk.Frame(self.table_frame)
        self.header.pack(fill="x", pady=(0, 6))

        self.configure_table_grid(self.header)

        self.make_header_label(self.header, "Run GUI Button", 0, "w")
        self.make_header_label(self.header, "Description", 1, "w")
        self.make_header_label(self.header, "Developer Name", 2, "w")
        self.make_header_label(self.header, "Last Used", 3, "w")
        self.make_header_label(self.header, "Folder", 4, "center")
        self.make_header_label(self.header, "Rename", 5, "center")
        self.make_header_label(self.header, "Remove", 6, "center")

        self.rows_frame = tk.Frame(self.table_frame)
        self.rows_frame.pack(fill="both", expand=True)

        # Bottom status
        bottom = tk.Frame(self, relief="groove", bd=1)
        bottom.pack(fill="x", padx=12, pady=8)

        self.autosave_label = tk.Label(
            bottom,
            text=f"Autosave Location: {self.autosave_file}",
            anchor="w"
        )
        self.autosave_label.pack(fill="x", padx=8, pady=2)

        self.selected_label = tk.Label(
            bottom,
            text="Selected BAT: None",
            anchor="w"
        )
        self.selected_label.pack(fill="x", padx=8, pady=2)

        self.status_label = tk.Label(
            bottom,
            text="Status: Ready",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=8, pady=2)

    def configure_table_grid(self, frame):
        # Adjustable layout:
        # Fixed-ish columns: Run, Last Used, Folder, Rename, Remove
        # Expanding columns: Description strongly, Developer mildly
        frame.grid_columnconfigure(0, minsize=210, weight=0)
        frame.grid_columnconfigure(1, minsize=360, weight=8)
        frame.grid_columnconfigure(2, minsize=170, weight=2)
        frame.grid_columnconfigure(3, minsize=165, weight=0)
        frame.grid_columnconfigure(4, minsize=80, weight=0)
        frame.grid_columnconfigure(5, minsize=80, weight=0)
        frame.grid_columnconfigure(6, minsize=80, weight=0)

    def make_header_label(self, parent, text, col, anchor):
        tk.Label(
            parent,
            text=text,
            anchor=anchor,
            font=("Arial", 10, "bold")
        ).grid(row=0, column=col, sticky="ew", padx=4, pady=(0, 6))

    def on_canvas_configure(self, event):
        # Make the table match the visible window width.
        # If window becomes smaller than natural table width, horizontal scrolling works.
        self.canvas.itemconfig(self.canvas_window, width=max(event.width, 1145))
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        # Vertical up/down scrolling.
        # Works for standard Windows mouse wheel.
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_key_scroll_up(self, event):
        self.canvas.yview_scroll(-1, "units")

    def on_key_scroll_down(self, event):
        self.canvas.yview_scroll(1, "units")

    def on_key_page_up(self, event):
        self.canvas.yview_scroll(-1, "pages")

    def on_key_page_down(self, event):
        self.canvas.yview_scroll(1, "pages")

    def on_key_home(self, event):
        self.canvas.yview_moveto(0)

    def on_key_end(self, event):
        self.canvas.yview_moveto(1)

    # -----------------------------
    # Settings and autosave
    # -----------------------------
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                saved = data.get("autosave_file")
                if saved:
                    self.autosave_file = saved
            except Exception:
                pass

    def save_settings(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump({"autosave_file": self.autosave_file}, f, indent=4)
        except Exception:
            pass

    def normalize_items(self, data):
        if not isinstance(data, list):
            return []

        normalized = []
        for item in data:
            if not isinstance(item, dict):
                continue

            if "path" in item and "bat_path" not in item:
                item["bat_path"] = item["path"]

            normalized.append({
                "name": item.get("name", ""),
                "description": item.get("description", ""),
                "developer": item.get("developer", ""),
                "last_used": item.get("last_used", "Never"),
                "bat_path": item.get("bat_path", "")
            })

        return normalized

    def load_items(self):
        if not os.path.exists(self.autosave_file):
            self.items = []
            return

        try:
            with open(self.autosave_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.items = self.normalize_items(data)
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load autosave JSON:\n{e}")
            self.items = []

    def save_items(self):
        try:
            folder = os.path.dirname(self.autosave_file)
            if folder:
                os.makedirs(folder, exist_ok=True)

            with open(self.autosave_file, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=4)

            self.status_label.config(text="Status: Autosaved")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def set_autosave_location(self):
        path = filedialog.asksaveasfilename(
            title="Set Autosave JSON File Location",
            defaultextension=".json",
            filetypes=[("JSON file", "*.json")],
            initialfile="bat_launcher_list.json"
        )

        if not path:
            return

        self.autosave_file = path
        self.save_settings()
        self.autosave_label.config(text=f"Autosave Location: {self.autosave_file}")

        if os.path.exists(path):
            answer = messagebox.askyesno(
                "Existing JSON Found",
                "This autosave JSON already exists.\n\nDo you want to load its saved launcher entries now?"
            )
            if answer:
                self.load_items()
                self.refresh_list()
                self.status_label.config(text="Status: Loaded existing autosave JSON")
                return

        self.save_items()
        self.refresh_list()

    def load_autosave_json(self):
        json_path = filedialog.askopenfilename(
            title="Load / Upload Previous Autosave JSON",
            filetypes=[("JSON file", "*.json")]
        )

        if not json_path:
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            loaded_items = self.normalize_items(data)

            if not loaded_items:
                messagebox.showwarning(
                    "No Entries Found",
                    "This JSON file did not contain valid launcher entries."
                )
                return

            choice = messagebox.askyesnocancel(
                "Load Autosave JSON",
                "Do you want to REPLACE the current launcher list with this JSON?\n\n"
                "Yes = Replace current list\n"
                "No = Merge with current list\n"
                "Cancel = Do nothing"
            )

            if choice is None:
                return

            if choice is True:
                self.items = loaded_items
                action = "replaced"
            else:
                existing_paths = {item.get("bat_path", "") for item in self.items}
                added = 0
                for item in loaded_items:
                    if item.get("bat_path", "") not in existing_paths:
                        self.items.append(item)
                        existing_paths.add(item.get("bat_path", ""))
                        added += 1
                action = f"merged, added {added} new entries"

            make_active = messagebox.askyesno(
                "Use This JSON As Autosave Location?",
                "Do you want to use this loaded JSON file as the active autosave location?\n\n"
                "Yes = Future edits autosave into this JSON\n"
                "No = Keep current autosave location and copy loaded entries there"
            )

            if make_active:
                self.autosave_file = json_path
                self.save_settings()
                self.autosave_label.config(text=f"Autosave Location: {self.autosave_file}")

            self.save_items()
            self.refresh_list()
            self.status_label.config(text=f"Status: Loaded autosave JSON ({action})")

        except Exception as e:
            messagebox.showerror("JSON Load Error", f"Could not load JSON file:\n{e}")

    # -----------------------------
    # Add / refresh list
    # -----------------------------
    def add_bat_file(self):
        bat_path = filedialog.askopenfilename(
            title="Select BAT File",
            filetypes=[("Batch files", "*.bat")]
        )

        if not bat_path:
            return

        default_name = os.path.splitext(os.path.basename(bat_path))[0]

        name = simpledialog.askstring(
            "Button Name",
            "Enter GUI button name:",
            initialvalue=default_name
        )

        if not name:
            name = default_name

        description = simpledialog.askstring(
            "Description",
            "Enter GUI description:",
            initialvalue=""
        )

        developer = simpledialog.askstring(
            "Developer Name",
            "Enter developer name:",
            initialvalue=AUTHOR
        )

        self.items.append({
            "name": name,
            "description": description or "",
            "developer": developer or "",
            "last_used": "Never",
            "bat_path": bat_path
        })

        self.save_items()
        self.refresh_list()

    def refresh_list(self):
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().lower().strip()

        for idx, item in enumerate(self.items):
            name = item.get("name", "")
            description = item.get("description", "")
            developer = item.get("developer", "")
            last_used = item.get("last_used", "Never")
            bat_path = item.get("bat_path", "")

            if query:
                combined = f"{name} {description} {developer} {last_used} {bat_path}".lower()
                if query not in combined:
                    continue

            row = tk.Frame(self.rows_frame, bd=1, relief="solid", padx=6, pady=6)
            row.pack(fill="x", expand=True, pady=4)

            self.configure_table_grid(row)

            run_btn = tk.Button(
                row,
                text=name,
                height=2,
                command=lambda p=bat_path, i=idx: self.run_bat(p, i)
            )
            run_btn.grid(row=0, column=0, sticky="ew", padx=4)

            desc_var = tk.StringVar(value=description)
            desc_entry = tk.Entry(row, textvariable=desc_var, font=("Arial", 10))
            desc_entry.grid(row=0, column=1, sticky="ew", padx=4, ipady=7)
            # Save description automatically while typing, and also on Enter / focus-out.
            desc_entry.bind("<KeyRelease>", lambda e, i=idx, v=desc_var: self.update_field(i, "description", v.get()))
            desc_entry.bind("<FocusOut>", lambda e, i=idx, v=desc_var: self.update_field(i, "description", v.get()))
            desc_entry.bind("<Return>", lambda e, i=idx, v=desc_var: self.update_field(i, "description", v.get()))

            dev_var = tk.StringVar(value=developer)
            dev_entry = tk.Entry(row, textvariable=dev_var, font=("Arial", 10))
            dev_entry.grid(row=0, column=2, sticky="ew", padx=4, ipady=7)
            # Save developer automatically while typing, and also on Enter / focus-out.
            dev_entry.bind("<KeyRelease>", lambda e, i=idx, v=dev_var: self.update_field(i, "developer", v.get()))
            dev_entry.bind("<FocusOut>", lambda e, i=idx, v=dev_var: self.update_field(i, "developer", v.get()))
            dev_entry.bind("<Return>", lambda e, i=idx, v=dev_var: self.update_field(i, "developer", v.get()))

            last_label = tk.Label(row, text=last_used, anchor="w")
            last_label.grid(row=0, column=3, sticky="ew", padx=4)

            tk.Button(
                row,
                text="Open",
                command=lambda p=bat_path: self.open_bat_folder(p)
            ).grid(row=0, column=4, sticky="ew", padx=4)

            tk.Button(
                row,
                text="Edit",
                command=lambda i=idx: self.rename_item(i)
            ).grid(row=0, column=5, sticky="ew", padx=4)

            tk.Button(
                row,
                text="X",
                command=lambda i=idx: self.remove_item(i)
            ).grid(row=0, column=6, sticky="ew", padx=4)

            for w in (row, desc_entry, dev_entry, last_label):
                w.bind("<Button-1>", lambda e, p=bat_path: self.select_bat(p))

    # -----------------------------
    # Actions
    # -----------------------------
    def select_bat(self, path):
        self.selected_bat = path
        self.selected_label.config(text=f"Selected BAT: {path}")

    def run_bat(self, path, idx):
        self.select_bat(path)

        if not os.path.exists(path):
            messagebox.showerror("Missing BAT File", f"BAT file not found:\n{path}")
            return

        try:
            subprocess.Popen(f'start "" "{path}"', shell=True)

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if idx < len(self.items):
                self.items[idx]["last_used"] = now
                self.save_items()

            self.status_label.config(text=f"Status: Launched {os.path.basename(path)}")
            self.refresh_list()

        except Exception as e:
            messagebox.showerror("Launch Error", str(e))

    def open_bat_folder(self, path):
        self.select_bat(path)
        folder = os.path.dirname(path)

        if not os.path.exists(folder):
            messagebox.showerror("Missing Folder", f"Folder not found:\n{folder}")
            return

        try:
            os.startfile(folder)
            self.status_label.config(text=f"Status: Opened folder {folder}")
        except Exception as e:
            messagebox.showerror("Folder Error", str(e))

    def rename_item(self, idx):
        if idx >= len(self.items):
            return

        old_name = self.items[idx].get("name", "")

        new_name = simpledialog.askstring(
            "Rename Button",
            "Enter new GUI button name:",
            initialvalue=old_name
        )

        if new_name:
            self.items[idx]["name"] = new_name
            self.save_items()
            self.refresh_list()

    def update_field(self, idx, field, value):
        if idx < len(self.items):
            self.items[idx][field] = value
            self.save_items()

    def remove_item(self, idx):
        if idx >= len(self.items):
            return

        name = self.items[idx].get("name", "Selected GUI")

        confirm = messagebox.askyesno(
            "Remove Entry",
            f"Remove '{name}' from launcher?\n\nThis will not delete the BAT file."
        )

        if confirm:
            self.items.pop(idx)
            self.save_items()
            self.refresh_list()


if __name__ == "__main__":
    app = BATLauncherDashboard()
    app.mainloop()
