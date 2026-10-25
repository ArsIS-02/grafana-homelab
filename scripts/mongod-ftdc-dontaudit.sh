#!/usr/bin/env bash
# Убирает из журнала аудита безвредные отказы SELinux:
#   mongod_t (поток ftdc) -> search по /var/lib/containers (container_var_lib_t)
# Это правило dontaudit: оно НИЧЕГО НЕ РАЗРЕШАЕТ, а лишь перестаёт писать эти отказы.
# Запуск: sudo bash mongod-ftdc-dontaudit.sh
# Откат:  sudo semodule -r mongod_ftdc_dontaudit
set -eu

NAME=mongod_ftdc_dontaudit
mode="$(getenforce 2>/dev/null || echo Disabled)"
[ "$mode" = "Disabled" ] && { echo "SELinux выключен — делать нечего."; exit 0; }
for c in checkmodule semodule_package semodule; do
  command -v "$c" >/dev/null || { echo "Не найден $c. Установите: sudo dnf install checkpolicy policycoreutils"; exit 1; }
done
if semodule -l | grep -q "^$NAME\b"; then echo "Модуль $NAME уже установлен."; exit 0; fi

W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
cat > "$W/$NAME.te" <<'EOF'
module mongod_ftdc_dontaudit 1.0;

require {
    type mongod_t;
    type container_var_lib_t;
    class dir search;
}

dontaudit mongod_t container_var_lib_t:dir search;
EOF
checkmodule -M -m -o "$W/$NAME.mod" "$W/$NAME.te"
semodule_package -o "$W/$NAME.pp" -m "$W/$NAME.mod"
semodule -i "$W/$NAME.pp"
echo "Установлено: $(semodule -l | grep "^$NAME")"
echo "Новые отказы mongod_t/ftdc должны перестать появляться. Откат: semodule -r $NAME"
