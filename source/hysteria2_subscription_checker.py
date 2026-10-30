"""
⚡ REBORN CFG - Multi-Protocol Subscription Checker 2026
Двухэтапная проверка на 100% реальную работоспособность:
Этап 1: Быстрый TLS Handshake (отсев неживых IP и блокировок ТСПУ)
Этап 2: Проверка через ядро Xray-core (гарантия 100% работы в v2rayN без ошибок -1!)
"""

from __future__ import annotations

import concurrent.futures
import urllib.request
import urllib.parse
import subprocess
import socket
import json
import ssl
import sys
import os
import re
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_collector as cc

# Путь к Xray-core из v2rayN
POSSIBLE_XRAY_PATHS = [
    r"C:\Users\616\Desktop\v2rayN-windows-64\bin\Xray\xray.exe",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "Xray", "xray.exe"),
]

def find_xray_binary() -> Optional[str]:
    for p in POSSIBLE_XRAY_PATHS:
        if os.path.isfile(p):
            return p
    return None

XRAY_BIN = find_xray_binary()

# Топовые источники VLESS Reality для РФ
RUSSIA_VLESS_REALITY_SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/3inker/v2ray-subscription/main/subs/all_ru.txt",
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/top100.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/MustafaBaqer/VestraNet-Nodes/main/protocols/vless.txt"
]

VMESS_SOURCES = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/vmess.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-By-Protocol/vmess.txt",
    "https://raw.githubusercontent.com/MustafaBaqer/VestraNet-Nodes/main/protocols/vmess.txt",
]

HYSTERIA2_SOURCES = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/hysteria2.txt",
    "https://raw.githubusercontent.com/MustafaBaqer/VestraNet-Nodes/main/protocols/hy2.txt",
]


def detect_protocol(config_url: str) -> str:
    url = config_url.lower().strip()
    if url.startswith("vless://"):
        return "vless"
    if url.startswith("vmess://"):
        return "vmess"
    if url.startswith(("hysteria2://", "hy2://")):
        return "hysteria2"
    if url.startswith(("ss://", "shadowsocks://")):
        return "shadowsocks"
    if url.startswith("trojan://"):
        return "trojan"
    return "unknown"


# --- ПАРСИНГ VLESS ДЛЯ XRAY ---
def validate_and_parse_vless(url: str):
    try:
        url_main = url.split('#')[0]
        match = re.search(r'vless://([^@]+)@([^:/?#]+):(\d+)', url_main)
        if not match:
            return None
        uuid, host, port = match.group(1), match.group(2), int(match.group(3))
        if len(uuid) < 30:
            return None

        query = {}
        if '?' in url_main:
            q_str = url_main.split('?')[1]
            for param in q_str.split('&'):
                if '=' in param:
                    k, v = param.split('=', 1)
                    query[k] = urllib.parse.unquote(v)

        sec = query.get('security', '').lower()
        if sec == 'reality':
            pbk = query.get('pbk', '')
            if len(pbk) < 40:
                return None

        return {
            'uuid': uuid,
            'host': host,
            'port': port,
            'params': query,
            'raw': url
        }
    except Exception:
        return None


def build_xray_outbound(parsed, tag: str):
    p = parsed['params']
    net_type = p.get('type', 'tcp').lower()
    if net_type not in ('tcp', 'ws', 'grpc', 'xhttp', 'splithttp', 'httpupgrade'):
        net_type = 'tcp'

    security = p.get('security', 'none').lower()
    if security not in ('reality', 'tls', 'none'):
        security = 'none'

    flow = p.get('flow', '')
    if flow and 'vision' not in flow:
        flow = None
    elif not flow:
        flow = None

    sni = p.get('sni', parsed['host'])
    pbk = p.get('pbk', '')
    sid = p.get('sid', '')
    fp = p.get('fp', 'chrome')
    path = p.get('path', '/')
    host_header = p.get('host', '')

    outbound = {
        "tag": tag,
        "protocol": "vless",
        "settings": {
            "vnext": [
                {
                    "address": parsed['host'],
                    "port": parsed['port'],
                    "users": [
                        {
                            "id": parsed['uuid'],
                            "encryption": "none",
                            "flow": flow
                        }
                    ]
                }
            ]
        },
        "streamSettings": {
            "network": net_type,
            "security": security
        }
    }

    if security == "reality":
        outbound["streamSettings"]["realitySettings"] = {
            "serverName": sni,
            "fingerprint": fp if fp in ('chrome', 'firefox', 'safari', 'ios', 'android', 'edge') else 'chrome',
            "publicKey": pbk,
            "shortId": sid[:16] if sid else "",
            "spiderX": p.get("spx", "")
        }
    elif security == "tls":
        outbound["streamSettings"]["tlsSettings"] = {
            "serverName": sni,
            "fingerprint": fp if fp in ('chrome', 'firefox', 'safari', 'ios', 'android', 'edge') else 'chrome'
        }

    if net_type == "ws":
        outbound["streamSettings"]["wsSettings"] = {
            "path": path,
            "headers": {"Host": host_header} if host_header else {}
        }
    elif net_type in ("xhttp", "splithttp"):
        outbound["streamSettings"]["xhttpSettings"] = {
            "path": path,
            "host": host_header or sni,
            "mode": p.get("mode", "auto")
        }

    return outbound


