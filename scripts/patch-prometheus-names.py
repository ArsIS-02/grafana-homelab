#!/usr/bin/env python3
"""Подписывает безымянные rootful-контейнеры в метриках cAdvisor.

cAdvisor без доступа к сокету podman знает контейнер только по cgroup-пути, и
правило в prometheus.yml превращает его в podman-<12 hex>. Здесь эти id
сопоставляются с именами из `sudo podman ps`.

Важно: id меняется, когда контейнер пересоздаётся (обновление образа, ручной
`podman run`). Тогда имя пропадёт и вернётся podman-<id>: просто обновите список.

  python3 patch-prometheus-names.py /home/user/monitoring/prometheus.yml
Файл переписывается на месте (тот же inode — он смонтирован в контейнер файлом).
"""
import sys

NAMES = [  # (id, имя, хост — только для комментария)
    ("d89433967925", "netalertx",       "homeserver"),
    ("d31aa6f674a1", "portainer_agent", "homeserver"),
    ("7564d00da4bd", "fluent-bit",      "homeserver"),
    ("1dcd97cba7d3", "promtail",        "homeserver"),
    ("7ea1223768f4", "cadvisor",        "homeserver"),
    ("9ca5f541401a", "promtail",        "wazuh-homelab"),
    ("a98c29e3f8a0", "heimdall",        "wazuh-homelab"),
    ("6de62a7e9d45", "portainer_agent", "wazuh-homelab"),
    ("f452fbd83518", "fluent-bit",      "wazuh-homelab"),
    ("3a3267167a64", "wyl",             "wazuh-homelab"),
    ("b2229a7e3c8f", "cadvisor",        "wazuh-homelab"),
    ("ab65c605c68f", "portainer_agent", "redos-raspi"),
    ("884bf03dae91", "fluent-bit",      "redos-raspi"),
    ("26b75111d1be", "promtail",        "redos-raspi"),
    ("e6e2361a5850", "cadvisor",        "redos-raspi"),
]
MARK = "# имена rootful-контейнеров (id из `podman ps`)"
ANCHOR = "      # выкидываем метрики cgroup'ов, которые не являются контейнерами\n"

path = sys.argv[1]
src = open(path, encoding="utf-8").read()
if MARK in src:
    print("Сопоставление имён уже есть — для обновления удалите блок «имена rootful-контейнеров» и запустите снова.")
    sys.exit(0)
if src.count(ANCHOR) != 1:
    sys.exit(f"ОШИБКА: ожидал ровно одно место вставки, нашёл {src.count(ANCHOR)}. Файл не изменён.")

block = f"      {MARK}\n"
for cid, name, host in NAMES:
    block += (f"      - source_labels: [container]   # {host}\n"
              f"        regex: 'podman-{cid}'\n"
              f"        target_label: container\n"
              f"        replacement: '{name}'\n")
with open(path, "w", encoding="utf-8") as f:   # тот же inode
    f.write(src.replace(ANCHOR, block + ANCHOR))
print(f"Добавлено правил: {len(NAMES)}.")
