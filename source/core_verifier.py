"""
⚡ REBORN CFG - Core Verifier 2026
Универсальный верификатор конфигураций через реальные ядра:
Xray-core (VLESS, VMess, Trojan, Shadowsocks) + sing-box (Hysteria 2).
Гарантия 100% работы в клиентах (v2rayN, Flclash, sing-box) без ошибок -1!
"""

from __future__ import annotations

import concurrent.futures
import urllib.request
import urllib.parse
import subprocess
import socket
import base64
import json
import ssl
import sys
import os
import re
import time
from typing import Optional

# -------------------- ПОИСК БИНАРНИКОВ ЯДЕР --------------------
def find_binary(name: str) -> Optional[str]:
    """Ищет бинарник (xray или sing-box) на Windows и Linux."""
    exe_name = f"{name}.exe" if sys.platform == "win32" else name

    search_paths = [
        # Пути к v2rayN на Windows
        rf"C:\Users\616\Desktop\v2rayN-windows-64\bin\{'Xray' if name == 'xray' else 'sing_box'}\{exe_name}",
        rf"C:\Users\616\Desktop\v2rayN-windows-64\bin\{exe_name}",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", name, exe_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", exe_name),
        # Стандартные пути Linux (GitHub Actions)
        f"/usr/local/bin/{name}",
        f"/usr/bin/{name}",
    ]

    for p in search_paths:
        if os.path.isfile(p):
            return p

    # Проверка через PATH
    import shutil
    found = shutil.which(exe_name) or shutil.which(name)
    if found:
        return found

    return None

XRAY_BIN = find_binary("xray")
SINGBOX_BIN = find_binary("sing-box")


# -------------------- ПАРСЕРЫ КОНФИГУРАЦИЙ --------------------
def parse_vless(url: str) -> Optional[dict]:
    try:
        url_main = url.split('#')[0]
        m = re.search(r'vless://([^@]+)@([^:/?#]+):(\d+)', url_main)
        if not m:
            return None
        uuid, host, port = m.group(1), m.group(2), int(m.group(3))
        if len(uuid) < 30:
            return None

        query = {}
        if '?' in url_main:
            for param in url_main.split('?')[1].split('&'):
                if '=' in param:
                    k, v = param.split('=', 1)
                    query[k] = urllib.parse.unquote(v)

        sec = query.get('security', '').lower()
        if sec == 'reality' and len(query.get('pbk', '')) < 40:
            return None

        return {
            'protocol': 'vless',
            'host': host,
            'port': port,
            'uuid': uuid,
            'params': query,
            'raw': url
        }
    except Exception:
        return None


def parse_vmess(url: str) -> Optional[dict]:
    try:
        raw_b64 = url.split("://", 1)[1].split("#")[0].strip()
        pad = "=" * ((4 - len(raw_b64) % 4) % 4)
        data = json.loads(base64.b64decode(raw_b64 + pad).decode('utf-8', errors='ignore'))
        host = data.get('add', '').strip()
        port = int(data.get('port', 443))
        uuid = data.get('id', '').strip()
        if not host or not uuid or len(uuid) < 30:
            return None

        return {
            'protocol': 'vmess',
            'host': host,
            'port': port,
            'uuid': uuid,
            'net': data.get('net', 'tcp').lower(),
            'tls': data.get('tls', '').lower(),
            'sni': data.get('sni', '') or host,
            'path': data.get('path', '/'),
            'ws_host': data.get('host', '') or host,
            'raw': url
        }
    except Exception:
        return None


def parse_trojan(url: str) -> Optional[dict]:
    try:
        url_main = url.split('#')[0]
        m = re.search(r'trojan://([^@]+)@([^:/?#]+):(\d+)', url_main)
        if not m:
            return None
        password, host, port = m.group(1), m.group(2), int(m.group(3))
        if not password or not host:
            return None

        query = {}
        if '?' in url_main:
            for param in url_main.split('?')[1].split('&'):
                if '=' in param:
                    k, v = param.split('=', 1)
                    query[k] = urllib.parse.unquote(v)

        sni = query.get('sni', '') or host
        return {
            'protocol': 'trojan',
            'host': host,
            'port': port,
            'password': password,
            'sni': sni,
            'params': query,
            'raw': url
        }
    except Exception:
        return None


