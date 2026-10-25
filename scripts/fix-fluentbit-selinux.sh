#!/usr/bin/env bash
# Разрешает контейнеру Fluent Bit читать журнал systemd под SELinux.
# Добавляет в [Container] строку SecurityLabelType=spc_t, только если:
#   - SELinux включён,
#   - файл fluent-bit.container существует и в нём ещё нет этой строки,
#   - за сегодня есть отказы flb-pipeline (или передан ключ --force).
# Перед правкой делает резервную копию. Запуск: sudo bash fix-fluentbit-selinux.sh [--force]
set -u

F="${FLUENTBIT_UNIT:-/etc/containers/systemd/fluent-bit.container}"
FORCE=0; [ "${1:-}" = "--force" ] && FORCE=1
STAMP="$(date +%Y%m%d)"

mode="$(getenforce 2>/dev/null || echo Disabled)"
echo "Хост: $(hostname), SELinux: $mode"
if [ "$mode" = "Disabled" ]; then echo "SELinux выключен — править нечего."; exit 0; fi
if [ ! -f "$F" ]; then echo "Нет файла $F — на этом хосте Fluent Bit не как Quadlet, пропускаю."; exit 0; fi
if grep -q '^SecurityLabelType=' "$F"; then echo "SecurityLabelType уже задан: $(grep '^SecurityLabelType=' "$F")"; exit 0; fi

n="$(ausearch -m avc -c flb-pipeline -ts today 2>/dev/null | grep -c 'type=AVC')"
echo "Отказов flb-pipeline за сегодня: $n"
if [ "$n" -eq 0 ] && [ "$FORCE" -eq 0 ]; then
  echo "Отказов нет — ничего не меняю (для принудительной правки: --force)."
  exit 0
fi

cp -p "$F" "$F.bak-$STAMP" || { echo "Не удалось сделать копию, прекращаю."; exit 1; }
if ! grep -q '^Network=host$' "$F"; then
  # Без Network=host вставляем строку сразу после [Container]
  sed -i 's/^\[Container\]$/[Container]\nSecurityLabelType=spc_t/' "$F"
else
  sed -i 's/^Network=host$/Network=host\nSecurityLabelType=spc_t/' "$F"
fi
if [ "$(grep -c '^SecurityLabelType=spc_t$' "$F")" -ne 1 ]; then
  echo "Правка не применилась, возвращаю файл."; cp -p "$F.bak-$STAMP" "$F"; exit 1
fi

systemctl daemon-reload
systemctl restart fluent-bit
sleep 15
echo "Служба: $(systemctl is-active fluent-bit)"
echo "Метка процесса: $(podman inspect fluent-bit --format '{{.ProcessLabel}}' 2>/dev/null)"
echo "Новых отказов за последние 10 минут: $(ausearch -m avc -c flb-pipeline -ts recent 2>/dev/null | grep -c 'type=AVC')"
echo "Откат: cp -p $F.bak-$STAMP $F && systemctl daemon-reload && systemctl restart fluent-bit"
