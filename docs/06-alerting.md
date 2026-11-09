# Алертинг Grafana

Graylog алертит по логам, а инфраструктурные метрики (Prometheus) раньше
никто не сторожил: хост упал или диск кончился — узнавали случайно. Этот
контур закрывает метрики. Оповещения идут в существующий Alertmanager,
поэтому алерты Grafana появляются на дашборде «Алерты» рядом с остальными.

## Правила

Группа `infrastructure`, папка «Инфраструктура», проверка раз в минуту:

| Правило | Условие | Терпим | Серьёзность |
|---|---|---|---|
| Хост не отвечает (node_exporter) | `up{job="node_exporters"} == 0` | 5 мин | critical |
| Веб-сервис недоступен (blackbox) | `probe_success{job="blackbox_http"} == 0` | 10 мин | warning |
| Диск заполнен > 85% | `1 - avail/size` по корневому разделу | 30 мин | warning |
| Контейнер молчит | `time() - container_last_seen > 15 мин` (cAdvisor) | 15 мин | warning |

Экспорт: [provisioning/alert-rules.json](../provisioning/alert-rules.json).
Импорт обратно — API `POST /api/v1/provisioning/alert-rules` для каждого
объекта из массива.

## Канал и маршрутизация

- Контактная точка `Alertmanager` (тип `prometheus-alertmanager`,
  адрес `http://alertmanager:9093` — имя контейнера в общей podman-сети).
- Корневая политика оповещений указывает на неё
  ([provisioning/policies.json](../provisioning/policies.json),
  [provisioning/contact-points.json](../provisioning/contact-points.json)).
- Штатный `grafana-default-email` не используется: без SMTP в `grafana.ini`
  письма из Grafana не уходят, а Alertmanager уже умеет в webhook-sink.

## Грабли

- **Порог в threshold-условии должен соответствовать выражению.** Для
  `1 - up` порог `> 0.5`, для доли занятого диска — `> 0.85`, для минут
  молчания контейнера — `> 15`. Универсального порога нет: правило с
  порогом 0.5 на «доли диска» горит постоянно.
- Падающий хост в `node_exporters` — это нормальный `up=0` (Prometheus
  пишет серию даже при неудачном scrape), поэтому `absent()` не нужен.
- Правила, созданные через API provisioning, в интерфейсе read-only —
  править их снова через API (или снять признак `X-Disable-Provenance`).

## Проверка

```bash
# состояние правил
curl -sk -u admin:*** \
  https://grafana.example/api/prometheus/grafana/api/v1/rules | jq '.data.groups[].rules[] | {name, state}'

# дошло ли до Alertmanager
curl -sk https://alertmanager.example/api/v2/alerts | jq '.[].labels.alertname'
```
