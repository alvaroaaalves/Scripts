import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os
from PIL import Image as PILImage, ImageTk  # Pillow (PIL)


class BudgetApp:
    def __init__(self, master):
        self.master = master
        master.title("ALTH Informática - Tecnologia e Desenvolvimento")
        master.geometry("900x750")  # Aumentado o tamanho da janela

        # Definir ícone da janela
        try:
            self.icon_image = PILImage.open("alth.png")  # Carrega a imagem
            self.icon_photo = ImageTk.PhotoImage(self.icon_image)  # Converte para PhotoImage
            master.iconphoto(True, self.icon_photo)  # Define o ícone da janela
        except FileNotFoundError:
            print("Arquivo alth.png não encontrado. O ícone da janela não será definido.")
        except Exception as e:
            print(f"Erro ao carregar o ícone da janela: {e}")

        # Notebook para organizar as abas (Cliente, Aparelho, Serviços)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, expand=True, fill="both")

        # Aba Cliente
        self.client_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.client_frame, text="Cliente")
        self.create_client_tab(self.client_frame)

        # Aba Aparelho
        self.device_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.device_frame, text="Aparelho")
        self.create_device_tab(self.device_frame)

        # Aba Serviços
        self.services_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.services_frame, text="Serviços")
        self.create_services_tab(self.services_frame)

        # Aba Resumo e Geração de PDF
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Resumo/PDF")
        self.create_summary_tab(self.summary_frame)

    def create_client_tab(self, frame):
        # Labels e Entries para dados do cliente
        tk.Label(frame, text="Nome Completo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.client_name_entry = tk.Entry(frame, width=60)
        self.client_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(frame, text="Telefone:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.client_phone_entry = tk.Entry(frame, width=60)
        self.client_phone_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(frame, text="Email (Opcional):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.client_email_entry = tk.Entry(frame, width=60)
        self.client_email_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        frame.columnconfigure(1, weight=1)

    def create_device_tab(self, frame):
        # Labels e Entries para dados do aparelho
        tk.Label(frame, text="Marca:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.device_brand_entry = tk.Entry(frame, width=60)
        self.device_brand_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(frame, text="Modelo:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.device_model_entry = tk.Entry(frame, width=60)
        self.device_model_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(frame, text="IMEI (Opcional):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.device_imei_entry = tk.Entry(frame, width=60)
        self.device_imei_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Correção da caixa de texto "Problema Relatado"
        tk.Label(frame, text="Problema Relatado:").grid(row=3, column=0, padx=5, pady=5, sticky="nw")
        self.device_problem_text = tk.Text(frame, width=60, height=10)  # Altura inicial
        self.device_problem_text.grid(row=3, column=1, padx=5, pady=5, sticky="nsew")  # sticky="nsew" para expandir

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)  # Permite que a linha 3 (onde está o Text) se expanda

    def create_services_tab(self, frame):
        self.services_list = []  # Lista para armazenar os Entry widgets de serviço

        # Cabeçalho da tabela de serviços
        tk.Label(frame, text="Descrição do Serviço/Peça").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(frame, text="Valor Unitário").grid(row=0, column=1, padx=5, pady=5)
        tk.Label(frame, text="Quantidade").grid(row=0, column=2, padx=5, pady=5)
        tk.Label(frame, text="Subtotal").grid(row=0, column=3, padx=5, pady=5)

        self.services_canvas = tk.Canvas(frame)
        self.services_canvas.grid(row=1, column=0, columnspan=4, sticky="nsew")

        self.services_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.services_canvas.yview)
        self.services_scrollbar.grid(row=1, column=4, sticky="ns")

        self.services_canvas.configure(yscrollcommand=self.services_scrollbar.set)
        self.services_canvas.bind("<Configure>", lambda e: self.services_canvas.configure(scrollregion=self.services_canvas.bbox("all")))

        self.services_inner_frame = ttk.Frame(self.services_canvas)
        self.services_canvas.create_window((0, 0), window=self.services_inner_frame, anchor="nw")

        # Totalizadores - MOVIDOS PARA ANTES DE add_service_row()
        tk.Label(frame, text="Subtotal dos Serviços:").grid(row=3, column=2, padx=5, pady=5, sticky="e")
        self.total_services_label = tk.Label(frame, text="R$ 0.00")
        self.total_services_label.grid(row=3, column=3, padx=5, pady=5, sticky="w")

        tk.Label(frame, text="Desconto (R$):").grid(row=4, column=2, padx=5, pady=5, sticky="e")
        self.discount_entry = tk.Entry(frame, width=10)
        self.discount_entry.grid(row=4, column=3, padx=5, pady=5, sticky="w")
        self.discount_entry.insert(0, "0.00")
        self.discount_entry.bind("<KeyRelease>", self.calculate_total)

        tk.Label(frame, text="Valor Total Final:").grid(row=5, column=2, padx=5, pady=5, sticky="e")
        self.final_total_label = tk.Label(frame, text="R$ 0.00", font=("Arial", 12, "bold"))
        self.final_total_label.grid(row=5, column=3, padx=5, pady=5, sticky="w")

        self.add_service_row()  # Adiciona a primeira linha de serviço

        # Botões para adicionar/remover serviço
        add_button = tk.Button(frame, text="Adicionar Serviço", command=self.add_service_row)
        add_button.grid(row=2, column=0, padx=5, pady=5)

        remove_button = tk.Button(frame, text="Remover Último Serviço", command=self.remove_service_row)
        remove_button.grid(row=2, column=1, padx=5, pady=5)

        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.rowconfigure(1, weight=1)

    def add_service_row(self):
        row_num = len(self.services_list) + 1

        desc_entry = tk.Entry(self.services_inner_frame, width=50)
        desc_entry.grid(row=row_num, column=0, padx=5, pady=2, sticky="ew")

        value_entry = tk.Entry(self.services_inner_frame, width=15)
        value_entry.grid(row=row_num, column=1, padx=5, pady=2, sticky="ew")
        value_entry.insert(0, "0.00")
        value_entry.bind("<KeyRelease>", self.calculate_total)

        qty_entry = tk.Entry(self.services_inner_frame, width=10)
        qty_entry.grid(row=row_num, column=2, padx=5, pady=2, sticky="ew")
        qty_entry.insert(0, "1")
        qty_entry.bind("<KeyRelease>", self.calculate_total)

        subtotal_label = tk.Label(self.services_inner_frame, text="R$ 0.00")
        subtotal_label.grid(row=row_num, column=3, padx=5, pady=2, sticky="w")

        self.services_list.append({
            "desc": desc_entry,
            "value": value_entry,
            "qty": qty_entry,
            "subtotal_label": subtotal_label
        })
        self.services_inner_frame.update_idletasks()
        self.services_canvas.config(scrollregion=self.services_canvas.bbox("all"))
        self.calculate_total()

    def remove_service_row(self):
        if self.services_list:
            last_service = self.services_list.pop()
            last_service["desc"].destroy()
            last_service["value"].destroy()
            last_service["qty"].destroy()
            last_service["subtotal_label"].destroy()
            self.services_inner_frame.update_idletasks()
            self.services_canvas.config(scrollregion=self.services_canvas.bbox("all"))
            self.calculate_total()

    def calculate_total(self, event=None):
        total_services_cost = 0.0
        for service in self.services_list:
            try:
                value = float(service["value"].get().replace(",", "."))
                qty = int(service["qty"].get())
                subtotal = value * qty
                service["subtotal_label"].config(text=f"R$ {subtotal:.2f}")
                total_services_cost += subtotal
            except ValueError:
                service["subtotal_label"].config(text="R$ 0.00")

        # Garante que os labels existam antes de tentar configurá-los
        if hasattr(self, "total_services_label"):
            self.total_services_label.config(text=f"R$ {total_services_cost:.2f}")

        try:
            discount = float(self.discount_entry.get().replace(",", "."))
        except ValueError:
            discount = 0.0

        final_total = total_services_cost - discount
        if hasattr(self, "final_total_label"):
            self.final_total_label.config(text=f"R$ {final_total:.2f}")

    def create_summary_tab(self, frame):
        tk.Label(frame, text="Condições de Pagamento:").pack(pady=5, padx=5, anchor="w")
        self.payment_conditions_text = tk.Text(frame, width=80, height=8)
        self.payment_conditions_text.pack(pady=5, padx=5, fill="x")

        tk.Label(frame, text="Observações:").pack(pady=5, padx=5, anchor="w")
        self.observations_text = tk.Text(frame, width=80, height=12)
        self.observations_text.pack(pady=5, padx=5, fill="x")

        generate_pdf_button = tk.Button(frame, text="Gerar Orçamento em PDF", command=self.generate_pdf)
        generate_pdf_button.pack(pady=20)

    def generate_pdf(self):
        # Coleta de dados
        client_name = self.client_name_entry.get()
        client_phone = self.client_phone_entry.get()
        client_email = self.client_email_entry.get()

        device_brand = self.device_brand_entry.get()
        device_model = self.device_model_entry.get()
        device_imei = self.device_imei_entry.get()
        device_problem = self.device_problem_text.get("1.0", tk.END).strip()

        services_data = []
        for service in self.services_list:
            desc = service["desc"].get()
            value = service["value"].get().replace(",", ".")
            qty = service["qty"].get()
            # Pega o subtotal diretamente do label, que já está formatado
            subtotal = service["subtotal_label"].cget("text").replace("R$", "").strip()
            services_data.append([desc, value, qty, subtotal])

        total_services_cost = self.total_services_label.cget("text").replace("R$", "").strip()
        discount_str_raw = self.discount_entry.get().replace(",", ".")
        try:
            discount_value = float(discount_str_raw)
        except ValueError:
            discount_value = 0.0
        discount_str = f"{discount_value:.2f}"
        final_total = self.final_total_label.cget("text").replace("R$", "").strip()

        payment_conditions = self.payment_conditions_text.get("1.0", tk.END).strip()
        observations = self.observations_text.get("1.0", tk.END).strip()

        if not client_name or not client_phone or not device_brand or not device_model or not services_data:
            messagebox.showwarning("Dados Incompletos", "Por favor, preencha todos os campos obrigatórios (Nome, Telefone, Marca, Modelo e pelo menos um serviço).")
            return

        # Salvar o arquivo PDF
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                               filetypes=[("Arquivos PDF", "*.pdf")],
                                               initialfile=f"Orcamento_{client_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf")
        if not file_path:
            return

        try:
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()

            # Estilos personalizados (nomes únicos para evitar conflito com o sample style sheet)
            if "TitleStyle" not in styles.byName:
                styles.add(ParagraphStyle(name='TitleStyle', fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=12))
            if "Heading2Custom" not in styles.byName:
                styles.add(ParagraphStyle(name='Heading2Custom', fontSize=14, leading=18, spaceAfter=6, textColor=colors.darkblue))
            if "BodyTextCustom" not in styles.byName:
                styles.add(ParagraphStyle(name='BodyTextCustom', fontSize=10, leading=12, spaceAfter=6))
            if "BoldBodyText" not in styles.byName:
                styles.add(ParagraphStyle(name='BoldBodyText', fontSize=10, leading=12, spaceAfter=6, fontName='Helvetica-Bold'))
            if "TotalStyle" not in styles.byName:
                styles.add(ParagraphStyle(name='TotalStyle', fontSize=12, leading=14, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.red))

            # Conteúdo do PDF
            story = []

            # Adicionar logo ao PDF
            try:
                logo_path = "alth.png"
                if os.path.exists(logo_path):
                    img_width = 1.5 * inch
                    # a classe Image do platypus já calcula a altura; passamos width e height
                    logo = RLImage(logo_path, width=img_width, height=None)
                    story.append(logo)
                    story.append(Spacer(1, 0.1 * inch))
                else:
                    story.append(Paragraph("ALTH Informática", styles["TitleStyle"]))
            except Exception as e:
                print(f"Erro ao adicionar logo ao PDF: {e}")
                story.append(Paragraph("ALTH Informática", styles["TitleStyle"]))

            story.append(Paragraph("Orçamento de Serviço", styles["TitleStyle"]))
            story.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["BodyTextCustom"]))
            story.append(Spacer(1, 0.2 * inch))

            # Dados do Cliente
            story.append(Paragraph("Dados do Cliente:", styles["Heading2Custom"]))
            story.append(Paragraph(f"<b>Nome:</b> {client_name}", styles["BodyTextCustom"]))
            story.append(Paragraph(f"<b>Telefone:</b> {client_phone}", styles["BodyTextCustom"]))
            if client_email: 
                story.append(Paragraph(f"<b>Email:</b> {client_email}", styles["BodyTextCustom"]))
            story.append(Spacer(1, 0.2 * inch))

            # Dados do Aparelho
            story.append(Paragraph("Dados do Aparelho:", styles["Heading2Custom"]))
            story.append(Paragraph(f"<b>Marca:</b> {device_brand}", styles["BodyTextCustom"]))
            story.append(Paragraph(f"<b>Modelo:</b> {device_model}", styles["BodyTextCustom"]))
            if device_imei: 
                story.append(Paragraph(f"<b>IMEI:</b> {device_imei}", styles["BodyTextCustom"]))
            story.append(Paragraph(f"<b>Problema Relatado:</b> {device_problem}", styles["BodyTextCustom"]))
            story.append(Spacer(1, 0.2 * inch))

            # Tabela de Serviços
            story.append(Paragraph("Serviços e Peças:", styles["Heading2Custom"]))
            table_data = [['Descrição', 'Valor Unit.', 'Qtd.', 'Subtotal']]
            for item in services_data:
                table_data.append(item)
            
            table_style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ])
            # Ajuste de colWidths para melhor visualização
            service_table = Table(table_data, colWidths=[3.5*inch, 1*inch, 0.7*inch, 1*inch])
            service_table.setStyle(table_style)
            story.append(service_table)
            story.append(Spacer(1, 0.2 * inch))

            # Resumo de Valores
            story.append(Paragraph(f"<b>Subtotal dos Serviços:</b> R$ {total_services_cost}", styles["BoldBodyText"]))
            if discount_value > 0: 
                story.append(Paragraph(f"<b>Desconto:</b> R$ {discount_str}", styles["BoldBodyText"]))
            story.append(Paragraph(f"<b>Valor Total Final:</b> R$ {final_total}", styles["TotalStyle"]))
            story.append(Spacer(1, 0.2 * inch))

            # Condições de Pagamento e Observações
            story.append(Paragraph("Condições de Pagamento:", styles["Heading2Custom"]))
            story.append(Paragraph(payment_conditions if payment_conditions else "Não informado.", styles["BodyTextCustom"]))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("Observações:", styles["Heading2Custom"]))
            story.append(Paragraph(observations if observations else "Nenhuma observação.", styles["BodyTextCustom"]))
            story.append(Spacer(1, 0.5 * inch))

            # Rodapé para assinatura
            story.append(Paragraph("______________________________________", styles["BodyTextCustom"]))
            story.append(Paragraph("Assinatura do Cliente", styles["BodyTextCustom"]))
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph("______________________________________", styles["BodyTextCustom"]))
            story.append(Paragraph("Assinatura do Técnico", styles["BodyTextCustom"]))

            doc.build(story)
            messagebox.showinfo("Sucesso", "Orçamento gerado com sucesso!")

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao gerar o PDF: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()
