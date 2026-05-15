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
from pathlib import Path

import gradio as gr

from llm_content_recylcer.const import PATH_TO_DB, MODEL_NAME, INIT_PROMT
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

def process_urls(urls_text: str, wishes: str, make_post_flag: bool, progress=gr.Progress()):
    if not urls_text.strip():
        return "️  Введите хотя бы одну ссылку.", gr.update(value="", visible=False)

    urls = [u.strip() for u in urls_text.strip().splitlines() if u.strip()]
    init_db(DB_PATH)
    log_lines  = []
    last_video = None

    for i, url in enumerate(urls):
        progress((i + 1) / len(urls), desc=f"Обрабатываю {i+1}/{len(urls)}")
        try:
            model, chat = _get_model()
            download_and_analyze_content(url, DB_PATH, model, chat)

            all_v = _all_videos()
            saved = next((v for v in reversed(all_v) if v["url"] == url), None)
            tag   = saved["tag"] if saved else "?"
            last_video = saved

            log_lines.append(f"  [{i+1}/{len(urls)}]  {url}\n     тег: {tag}")

        except Exception as e:
            log_lines.append(f"  [{i+1}/{len(urls)}]  {url}\n     ошибка: {e}")

    log_out  = "\n\n".join(log_lines)
    post_out = ""
    visible  = False

    if make_post_flag and last_video:
        progress(0.95, desc="Генерирую пост...")
        post_out = _make_post(last_video, wishes)
        visible  = True

    return log_out, gr.update(value=post_out, visible=visible)

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
# CSS
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

::selection { background: #C1DBE8; color: #43302E; }

/* === Gradio internals === */
:root, .gradio-container {
    --color-orange-500:                  #C1DBE8 !important;
    --color-orange-600:                  #9dc4d8 !important;
    --primary-50:   #FFF1B5 !important;
    --primary-100:  #C1DBE8 !important;
    --primary-200:  #C1DBE8 !important;
    --primary-300:  #9dc4d8 !important;
    --primary-400:  #7aaac8 !important;
    --primary-500:  #43302E !important;
    --primary-600:  #362420 !important;
    --primary-700:  #2a1a18 !important;
    --primary-800:  #1e1210 !important;
    --primary-900:  #120a08 !important;
    --primary-950:  #080402 !important;
    --body-background-fill:              #43302E !important;
    --background-fill-primary:           #43302E !important;
    --background-fill-secondary:         #362420 !important;
    --block-background-fill:             #43302E !important;
    --block-border-color:                #4e3430 !important;
    --block-label-background-fill:       transparent !important;
    --block-label-border-color:          transparent !important;
    --block-label-text-color:            #c9a898 !important;
    --block-title-text-color:            #c9a898 !important;
    --panel-background-fill:             #43302E !important;
    --panel-border-color:                #4e3430 !important;
    --border-color-primary:              #5a3e3a !important;
    --border-color-accent:               #C1DBE8 !important;
    --input-background-fill:             #362420 !important;
    --input-border-color:                #5a3e3a !important;
    --checkbox-background-color:         #362420 !important;
    --checkbox-background-color-selected:#C1DBE8 !important;
    --checkbox-border-color:             #c9a898 !important;
    --checkbox-border-color-selected:    #C1DBE8 !important;
    --button-primary-background-fill:    #C1DBE8 !important;
    --button-primary-text-color:         #43302E !important;
    --button-secondary-background-fill:  transparent !important;
    --button-secondary-text-color:       #c9a898 !important;
    --button-secondary-border-color:     #5a3e3a !important;
    --color-accent:                      #C1DBE8 !important;
    --neutral-50:   #FFF1B5 !important;
    --neutral-100:  #e8d890 !important;
    --neutral-200:  #c9a898 !important;
    --neutral-300:  #a07868 !important;
    --neutral-400:  #7a5048 !important;
    --neutral-500:  #5a3e3a !important;
    --neutral-600:  #4e3430 !important;
    --neutral-700:  #43302E !important;
    --neutral-800:  #362420 !important;
    --neutral-900:  #2a1a18 !important;
    --neutral-950:  #1e1210 !important;
}

* { box-sizing: border-box; }

body, .gradio-container {
    font-family: 'Inter', sans-serif !important;
    background: #43302E !important;
}
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 2.5rem 5rem !important;
}

.gr-box, .gr-form, .gr-panel { box-shadow: none !important; }

