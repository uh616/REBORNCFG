"""
⚡ REBORN CFG - Multi-Protocol Subscription Checker 2026
Проверка подписок любого типа на реальную доступность:
Hysteria2 | VLESS (Reality / gRPC / WS) | VMESS | Shadowsocks | Trojan
"""

from __future__ import annotations

import concurrent.futures
import sys
import os
import time
from typing import Optional

# Добавляем путь к source чтобы импортировать config_collector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_collector as cc


def detect_protocol(config_url: str) -> str:
    """Определяет тип протокола по префиксу URL."""
    url = config_url.lower().strip()
    if url.startswith(("hysteria2://", "hy2://")):
        return "hysteria2"
    if url.startswith("vless://"):
        return "vless"
    if url.startswith("vmess://"):
        return "vmess"
    if url.startswith(("ss://", "shadowsocks://")):
        return "shadowsocks"
    if url.startswith("trojan://"):
        return "trojan"
    return "unknown"


def quick_check_config(config_url: str) -> tuple[Optional[str], Optional[float], str]:
    """
    Быстрая и точная проверка одного конфига:
    - Извлекает host:port
    - Для Hysteria2 проверяет TCP / UDP QUIC probe
    - Для VLESS / VMESS / SS / Trojan проверяет быстрый TCP handshake
    Возвращает (config_url, ping_ms, protocol) при успехе, иначе (None, None, protocol)
    """
    proto = detect_protocol(config_url)
    try:
        if proto == "hysteria2":
            if not cc.validate_hysteria2_config(config_url):
                return (None, None, proto)
            parsed = cc.parse_hysteria2_url(config_url)
            if not parsed:
                return (None, None, proto)
            host = parsed["host"]
            port = parsed["port"]
        else:
            host_port = cc.extract_host_from_config(config_url)
            if not host_port:
                return (None, None, proto)
            host, port = host_port

        # Проверка соединения с замером пинга
        ping = cc.test_host_connectivity(host, port, protocol=proto, timeout=1.5)
        if ping is not None:
            return (config_url, ping, proto)
        return (None, None, proto)
    except Exception:
        return (None, None, proto)


def main():
    print("=" * 64)
    print(" ⚡ REBORN CFG - Multi-Protocol Subscription Checker 2026")
    print(" Поддерживает: Hysteria2 | VLESS Reality | VMESS | SS | Trojan")
    print("=" * 64)
    print()

    # Получаем URL подписки
    if len(sys.argv) >= 2:
        subscription_url = sys.argv[1].strip()
    else:
        subscription_url = input(
            "Вставьте ссылку на подписку (или путь к .txt файлу):\n> "
        ).strip()

    if not subscription_url:
        print("❌ URL или путь к подписке не указан.")
        return

    # Загружаем данные
    if os.path.isfile(subscription_url):
        cc.log(f"📂 Чтение локального файла: {subscription_url}")
        with open(subscription_url, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
    else:
        cc.log(f"🌐 Загрузка подписки: {subscription_url}")
        data = cc.fetch_data(subscription_url)

    if not data:
        cc.log("❌ Не удалось загрузить данные (пустой ответ или ошибка сети).")
        return

    # Извлечение всех протоколов
    hysteria_configs = cc.extract_hysteria2_configs(data)
    vless_configs = cc.extract_vless_configs(data)
    vmess_configs = cc.extract_vmess_configs(data)
    ss_configs = cc.extract_shadowsocks_configs(data)
    trojan_configs = cc.extract_trojan_configs(data)

    all_configs = (
        hysteria_configs
        + vless_configs
        + vmess_configs
        + ss_configs
        + trojan_configs
    )

    if not all_configs:
        cc.log("⚠️ В подписке не обнаружено поддерживаемых VPN-конфигураций.")
        return

    cc.log(
        f"📦 Найдено конфигов: Hysteria2={len(hysteria_configs)}, "
        f"VLESS={len(vless_configs)}, VMESS={len(vmess_configs)}, "
        f"Shadowsocks={len(ss_configs)}, Trojan={len(trojan_configs)} | Всего: {len(all_configs)}"
    )

    # Дедупликация
    unique_configs = cc.deduplicate_configs(all_configs, protocol=None, show_log=False)
    if len(unique_configs) != len(all_configs):
        cc.log(f"🔍 После дедупликации: {len(unique_configs)} уникальных (удалено дубликатов: {len(all_configs) - len(unique_configs)})")

    # Многопоточная проверка
    max_workers = min(cc.DEFAULT_MAX_WORKERS, 40)
    cc.log(f"🧪 Запуск параллельной проверки ({max_workers} потоков)...")

    working_results = []
    checked = 0
    t0 = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(quick_check_config, cfg): cfg for cfg in unique_configs}

        for future in concurrent.futures.as_completed(futures):
            checked += 1
            try:
                cfg, ping, proto = future.result()
                if cfg:
                    working_results.append((ping, cfg, proto))
            except Exception:
                pass

            if checked % 25 == 0 or checked == len(unique_configs):
                pct = (checked * 100) // len(unique_configs)
                print(f"📊 Прогресс: {checked}/{len(unique_configs)} ({pct}%) | Живых серверов: {len(working_results)}", end="\r", flush=True)

    print()
    elapsed = round(time.time() - t0, 1)
    cc.log(f"⏱️ Проверка завершена за {elapsed} сек! Живых серверов: {len(working_results)} / {len(unique_configs)}")

    if not working_results:
        cc.log("❌ К сожалению, ни один сервер не ответил на проверку доступности.")
        return

    # Сортировка по минимальному пингу
    working_results.sort(key=lambda x: x[0] if x[0] is not None else 9999)
    working_configs = [item[1] for item in working_results]

    # Статистика по протоколам
    stats_by_proto = {}
    for _, _, proto in working_results:
        stats_by_proto[proto] = stats_by_proto.get(proto, 0) + 1

    proto_summary = ", ".join(f"{p}: {cnt}" for p, cnt in sorted(stats_by_proto.items()))
    cc.log(f"📈 Живые по протоколам: {proto_summary}")

    # Сохраняем результат
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "working-from-subscription.txt")
    cc.create_subscription_file(working_configs, output_file)

    # Сохраняем также отдельно по протоколам
    for proto in stats_by_proto:
        proto_cfgs = [c for _, c, p in working_results if p == proto]
        if proto_cfgs:
            p_file = os.path.join(output_dir, f"working-{proto}.txt")
            cc.create_subscription_file(proto_cfgs, p_file)

    cc.log(f"✅ Рабочие конфиги сохранены в: {output_file}")
    cc.log("🎉 Готово! Скопируйте строки из файла и вставьте в v2rayN, NekoBox, Clash Verge или Hiddify.")


if __name__ == "__main__":
    main()
