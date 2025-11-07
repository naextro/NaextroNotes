"""
tk_info_manager.py

- Dark-themed Tkinter app to manage info.json by date/subject and drag/drop or pick images.
- Creates backups of info.json before modifying.
- Copies dropped/selected images into images/<date>/ with naming scheme <subject_key><n>.<ext>.
"""

import os
import json
import shutil
import datetime
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Try to import drag-and-drop support (tkinterdnd2). If not available, fallback to file dialog.
TRY_TKDNDF = True
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:
    TRY_TKDNDF = False

# ----------------------------
# Helpers
# ----------------------------
INFO_JSON = Path("info.json")
BACKUP_DIR = Path("backups")
IMAGES_ROOT = Path("images")


def ensure_dirs():
    BACKUP_DIR.mkdir(exist_ok=True)
    IMAGES_ROOT.mkdir(exist_ok=True)


def read_json():
    if not INFO_JSON.exists():
        return []
    with INFO_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data):
    with INFO_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def backup_json():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    BACKUP_DIR.mkdir(exist_ok=True)
    dest = BACKUP_DIR / f"info_backup_{timestamp}.json"
    if INFO_JSON.exists():
        shutil.copy2(INFO_JSON, dest)
    return dest


def normalize_subject_key(subject):
    # Make a concise key for filenames: letters + numbers, lowercase, no spaces.
    return re.sub(r'[^a-z0-9]+', '', subject.lower())


def date_str_from_date(dt: datetime.date):
    return dt.strftime("%d-%m-%Y")


def parse_date_str(s: str):
    try:
        d = datetime.datetime.strptime(s, "%d-%m-%Y").date()
        return d
    except Exception:
        return None


def get_day_entry(data, date_str):
    for entry in data:
        if entry.get("date") == date_str:
            return entry
    return None


def create_day_entry(data, date_str):
    entry = {"date": date_str, "subjects": []}
    data.append(entry)
    return entry


def get_subject_entry(day_entry, subject_name):
    for s in day_entry.get("subjects", []):
        if s.get("subject") == subject_name:
            return s
    return None


def create_subject_entry(day_entry, subject_name):
    subj = {"subject": subject_name, "images": []}
    day_entry.setdefault("subjects", []).append(subj)
    return subj


def next_image_name_for(subject_key, date_folder: Path, ext):
    # find files in date_folder that start with subject_key and end with ext, like chem1.jpg
    existing = []
    if date_folder.exists():
        for f in date_folder.iterdir():
            if f.is_file():
                nm = f.name
                if nm.lower().startswith(subject_key) and nm.lower().endswith(ext.lower()):
                    # extract trailing number if present
                    m = re.match(rf'^{re.escape(subject_key)}(\d+)\{re.escape(ext.lower())}$', nm.lower())
                    if m:
                        try:
                            existing.append(int(m.group(1)))
                        except:
                            pass
                    else:
                        # name exists but without number -> consider 1 as used (reserve)
                        existing.append(1)
    # choose smallest positive integer not in existing
    n = 1
    existing_set = set(existing)
    while n in existing_set:
        n += 1
    return f"{subject_key}{n}{ext}"


def copy_images_to_folder(files, date_str, subject_name):
    """
    files: list of filesystem paths (strings)
    date_str: DD-MM-YYYY
    subject_name: string
    """
    ensure_dirs()
    date_folder = IMAGES_ROOT / date_str
    date_folder.mkdir(parents=True, exist_ok=True)

    subject_key = normalize_subject_key(subject_name)

    copied_paths = []
    for src in files:
        src_path = Path(src)
        if not src_path.exists():
            continue
        ext = src_path.suffix  # includes dot
        new_name = next_image_name_for(subject_key, date_folder, ext)
        dst = date_folder / new_name
        # ensure we don't overwrite (shouldn't due to naming logic, but safe)
        shutil.copy2(src_path, dst)
        copied_paths.append(str(dst.as_posix()))
    return copied_paths


