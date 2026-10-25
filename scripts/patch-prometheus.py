#!/usr/bin/env python3
"""Правка prometheus.yml: красивый instance для wazuh-homelab и (по ключу) цели cAdvisor.

  python3 patch-prometheus.py /home/user/monitoring/prometheus.yml            # только instance
  python3 patch-prometheus.py /home/user/monitoring/prometheus.yml --cadvisor # + cAdvisor на .56 и .149

Файл перезаписывается на месте (тот же inode) — это важно, потому что он
смонтирован в контейнер одним файлом: sed -i создал бы новый inode, и
контейнер продолжил бы видеть старую версию.
"""
import sys

path = sys.argv[1]
with_cadvisor = "--cadvisor" in sys.argv[2:]
src = open(path, encoding="utf-8").read()
out = src

RELABEL = (
    "    # Контейнер Prometheus ходит на хост через host.containers.internal;\n"
    "    # в метках показываем реальный адрес хоста.\n"
    "    relabel_configs:\n"
    "      - source_labels: [__address__]\n"
    "        regex: 'host\\.containers\\.internal:(\\d+)'\n"
    "        target_label: instance\n"
    "        replacement: '192.168.1.37:$1'\n"
)

def once(text, old, new, what):
    if text.count(old) != 1:
        sys.exit(f"ОШИБКА: не нашёл ровно одно место для «{what}» (нашёл {text.count(old)}). Файл не изменён.")
    return text.replace(old, new)

if "target_label: instance\n        replacement: '192.168.1.37" not in out:
    out = once(out,
        "    scrape_interval: 15s\n\n  - job_name: 'cadvisor_all'",
        "    scrape_interval: 15s\n" + RELABEL + "\n  - job_name: 'cadvisor_all'",
        "job node_exporters")
    out = once(out,
        "    scrape_interval: 15s\n    # cAdvisor запущен без runtime-сокета",
        "    scrape_interval: 15s\n" + RELABEL + "    # cAdvisor запущен без runtime-сокета",
        "job cadvisor_all")

if with_cadvisor:
    out = once(out, "          # - '192.168.1.56:8080'    # homeserver",
                    "          - '192.168.1.56:8080'    # homeserver", "cadvisor homeserver")
    out = once(out, "          # - '192.168.1.149:8080'   # redos-raspi",
                    "          - '192.168.1.149:8080'   # redos-raspi", "cadvisor redos-raspi")
    out = out.replace("# На остальных хостах cAdvisor не запущен (было вечно DOWN):",
                      "# Остальные хосты: cAdvisor есть на homeserver и redos-raspi, на прочих не проверялось:")

if out == src:
    print("Изменений нет, файл уже в нужном виде.")
else:
    with open(path, "w", encoding="utf-8") as f:   # тот же inode
        f.write(out)
    print("Файл обновлён.")
