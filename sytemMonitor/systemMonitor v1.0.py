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
# CONFIGURAÇÕES DO SUPABASE
# ==========================================
SUPABASE_URL = "https://hcyyvetgzscnzjxlwkcj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhjeXl2ZXRnenNjbnpqeGx3a2NqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc0NjgxNjMsImV4cCI6MjEwMzA0NDE2M30.7aTHDGL70L05IIvJZHNx5GjdYdozmpewITiqhaAz1NQ"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# Caminho para salvar o cache local na pasta temporária do Windows
CACHE_FILE = os.path.join(os.environ.get("TEMP", "C:\\"), "client_monitor_cache.json")


def obter_mac_address():
    """Captura o MAC Address principal da placa de rede ativa (Cabo ou Wi-Fi)"""
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
print(f"MAC Address identificado: {MAC_ADDRESS}")
print(f"Nome da máquina: {obter_nome_maquina()}")


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


def sincronizar_com_supabase():
    """Sem try/except: vai exibir qualquer erro de conexão ou requisição na tela"""
    nome_atual = obter_nome_maquina()
    url = f"{SUPABASE_URL}/rest/v1/equipamentos?mac_address=eq.{MAC_ADDRESS}"
    
    print(f"Consultando Supabase em: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=10)
    print(f"Status da resposta GET: {resp.status_code}")
    
    if resp.status_code == 200:
        dados_servidor = resp.json()
        if len(dados_servidor) > 0:
            maquina = dados_servidor[0]
            
            if maquina.get("nome_maquina") != nome_atual:
                print("Atualizando nome da máquina no Supabase...")
                patch_resp = requests.patch(
                    f"{SUPABASE_URL}/rest/v1/equipamentos?id=eq.{maquina['id']}", 
                    json={"nome_maquina": nome_atual}, 
                    headers=HEADERS, 
                    timeout=10
                )
                print(f"Status patch nome: {patch_resp.status_code}")
                maquina["nome_maquina"] = nome_atual
            
            return maquina
        else:
            print("Máquina não encontrada no Supabase. Criando registro inicial...")
            payload = {
                "mac_address": MAC_ADDRESS,
                "nome_maquina": nome_atual,
                "limite_horas": 3.0,
                "minutos_usados_hoje": 0,
                "data_ultimo_registro": str(datetime.date.today()),
            }
            resp_post = requests.post(f"{SUPABASE_URL}/rest/v1/equipamentos", json=payload, headers=HEADERS, timeout=10)
            print(f"Status POST criação: {resp_post.status_code} - Resposta: {resp_post.text}")
            if resp_post.status_code == 201:
                return resp_post.json()[0]
    else:
        print(f"Erro retornado pelo Supabase: {resp.text}")
    
    return None


def enviar_atualizacao_servidor(maquina_id, minutos, hoje):
    url_patch = f"{SUPABASE_URL}/rest/v1/equipamentos?id=eq.{maquina_id}"
    payload_update = {
        "minutos_usados_hoje": minutos,
        "data_ultimo_registro": hoje,
        "status_online": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    resp = requests.patch(url_patch, json=payload_update, headers=HEADERS, timeout=10)
    print(f"Atualização enviada para a nuvem. Status: {resp.status_code}")
    return True


def salvar_historico_dia_anterior(data_anterior, minutos, nome_maquina):
    url_historico = f"{SUPABASE_URL}/rest/v1/historico_uso"
    payload = {
        "mac_address": MAC_ADDRESS,
        "nome_maquina": nome_maquina,
        "data": data_anterior,
        "minutos_usados": minutos,
    }
    requests.post(url_historico, json=payload, headers=HEADERS, timeout=10)


def desligar_maquina():
    print("Limite diário atingido. Disparando aviso de desligamento...")
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
    data_ultima = cache.get("data", str(datetime.date.today()))
    
    maquina_id = None

    while True:
        hoje = str(datetime.date.today())

        # Sincroniza (agora exibindo erros se houverem)
        dados_nuvem = sincronizar_com_supabase()
        
        if dados_nuvem:
            maquina_id = dados_nuvem.get("id")
            limite_horas = float(dados_nuvem.get("limite_horas", 3.0))
            minutos_nuvem = dados_nuvem.get("minutos_usados_hoje", 0)
            data_registro = dados_nuvem.get("data_ultimo_registro")
            
            if data_registro and data_registro != hoje:
                if minutos_nuvem > 0:
                    salvar_historico_dia_anterior(data_registro, minutos_nuvem, dados_nuvem.get("nome_maquina"))
                minutos_atuais = 0
            else:
                minutos_atuais = max(minutos_atuais, minutos_nuvem)
        
        if data_ultima != hoje:
            minutos_atuais = 0
            data_ultima = hoje

        minutos_atuais += 1
        limite_em_minutos = limite_horas * 60

        salvar_cache_local(limite_horas, minutos_atuais, hoje)

        if maquina_id:
            enviar_atualizacao_servidor(maquina_id, minutos_atuais, hoje)

        print(f"Tempo usado hoje: {minutos_atuais} min / Limite: {limite_em_minutos} min")

        if minutos_atuais >= limite_em_minutos:
            desligar_maquina()
            break

        time.sleep(60)


if __name__ == "__main__":
    monitorar()
