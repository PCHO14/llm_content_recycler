import lmstudio as lms
from lmstudio import LLM, Chat
from llm_content_recylcer.const import LLM_API
import re


def get_tag(llm_model: LLM, chat: Chat, text: str) -> str:
    chat.add_user_message(text)
    result = llm_model.respond(chat)
    result_cleaned = re.sub(r'.*?</think>\n\n', '', str(result), flags=re.DOTALL)
    return result_cleaned


def init_model(model_name: str, init_promt: str) -> tuple[LLM, Chat]:
    client = lms.Client(api_host=LLM_API)
    llm_model = client.llm.model(model_name)
    chat = lms.Chat()
    chat.add_user_message(init_promt)
    llm_model.respond(chat)

    return llm_model, chat


def create_content(
    llm_model,
    chat,
    url: str,
    title: str,
    transcription: str,
    tag: str
) -> str:
    llm_request = (
        f'- url: {url} '
        f'- title: {title} '
        f'- transcription: {transcription} '
        f'- tag: {tag}'
    )
    chat.add_user_message(llm_request)
    result = llm_model.respond(chat)
    result_cleaned = re.sub(r'.*?</think>\n\n', '', str(result), flags=re.DOTALL)
    return result_cleaned
