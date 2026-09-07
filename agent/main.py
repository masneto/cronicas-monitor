import os
import sys
import time
import platform
import logging
import requests
import psycopg2
import subprocess
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("cronicas-monitor")

SITES = ["https://google.com", "https://youtube.com", "https://rnp.br", "https://cronicas-app.pages.dev"]
PING_HOSTS = ["google.com", "youtube.com", "rnp.br", "cronicas-app.pages.dev"]
VIAIPE_REGION = "norte"


def db_connect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def save_ping(conn, host, rtt_avg, packet_loss):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO ping (host, rtt_avg, packet_loss) VALUES (%s, %s, %s)",
            (host, rtt_avg, packet_loss),
        )
    logger.info("[PING] %s - RTT medio: %.2fms, Perda: %.1f%%", host, rtt_avg, packet_loss)


def save_http(conn, host, latency, status_code):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO http_check (host, latency_ms, status_code) VALUES (%s, %s, %s)",
            (host, latency, status_code),
        )
    latency_str = f"{latency:.2f}ms" if latency is not None else "N/A"
    logger.info("[HTTP] %s - Latencia: %s, Status: %d", host, latency_str, status_code)


def save_viaipe(conn, cliente, disponibilidade, qualidade, consumo_mbps):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO viaipe (cliente, disponibilidade, qualidade, consumo_mbps) VALUES (%s, %s, %s, %s)",
            (cliente, disponibilidade, qualidade, consumo_mbps),
        )
    logger.info(
        "[VIAIPE] %s - Disp: %.2f%%, Qualidade: %s, Consumo: %.2f Mbps",
        cliente, disponibilidade, qualidade, consumo_mbps,
    )


def ping_host(host):
    is_windows = platform.system().lower() == "windows"
    count_flag = "-n" if is_windows else "-c"
    try:
        result = subprocess.run(
            ["ping", count_flag, "4", host],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        logger.warning("[PING] Timeout ao fazer ping em %s", host)
        return None, None
    except OSError as e:
        logger.error("[PING] Comando ping indisponivel: %s", e)
        return None, None

    output = result.stdout
    loss_line = [line for line in output.splitlines() if "packet loss" in line]
    stats_line = [line for line in output.splitlines() if "rtt min" in line]

    if not loss_line or not stats_line:
        logger.warning("[PING] Falha ao obter estatisticas de %s", host)
        return None, None

    try:
        packet_loss = float(loss_line[0].split(",")[2].strip().split("%")[0])
        rtt_avg = float(stats_line[0].split("/")[4])
        return rtt_avg, packet_loss
    except (IndexError, ValueError) as e:
        logger.warning("[PING] Erro ao interpretar resposta do ping para %s: %s", host, e)
        return None, None


def check_http(url):
    start = time.time()
    try:
        r = requests.get(url, timeout=5)
        latency = (time.time() - start) * 1000
        return latency, r.status_code
    except requests.RequestException as e:
        logger.warning("[HTTP] Erro ao acessar %s: %s", url, e)
        return None, None


def fetch_viaipe(region="norte"):
    url = f"https://viaipe.rnp.br/api/{region}"
    logger.info("[VIAIPE] Iniciando chamada a API: %s", url)
    try:
        response = requests.get(url, timeout=10)
        logger.info("[VIAIPE] Status HTTP: %d", response.status_code)

        if response.status_code != 200:
            logger.warning("[VIAIPE] Erro de resposta (HTTP %d): %s", response.status_code, response.text[:300])
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
                for iface in interfaces
                if iface.get("client_side")
            )
            consumo_mbps = consumo_total_bps / (1024 * 1024)

            processed.append({
                "cliente": cliente,
                "disponibilidade": disponibilidade,
                "qualidade": qualidade,
                "consumo_mbps": consumo_mbps,
            })

        return processed

    except requests.RequestException as e:
        logger.error("[VIAIPE] Erro de conexao com API: %s", e)
        return []
    except ValueError as e:
        logger.error("[VIAIPE] Erro ao decodificar JSON: %s", e)
        return []


def main():
    try:
        while True:
            logger.info("Iniciando coleta de metricas...")

            conn = None
            try:
                conn = db_connect()
                logger.info("Conexao com DB estabelecida")

                for host in PING_HOSTS:
                    rtt, loss = ping_host(host)
                    if rtt is not None:
                        save_ping(conn, host, rtt, loss)

                for url in SITES:
                    latency, status = check_http(url)
                    logger.info("URL: %s - Latencia: %s, Status: %s", url, latency, status)
                    if status is not None:
                        save_http(conn, url, latency, status)

                clientes = fetch_viaipe(VIAIPE_REGION)
                for cliente in clientes:
                    save_viaipe(
                        conn,
                        cliente["cliente"],
                        cliente["disponibilidade"],
                        cliente["qualidade"],
                        cliente["consumo_mbps"],
                    )

                conn.commit()
                logger.info("Coleta commitada com sucesso")

            except psycopg2.OperationalError as e:
                logger.error("Erro de conexao com o banco: %s", e)
            except psycopg2.DatabaseError as e:
                logger.error("Erro ao persistir dados: %s", e)
                if conn:
                    conn.rollback()
            except requests.RequestException as e:
                logger.error("Erro de rede durante coleta: %s", e)
            except (KeyError, ValueError) as e:
                logger.error("Erro ao processar dados coletados: %s", e)
            finally:
                if conn and not conn.closed:
                    conn.close()
                    logger.info("Conexao com DB encerrada")

            logger.info("Coleta finalizada. Aguardando 60s...")
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Interrupcao manual recebida. Encerrando o programa...")


if __name__ == "__main__":
    main()
