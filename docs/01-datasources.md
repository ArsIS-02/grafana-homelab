# Источники данных

Дашборды ссылаются на источники по uid. Создавайте источники с теми же uid (в интерфейсе uid задаётся через API или provisioning, а не в форме).

| Название | Тип | uid | Адрес |
|---|---|---|---|
| Prometheus | prometheus | `bg23rxlukphc0f` | `http://prometheus:9090` |
| Graylog Events | elasticsearch | `eg27m552vbgn4e` | OpenSearch, индекс `gl-events_*`, поле времени `timestamp` |
| Graylog OpenSearch | elasticsearch | `eg242vho5o45cc` | OpenSearch, индексы Graylog (`graylog_*`) |
| Loki | loki | `cf1ikgnvi3chsf` | `http://loki:3100` |
| Zabbix-homeserver | alexanderzobnin-zabbix-datasource | `eg2asfb9khv5sa` | см. [04-zabbix.md](04-zabbix.md) |

## Создание с нужным uid через API

```bash
curl -s -u admin:*** -H 'Content-Type: application/json' \
  -X POST https://grafana.example/api/datasources -d '{
    "name": "Prometheus", "type": "prometheus", "uid": "bg23rxlukphc0f",
    "url": "http://prometheus:9090", "access": "proxy", "isDefault": true }'
```

Пароли и токены в репозиторий не кладём: при provisioning берите их из переменных окружения (`$__env{...}`) или `secureJsonData`.

## Что важно

- Источник «Graylog OpenSearch» нельзя удалять «для уборки»: все панели логов начнут отвечать «Data source not found». Если он всё же удалён, создайте его заново с тем же uid, панели оживут без правки дашбордов.
- Для событий Graylog нужен отдельный источник на `gl-events_*`, потому что в основном индексе событий (алертов) нет.
