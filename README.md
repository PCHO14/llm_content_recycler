# Модуль для переиспользования видео-контента с помощью LLM

На данный момент реализован механизм скачивания видео с RuTube с помощью
[rutube-transcriber](https://github.com/PixelNinja123/rutube-transcriber/tree/create_module#), а
также определение тематики видео с помощью локальной LLM

Запуск скачивания и определения тематики видео:

```bash
uv run -m llm_content_recylcer.download_and_analyze_content <ссылка_на_видео>
```

В результате в папке **files/** будет создан ***.db*** файл формата:

```
| id | video_id | url | title | transcription | tag |
|----|----------|-----|-------|---------------|-----|
|    |          |     |       |               |     |
```

Для работы с другими проектами есть 3 основные функции, ничего кроме них не должно использоваться:

- llm_content_recylcer.download_and_analyze_content.download_and_analyze_content()
- llm_content_recylcer.llm_module.init_model()
- rutube_transcriber.database.init_db()
