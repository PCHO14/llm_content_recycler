"""
Gradio UI для llm-content-recycler.
Запуск: python app.py

Два сценария:
  TAB 1 — загрузка: ссылки → download_and_analyze_content() → БД → (опц.) сразу пост
  TAB 2 — из базы:  выбрать видео из БД → сгенерировать пост

POST_MOCK = True  — заглушка для генерации поста
POST_MOCK = False — реальный вызов LLM
"""

import json
import re
import sqlite3
import time

import gradio as gr

from llm_content_recylcer.const import PATH_TO_DB, MODEL_NAME, INIT_PROMT
from llm_content_recylcer.css import CSS
from llm_content_recylcer.llm_module import init_model, get_tag
from llm_content_recylcer.download_and_analyze_content import download_and_analyze_content
from rutube_transcriber.database import init_db

# ---------------------------------------------------------------------------
# Конфиг
# ---------------------------------------------------------------------------
DB_PATH   = PATH_TO_DB
POST_MOCK = False   # ← False когда LLM доступен для генерации постов

# ---------------------------------------------------------------------------
# Модель — ленивая инициализация
# ---------------------------------------------------------------------------
_llm_model = None
_llm_chat  = None


def _get_model():
    global _llm_model, _llm_chat
    if _llm_model is None:
        _llm_model, _llm_chat = init_model(MODEL_NAME, INIT_PROMT)
    return _llm_model, _llm_chat

# ---------------------------------------------------------------------------
# Промт для поста (скрыт от пользователя, пожелания подставляются в {wishes})
# ---------------------------------------------------------------------------
_PROMPT_POST = """\
Ты — контент-мейкер. Создай лаконичный пост для Telegram на основе видео.

Видео:
  Название: {video_title}
  Тег: {video_tag}
  Ссылка: {video_url}
  Транскрипция: {transcription}

Пожелания к посту: {wishes}

Формат ответа (строго валидный JSON, без markdown):
{{
  "post_title": "цепляющий заголовок (5-8 слов)",
  "post_text": "2-4 предложения, суть + польза (макс. 250 символов)",
  "video_link": "[Смотреть видео]({video_url})",
  "hashtag": "#тег (из video_tag)"
}}

Правила: только факты из транскрипции, без выдумок, без текста вне JSON.
Если пожелания заданы — обязательно учти их.
"""

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _all_videos() -> list:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
        cur.execute("SELECT video_id, title, url, transcription, tag FROM videos")
        rows = cur.fetchall()
        conn.close()
        return [{"id": r[0], "title": r[1], "url": r[2], "transcription": r[3], "tag": r[4]} for r in rows]
    except Exception:
        return []


def _get_top_tags() -> list:
    seen, result = set(), []
    for v in _all_videos():
        tag   = v.get("tag", "") or ""
        parts = tag.split(":")
        short = ":".join(parts[:2]) if len(parts) >= 2 else tag
        if short and short not in seen:
            seen.add(short)
            result.append(short)
    return sorted(result)

def _videos_by_prefix(prefix: str) -> list:
    prefix = prefix.lower().strip()
    return [
        v for v in _all_videos()
        if (v.get("tag") or "").lower() == prefix
        or (v.get("tag") or "").lower().startswith(prefix + ":")
    ]

# ---------------------------------------------------------------------------
# Генерация поста
# ---------------------------------------------------------------------------


def _parse_json(text: str):
    try:
        return json.loads(re.sub(r'```json|```', '', text).strip())
    except Exception:
        return None


def _make_post(video: dict, wishes: str = "") -> str:
    wishes = wishes.strip() or "нет"

    if POST_MOCK:
        time.sleep(1.0)
        hashtag = "#" + (video.get("tag") or "видео").replace(":", "_")
        wishes_line = f"\n*пожелания учтены: {wishes}*" if wishes != "нет" else ""
        return (
            f"###  {video['title']}\n\n"
            f"Нашли видео, которое объясняет тему понятным языком — без воды, только суть. "
            f"Автор разбирает ключевые моменты так, что хочется пересмотреть ещё раз.\n\n"
            f"[Смотреть видео]({video['url']})\n"
            f"{hashtag}"
            f"{wishes_line}\n\n"
            f"*️ POST_MOCK=True — замени на False для реального LLM*"
        )

    try:
        model, chat = _get_model()
        prompt = _PROMPT_POST.format(
            video_title   = video["title"],
            video_tag     = video.get("tag", ""),
            video_url     = video["url"],
            transcription = (video.get("transcription") or "")[:2000],
            wishes        = wishes,
        )
        raw  = get_tag(model, chat, prompt)
        post = _parse_json(raw)
        if not post:
            return f" Не удалось распарсить ответ LLM.\n\n```\n{raw}\n```"

        parts = [
            f"### {post.get('post_title', '')}",
            "",
            post.get("post_text", ""),
            "",
            post.get("video_link", f"[Смотреть видео]({video['url']})"),
            post.get("hashtag", ""),
        ]
        return "\n".join(parts)

    except Exception as e:
        return f" Ошибка при генерации поста: {e}"