/* ХЭДЕР */
.app-header {
    margin-bottom: 2rem; padding-bottom: 1.25rem;
    border-bottom: 1px solid #4e3430;
    display: flex; align-items: baseline; gap: 1rem;
}
.app-header h1 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem; font-weight: 600; color: #FFF1B5;
    letter-spacing: -.02em; margin: 0;
}
.app-header h1 span { color: #C1DBE8; }
.app-header p { font-size: .8rem; color: #c9a898; font-family: 'JetBrains Mono', monospace; margin: 0; }

/* ТАБЫ */
.tab-nav { border-bottom: 1px solid #4e3430 !important; background: transparent !important; gap: 0 !important; }
.tab-nav button {
    font-family: 'JetBrains Mono', monospace !important; font-size: .85rem !important;
    color: #c9a898 !important; border: none !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important; padding: .65rem 1.5rem !important;
    border-radius: 0 !important; transition: all .15s !important; font-weight: 400 !important;
}
.tab-nav button.selected { color: #FFF1B5 !important; border-bottom: 2px solid #C1DBE8 !important; font-weight: 600 !important; }
.tab-nav button:hover:not(.selected) { color: #FFF1B5 !important; }

/* ПОЛЯ ВВОДА */
textarea, input[type="text"] {
    background: #362420 !important; border: 1px solid #5a3e3a !important;
    color: #FFF1B5 !important; border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important; font-size: 1rem !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #C1DBE8 !important; outline: none !important;
    box-shadow: 0 0 0 3px rgba(193,219,232,.15) !important;
}
textarea::placeholder, input::placeholder { color: #c9a898 !important; }

/* ЛЕЙБЛЫ — все одинаковые */
label span, .block label span, label > span,
.gr-form label span, fieldset legend,
.block > label > span, .block-label span,
span.svelte-1gfkn6j, p.svelte-1gfkn6j,
.block-label, .block-label p, .block-label span {
    font-size: .72rem !important; font-weight: 600 !important; color: #c9a898 !important;
    letter-spacing: .08em !important; text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* КНОПКИ PRIMARY */
button.primary, button[class*="primary"] {
    background: #C1DBE8 !important; color: #43302E !important; border: none !important;
    border-radius: 6px !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: .88rem !important; font-weight: 700 !important;
    padding: .65rem 1.5rem !important; transition: all .15s !important;
}
button.primary:hover, button[class*="primary"]:hover { background: #9dc4d8 !important; color: #43302E !important; }

/* КНОПКИ SECONDARY */
button.secondary, button[class*="secondary"] {
    background: transparent !important; color: #c9a898 !important;
    border: 1px solid #5a3e3a !important; border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: .88rem !important;
}
button.secondary:hover, button[class*="secondary"]:hover { border-color: #C1DBE8 !important; color: #FFF1B5 !important; }

/* БЛОК ПОСТА — полутон коричневого как фильтр */
.md-out {
    background: #4e3430 !important; border: 1px solid #5a3e3a !important;
    border-radius: 6px !important; padding: 1.5rem 1.75rem !important;
    color: #FFF1B5 !important; font-size: 1rem !important; line-height: 1.9 !important;
    min-height: 140px;
}
.md-out h3 { color: #FFF1B5 !important; font-weight: 700 !important; font-size: 1.1rem !important; margin-bottom: .6rem !important; }
.md-out p { color: #FFF1B5 !important; }
.md-out a  { color: #C1DBE8 !important; text-decoration: underline !important; }
.md-out blockquote { border-left: 3px solid #C1DBE8; padding-left: .75rem; color: #c9a898 !important; }
.md-out strong { color: #FFF1B5 !important; }
.md-out em { color: #C1DBE8 !important; }

/* ЛОГ — полутон коричневого как фильтр */
.log-out {
    background: #4e3430 !important; border: 1px solid #5a3e3a !important;
    border-radius: 6px !important; padding: 1.25rem 1.5rem !important;
    color: #FFF1B5 !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: .88rem !important; line-height: 1.8 !important; min-height: 140px;
}

/* ПОЖЕЛАНИЯ */
.wishes-box textarea { border-color: #5a3e3a !important; color: #FFF1B5 !important; min-height: 52px !important; }
.wishes-box textarea::placeholder { color: #c9a898 !important; font-style: italic !important; }
.wishes-box textarea:focus { border-color: #C1DBE8 !important; }

/* ЧЕКБОКС */
input[type="checkbox"] {
    appearance: none !important; -webkit-appearance: none !important;
    width: 16px !important; height: 16px !important;
    border: 2px solid #c9a898 !important; border-radius: 3px !important;
    background: #362420 !important; cursor: pointer !important;
    position: relative !important; flex-shrink: 0 !important;
}
input[type="checkbox"]:checked { background: #C1DBE8 !important; border-color: #C1DBE8 !important; }
input[type="checkbox"]:checked::after {
    content: '' !important; position: absolute !important;
    left: 3px !important; top: 0px !important;
    width: 5px !important; height: 9px !important;
    border: 2px solid #43302E !important;
    border-top: none !important; border-left: none !important;
    transform: rotate(45deg) !important; display: block !important;
}

/* РАДИО */
input[type="radio"] {
    appearance: none !important; -webkit-appearance: none !important;
    width: 16px !important; height: 16px !important;
    border: 2px solid #c9a898 !important; border-radius: 50% !important;
    background: #362420 !important; cursor: pointer !important; flex-shrink: 0 !important;
}
input[type="radio"]:checked {
    border-color: #C1DBE8 !important; background: #C1DBE8 !important;
    box-shadow: inset 0 0 0 3px #362420 !important;
}

/* RADIO-BOX — точно как select */
.radio-box, .radio-box > div, .radio-box > div > div {
    background: #4e3430 !important;
    border-radius: 6px !important; border: 1px solid #5a3e3a !important;
    box-shadow: none !important; overflow: hidden !important;
    width: 100% !important; max-width: 100% !important; min-width: 0 !important;
}
.radio-box label, .radio-box span {
    background: transparent !important; border: none !important; box-shadow: none !important;
    white-space: normal !important; word-break: break-word !important;
    width: 100% !important; color: #FFF1B5 !important;
    font-size: .9rem !important; font-family: 'Inter', sans-serif !important;
}
.gr-radio label { padding: .4rem .6rem !important; font-size: .9rem !important; color: #FFF1B5 !important; }
.gr-radio input:checked + label { color: #C1DBE8 !important; font-weight: 600 !important; }
div[data-testid="radio-group"], div[data-testid="radio-group"] > div {
    background: transparent !important; border: none !important; box-shadow: none !important;
}

/* SELECT */
select {
    background: #362420 !important; border: 1px solid #5a3e3a !important;
    color: #FFF1B5 !important; border-radius: 6px !important;
    font-size: .9rem !important; padding: .4rem .6rem !important;
}
select option { background: #43302E !important; color: #FFF1B5 !important; }
select:focus { outline: none !important; border-color: #C1DBE8 !important; }

/* ДРОПДАУН GRADIO */
ul[role="listbox"], ul[role="listbox"] li,
div[role="listbox"], div[role="option"],
.dropdown, .dropdown > div,
div[class*="dropdown"], div[class*="listbox"],
.gr-dropdown, .gr-dropdown ul, .gr-dropdown li {
    background: #43302E !important; background-color: #43302E !important;
    color: #FFF1B5 !important; border-color: #5a3e3a !important;
}
ul[role="listbox"] li:hover, div[role="option"]:hover { background: #5a3e3a !important; color: #FFF1B5 !important; }
ul[role="listbox"] li[aria-selected="true"], div[role="option"][aria-selected="true"] {
    background: #4e3430 !important; color: #C1DBE8 !important;
}

/* ПРОГРЕСС */
.generating { background: transparent !important; border: none !important; }
.progress-bar { background: #362420 !important; border-radius: 3px !important; height: 6px !important; }
.progress-bar > div { background: #C1DBE8 !important; border-radius: 3px !important; }
.generating span { color: #FFF1B5 !important; font-size: .8rem !important; }
.eta-bar { display: none !important; }
progress::-webkit-progress-bar  { background: #362420 !important; border-radius: 3px !important; }
progress::-webkit-progress-value { background: #C1DBE8 !important; border-radius: 3px !important; }
progress::-moz-progress-bar { background: #C1DBE8 !important; }
"""


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

                        wishes_tab1 = gr.Textbox(
                            label="пожелания к посту",
                            placeholder="например: экспертный тон, для школьников, без эмодзи...",
                            lines=2,
                            elem_classes="wishes-box",
                        )

                        make_post_cb = gr.Checkbox(
                            label="сгенерировать пост сразу после загрузки",
                            value=True,
                        )

                        with gr.Row():
                            load_btn  = gr.Button("▶  скачать и обработать", variant="primary")
                            clear_btn = gr.Button("очистить", variant="secondary")

                    # правая колонка — лог
                    with gr.Column(scale=2):
                        load_log = gr.Markdown(elem_classes="log-out", value="", label="лог")

                # пост под двумя колонками — на всю ширину
                post_out_tab1 = gr.Markdown(
                    elem_classes="md-out", visible=False, value="", label="готовый пост",
                )

                def _on_load(urls, wishes, flag, progress=gr.Progress()):
                    log, post_update = process_urls(urls, wishes, flag, progress)
                    return log, post_update

                load_btn.click(
                    fn=_on_load,
                    inputs=[urls_input, wishes_tab1, make_post_cb],
                    outputs=[load_log, post_out_tab1],
                )
                clear_btn.click(
                    fn=lambda: ("", "", gr.update(value="", visible=False)),
                    outputs=[urls_input, load_log, post_out_tab1],
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

if __name__ == "__main__":
    init_db(DB_PATH)
    app = build_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=False,
        css=CSS,
    )
