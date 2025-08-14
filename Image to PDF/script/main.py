import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk # Import ImageTk
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import threading

class ImageToPDFConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Imagens para PDF")

        self.source_dir = ""
        self.output_base_dir = ""
        self.image_files_to_process = []

        # Frame para seleção do diretório de origem
        self.frame_source = tk.LabelFrame(root, text="Diretório de Origem", padx=10, pady=10)
        self.frame_source.pack(pady=10, padx=10, fill="x")

        self.btn_select_source_dir = tk.Button(self.frame_source, text="Selecionar Diretório de Origem", command=self.select_source_directory)
        self.btn_select_source_dir.pack(side="left", padx=5, pady=5)

        self.lbl_source_dir = tk.Label(self.frame_source, text="Nenhum diretório de origem selecionado.")
        self.lbl_source_dir.pack(side="left", padx=5, pady=5)

        # Frame para seleção do diretório de saída
        self.frame_output = tk.LabelFrame(root, text="Diretório de Saída", padx=10, pady=10)
        self.frame_output.pack(pady=10, padx=10, fill="x")

        self.btn_select_output_dir = tk.Button(self.frame_output, text="Selecionar Diretório de Saída", command=self.select_output_directory)
        self.btn_select_output_dir.pack(side="left", padx=5, pady=5)

        self.lbl_output_dir = tk.Label(self.frame_output, text="Nenhum diretório de saída selecionado.")
        self.lbl_output_dir.pack(side="left", padx=5, pady=5)

        # Frame para opções de PDF
        self.frame_pdf_options = tk.LabelFrame(root, text="Opções de PDF", padx=10, pady=10)
        self.frame_pdf_options.pack(pady=10, padx=10, fill="x")

        self.pdf_mode = tk.StringVar(value="separados")
        
        self.radio_separados = tk.Radiobutton(
            self.frame_pdf_options, 
            text="PDFs Separados (um PDF por imagem)", 
            variable=self.pdf_mode, 
            value="separados"
        )
        self.radio_separados.pack(anchor="w", padx=5, pady=2)

        self.radio_juntos = tk.Radiobutton(
            self.frame_pdf_options, 
            text="PDFs por Pasta (todas as imagens da mesma pasta em um PDF)", 
            variable=self.pdf_mode, 
            value="juntos"
        )
        self.radio_juntos.pack(anchor="w", padx=5, pady=2)

        # Botão de conversão
        self.btn_convert = tk.Button(root, text="Converter para PDF", command=self.start_conversion_thread)
        self.btn_convert.pack(pady=20)

        # Status
        self.status_label = tk.Label(root, text="")
        self.status_label.pack(pady=5)

        self.loading_window = None
        self.loading_progress_label = None
        self.cigar_faded_tk = None
        self.cigar_filled_tk = None
        self.cigar_canvas = None
        self.cigar_filled_id = None

        # Load cigar images
        try:
            self.cigar_faded_pil = Image.open("cigar_faded.png").resize((200, 50), Image.LANCZOS)
            self.cigar_filled_pil = Image.open("cigar_filled.png").resize((200, 50), Image.LANCZOS)
            self.cigar_faded_tk = ImageTk.PhotoImage(self.cigar_faded_pil)
            self.cigar_filled_tk = ImageTk.PhotoImage(self.cigar_filled_pil)
        except FileNotFoundError:
            messagebox.showerror("Erro de Imagem", "As imagens do charuto (cigar_faded.png, cigar_filled.png) não foram encontradas. Certifique-se de que estão no mesmo diretório do script.")
            self.cigar_faded_tk = None
            self.cigar_filled_tk = None

    def select_source_directory(self):
        directory = filedialog.askdirectory(title="Selecionar Diretório de Origem")
        if directory:
            self.source_dir = directory
            self.lbl_source_dir.config(text=self.source_dir)
            self.image_files_to_process = self._find_image_files(self.source_dir)
            self.status_label.config(text=f"{len(self.image_files_to_process)} imagens encontradas.")

    def select_output_directory(self):
        directory = filedialog.askdirectory(title="Selecionar Diretório de Saída")
        if directory:
            self.output_base_dir = directory
            self.lbl_output_dir.config(text=self.output_base_dir)

    def _find_image_files(self, directory):
        image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
        found_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(image_extensions):
                    found_files.append(os.path.join(root, file))
        return found_files

    def _group_images_by_folder(self, image_files):
        """Agrupa imagens por pasta"""
        folder_groups = {}
        for image_path in image_files:
            relative_path = os.path.relpath(image_path, self.source_dir)
            folder = os.path.dirname(relative_path)
            if folder == "":
                folder = "root"  # Para arquivos na pasta raiz
            
            if folder not in folder_groups:
                folder_groups[folder] = []
            folder_groups[folder].append(image_path)
        
        return folder_groups

    def show_loading_screen(self):
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Convertendo...")
        self.loading_window.transient(self.root)
        self.loading_window.grab_set()

        self.loading_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (250 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (180 // 2) # Adjusted height for cigar
        self.loading_window.geometry(f"250x180+{x}+{y}") # Adjusted height for cigar
        self.loading_window.resizable(False, False)

        tk.Label(self.loading_window, text="Convertendo arquivos... Por favor, aguarde.").pack(pady=10)

        if self.cigar_faded_tk and self.cigar_filled_tk:
            self.cigar_canvas = tk.Canvas(self.loading_window, width=200, height=50, highlightthickness=0)
            self.cigar_canvas.pack(pady=5)
            self.cigar_canvas.create_image(0, 0, anchor=tk.NW, image=self.cigar_faded_tk)
            self.cigar_filled_id = self.cigar_canvas.create_image(0, 0, anchor=tk.NW, image=self.cigar_filled_tk)
            self.cigar_canvas.itemconfig(self.cigar_filled_id, state="hidden") # Initially hidden

        self.loading_progress_label = tk.Label(self.loading_window, text="")
        self.loading_progress_label.pack(pady=5)

    def update_cigar_animation(self, progress):
        if self.cigar_canvas and self.cigar_filled_id:
            fill_width = int(self.cigar_filled_pil.width * progress)
            if fill_width > 0:
                cropped_filled_img = self.cigar_filled_pil.crop((0, 0, fill_width, self.cigar_filled_pil.height))
                self.cigar_filled_tk_cropped = ImageTk.PhotoImage(cropped_filled_img)
                self.cigar_canvas.itemconfig(self.cigar_filled_id, image=self.cigar_filled_tk_cropped, state="normal")
            else:
                self.cigar_canvas.itemconfig(self.cigar_filled_id, state="hidden")
            self.loading_window.update_idletasks()

    def hide_loading_screen(self):
        if self.loading_window:
            self.loading_window.grab_release()
            self.loading_window.destroy()
            self.loading_window = None

    def start_conversion_thread(self):
        if not self.image_files_to_process:
            messagebox.showwarning("Aviso", "Por favor, selecione um diretório com imagens.")
            return
        if not self.output_base_dir:
            messagebox.showwarning("Aviso", "Por favor, selecione um diretório de saída.")
            return

        self.show_loading_screen()
        conversion_thread = threading.Thread(target=self.convert_files)
        conversion_thread.start()

    def convert_files(self):
        try:
            if self.pdf_mode.get() == "separados":
                self._convert_separate_pdfs()
            else:
                self._convert_grouped_pdfs()

            self.root.after(100, lambda: self.conversion_complete(True, "CONVERTEU GOSTOSO COM SUCESSO AINNNN"))

        except Exception as e:
            self.root.after(100, lambda: self.conversion_complete(False, f"Ocorreu um erro durante a conversão: {e}"))

    def _convert_separate_pdfs(self):
        """Converte cada imagem em um PDF separado (comportamento original)"""
        total_files = len(self.image_files_to_process)
        for i, image_path in enumerate(self.image_files_to_process):
            current_progress = (i + 1) / total_files
            self.root.after(0, lambda p=current_progress, name=os.path.basename(image_path): self.loading_progress_label.config(text=f"Processando {i+1}/{total_files}: {name}"))
            self.root.after(0, lambda p=current_progress: self.update_cigar_animation(p))

            relative_path = os.path.relpath(image_path, self.source_dir)
            output_subdir = os.path.dirname(relative_path)
            
            # Ensure output directory exists
            final_output_dir = os.path.join(self.output_base_dir, output_subdir)
            os.makedirs(final_output_dir, exist_ok=True)

            base_name = os.path.basename(image_path)
            pdf_name = os.path.splitext(base_name)[0] + ".pdf"
            pdf_path = os.path.join(final_output_dir, pdf_name)

            img = Image.open(image_path)
            width, height = img.size

            c = canvas.Canvas(pdf_path, pagesize=(width, height))
            c.drawImage(image_path, 0, 0, width, height)
            c.save()

    def _convert_grouped_pdfs(self):
        """Converte imagens agrupadas por pasta em PDFs únicos"""
        folder_groups = self._group_images_by_folder(self.image_files_to_process)
        total_folders = len(folder_groups)
        
        folder_index = 0
        for folder, images in folder_groups.items():
            folder_index += 1
            current_progress = folder_index / total_folders
            
            folder_name = folder if folder != "root" else "pasta_raiz"
            self.root.after(0, lambda p=current_progress, name=folder_name: self.loading_progress_label.config(text=f"Processando pasta {folder_index}/{total_folders}: {name}"))
            self.root.after(0, lambda p=current_progress: self.update_cigar_animation(p))

            # Determinar diretório de saída
            if folder == "root":
                final_output_dir = self.output_base_dir
                pdf_name = "imagens_pasta_raiz.pdf"
            else:
                final_output_dir = os.path.join(self.output_base_dir, folder)
                folder_basename = os.path.basename(folder)
                pdf_name = f"imagens_{folder_basename}.pdf"
            
            os.makedirs(final_output_dir, exist_ok=True)
            pdf_path = os.path.join(final_output_dir, pdf_name)

            # Criar PDF com múltiplas páginas
            c = canvas.Canvas(pdf_path, pagesize=letter)
            
            for image_path in images:
                img = Image.open(image_path)
                width, height = img.size
                
                # Ajustar tamanho da página para a imagem
                c.setPageSize((width, height))
                c.drawImage(image_path, 0, 0, width, height)
                c.showPage()  # Nova página para próxima imagem
            
            c.save()

    def conversion_complete(self, success, message):
        self.hide_loading_screen()
        if success:
            messagebox.showinfo("Sucesso", message)
            self.status_label.config(text="Conversão concluída.")
        else:
            messagebox.showerror("Erro", message)
            self.status_label.config(text="Erro na conversão.")

if __name__ == '__main__':
    root = tk.Tk()
    app = ImageToPDFConverter(root)
    root.mainloop()