# ---------------------------------------------------------------------------
# TAB 1 — Загрузка
# ---------------------------------------------------------------------------

def process_urls(urls_text: str, progress=gr.Progress()):
    if not urls_text.strip():
        return "Введите хотя бы одну ссылку."

    urls = [u.strip() for u in urls_text.strip().splitlines() if u.strip()]
    init_db(DB_PATH)
    log_lines = []
    n = len(urls)

    for i, url in enumerate(urls):
        base = i / n
        step = 1 / n

        try:
            # шаг 1 — подключение к LLM
            progress(base + step * 0.1, desc=f"[{i+1}/{n}] Подключаю модель...")
            model, chat = _get_model()

            # шаг 2 — скачивание аудио
            progress(base + step * 0.3, desc=f"[{i+1}/{n}] Скачиваю аудио...")

            # шаг 3 — транскрибация
            progress(base + step * 0.6, desc=f"[{i+1}/{n}] Транскрибирую...")

            # шаг 4 — анализ LLM
            progress(base + step * 0.85, desc=f"[{i+1}/{n}] Определяю тег...")

            download_and_analyze_content(url, DB_PATH, model, chat)

            all_v = _all_videos()
            saved = next((v for v in reversed(all_v) if v["url"] == url), None)
            tag   = saved["tag"] if saved else "?"

            progress(base + step, desc=f"[{i+1}/{n}] Готово")
            log_lines.append(f"[{i+1}/{n}]  {url}\n     тег: {tag}")

        except Exception as e:
            log_lines.append(f"[{i+1}/{n}]  {url}\n     ошибка: {e}")

    progress(1.0, desc="Все видео обработаны")
    return "\n\n".join(log_lines)

# ---------------------------------------------------------------------------
# TAB 2 — Из базы
# ---------------------------------------------------------------------------


def refresh_tags():
    tags = _get_top_tags()
    return gr.update(choices=["— все —"] + tags, value="— все —")


def filter_videos(tag_filter: str):
    if not tag_filter or tag_filter == "— все —":
        videos = _all_videos()
    else:
        videos = _videos_by_prefix(tag_filter)
    choices = [f"{v['title']}  [{v['tag']}]" for v in videos]
    return gr.update(choices=choices, value=choices[0] if choices else None)


