import lmstudio as lms
from lmstudio import LLM, Chat
from src.const import INIT_PROMT, MODEL_NAME, PATH_TO_DB, LLM_API
import re

from src.utils import read_db


def get_tag(llm_model: LLM, chat: Chat, text: str) -> str:
    chat.add_user_message(text)
    result = llm_model.respond(chat)
    result_cleaned = re.sub(r'.*?</think>\n\n', '', str(result), flags=re.DOTALL)
    return result_cleaned


def init_model(model_name: str) -> tuple[LLM, Chat]:
    client = lms.Client(api_host=LLM_API)
    llm_model = client.llm.model(model_name)
    chat = lms.Chat()
    chat.add_user_message(INIT_PROMT)
    llm_model.respond(chat)

    return llm_model, chat


if __name__ == '__main__':
    model, model_chat = init_model(MODEL_NAME)
    text_for_analyze = read_db(PATH_TO_DB)
    print(get_tag(model, model_chat, text_for_analyze))