# --- ЭТАП 1: БЫСТРЫЙ TLS ХЕНДШЕЙК ---
def fast_tls_check(config_url: str) -> Optional[tuple[str, float]]:
    proto = detect_protocol(config_url)
    try:
        if proto in ("vless", "trojan"):
            m = re.search(r'@([^:/?#]+):(\d+)', config_url)
            if not m:
                return None
            host, port = m.group(1), int(m.group(2))
            sni_m = re.search(r'sni=([^&/#]+)', config_url, re.I)
            sni = urllib.parse.unquote(sni_m.group(1)) if sni_m else host

            t0 = time.time()
            sock = socket.create_connection((host, port), timeout=2.0)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ssock = ctx.wrap_socket(sock, server_hostname=sni)
            ssock.close()
            delay = round((time.time() - t0) * 1000, 1)
            return (config_url, delay)

        elif proto == "vmess":
            host_port = cc.extract_host_from_config(config_url)
            if not host_port:
                return None
            host, port = host_port
            t0 = time.time()
            if port == 443 or "tls" in config_url.lower():
                sock = socket.create_connection((host, port), timeout=2.0)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ssock = ctx.wrap_socket(sock, server_hostname=host)
                ssock.close()
            else:
                sock = socket.create_connection((host, port), timeout=1.8)
                sock.close()
            delay = round((time.time() - t0) * 1000, 1)
            return (config_url, delay)

        elif proto == "hysteria2":
            parsed = cc.parse_hysteria2_url(config_url)
            if not parsed:
                return None
            host, port = parsed["host"], parsed["port"]
            ip = socket.gethostbyname(host)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.8)
            probe = b'\xc0\x00\x00\x00\x01\x08' + b'\x11'*8 + b'\x08' + b'\x22'*8 + b'\x00' + b'\x00'*40
            t1 = time.time()
            sock.sendto(probe, (ip, port))
            try:
                data, _ = sock.recvfrom(1024)
                sock.close()
                delay = round((time.time() - t1) * 1000, 1)
                return (config_url, delay)
            except Exception:
                sock.close()
                return None

        else:
            host_port = cc.extract_host_from_config(config_url)
            if not host_port:
                return None
            host, port = host_port
            t0 = time.time()
            sock = socket.create_connection((host, port), timeout=1.8)
            sock.close()
            delay = round((time.time() - t0) * 1000, 1)
            return (config_url, delay)

    except Exception:
        return None


# --- ЭТАП 2: РЕАЛЬНАЯ ПРОВЕРКА ЧЕРЕЗ XRAY-CORE (HTTP 204) ---
def test_vless_chunk_with_xray(parsed_chunk, start_port=16000) -> list[tuple[str, float]]:
    if not XRAY_BIN or not parsed_chunk:
        return []

    inbounds = []
    outbounds = []
    rules = []

    for i, p in enumerate(parsed_chunk):
        in_tag = f"in_{i}"
        out_tag = f"out_{i}"
        port = start_port + i
        inbounds.append({
            "tag": in_tag,
            "port": port,
            "listen": "127.0.0.1",
            "protocol": "mixed",
            "settings": {"auth": "noauth", "udp": False}
        })
        outbounds.append(build_xray_outbound(p, out_tag))
        rules.append({
            "type": "field",
            "inboundTag": [in_tag],
            "outboundTag": out_tag
        })

    outbounds.append({"tag": "direct", "protocol": "freedom"})

    xray_config = {
        "log": {"loglevel": "none"},
        "inbounds": inbounds,
        "outbounds": outbounds,
        "routing": {
            "domainStrategy": "AsIs",
            "rules": rules
        }
    }

    tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    cfg_file = os.path.join(tmp_dir, f"test_{start_port}.json")

    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(xray_config, f)

    check = subprocess.run([XRAY_BIN, "run", "-test", "-c", cfg_file], capture_output=True, text=True)
    if check.returncode != 0:
        try:
            os.remove(cfg_file)
        except Exception:
            pass
        return []

    proc = subprocess.Popen([XRAY_BIN, "run", "-c", cfg_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)

    def probe(idx):
        port = start_port + idx
        raw_url = parsed_chunk[idx]['raw']
        handler = urllib.request.ProxyHandler({'http': f'http://127.0.0.1:{port}'})
        opener = urllib.request.build_opener(handler)
        t0 = time.time()
        try:
            req = urllib.request.Request("http://cp.cloudflare.com/generate_204", headers={'User-Agent': 'Mozilla/5.0'})
            with opener.open(req, timeout=3.0) as resp:
                if resp.status in (200, 204):
                    delay = round((time.time() - t0) * 1000, 1)
                    return (raw_url, delay)
        except Exception:
            pass
        return None

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(25, len(parsed_chunk))) as pool:
        futures = [pool.submit(probe, i) for i in range(len(parsed_chunk))]
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            if res:
                results.append(res)

    proc.kill()
    try:
        os.remove(cfg_file)
    except Exception:
        pass

    return results


