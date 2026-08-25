import datetime
import json
import os
import re
import socket
import subprocess
import time
import uuid
import requests

# ==========================================
# CONFIGURAÇÕES DO SUPABASE (Configuradas)
# ==========================================
SUPABASE_URL = "https://hcyyvetgzscnzjxlwkcj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhjeXl2ZXRnenNjbnpqeGx3a2NqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc0NjgxNjMsImV4cCI6MjEwMzA0NDE2M30.7aTHDGL70L05IIvJZHNx5GjdYdozmpewITiqhaAz1NQ"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# Caminho para o cache local na pasta temporária do Windows
CACHE_FILE = os.path.join(os.environ.get("TEMP", "C:\\"), "client_monitor_cache.json")


def obter_mac_address():
    try:
        output = subprocess.check_output("getmac /fo list /v", shell=True, text=True, encoding="cp850")
        linhas = output.split('\n')
        for i, linha in enumerate(linhas):
            if "Conectado" in linha or "Connected" in linha:
                for j in range(max(0, i-5), min(len(linhas), i+5)):
                    match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", linhas[j])
                    if match:
                        return match.group(0).replace("-", ":").upper()
    except Exception:
        pass
    
    mac = uuid.getnode()
    return ":".join([f"{(mac >> ele) & 0xFF:02x}" for ele in range(0, 8 * 6, 8)][::-1]).upper()


def obter_nome_maquina():
    return socket.gethostname()


MAC_ADDRESS = obter_mac_address()


def carregar_cache_local():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"limite_horas": 3.0, "minutos_usados_hoje": 0, "data": str(datetime.date.today())}


def salvar_cache_local(limite, minutos, data):
    dados = {
        "limite_horas": limite,
        "minutos_usados_hoje": minutos,
        "data": data
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f)


def salvar_historico_dia_anterior(data_anterior, minutos, nome_maquina):
    try:
        url_historico = f"{SUPABASE_URL}/rest/v1/historico_uso"
        payload = {
            "mac_address": MAC_ADDRESS,
            "nome_maquina": nome_maquina,
            "data": data_anterior,
            "minutos_usados": minutos,
        }
        requests.post(url_historico, json=payload, headers=HEADERS, timeout=10)
    except Exception:
        pass


def sincronizar_com_supabase():
    try:
        nome_atual = obter_nome_maquina()
        url = f"{SUPABASE_URL}/rest/v1/equipamentos?mac_address=eq.{MAC_ADDRESS}"
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        if resp.status_code == 200:
            dados_servidor = resp.json()
            if len(dados_servidor) > 0:
                maquina = dados_servidor[0]
                
                if maquina.get("nome_maquina") != nome_atual:
                    requests.patch(
                        f"{SUPABASE_URL}/rest/v1/equipamentos?id=eq.{maquina['id']}", 
                        json={"nome_maquina": nome_atual}, 
                        headers=HEADERS, 
                        timeout=10
                    )
                    maquina["nome_maquina"] = nome_atual
                
                return maquina
            else:
                payload = {
                    "mac_address": MAC_ADDRESS,
                    "nome_maquina": nome_atual,
                    "limite_horas": 3.0,
                    "minutos_usados_hoje": 0,
                    "data_ultimo_registro": str(datetime.date.today()),
                }
                resp_post = requests.post(f"{SUPABASE_URL}/rest/v1/equipamentos", json=payload, headers=HEADERS, timeout=10)
                if resp_post.status_code == 201:
                    return resp_post.json()[0]
    except Exception:
        pass
    return None


def enviar_atualizacao_servidor(maquina_id, minutos, hoje):
    try:
        url_patch = f"{SUPABASE_URL}/rest/v1/equipamentos?id=eq.{maquina_id}"
        payload_update = {
            "minutos_usados_hoje": minutos,
            "data_ultimo_registro": hoje,
            "status_online": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        requests.patch(url_patch, json=payload_update, headers=HEADERS, timeout=10)
    except Exception:
        pass


def desligar_maquina():
    subprocess.run([
        "shutdown",
        "/s",
        "/f",
        "/t",
        "120",
        "/c",
        "O limite diario foi atingido, o computador desligara em 2 minutos. Salve seus arquivos!",
    ])


def monitorar():
    cache = carregar_cache_local()
    limite_horas = float(cache.get("limite_horas", 3.0))
    minutos_atuais = int(cache.get("minutos_usados_hoje", 0))
    data_cache = cache.get("data", str(datetime.date.today()))
    
    hoje = str(datetime.date.today())

    # Garante o reset imediato se o dia mudou desde o último uso
    if data_cache != hoje:
        if minutos_atuais > 0:
            salvar_historico_dia_anterior(data_cache, minutos_atuais, obter_nome_maquina())
        minutos_atuais = 0
        data_cache = hoje
        salvar_cache_local(limite_horas, minutos_atuais, hoje)

    maquina_id = None

    while True:
        hoje = str(datetime.date.today())

        dados_nuvem = sincronizar_com_supabase()
        
        if dados_nuvem:
            maquina_id = dados_nuvem.get("id")
            limite_horas = float(dados_nuvem.get("limite_horas", 3.0))
            minutos_nuvem = dados_nuvem.get("minutos_usados_hoje", 0)
            data_registro_nuvem = dados_nuvem.get("data_ultimo_registro")
            
            if data_registro_nuvem and data_registro_nuvem != hoje:
                if minutos_nuvem > 0:
                    salvar_historico_dia_anterior(data_registro_nuvem, minutos_nuvem, dados_nuvem.get("nome_maquina"))
                minutos_nuvem = 0
                enviar_atualizacao_servidor(maquina_id, 0, hoje)

            minutos_atuais = max(minutos_atuais, minutos_nuvem)

        minutos_atuais += 1
        limite_em_minutos = limite_horas * 60

        salvar_cache_local(limite_horas, minutos_atuais, hoje)

        if maquina_id:
            enviar_atualizacao_servidor(maquina_id, minutos_atuais, hoje)

        if minutos_atuais >= limite_em_minutos:
            desligar_maquina()
            break

        time.sleep(60)


if __name__ == "__main__":
    monitorar()