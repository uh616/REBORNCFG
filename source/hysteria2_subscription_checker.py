"""
⚡ REBORN CFG - Multi-Protocol Subscription Checker 2026
Проверка подписок любого типа на реальную доступность:
Hysteria2 | VLESS (Reality / gRPC / WS) | VMESS | Shadowsocks | Trojan
"""

from __future__ import annotations

import concurrent.futures
import subprocess
import sys
import os
import time
from typing import Optional

# Добавляем путь к source
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_collector as cc

# Экспресс-источники 2026 года (только проверенные быстрые выборки)
EXPRESS_2026_SOURCES = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/top100.txt",
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/hysteria2.txt",
    "https://raw.githubusercontent.com/MustafaBaqer/VestraNet-Nodes/main/protocols/hy2.txt",
    "https://raw.githubusercontent.com/MohammadBahemmat/V2ray-Collector/main/Tested.txt",
    "https://raw.githubusercontent.com/3inker/v2ray-subscription/main/subs/all_ru.txt",
]

# Полные онлайн-базы
FULL_ONLINE_SOURCES = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/vless.txt",
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/vmess.txt",
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/shadowsocks.txt",
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/trojan.txt",
    "https://raw.githubusercontent.com/MustafaBaqer/VestraNet-Nodes/main/protocols/vless.txt",
]


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
    """Быстрая проверка соединения с замером пинга."""
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

    # Меню выбора источника
    if len(sys.argv) >= 2:
        user_input = sys.argv[1].strip()
    else:
        print("Выберите действие (нажмите цифру или просто нажмите ENTER):")
        print(" [1] 🔥 Экспресс-проверка лучших серверов 2026 (По умолчанию - просто ENTER)")
        print(" [2] ⚡ Проверить лучшие VLESS Reality (из папки vless\\best-1.txt)")
        print(" [3] 🚀 Проверить лучшие Hysteria2 (из папки hysteria2\\best-1.txt)")
        print(" [4] 🌐 Полная глубокая проверка (10 000+ конфигов из сети)")
        print(" [5] 📝 Вставить свою ссылку на подписку или путь к файлу")
        print()
        user_input = input("Ваш выбор > ").strip()

    data = ""
    clean_choice = user_input.replace('\ufeff', '').strip()

    # Обработка выбора
    if not clean_choice or clean_choice == "1":
        cc.log("🔥 Загрузка и экспресс-проверка топовых серверов 2026 года...")
        chunks = []
        for src in EXPRESS_2026_SOURCES:
            txt = cc.fetch_data(src)
            if txt:
                chunks.append(txt)
        data = "\n".join(chunks)

    elif clean_choice == "2":
        path = os.path.join("vless", "best-1.txt")
        if os.path.isfile(path):
            cc.log(f"📂 Чтение {path}...")
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        else:
            cc.log("⚠️ Локальный файл не найден, загружаю из сети...")
            data = cc.fetch_data("https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/vless.txt")

    elif clean_choice == "3":
        path = os.path.join("hysteria2", "best-1.txt")
        if os.path.isfile(path):
            cc.log(f"📂 Чтение {path}...")
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        else:
            cc.log("⚠️ Локальный файл не найден, загружаю из сети...")
            data = cc.fetch_data("https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/hysteria2.txt")

    elif clean_choice == "4":
        cc.log("🌐 Загрузка полных онлайн-баз 2026 года...")
        chunks = []
        for src in EXPRESS_2026_SOURCES + FULL_ONLINE_SOURCES:
            txt = cc.fetch_data(src)
            if txt:
                chunks.append(txt)
        data = "\n".join(chunks)

    elif clean_choice == "5":
        custom = input("Вставьте ссылку на подписку или путь к файлу:\n> ").strip()
        if os.path.isfile(custom):
            with open(custom, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        else:
            data = cc.fetch_data(custom)

    else:
        # Если пользователь сразу вставил ссылку или путь к файлу
        if os.path.isfile(user_input):
            cc.log(f"📂 Чтение локального файла: {user_input}")
            with open(user_input, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        else:
            cc.log(f"🌐 Загрузка подписки: {user_input}")
            data = cc.fetch_data(user_input)

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
        cc.log("⚠️ В источниках не обнаружено подходящих конфигураций.")
        return

    cc.log(
        f"📦 Найдено серверов: Hysteria2={len(hysteria_configs)}, "
        f"VLESS={len(vless_configs)}, VMESS={len(vmess_configs)}, "
        f"Shadowsocks={len(ss_configs)}, Trojan={len(trojan_configs)} | Всего: {len(all_configs)}"
    )

    # Дедупликация
    unique_configs = cc.deduplicate_configs(all_configs, protocol=None, show_log=False)
    if len(unique_configs) != len(all_configs):
        cc.log(f"🔍 После дедупликации: {len(unique_configs)} уникальных серверов")

    # Многопоточная проверка
    max_workers = min(cc.DEFAULT_MAX_WORKERS, 40)
    cc.log(f"🧪 Запуск параллельной проверки доступности ({max_workers} потоков)...")

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
        cc.log("❌ Ни один сервер не ответил.")
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

    for proto in stats_by_proto:
        proto_cfgs = [c for _, c, p in working_results if p == proto]
        if proto_cfgs:
            p_file = os.path.join(output_dir, f"working-{proto}.txt")
            cc.create_subscription_file(proto_cfgs, p_file)

    print()
    print("=" * 64)
    cc.log(f"✅ Рабочие серверы сохранены в: {output_file}")
    print("=" * 64)
    print()
    print("⭐ ТОП-5 САМЫХ БЫСТРЫХ СЕРВЕРОВ (можно сразу копировать в клиент):")
    print("-" * 64)
    for i, (ping, cfg, proto) in enumerate(working_results[:5], 1):
        print(f"[{i}] Пинг: {ping} ms | Протокол: {proto.upper()}")
        print(f"    {cfg}")
        print()
    print("-" * 64)
    cc.log("🎉 Готово! Все рабочие строки находятся в файле results\\working-from-subscription.txt")

    # Автоматически открываем файл результатов в блокноте на Windows
    try:
        os.startfile(output_file)
    except Exception:
        pass


if __name__ == "__main__":
    main()
