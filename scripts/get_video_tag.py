from llm_content_recylcer.const import PATH_TO_DB, MODEL_NAME, INIT_PROMT
from llm_content_recylcer.llm_module import get_tag, init_model
from llm_content_recylcer.utils import read_db

if __name__ == '__main__':
    model, model_chat = init_model(MODEL_NAME, INIT_PROMT)
    text_for_analyze = read_db(PATH_TO_DB)
    print(get_tag(model, model_chat, text_for_analyze))
