import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import requests
from PIL import Image, ImageTk
import win32print
import win32ui
from PIL import ImageWin
import os
import tempfile
import configparser

CONFIG_FILE = "config.ini"


class QRPrinterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Printer App")
        self.root.geometry("500x400")
        self.config = configparser.ConfigParser()
        self.load_config()
        self.url_label = tk.Label(root, text="Введите ссылку:")
        self.url_label.pack(pady=10)
        self.url_entry = tk.Entry(root, width=60)
        self.url_entry.pack(pady=5)
        self.add_context_menu(self.url_entry)
        self.download_button = tk.Button(root, text="Загрузить изображение", command=self.download_image)
        self.download_button.pack(pady=10)
        self.image_label = tk.Label(root)
        self.image_label.pack()
        self.print_button = tk.Button(root, text="Печать", command=self.print_code)
        self.print_button.pack(pady=10)
        self.printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        self.selected_printer = tk.StringVar()
        self.printer_combo = ttk.Combobox(root, values=self.printers, textvariable=self.selected_printer)
        self.printer_combo.pack(pady=5)
        saved_printer = self.config.get("Settings", "printer", fallback="")
        if saved_printer in self.printers:
            self.selected_printer.set(saved_printer)
        else:
            self.selected_printer.set(self.printers[0] if self.printers else "")
        self.printer_combo.bind("<<ComboboxSelected>>", self.save_printer)
        self.generated_image = None

    def add_context_menu(self, widget):

        context_menu = tk.Menu(widget, tearoff=0)
        context_menu.add_command(label="Вставить", command=lambda: widget.event_generate("<<Paste>>"))
        context_menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
        context_menu.add_command(label="Выделить всё", command=lambda: widget.event_generate("<<SelectAll>>"))
        context_menu.add_command(label="Отменить", command=lambda: widget.event_generate("<<Undo>>"))
        widget.bind("<Button-3>", lambda event: context_menu.tk_popup(event.x_root, event.y_root))
        widget.bind("<Control-v>", lambda event: widget.event_generate("<<Paste>>"))
        widget.bind("<Control-c>", lambda event: widget.event_generate("<<Copy>>"))
        widget.bind("<Control-a>", lambda event: widget.event_generate("<<SelectAll>>"))
        widget.bind("<Control-z>", lambda event: widget.event_generate("<<Undo>>"))

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)
        else:
            self.config["Settings"] = {}

    def save_printer(self, event=None):
        printer_name = self.selected_printer.get()
        self.config["Settings"]["printer"] = printer_name
        with open(CONFIG_FILE, "w") as config_file:
            self.config.write(config_file)

    def download_image(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Ошибка", "Введите ссылку!")
            return
        try:
            response = requests.get(url)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            self.generated_image = Image.open(temp_path)
            self.show_image()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {str(e)}")

    def show_image(self):
        img = self.generated_image.resize((200, 200), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk

    def print_code(self):
        if not self.generated_image:
            messagebox.showerror("Ошибка", "Сначала загрузите изображение!")
            return
        printer_name = self.selected_printer.get()
        if not printer_name:
            messagebox.showerror("Ошибка", "Выберите принтер!")
            return
        temp_path = tempfile.mktemp(suffix=".bmp")
        self.generated_image.save(temp_path, format="BMP")
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc("Image Print")
        hdc.StartPage()
        img = Image.open(temp_path)
        dib = ImageWin.Dib(img)
        dib.draw(hdc.GetHandleOutput(), (0, 0, img.size[0], img.size[1]))
        hdc.EndPage()
        hdc.EndDoc()
        hdc.DeleteDC()
        os.remove(temp_path)
        messagebox.showinfo("Успех", "Изображение успешно отправлено на печать!")


if __name__ == "__main__":
    root = tk.Tk()
    app = QRPrinterApp(root)
    root.mainloop()
