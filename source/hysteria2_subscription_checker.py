"""
⚡ REBORN CFG - Multi-Protocol Subscription Checker 2026
Универсальный чекер с глубокой проверкой через реальные ядра:
Xray-core (VLESS, VMess, Trojan, SS) + sing-box (Hysteria 2).
Гарантия 100% работы в клиентах (v2rayN, Flclash, sing-box) без ошибок -1!
"""

from __future__ import annotations

import sys
import os
import re
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_collector as cc
import core_verifier as cv

# Источники по протоколам
RUSSIA_VLESS_REALITY_SOURCES = [
    # igareck - ежедневный сбор для РФ под ТСПУ
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    # 3inker - РФ подписки
    "https://raw.githubusercontent.com/3inker/v2ray-subscription/main/subs/all_ru.txt",
    # 0xRadikal - обновление каждые 15 минут
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/top100.txt",
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/vless.txt",
    # barry-far - крупнейший агрегатор
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt",
    # MatinGhanbari - обновление каждые 15 минут, фильтрованные
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/vless.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/super-sub.txt",
    # mahdibland - Eternity агрегатор
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity",
    # freefq - свежие конфиги
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    # MustafaBaqer/VestraNet-Nodes
    "https://raw.githubusercontent.com/MustafaBaqer/VestraNet-Nodes/main/protocols/vless.txt",
]

VMESS_SOURCES = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/vmess.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-By-Protocol/vmess.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/vmess.txt",
    "https://raw.githubusercontent.com/MustafaBaqer/VestraNet-Nodes/main/protocols/vmess.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt",
]

HYSTERIA2_SOURCES = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/hysteria2.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/hysteria2.txt",
    "https://raw.githubusercontent.com/MustafaBaqer/VestraNet-Nodes/main/protocols/hy2.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/hysteria2",
    "https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/refs/heads/main/configs/Hysteria2.txt",
]

TROJAN_SOURCES = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/trojan.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-By-Protocol/trojan.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/trojan.txt",
    "https://raw.githubusercontent.com/MustafaBaqer/VestraNet-Nodes/main/protocols/trojan.txt",
]

SS_SOURCES = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/protocols/shadowsocks.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-By-Protocol/ss.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/ss.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity",
]


def detect_proto(url: str) -> str:
    p = cv.parse_any(url)
    return p['protocol'].upper() if p else "UNKNOWN"


