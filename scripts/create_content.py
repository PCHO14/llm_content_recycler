from llm_content_recylcer.const import PATH_TO_DB, MODEL_NAME, CREATE_TEXT_PROMT
from llm_content_recylcer.llm_module import init_model, create_content
from llm_content_recylcer.utils import get_row_by_index

if __name__ == "__main__":
    row_index = 0
    video_data = get_row_by_index(PATH_TO_DB, row_index)
    model, model_chat = init_model(MODEL_NAME, CREATE_TEXT_PROMT)

    print(create_content(
        model,
        model_chat,
        video_data.url,
        video_data.title,
        video_data.transcription,
        video_data.tag
    ))