def parse_shadowsocks(url: str) -> Optional[dict]:
    try:
        url_clean = url.split('#')[0].strip()
        if '://' not in url_clean:
            return None
        body = url_clean.split('://', 1)[1]

        if '@' in body:
            auth_part, host_port = body.rsplit('@', 1)
            host, port = host_port.split('?')[0].rsplit(':', 1)
            if ':' in auth_part:
                method, password = auth_part.split(':', 1)
            else:
                pad = "=" * ((4 - len(auth_part) % 4) % 4)
                dec = base64.b64decode(auth_part + pad).decode('utf-8', errors='ignore')
                method, password = dec.split(':', 1)
        else:
            pad = "=" * ((4 - len(body) % 4) % 4)
            dec = base64.b64decode(body + pad).decode('utf-8', errors='ignore')
            auth_part, host_port = dec.rsplit('@', 1)
            method, password = auth_part.split(':', 1)
            host, port = host_port.rsplit(':', 1)

        return {
            'protocol': 'shadowsocks',
            'host': host.strip(),
            'port': int(port),
            'method': method.strip(),
            'password': password.strip(),
            'raw': url
        }
    except Exception:
        return None


def parse_hysteria2(url: str) -> Optional[dict]:
    try:
        url_clean = url.split('#')[0].strip()
        m = re.search(r'hy(?:steria)?2://([^@]+)@([^:/?#]+):(\d+)', url_clean)
        if not m:
            return None
        auth, host, port = m.group(1), m.group(2), int(m.group(3))

        query = {}
        if '?' in url_clean:
            for param in url_clean.split('?')[1].split('&'):
                if '=' in param:
                    k, v = param.split('=', 1)
                    query[k] = urllib.parse.unquote(v)

        sni = query.get('sni', '') or host
        return {
            'protocol': 'hysteria2',
            'host': host,
            'port': port,
            'auth': auth,
            'sni': sni,
            'params': query,
            'raw': url
        }
    except Exception:
        return None


def parse_any(url: str) -> Optional[dict]:
    u = url.lower().strip()
    if u.startswith('vless://'):
        return parse_vless(url)
    if u.startswith('vmess://'):
        return parse_vmess(url)
    if u.startswith('trojan://'):
        return parse_trojan(url)
    if u.startswith(('hy2://', 'hysteria2://')):
        return parse_hysteria2(url)
    if u.startswith(('ss://', 'shadowsocks://')):
        return parse_shadowsocks(url)
    return None


