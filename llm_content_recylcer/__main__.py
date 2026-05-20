import argparse

from rutube_transcriber.database import init_db

from llm_content_recylcer.css import CSS
from llm_content_recylcer.web_gui import DB_PATH, build_app


def main(model_name: str) -> None:
    init_db(DB_PATH)
    app = build_app(model_name)
    app.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=True,
        css=CSS
    )


if __name__ == "__main__":
    description = 'Генерация контента на осовнове видео'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        'model_name',
        type=str,
        help='Название модели из LM Studio',
    )
    args = parser.parse_args()
    main(args.model_name)
