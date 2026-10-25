# Грабли и решения

## Zabbix: 404
Путь API должен быть `/zabbix/api_jsonrpc.php`. Без `/zabbix/` веб-сервер отвечает 404. См. [04-zabbix.md](04-zabbix.md).

## «Data source not found» после уборки
Удалённый источник ломает все панели, которые на него ссылаются. Пересоздайте источник с тем же uid.

## node_exporter: порт занят
Если на хосте уже работает контейнер (rootless Podman) с публикацией порта 9100, системный node_exporter не стартует. Разведите порты или уберите дубль.

## Нужные коллекторы node_exporter
По умолчанию не включены `tcpstat`, `interrupts`, `powersupplyclass`. Роль для Ansible: `scripts/node-exporter-collectors.yml` (после рестарта пауза 5 секунд, иначе проверка порта ложно падает).

## cAdvisor при Docker с FORWARD DROP
Контейнер в мостовой сети не достаёт до хоста. Запускайте с `--network=host` и `--cgroupns=host`, иначе метрик контейнеров не будет.

## Названия контейнеров вместо хэшей
cAdvisor отдаёт `id`. Подписи добавляются relabel-правилом: `scripts/patch-prometheus-names.py`.

## Красивый instance
Prometheus в контейнере ходит на хост через `host.containers.internal`. Чтобы в метках был реальный адрес, используйте relabel из `scripts/patch-prometheus.py`. Файл `prometheus.yml`, смонтированный одним файлом, нельзя править через `sed -i`: меняется inode, и контейнер продолжает видеть старую версию. Скрипт пишет в тот же inode.

## SELinux и Fluent Bit
Fluent Bit в контейнере не читает журналы хоста. Решение: `SecurityLabelType=spc_t` в Quadlet-юните (`scripts/fix-fluentbit-selinux.sh`).

## SELinux и MongoDB
Отказы `mongod_t` на `container_var_lib_t:dir search` (FTDC) шумят в журнале. Безопасный вариант: модуль `dontaudit` (`scripts/mongod-ftdc-dontaudit.sh`), не `permissive`.

## Аннотации Graylog пустые
Нужен отдельный источник на `gl-events_*` и запрос `alert:true`, см. [03-annotations.md](03-annotations.md).

## Пустые панели
Не оставляйте их: либо найдите источник данных, либо уберите панель. Панель, пустая по смыслу («Что не отвечает»), получает понятную подпись.
