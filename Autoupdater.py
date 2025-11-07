import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import json
import os
import shutil
from datetime import datetime

# --- Constants ---
INFO_JSON = 'info.json'
IMAGES_DIR = 'images'
BACKUP_SUFFIX = '.bak'

# --- Helper Functions ---
def backup_json():
    backup_path = INFO_JSON + BACKUP_SUFFIX
    shutil.copy2(INFO_JSON, backup_path)

def load_json():
    with open(INFO_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data):
    with open(INFO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_dates(data):
    return [entry['date'] for entry in data]

def get_subjects_for_date(data, date):
    for entry in data:
        if entry['date'] == date:
            return [s['subject'] for s in entry['subjects']]
    return []

def get_next_image_name(date_folder, subject):
    # Find next available image name for subject in date_folder
    files = os.listdir(date_folder) if os.path.exists(date_folder) else []
    prefix = subject[:3].lower()
    nums = [int(f[len(prefix):-4]) for f in files if f.startswith(prefix) and f.endswith('.jpg') and f[len(prefix):-4].isdigit()]
    next_num = max(nums, default=0) + 1
    return f"{prefix}{next_num}.jpg"

# --- UI Setup ---
class DarkStyle(ttk.Style):
    def __init__(self, root):
        super().__init__(root)
        self.theme_use('clam')
        self.configure('.', background='#23272e', foreground='#f8f8f2', fieldbackground='#23272e')
        self.configure('TLabel', background='#23272e', foreground='#f8f8f2')
        self.configure('TButton', background='#44475a', foreground='#f8f8f2')
        self.configure('TCombobox', fieldbackground='#23272e', background='#44475a', foreground='#f8f8f2')
        self.configure('TCombobox.TEntry', fieldbackground='#23272e', background='#23272e', foreground='#f8f8f2')
        self.map('TButton', background=[('active', '#6272a4')])
        self.map('TCombobox', fieldbackground=[('readonly', '#23272e')], background=[('readonly', '#23272e')], foreground=[('readonly', '#f8f8f2')])

class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title('NaextroNotes Updater')
        self.geometry('500x400')
        self.configure(bg='#23272e')
        DarkStyle(self)
        self.resizable(False, False)

        # Load data
        self.data = load_json()
        self.selected_date = tk.StringVar()
        self.selected_subject = tk.StringVar()
        self.new_subject = tk.StringVar()

        # --- Date Selection ---
        ttk.Label(self, text='Date:').pack(pady=(20, 0))
        self.date_combo = ttk.Combobox(self, textvariable=self.selected_date, values=get_dates(self.data), state='readonly', style='TCombobox')
        self.date_combo.pack(pady=5)
        dates = get_dates(self.data)
        today = datetime.now().strftime('%d-%m-%Y')
        if today in dates:
            self.date_combo.set(today)
        elif dates:
            self.date_combo.set(dates[0])
        else:
            self.date_combo.set('')
        self.date_combo.bind('<<ComboboxSelected>>', self.update_subjects)

        # --- Subject Selection ---
        ttk.Label(self, text='Subject:').pack(pady=(20, 0))
        self.subject_combo = ttk.Combobox(self, textvariable=self.selected_subject, values=[], state='readonly', style='TCombobox')
        self.subject_combo.pack(pady=5)
        self.subject_combo.bind('<<ComboboxSelected>>', self.clear_new_subject)
        self.update_subjects()

        ttk.Label(self, text='Or add new subject:').pack(pady=(10, 0))
        self.new_subject_entry = ttk.Entry(self, textvariable=self.new_subject)
        self.new_subject_entry.pack(pady=5)

        # --- Drag and Drop Area ---
        self.drop_label = ttk.Label(self, text='Drag and drop images here', anchor='center', relief='ridge', padding=30)
        self.drop_label.pack(fill='x', padx=40, pady=30)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)

        # --- Save Button ---
        self.save_btn = ttk.Button(self, text='Save Entry', command=self.save_entry)
        self.save_btn.pack(pady=10)

    def update_subjects(self, event=None):
        date = self.selected_date.get()
        subjects = get_subjects_for_date(self.data, date)
        self.subject_combo['values'] = subjects
        if subjects:
            self.subject_combo.set(subjects[0])
        else:
            self.subject_combo.set('')
        self.selected_subject.set(self.subject_combo.get())

    def clear_new_subject(self, event=None):
        self.new_subject.set('')

    def handle_drop(self, event):
        files = self.tk.splitlist(event.data)
        for file_path in files:
            if os.path.isfile(file_path) and file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                self.process_image(file_path)
            else:
                messagebox.showerror('Invalid File', f'File {file_path} is not a supported image.')

    def process_image(self, src_path):
        date = self.selected_date.get()
        subject = self.new_subject.get().strip() or self.selected_subject.get()
        if not subject:
            messagebox.showerror('No Subject', 'Please select or enter a subject.')
            return
        date_folder = os.path.join(IMAGES_DIR, date)
        os.makedirs(date_folder, exist_ok=True)
        img_name = get_next_image_name(date_folder, subject)
        dest_path = os.path.join(date_folder, img_name)
        shutil.copy2(src_path, dest_path)
        self.add_image_to_json(date, subject, dest_path.replace('\\', '/'))
        messagebox.showinfo('Image Added', f'Image added as {img_name}')

    def add_image_to_json(self, date, subject, img_path):
        backup_json()
        found_date = False
        for entry in self.data:
            if entry['date'] == date:
                found_date = True
                for subj in entry['subjects']:
                    if subj['subject'] == subject:
                        subj['images'].append(img_path)
                        break
                else:
                    entry['subjects'].append({'subject': subject, 'images': [img_path]})
                break
        if not found_date:
            self.data.append({'date': date, 'subjects': [{'subject': subject, 'images': [img_path]}]})
        save_json(self.data)
        self.update_subjects()

    def save_entry(self):
        # For manual save (if needed)
        messagebox.showinfo('Saved', 'Entry saved to info.json.')

if __name__ == '__main__':
    app = App()
    app.mainloop()
