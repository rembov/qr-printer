import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import requests
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import win32print
import win32ui
from PIL import ImageWin
import os
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class QRPrinterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Printer App")
        self.root.geometry("500x400")

        # Поле ввода ссылки
        self.url_label = tk.Label(root, text="Введите ссылку:")
        self.url_label.pack(pady=10)
        self.url_entry = tk.Entry(root, width=60)
        self.url_entry.pack(pady=5)

        # Кнопка загрузки
        self.download_button = tk.Button(root, text="Загрузить QR-код", command=self.process_link)
        self.download_button.pack(pady=10)

        # Поле для отображения изображения
        self.image_label = tk.Label(root)
        self.image_label.pack()

        # Кнопка печати
        self.print_button = tk.Button(root, text="Печать", command=self.print_code)
        self.print_button.pack(pady=10)

        # Выбор принтера
        self.printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        self.selected_printer = tk.StringVar(value=self.printers[0] if self.printers else "")
        self.printer_combo = ttk.Combobox(root, values=self.printers, textvariable=self.selected_printer)
        self.printer_combo.pack(pady=5)

        self.generated_image = None

    def process_link(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Ошибка", "Введите ссылку!")
            return

        try:
            if url.startswith("blob:"):
                # Обработка ссылки blob: с использованием Selenium
                self.download_blob_image(url)
            elif url.endswith(".pdf"):
                # Обработка PDF-файла
                self.download_pdf(url)
            else:
                # Загрузка изображения по прямой ссылке
                response = requests.get(url)
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    temp_file.write(response.content)
                    self.generated_image = Image.open(temp_file.name)
                    self.show_image()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {str(e)}")

    def download_blob_image(self, url):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)

        try:
            # Ожидание загрузки изображения
            image_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "img"))
            )
            src = image_element.get_attribute("src")
            response = requests.get(src)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_file.write(response.content)
                self.generated_image = Image.open(temp_file.name)
                self.show_image()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение blob: {str(e)}")
        finally:
            driver.quit()

    def download_pdf(self, url):
        response = requests.get(url)
        response.raise_for_status()

        pdf_path = tempfile.mktemp(suffix=".pdf")
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(response.content)

        # Извлечение QR-кода из PDF
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                pix = page.get_pixmap()
                image_path = tempfile.mktemp(suffix=".png")
                pix.save(image_path)
                self.generated_image = Image.open(image_path)
                self.show_image()
                break

    def show_image(self):
        img = self.generated_image.resize((200, 200), Image.ANTIALIAS)
        img_tk = ImageTk.PhotoImage(img)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk

    def print_code(self):
        if not self.generated_image:
            messagebox.showerror("Ошибка", "Сначала загрузите QR-код!")
            return

        printer_name = self.selected_printer.get()
        if not printer_name:
            messagebox.showerror("Ошибка", "Выберите принтер!")
            return

        temp_path = tempfile.mktemp(suffix=".png")
        self.generated_image.save(temp_path)

        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc("QR Code Print")
        hdc.StartPage()

        img = Image.open(temp_path)
        dib = ImageWin.Dib(img)
        dib.draw(hdc.GetHandleOutput(), (0, 0, img.size[0], img.size[1]))

        hdc.EndPage()
        hdc.EndDoc()
        hdc.DeleteDC()

        os.remove(temp_path)
        messagebox.showinfo("Успех", "QR-код успешно отправлен на печать!")

if __name__ == "__main__":
    root = tk.Tk()
    app = QRPrinterApp(root)
    root.mainloop()
