# Аннотации из Graylog

Идея: алерты Graylog рисуются вертикальными линиями на графиках метрик. Видно, что именно сработало в момент всплеска CPU или падения сервиса.

## Как устроено

Graylog пишет события (Events) в индекс `gl-events_*`. Источник данных Elasticsearch/OpenSearch на этот индекс (uid `eg27m552vbgn4e`) используется как источник аннотаций:

| Поле | Значение |
|---|---|
| Query | `alert:true` |
| Time field | `timestamp` |
| Text field | `message` |
| Tags field | `source` |

В JSON дашборда это выглядит так:

```json
{
  "datasource": {"type": "elasticsearch", "uid": "eg27m552vbgn4e"},
  "enable": true,
  "iconColor": "red",
  "name": "События Graylog",
  "target": {"query": "alert:true", "tagsField": "source", "textField": "message", "timeField": "timestamp"}
}
```

Блок уже есть во всех дашбордах репозитория.

## Подводные камни

- Если в индексе нет поля `alert`, запрос вернёт пусто; проверьте в Discover.
- Слишком частые алерты превращаются в «забор» линий. Ограничьте запрос (например, `alert:true AND priority:>=3`).
