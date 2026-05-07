import argparse

from rutube_transcriber.database import init_db

from llm_content_recylcer.const import PATH_TO_DB, MODEL_NAME, INIT_PROMT
from llm_content_recylcer.download_and_analyze_content import download_and_analyze_content
from llm_content_recylcer.llm_module import init_model

if __name__ == '__main__':
    description = 'Загрузка и анализ видео с Rutube с помощью модуля rutube-transcriber'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        'video_url', type=str, help='Ссылка на видео Rutube'
    )
    args = parser.parse_args()

    init_db(PATH_TO_DB)
    model, model_chat = init_model(MODEL_NAME, INIT_PROMT)

    download_and_analyze_content(args.video_url, PATH_TO_DB, model, model_chat)
