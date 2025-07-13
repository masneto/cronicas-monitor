import os
import time
import requests
import psycopg2
import subprocess
from datetime import datetime

print("🚀 Entrando no container")
print("🧪 DB_HOST:", os.getenv("DB_HOST"))

os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/certs/ca-certificates.crt'
SITES = ["https://google.com", "https://youtube.com", "https://rnp.br", "https://cronicas-app.pages.dev"]
PING_HOSTS = ['google.com', 'youtube.com', 'rnp.br', 'cronicas-app.pages.dev']
VIAIPE_REGION = "norte"

# SITES = ["https://google.com", "https://youtube.com", "https://rnp.br", "https://cronicas-app.pages.dev"]
# PING_HOSTS = ["8.8.8.8", "1.1.1.1"]

# def db_connect():
#     return psycopg2.connect(
#         host=os.getenv("DB_HOST"),
#         port=os.getenv("DB_PORT"),
#         dbname=os.getenv("DB_NAME"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD")
#     )

def db_connect():
    env_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [var for var in env_vars if not os.getenv(var)]

    if missing:
        raise Exception(f"❌ Variáveis de ambiente ausentes: {', '.join(missing)}")

    print("🔌 Tentando conectar ao banco com as seguintes variáveis:")
    print(f"  - DB_HOST: {os.getenv('DB_HOST')}")
    print(f"  - DB_NAME: {os.getenv('DB_NAME')}")
    print(f"  - DB_USER: {os.getenv('DB_USER')}")
    print(f"  - DB_PORT: {os.getenv('DB_PORT')}")

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def save_ping(conn, host, rtt_avg, packet_loss):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO ping (host, rtt_avg, packet_loss) VALUES (%s, %s, %s)",
            (host, rtt_avg, packet_loss)
        )
        conn.commit()
    print(f"[PING] {host} - RTT médio: {rtt_avg:.2f}ms, Perda: {packet_loss:.1f}%")

def save_http(conn, host, latency, status_code):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO http_check (host, latency_ms, status_code) VALUES (%s, %s, %s)",
            (host, latency, status_code)
        )
        conn.commit()
    print(f"[HTTP] {host} - Latência: {latency:.2f}ms, Status: {status_code}")

def save_viaipe(conn, cliente, disponibilidade, qualidade, consumo_mbps):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO viaipe (cliente, disponibilidade, qualidade, consumo_mbps) VALUES (%s, %s, %s, %s)",
            (cliente, disponibilidade, qualidade, consumo_mbps)
        )
        conn.commit()
    print(f"[VIAIPE] {cliente} - Disp: {disponibilidade:.2f}%, Qualidade: {qualidade}, Consumo: {consumo_mbps:.2f} Mbps")

# def ping_host(host):
#     result = subprocess.run(
#         ["ping", "-c", "4", host],
#         capture_output=True, text=True
#     )

#     output = result.stdout
#     loss_line = [line for line in output.splitlines() if "packet loss" in line]
#     stats_line = [line for line in output.splitlines() if "rtt min" in line]

#     if not loss_line or not stats_line:
#         print(f"[PING] Falha ao obter estatísticas de {host}")
#         return None, None

#     try:
#         packet_loss = float(loss_line[0].split(",")[2].strip().split("%")[0])
#         rtt_avg = float(stats_line[0].split("/")[4])
#         return rtt_avg, packet_loss
#     except Exception as e:
#         print(f"[PING] Erro ao interpretar resposta do ping para {host}: {e}")
#         return None, None

def ping_host(host):
    return 10.0, 0.0  # Simulação de resposta para testes

def check_http(url):
    start = time.time()
    try:
        r = requests.get(url, timeout=5)
        latency = (time.time() - start) * 1000
        return latency, r.status_code
    except Exception as e:
        print(f"[HTTP] Erro ao acessar {url}: {e}")
        return None, None

def fetch_viaipe(region="norte"):
    url = f"https://viaipe.rnp.br/api/{region}"
    print(f"[VIAIPE] Iniciando chamada à API: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"[VIAIPE] Status HTTP: {response.status_code}")

        if response.status_code != 200:
            print(f"[VIAIPE] Erro de resposta: {response.text[:300]}")
            return []

        raw_data = response.json()
        processed = []

        for item in raw_data:
            cliente = item.get("name", "Desconhecido")
            smoke = item.get("data", {}).get("smoke", {})
            interfaces = item.get("data", {}).get("interfaces", [])

            avg_loss = smoke.get("avg_loss", 1.0)
            disponibilidade = max(0.0, 100.0 * (1.0 - avg_loss))

            if avg_loss < 0.1:
                qualidade = "Boa"
            elif avg_loss < 0.3:
                qualidade = "Regular"
            else:
                qualidade = "Ruim"

            consumo_total_bps = sum(
                iface.get("avg_in", 0.0) + iface.get("avg_out", 0.0)
                for iface in interfaces if iface.get("client_side")
            )
            consumo_mbps = consumo_total_bps / (1024 * 1024)

            processed.append({
                "cliente": cliente,
                "disponibilidade": disponibilidade,
                "qualidade": qualidade,
                "consumo_mbps": consumo_mbps
            })

        return processed

    except Exception as e:
        print(f"[VIAIPE] Erro ao acessar API: {e}")
        return []

def main():
    while True:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando coleta de métricas...")

        try:
            conn = db_connect()
            print("✅ Conexão com DB iniciada")

            for host in PING_HOSTS:
                rtt, loss = ping_host(host)
                if rtt is not None:
                    save_ping(conn, host, rtt, loss)

            for url in SITES:
                latency, status = check_http(url)
                if status is None:
                    save_http(conn, url, None, 0)
                else:
                    save_http(conn, url, latency, status)                
                # if latency is not None:
                #     save_http(conn, url, latency, status)
                print(url, latency, status)

            clientes = fetch_viaipe(VIAIPE_REGION)
            for cliente in clientes:
                save_viaipe(
                    conn,
                    cliente["cliente"],
                    cliente["disponibilidade"],
                    cliente["qualidade"],
                    cliente["consumo_mbps"]
                )

            conn.close()
        except Exception as e:
            print(f"[ERRO] {e}")

        print("Coleta finalizada. Aguardando 60s...\n")
        time.sleep(60)

# if __name__ == "__main__":
#     main()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        time.sleep(20)