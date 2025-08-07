from PIL import Image
import os
import tkinter as tk
from tkinter import filedialog

# Abre popup para o usuário escolher a pasta raiz
janela = tk.Tk()
janela.withdraw() # Oculta janela principal
pasta_raiz = filedialog.askdirectory(title="Selecione a pasta raiz com as imagens")

# Verifica se uma pasta foi escolhida
if not pasta_raiz:
    print("⚠️ Nenhuma pasta selecionada. Encerrando script.")
    exit()

# Percorre as subpastas e salva PDFs em uma subpasta 'pdfs' dentro de cada uma
for dirpath, _, arquivos in os.walk(pasta_raiz):
    for arquivo in arquivos:
        if arquivo.lower().endswith(('.jpg', '.jpeg', '.png')):
            caminho_imagem = os.path.join(dirpath, arquivo)
            imagem = Image.open(caminho_imagem).convert('RGB')

# Cria subpasta 'pdfs' na mesma pasta da imagem
            subpasta_pdf = os.path.join(dirpath, "pdfs")
            os.makedirs(subpasta_pdf, exist_ok=True)
            nome_pdf = os.path.splitext(arquivo)[0] + ".pdf"
            caminho_pdf = os.path.join(subpasta_pdf, nome_pdf)
            imagem.save(caminho_pdf)

            print(f"✅ PDF salvo: {caminho_pdf}")