def gen_post_from_db(selected: str, wishes: str, progress=gr.Progress()):
    if not selected:
        return "️  Выберите видео из списка."
    title_part = selected.split("  [")[0].strip()
    video = next((v for v in _all_videos() if v["title"] == title_part), None)
    if not video:
        return "️  Видео не найдено в базе."
    progress(0.3, desc="Генерирую пост...")
    return _make_post(video, wishes)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def build_app():
    init_choices = [f"{v['title']}  [{v['tag']}]" for v in _all_videos()]

    theme = gr.themes.Base(
        primary_hue=gr.themes.colors.Color(
            c50="#FFF1B5", c100="#C1DBE8", c200="#C1DBE8", c300="#9dc4d8",
            c400="#7aaac8", c500="#43302E", c600="#362420", c700="#2a1a18",
            c800="#1e1210", c900="#120a08", c950="#080402",
        ),
        neutral_hue=gr.themes.colors.Color(
            c50="#FFF1B5", c100="#e8d890", c200="#c9a898", c300="#a07868",
            c400="#7a5048", c500="#5a3e3a", c600="#4e3430", c700="#43302E",
            c800="#362420", c900="#2a1a18", c950="#1e1210",
        ),
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        body_background_fill="#43302E",
        body_background_fill_dark="#43302E",
        block_background_fill="#43302E",
        block_background_fill_dark="#43302E",
        block_border_color="#4e3430",
        block_label_background_fill="#43302E",
        block_label_text_color="#c9a898",
        block_title_text_color="#c9a898",
        input_background_fill="#362420",
        input_background_fill_dark="#362420",
        input_border_color="#5a3e3a",
        input_border_color_focus="#C1DBE8",
        button_primary_background_fill="#C1DBE8",
        button_primary_background_fill_hover="#9dc4d8",
        button_primary_text_color="#43302E",
        button_secondary_background_fill="transparent",
        button_secondary_text_color="#c9a898",
        button_secondary_border_color="#5a3e3a",
        checkbox_background_color="#362420",
        checkbox_background_color_selected="#C1DBE8",
        checkbox_border_color="#c9a898",
        checkbox_border_color_selected="#C1DBE8",
        checkbox_label_background_fill="#43302E",
        checkbox_label_background_fill_selected="#362420",
        checkbox_label_text_color="#FFF1B5",
        color_accent="#C1DBE8",
        color_accent_soft="rgba(193,219,232,0.2)",
    )
    with gr.Blocks(title="content recycler") as demo:

        gr.HTML("""
        <div class="app-header">
          <h1>content <span>recycler</span></h1>
          <p>rutube → transcription → llm → post</p>
        </div>
        """)

        with gr.Tabs():

            # ── TAB 1: ЗАГРУЗКА ──────────────────────────────────────────
            with gr.Tab("01 / загрузка"):

                with gr.Row(equal_height=False):

                    # левая колонка — ввод
                    with gr.Column(scale=2):
                        urls_input = gr.Textbox(
                            label="ссылки на видео",
                            placeholder=(
                                "https://rutube.ru/video/abc123\n"
                                "https://rutube.ru/video/def456"
                            ),
                            lines=7, max_lines=30,
                        )

                        with gr.Row():
                            load_btn  = gr.Button("▶  скачать и обработать", variant="primary")
                            clear_btn = gr.Button("очистить", variant="secondary")

                    # правая колонка — лог
                    with gr.Column(scale=2):
                        load_log = gr.Markdown(elem_classes="log-out", value="", label="лог", show_label=True)

                load_btn.click(
                    fn=process_urls,
                    inputs=[urls_input],
                    outputs=[load_log],
                )
                clear_btn.click(
                    fn=lambda: ("", ""),
                    outputs=[urls_input, load_log],
                )

            # ── TAB 2: ИЗ БАЗЫ ──────────────────────────────────────────
            with gr.Tab("02 / из базы"):

                with gr.Row(equal_height=False):

                    # левая колонка — фильтр + список
                    with gr.Column(scale=1):

                        with gr.Row():
                            tag_filter = gr.Dropdown(
                                label="фильтр по тегу",
                                choices=["— все —"] + _get_top_tags(),
                                value="— все —",
                                interactive=True,
                                scale=3,
                            )
                            refresh_btn = gr.Button("↻", variant="secondary", size="sm", scale=1)

                        video_radio = gr.Radio(
                            label="видео из базы",
                            choices=init_choices,
                            value=init_choices[0] if init_choices else None,
                            interactive=True,
                            elem_classes="radio-box",
                        )

                    # правая колонка — пожелания + кнопки + результат
                    with gr.Column(scale=2):

                        wishes_tab2 = gr.Textbox(
                            label="пожелания к посту",
                            placeholder="например: экспертный тон, для школьников, без эмодзи...",
                            lines=2,
                            elem_classes="wishes-box",
                        )

                        with gr.Row():
                            gen_btn   = gr.Button("▶  сгенерировать пост", variant="primary")
                            regen_btn = gr.Button("↻  ещё раз", variant="secondary")

                        post_out_tab2 = gr.Markdown(
                            elem_classes="md-out", value="", label="готовый пост",
                        )

                tag_filter.change(fn=filter_videos, inputs=[tag_filter], outputs=[video_radio])
                refresh_btn.click(fn=refresh_tags, outputs=[tag_filter])
                gen_btn.click(fn=gen_post_from_db, inputs=[video_radio, wishes_tab2], outputs=[post_out_tab2])
                regen_btn.click(fn=gen_post_from_db, inputs=[video_radio, wishes_tab2], outputs=[post_out_tab2])

    return demo