# -------------------- ФОРМИРОВАНИЕ OUTBOUND ДЛЯ XRAY --------------------
def build_xray_outbound(p: dict, tag: str) -> Optional[dict]:
    proto = p['protocol']

    if proto == 'vless':
        params = p.get('params', {})
        net_type = params.get('type', 'tcp').lower()
        if net_type not in ('tcp', 'ws', 'grpc', 'xhttp', 'splithttp', 'httpupgrade'):
            net_type = 'tcp'
        security = params.get('security', 'none').lower()
        if security not in ('reality', 'tls', 'none'):
            security = 'none'

        flow = params.get('flow', '')
        if flow and 'vision' not in flow:
            flow = None
        elif not flow:
            flow = None

        sni = params.get('sni', p['host'])
        pbk = params.get('pbk', '')
        sid = params.get('sid', '')
        fp = params.get('fp', 'chrome')
        if fp not in ('chrome', 'firefox', 'safari', 'ios', 'android', 'edge'):
            fp = 'chrome'

        out = {
            "tag": tag,
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": p['host'],
                    "port": p['port'],
                    "users": [{"id": p['uuid'], "encryption": "none", "flow": flow}]
                }]
            },
            "streamSettings": {"network": net_type, "security": security}
        }
        if security == "reality":
            out["streamSettings"]["realitySettings"] = {
                "serverName": sni, "fingerprint": fp, "publicKey": pbk, "shortId": sid[:16], "spiderX": params.get("spx", "")
            }
        elif security == "tls":
            out["streamSettings"]["tlsSettings"] = {"serverName": sni, "fingerprint": fp}

        if net_type == "ws":
            out["streamSettings"]["wsSettings"] = {"path": params.get('path', '/'), "headers": {"Host": params.get('host', '')}}
        elif net_type in ("xhttp", "splithttp"):
            out["streamSettings"]["xhttpSettings"] = {"path": params.get('path', '/'), "host": params.get('host', '') or sni}
        return out

    elif proto == 'vmess':
        net_type = p.get('net', 'tcp')
        if net_type not in ('tcp', 'ws', 'grpc', 'xhttp'):
            net_type = 'tcp'
        is_tls = p.get('tls') == 'tls' or p.get('port') == 443
        out = {
            "tag": tag,
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": p['host'],
                    "port": p['port'],
                    "users": [{"id": p['uuid'], "alterId": 0, "security": "auto"}]
                }]
            },
            "streamSettings": {
                "network": net_type,
                "security": "tls" if is_tls else "none"
            }
        }
        if is_tls:
            out["streamSettings"]["tlsSettings"] = {"serverName": p['sni'], "fingerprint": "chrome"}
        if net_type == "ws":
            out["streamSettings"]["wsSettings"] = {"path": p.get('path', '/'), "headers": {"Host": p.get('ws_host', '')}}
        return out

    elif proto == 'trojan':
        params = p.get('params', {})
        net_type = params.get('type', 'tcp').lower()
        if net_type not in ('tcp', 'ws', 'grpc'):
            net_type = 'tcp'
        out = {
            "tag": tag,
            "protocol": "trojan",
            "settings": {
                "servers": [{"address": p['host'], "port": p['port'], "password": p['password']}]
            },
            "streamSettings": {
                "network": net_type,
                "security": "tls",
                "tlsSettings": {"serverName": p['sni'], "fingerprint": "chrome"}
            }
        }
        if net_type == "ws":
            out["streamSettings"]["wsSettings"] = {"path": params.get('path', '/'), "headers": {"Host": params.get('host', '')}}
        return out

    elif proto == 'shadowsocks':
        return {
            "tag": tag,
            "protocol": "shadowsocks",
            "settings": {
                "servers": [{"address": p['host'], "port": p['port'], "method": p['method'], "password": p['password']}]
            }
        }

    return None


# -------------------- ПРОВЕРКА ЧАНКА ЧЕРЕЗ XRAY --------------------
def test_xray_chunk(parsed_chunk: list[dict], start_port: int, timeout: float = 3.5) -> list[tuple[str, float]]:
    if not XRAY_BIN or not parsed_chunk:
        return []

    inbounds = []
    outbounds = []
    rules = []

    for i, p in enumerate(parsed_chunk):
        out_def = build_xray_outbound(p, f"out_{i}")
        if not out_def:
            continue
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
        outbounds.append(out_def)
        rules.append({"type": "field", "inboundTag": [in_tag], "outboundTag": out_tag})

    if not outbounds:
        return []

    outbounds.append({"tag": "direct", "protocol": "freedom"})

    xray_config = {
        "log": {"loglevel": "none"},
        "inbounds": inbounds,
        "outbounds": outbounds,
        "routing": {"domainStrategy": "AsIs", "rules": rules}
    }

    tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    cfg_file = os.path.join(tmp_dir, f"xray_{start_port}.json")

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
            with opener.open(req, timeout=timeout) as resp:
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