# ----------------------------
# GUI
# ----------------------------
class InfoManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Info.json Manager")
        self.data = []
        self.selected_date = date_str_from_date(datetime.date.today())
        self.selected_subject = None

        # Main frame
        self.main = ttk.Frame(root, padding=12)
        self.main.pack(fill=tk.BOTH, expand=True)

        self.setup_styles()
        self.build_ui()
        self.load_data()
        self.load_day()


    def setup_styles(self):
        # Basic dark theme tuning
        s = ttk.Style()
        # Use default theme but override specific colors
        try:
            s.theme_use("clam")
        except Exception:
            pass

        bg = "#141414"
        fg = "#E8E8E8"
        accent = "#2a9d8f"
        entry_bg = "#1E1E1E"

        self.root.configure(bg=bg)
        s.configure(".", background=bg, foreground=fg, fieldbackground=entry_bg)
        s.configure("TFrame", background=bg)
        s.configure("TLabel", background=bg, foreground=fg)
        s.configure("TButton", background=bg, foreground=fg, padding=6)
        s.configure("TEntry", padding=4)
        s.configure("Treeview", background=entry_bg, fieldbackground=entry_bg, foreground=fg)
        s.map("TButton",
              foreground=[('pressed', fg), ('active', fg)],
              background=[('active', '!disabled', accent)])

    def build_ui(self):
        top = ttk.Frame(self.main)
        top.pack(fill=tk.X, pady=(0, 8))

        # Date controls
        date_label = ttk.Label(top, text="Date (DD-MM-YYYY):")
        date_label.grid(row=0, column=0, sticky=tk.W)

        self.date_var = tk.StringVar(value=self.selected_date)
        self.date_entry = ttk.Entry(top, textvariable=self.date_var, width=15)
        self.date_entry.grid(row=0, column=1, padx=(6, 6))

        today_btn = ttk.Button(top, text="Use Today", command=self.set_today)
        today_btn.grid(row=0, column=2, padx=(0, 6))

        load_btn = ttk.Button(top, text="Load Day", command=self.load_day)
        load_btn.grid(row=0, column=3, padx=(0, 6))

        backup_btn = ttk.Button(top, text="Backup JSON Now", command=self.manual_backup)
        backup_btn.grid(row=0, column=4, padx=(0, 6))

        # Main panes
        panes = ttk.Frame(self.main)
        panes.pack(fill=tk.BOTH, expand=True)

        # Left: subjects
        left = ttk.Frame(panes)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        ttk.Label(left, text="Subjects:").pack(anchor=tk.W)
        self.subject_listbox = tk.Listbox(left, width=28, height=12, activestyle="dotbox",
                                          bg="#1E1E1E", fg="#E8E8E8", selectbackground="#2a9d8f")
        self.subject_listbox.pack(fill=tk.Y)
        self.subject_listbox.bind("<<ListboxSelect>>", self.on_subject_select)

        subj_entry_frame = ttk.Frame(left)
        subj_entry_frame.pack(fill=tk.X, pady=(8, 0))

        self.new_subject_var = tk.StringVar()
        self.new_subject_entry = ttk.Entry(subj_entry_frame, textvariable=self.new_subject_var)
        self.new_subject_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        add_subj_btn = ttk.Button(subj_entry_frame, text="Add Subject", command=self.add_subject)
        add_subj_btn.pack(side=tk.LEFT, padx=(6, 0))

        # Middle/right: images and DnD
        right = ttk.Frame(panes)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(right, text="Images for selected subject:").pack(anchor=tk.W)
        self.images_listbox = tk.Listbox(right, height=12, bg="#1E1E1E", fg="#E8E8E8",
                                         selectbackground="#2a9d8f")
        self.images_listbox.pack(fill=tk.BOTH, expand=True)

        images_btn_frame = ttk.Frame(right)
        images_btn_frame.pack(fill=tk.X, pady=(8, 0))

        add_img_btn = ttk.Button(images_btn_frame, text="Add images (file dialog)", command=self.add_images_via_dialog)
        add_img_btn.pack(side=tk.LEFT)

        remove_img_btn = ttk.Button(images_btn_frame, text="Remove selected", command=self.remove_selected_image)
        remove_img_btn.pack(side=tk.LEFT, padx=(6, 0))

        # Drag-and-drop area
        dnd_frame = ttk.Frame(right, height=80, relief=tk.SUNKEN)
        dnd_frame.pack(fill=tk.X, pady=(12, 0))
        dnd_label = ttk.Label(dnd_frame, text="Drag & drop images here (or use the Add images button)")
        dnd_label.pack(expand=True, pady=18)

        self.dnd_frame = dnd_frame  # keep ref for DnD binding
        if TRY_TKDNDF:
            try:
                self.register_dnd()
            except Exception:
                pass
        else:
            hint = ttk.Label(dnd_frame, text="(tkinterdnd2 not available — install for native drag-and-drop)",
                             font=("TkDefaultFont", 8))
            hint.pack()

        # Bottom: save button
        bottom = ttk.Frame(self.main)
        bottom.pack(fill=tk.X, pady=(12, 0))
        save_btn = ttk.Button(bottom, text="Save JSON (with backup)", command=self.save_json_with_backup)
        save_btn.pack(side=tk.RIGHT)

    def register_dnd(self):
        def drop_event(event):
            files = self.root.tk.splitlist(event.data)
            self.handle_dropped_files(files)

        # The drop target needs to be registered on a widget that supports it.
        try:
            self.dnd_frame.drop_target_register(DND_FILES)
            self.dnd_frame.dnd_bind('<<Drop>>', lambda e: drop_event(e))
        except Exception:
            # sometimes the dnd registration fails depending on platform / setup
            pass

    # --------------------
    # Data loading + UI sync
    # --------------------
    def load_data(self):
        self.data = read_json()
        self.load_day()  # populate subjects for current date

    def set_today(self):
        self.date_var.set(date_str_from_date(datetime.date.today()))
        self.load_day()

    def load_day(self):
        s = self.date_var.get().strip()
        if not s:
            messagebox.showerror("Invalid Date", "Date cannot be empty. Use DD-MM-YYYY.")
            return
        d = parse_date_str(s)
        if not d:
            messagebox.showerror("Invalid Date", "Date must be in DD-MM-YYYY format.")
            return
        date_str = date_str_from_date(d)
        self.selected_date = date_str
        # Ensure day exists in data
        day_entry = get_day_entry(self.data, date_str)
        if not day_entry:
            # create a new day entry (not saved to disk until Save JSON)
            day_entry = create_day_entry(self.data, date_str)
        self.populate_subjects_from_day(day_entry)

    def populate_subjects_from_day(self, day_entry):
        self.subject_listbox.delete(0, tk.END)
        for subj in day_entry.get("subjects", []):
            self.subject_listbox.insert(tk.END, subj.get("subject"))
        self.images_listbox.delete(0, tk.END)
        self.selected_subject = None

    def on_subject_select(self, event):
        sel = self.subject_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        subj_name = self.subject_listbox.get(idx)
        self.selected_subject = subj_name
        self.populate_images_for_subject(subj_name)

    def populate_images_for_subject(self, subject):
        self.images_listbox.delete(0, tk.END)
        all_images = []
        for day in self.data:
            for subj in day["subjects"]:
                if subj["subject"] == subject:
                    all_images.extend(subj["images"])
        for img_path in all_images:
            self.images_listbox.insert(tk.END, img_path)


    # ------------- fixed add_subject -------------
    def add_subject(self):
        name = self.new_subject_var.get().strip()
        if not name:
            messagebox.showerror("Empty Subject", "Please type a subject name.")
            return

        day_entry = get_day_entry(self.data, self.selected_date)
        if not day_entry:
            day_entry = create_day_entry(self.data, self.selected_date)

        subj_entry = get_subject_entry(day_entry, name)
        if subj_entry:
            messagebox.showinfo("Exists", f"Subject '{name}' already exists for {self.selected_date}.")
            return

        # Create new subject and add to UI, then select it
        create_subject_entry(day_entry, name)
        self.subject_listbox.insert(tk.END, name)
        self.new_subject_var.set("")

        # select newly added subject
        last = self.subject_listbox.size() - 1
        if last >= 0:
            self.subject_listbox.selection_clear(0, tk.END)
            self.subject_listbox.selection_set(last)
            self.subject_listbox.activate(last)
            # call selector handler to populate images (empty at this point)
            self.on_subject_select(None)

    # ------------- unified add_images -------------
    def add_images(self, paths):
        if not self.selected_subject:
            messagebox.showerror("No Subject Selected", "Please select a subject first (or add one).")
            return

        copied = copy_images_to_folder(paths, self.selected_date, self.selected_subject)
        if not copied:
            messagebox.showerror("Copy Failed", "No images were copied.")
            return

        # Only append to existing subject's 'images' field
        day_entry = get_day_entry(self.data, self.selected_date)
        if not day_entry:
            day_entry = create_day_entry(self.data, self.selected_date)

        subj_entry = get_subject_entry(day_entry, self.selected_subject)
        if not subj_entry:
            subj_entry = create_subject_entry(day_entry, self.selected_subject)

        # Append only new relative paths, avoid duplicates
        added = 0
        for p in copied:
            rel = os.path.normpath(p).replace(os.path.sep, '/')
            if rel not in subj_entry.get("images", []):
                subj_entry.setdefault("images", []).append(rel)
                added += 1

        self.populate_images_for_subject(self.selected_subject)
        messagebox.showinfo(
            "Images Added",
            f"Added {added} new image(s) to '{self.selected_subject}' ({self.selected_date})."
        )

    # --------------------
    # Image add / remove / DnD helpers
    # --------------------
    def handle_dropped_files(self, files):
        # Filter to image-like extensions
        image_files = [f for f in files if Path(f).suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")]
        if not image_files:
            messagebox.showwarning("No images", "No supported image files were dropped.")
            return
        self.add_images(image_files)

    def add_images_via_dialog(self):
        paths = filedialog.askopenfilenames(title="Select image files", filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"), ("All files", "*.*")
        ])
        if not paths:
            return
        self.add_images(paths)

    def remove_selected_image(self):
        sel = self.images_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        img_path = self.images_listbox.get(idx)
        # confirm removal from JSON (not deleting file)
        if not messagebox.askyesno("Remove", f"Remove image reference:\n{img_path}\n\nThis will not delete the image file."):
            return
        day_entry = get_day_entry(self.data, self.selected_date)
        subj_entry = get_subject_entry(day_entry, self.selected_subject) if day_entry else None
        if subj_entry and img_path in subj_entry.get("images", []):
            subj_entry["images"].remove(img_path)
        self.populate_images_for_subject(self.selected_subject)

    # --------------------
    # Save / Backup
    # --------------------
    def manual_backup(self):
        if not INFO_JSON.exists():
            messagebox.showinfo("No info.json", "No info.json file found to back up.")
            return
        dest = backup_json()
        messagebox.showinfo("Backup Created", f"Backup saved to:\n{dest}")

    def save_json_with_backup(self):
        # backup
        if INFO_JSON.exists():
            backup_json()
        # write JSON
        try:
            write_json(self.data)
            messagebox.showinfo("Saved", f"info.json updated (backup created).")
        except Exception as e:
            messagebox.showerror("Save Failed", f"Failed to save info.json:\n{e}")


def main():
    ensure_dirs()
    # If tkinterdnd2 is available, use its root class for better DnD
    if TRY_TKDNDF:
        try:
            root = TkinterDnD.Tk()
        except Exception:
            root = tk.Tk()
    else:
        root = tk.Tk()

    # set minimum size
    root.geometry("820x520")
    app = InfoManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