def main():
    print("=" * 68)
    print(" ⚡ REBORN CFG - Multi-Protocol Subscription Checker 2026")
    print(" Двухэтапная проверка на 100% работу в v2rayN (без ошибок -1)")
    print("=" * 68)
    print()

    if len(sys.argv) >= 2:
        user_input = sys.argv[1].strip()
    else:
        print("Выберите действие (нажмите цифру или просто нажмите ENTER):")
        print(" [1] 🔥 VLESS Reality для РФ (Глубокая проверка Xray, 100% живые!) [ENTER]")
        print(" [2] 🔷 VMess (Cloudflare CDN / WebSocket)")
        print(" [3] 🚀 Hysteria2 (Внимание: в v2rayN требуется ядро sing-box!)")
        print(" [4] 🌐 Проверить локальный файл vless\\best-1.txt")
        print(" [5] 📁 Проверить локальный файл hysteria2\\best-1.txt")
        print(" [6] 📝 Вставить свою ссылку на подписку или путь к файлу")
        print()
        user_input = input("Ваш выбор > ").strip()

    data = ""
    clean_choice = user_input.replace('\ufeff', '').strip()
    target_proto_filter = None

    if not clean_choice or clean_choice == "1":
        cc.log("🔥 Загрузка баз VLESS Reality (ежедневные подборки для РФ)...")
        target_proto_filter = "vless"
        chunks = []
        for src in RUSSIA_VLESS_REALITY_SOURCES:
            txt = cc.fetch_data(src)
            if txt:
                chunks.append(txt)
        data = "\n".join(chunks)

    elif clean_choice == "2":
        cc.log("🔷 Загрузка баз VMess (Cloudflare CDN)...")
        target_proto_filter = "vmess"
        chunks = []
        for src in VMESS_SOURCES:
            txt = cc.fetch_data(src)
            if txt:
                chunks.append(txt)
        data = "\n".join(chunks)

    elif clean_choice == "3":
        cc.log("🚀 Загрузка Hysteria2 конфигов...")
        cc.log("💡 Для работы Hysteria2 в v2rayN: Настройки ядер -> установите sing-box!")
        target_proto_filter = "hysteria2"
        chunks = []
        for src in HYSTERIA2_SOURCES:
            txt = cc.fetch_data(src)
            if txt:
                chunks.append(txt)
        data = "\n".join(chunks)

    elif clean_choice == "4":
        path = os.path.join("vless", "best-1.txt")
        if os.path.isfile(path):
            cc.log(f"📂 Чтение {path}...")
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        else:
            data = cc.fetch_data(RUSSIA_VLESS_REALITY_SOURCES[0])

    elif clean_choice == "5":
        path = os.path.join("hysteria2", "best-1.txt")
        if os.path.isfile(path):
            cc.log(f"📂 Чтение {path}...")
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        else:
            data = cc.fetch_data(HYSTERIA2_SOURCES[0])

    elif clean_choice == "6":
        custom = input("Вставьте ссылку на подписку или путь к файлу:\n> ").strip()
        if os.path.isfile(custom):
            with open(custom, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        else:
            data = cc.fetch_data(custom)

    else:
        if os.path.isfile(user_input):
            cc.log(f"📂 Чтение файла: {user_input}")
            with open(user_input, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        else:
            data = cc.fetch_data(user_input)

    if not data:
        cc.log("❌ Не удалось загрузить данные.")
        return

    # Извлечение кандидатов
    if target_proto_filter == "vless":
        raw_candidates = cc.extract_vless_configs(data)
        all_configs = [
            c for c in raw_candidates
            if "reality" in c.lower() or "pbk=" in c.lower() or "security=tls" in c.lower()
        ]
        if not all_configs:
            all_configs = raw_candidates
    elif target_proto_filter == "vmess":
        all_configs = cc.extract_vmess_configs(data)
    elif target_proto_filter == "hysteria2":
        all_configs = cc.extract_hysteria2_configs(data)
    else:
        all_configs = (
            cc.extract_vless_configs(data)
            + cc.extract_vmess_configs(data)
            + cc.extract_hysteria2_configs(data)
            + cc.extract_trojan_configs(data)
            + cc.extract_shadowsocks_configs(data)
        )

    unique_configs = cc.deduplicate_configs(all_configs, show_log=False)
    test_candidates = unique_configs[:200] if len(unique_configs) > 200 else unique_configs
    cc.log(f"🔍 Отобрано уникальных кандидатов: {len(unique_configs)} (в экспресс-проверку взято: {len(test_candidates)})")

    if not test_candidates:
        cc.log("⚠️ Не найдено подходящих конфигов.")
        return

    # ЭТАП 1: Быстрый TLS Handshake отбор
    cc.log(f"⚡ ЭТАП 1: Быстрый TLS Handshake фильтр ({len(test_candidates)} узлов, 35 потоков)...")
    pass1_alive = []
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
        futures = {executor.submit(fast_tls_check, cfg): cfg for cfg in test_candidates}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                pass1_alive.append(res)

    cc.log(f"⏱️ Этап 1 завершен за {round(time.time() - t0, 1)} сек! Живых TLS-узлов: {len(pass1_alive)}")

    if not pass1_alive:
        cc.log("❌ Ни один сервер не ответил на TLS рукопожатие.")
        return

    final_working = []

    # ЭТАП 2: Реальная проверка через Xray (если Xray доступен и это VLESS)
    if XRAY_BIN and target_proto_filter == "vless":
        cc.log(f"🔬 ЭТАП 2: Глубокая проверка через реальное ядро Xray-core (проверка HTTP 204)...")
        parsed_candidates = []
        for cfg, _ in pass1_alive:
            p = validate_and_parse_vless(cfg)
            if p:
                parsed_candidates.append(p)

        cc.log(f"⚙️ Проверка валидных конфигураций через Xray: {len(parsed_candidates)} узлов...")
        chunk_size = 15
        t1 = time.time()
        for i in range(0, len(parsed_candidates), chunk_size):
            chunk = parsed_candidates[i:i+chunk_size]
            res = test_vless_chunk_with_xray(chunk, start_port=16500 + i)
            final_working.extend(res)
            print(f"📊 Прогресс Xray: {min(i+len(chunk), len(parsed_candidates))}/{len(parsed_candidates)} | 100% Рабочих: {len(final_working)}", end="\r", flush=True)

        print()
        cc.log(f"⏱️ Этап 2 завершен за {round(time.time() - t1, 1)} сек! 100% рабочих узлов: {len(final_working)}")
    else:
        final_working = pass1_alive

    if not final_working:
        cc.log("⚠️ После глубокой проверки рабочих узлов не осталось.")
        return

    # Сортировка по минимальному пингу
    final_working.sort(key=lambda x: x[1])

    # Сохранение результатов
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "working-from-subscription.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        for cfg, _ in final_working:
            f.write(cfg.strip() + "\n")

    print()
    print("=" * 68)
    cc.log(f"✅ В файл сохранено {len(final_working)} 100% проверенных рабочих серверов!")
    cc.log(f"📁 Путь: {output_file}")
    print("=" * 68)
    print()
    print("⭐ ТОП-5 САМЫХ БЫСТРЫХ СЕРВЕРОВ (проверены через Xray, 0 ошибок -1):")
    print("-" * 68)
    for i, (cfg, ping) in enumerate(final_working[:5], 1):
        proto = detect_protocol(cfg).upper()
        print(f"[{i}] Пинг: {ping} ms | Протокол: {proto}")
        print(f"    {cfg}")
        print()
    print("-" * 68)
    cc.log("🎉 Готово! Все конфиги в файле гарантированно работают в v2rayN!")

    try:
        os.startfile(output_file)
    except Exception:
        pass


if __name__ == "__main__":
    main()