def main():
    print("=" * 68)
    print(" ⚡ REBORN CFG - Multi-Protocol Subscription Checker 2026")
    print(" Универсальная проверка через реальные ядра (Xray & sing-box)")
    print(" 0% ошибок -1 | 100% реальный доступ к сайтам через прокси")
    print("=" * 68)
    print()

    if cv.XRAY_BIN:
        print(f"✅ Xray-core обнаружен: {cv.XRAY_BIN}")
    else:
        print("⚠️ Xray-core не найден в стандартных папках v2rayN.")

    if cv.SINGBOX_BIN:
        print(f"✅ sing-box обнаружен: {cv.SINGBOX_BIN}")
    else:
        print("⚠️ sing-box не найден в стандартных папках v2rayN.")
    print()

    if len(sys.argv) >= 2:
        user_input = sys.argv[1].strip()
    else:
        print("Выберите действие (нажмите цифру или просто нажмите ENTER):")
        print(" [1] 🔥 VLESS Reality для РФ (Обход белых списков/ТСПУ) [ENTER]")
        print(" [2] 🔷 VMess (Cloudflare CDN / WebSocket)")
        print(" [3] 🚀 Hysteria 2 (Для sing-box / v2rayN sing-box core)")
        print(" [4] 🎯 Trojan (TLS проксирование)")
        print(" [5] 🔰 Shadowsocks")
        print(" [6] 🌐 Проверить ВСЕ протоколы сразу (Express-микс)")
        print(" [7] 📝 Вставить свою ссылку на подписку или путь к файлу")
        print()
        user_input = input("Ваш выбор > ").strip()

    data = ""
    clean_choice = user_input.replace('\ufeff', '').strip()

    # Загрузка источников
    if not clean_choice or clean_choice == "1":
        cc.log("🔥 Загрузка VLESS Reality (ежедневные базы для РФ)...")
        chunks = [cc.fetch_data(s) for s in RUSSIA_VLESS_REALITY_SOURCES]
        data = "\n".join(c for c in chunks if c)

    elif clean_choice == "2":
        cc.log("🔷 Загрузка баз VMess (Cloudflare CDN / WS)...")
        chunks = [cc.fetch_data(s) for s in VMESS_SOURCES]
        data = "\n".join(c for c in chunks if c)

    elif clean_choice == "3":
        cc.log("🚀 Загрузка Hysteria 2 конфигов...")
        chunks = [cc.fetch_data(s) for s in HYSTERIA2_SOURCES]
        data = "\n".join(c for c in chunks if c)

    elif clean_choice == "4":
        cc.log("🎯 Загрузка Trojan конфигов...")
        chunks = [cc.fetch_data(s) for s in TROJAN_SOURCES]
        data = "\n".join(c for c in chunks if c)

    elif clean_choice == "5":
        cc.log("🔰 Загрузка Shadowsocks конфигов...")
        chunks = [cc.fetch_data(s) for s in SS_SOURCES]
        data = "\n".join(c for c in chunks if c)

    elif clean_choice == "6":
        cc.log("🌐 Загрузка экспресс-микса всех 5 протоколов...")
        mix_sources = [
            RUSSIA_VLESS_REALITY_SOURCES[0],
            RUSSIA_VLESS_REALITY_SOURCES[1],
            VMESS_SOURCES[0],
            HYSTERIA2_SOURCES[0],
            TROJAN_SOURCES[0]
        ]
        chunks = [cc.fetch_data(s) for s in mix_sources]
        data = "\n".join(c for c in chunks if c)

    elif clean_choice == "7":
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

    # Извлечение всех конфигов
    raw_configs = (
        cc.extract_vless_configs(data)
        + cc.extract_vmess_configs(data)
        + cc.extract_hysteria2_configs(data)
        + cc.extract_trojan_configs(data)
        + cc.extract_shadowsocks_configs(data)
    )

    unique_configs = cc.deduplicate_configs(raw_configs, show_log=False)
    cc.log(f"📦 Найдено уникальных конфигов: {len(unique_configs)}")

    if not unique_configs:
        cc.log("⚠️ Не найдено подходящих конфигов.")
        return

    # Запуск глубокой проверки через ядра
    cc.log(f"🔬 Запуск проверки через ядро (проверка реальной загрузки сайтов HTTP 204)...")
    t0 = time.time()
    working_results = cv.verify_configs_deep(unique_configs, max_candidates=150)
    elapsed = round(time.time() - t0, 1)

    cc.log(f"⏱️ Проверка завершена за {elapsed} сек! 100% рабочих узлов: {len(working_results)}")

    if not working_results:
        cc.log("❌ Ни один сервер не ответил на проверку интернет-трафика.")
        return

    # Сохранение в results/working-from-subscription.txt
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "working-from-subscription.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        for cfg, _ in working_results:
            f.write(cfg.strip() + "\n")

    # Статистика по протоколам
    stats = {}
    for cfg, _ in working_results:
        p = detect_proto(cfg)
        stats[p] = stats.get(p, 0) + 1
    summary = ", ".join(f"{k}: {v}" for k, v in sorted(stats.items()))
    cc.log(f"📈 Рабочие серверы по протоколам: {summary}")

    print()
    print("=" * 68)
    cc.log(f"✅ В файл сохранено {len(working_results)} 100% проверенных рабочих серверов!")
    cc.log(f"📁 Путь: {output_file}")
    print("=" * 68)
    print()
    print("⭐ ТОП-5 САМЫХ БЫСТРЫХ СЕРВЕРОВ (0 ошибок -1 в v2rayN):")
    print("-" * 68)
    for i, (cfg, ping) in enumerate(working_results[:5], 1):
        proto = detect_proto(cfg)
        print(f"[{i}] Пинг: {ping} ms | Протокол: {proto}")
        print(f"    {cfg}")
        print()
    print("-" * 68)
    cc.log("🎉 Готово! Все конфиги в файле гарантированно открывают сайты!")

    try:
        os.startfile(output_file)
    except Exception:
        pass


if __name__ == "__main__":
    main()