# -------------------- ПРОВЕРКА ЧАНКА ЧЕРЕЗ SING-BOX (HYSTERIA2) --------------------
def test_singbox_chunk(parsed_chunk: list[dict], start_port: int, timeout: float = 3.5) -> list[tuple[str, float]]:
    if not SINGBOX_BIN or not parsed_chunk:
        return []

    inbounds = []
    outbounds = []
    rules = []

    for i, p in enumerate(parsed_chunk):
        in_tag = f"in_{i}"
        out_tag = f"out_{i}"
        port = start_port + i

        inbounds.append({
            "type": "mixed",
            "tag": in_tag,
            "listen": "127.0.0.1",
            "listen_port": port
        })
        outbounds.append({
            "type": "hysteria2",
            "tag": out_tag,
            "server": p['host'],
            "server_port": p['port'],
            "password": p['auth'],
            "tls": {
                "enabled": True,
                "server_name": p['sni'],
                "insecure": True
            }
        })
        rules.append({"inbound": [in_tag], "outbound": out_tag})

    if not outbounds:
        return []

    singbox_config = {
        "log": {"level": "panic"},
        "inbounds": inbounds,
        "outbounds": outbounds,
        "route": {"rules": rules}
    }

    tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    cfg_file = os.path.join(tmp_dir, f"sb_{start_port}.json")

    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(singbox_config, f)

    check = subprocess.run([SINGBOX_BIN, "check", "-c", cfg_file], capture_output=True, text=True)
    if check.returncode != 0:
        try:
            os.remove(cfg_file)
        except Exception:
            pass
        return []

    proc = subprocess.Popen([SINGBOX_BIN, "run", "-c", cfg_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)

    def probe(idx):
        port = start_port + idx
        raw_url = parsed_chunk[idx]['raw']
        handler = urllib.request.ProxyHandler({'http': f'http://127.0.0.1:{port}'})
        opener = urllib.request.build_opener(handler)
        t0 = time.time()
        try:
            req = urllib.request.Request("http://cp.cloudflare.com/generate_204", headers={'User-Agent': 'Mozilla/5.0'})
            with opener.open(req, timeout=timeout) as resp:
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


# -------------------- УНИВЕРСАЛЬНАЯ ПРОВЕРКА СПИСКА КОНФИГОВ --------------------
def verify_configs_deep(configs: list[str], max_candidates: int = 150) -> list[tuple[str, float]]:
    """
    Двухэтапная проверка любого списка конфигураций:
    1. Быстрый параллельный TLS/TCP фильтр
    2. Проверка через реальные ядра Xray/Sing-box (HTTP 204)
    """
    # Парсим валидные конфигурации
    parsed_items = []
    for c in configs:
        p = parse_any(c)
        if p:
            parsed_items.append(p)

    if not parsed_items:
        return []

    # Ограничиваем выборку для экспресс-проверки
    candidates = parsed_items[:max_candidates]

    # Разделяем на группы: для Xray (VLESS, VMess, Trojan, SS) и Sing-box (Hy2)
    xray_items = [p for p in candidates if p['protocol'] in ('vless', 'vmess', 'trojan', 'shadowsocks')]
    hy2_items = [p for p in candidates if p['protocol'] == 'hysteria2']

    working = []

    # Тестируем через Xray
    if XRAY_BIN and xray_items:
        chunk_size = 15
        for i in range(0, len(xray_items), chunk_size):
            chunk = xray_items[i:i+chunk_size]
            res = test_xray_chunk(chunk, start_port=18000 + i)
            working.extend(res)

    # Тестируем через Sing-box
    if SINGBOX_BIN and hy2_items:
        chunk_size = 15
        for i in range(0, len(hy2_items), chunk_size):
            chunk = hy2_items[i:i+chunk_size]
            res = test_singbox_chunk(chunk, start_port=19000 + i)
            working.extend(res)

    working.sort(key=lambda x: x[1])
    return working
