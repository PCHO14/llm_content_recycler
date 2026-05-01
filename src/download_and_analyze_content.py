import argparse
from pathlib import Path
from rutube_transcriber.database import init_db, is_exists, save
from rutube_transcriber.downloader import download_audio
from rutube_transcriber.transcriber import transcribe
from src.llm_module import init_model, get_tag
from src.const import PATH_TO_DB, MODEL_NAME
from lmstudio import LLM, Chat


def download_and_analyze_content(
    video_url: str, db_path: Path, llm_model: LLM, llm_chat: Chat
) -> None:
    video = download_audio(video_url)

    if is_exists(video.video_id, db_path):
        return

    text = transcribe(video.audio_path)
    video_tag = get_tag(llm_model, llm_chat, text)

    save(
        db_path,
        video_id=video.video_id,
        url=video.url,
        title=video.title,
        transcription=text,
        tag=video_tag,
    )


if __name__ == '__main__':
    description = 'Загрузка и анализ видео с Rutube с помощью модуля rutube-transcriber'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        'video_url', type=str, required=True, help='Ссылка на видео Rutube'
    )
    args = parser.parse_args()

    init_db(PATH_TO_DB)
    model, model_chat = init_model(MODEL_NAME)

    download_and_analyze_content(args.video_url, PATH_TO_DB, model, model_chat)
