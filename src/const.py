from textwrap import dedent
from pathlib import Path

MODEL_NAME = 'qwen3-4b-thinking-2507'

PATH_TO_DB = Path(__file__).parent.parent / 'files' / 'transcriptions.db'

LLM_API = "localhost:1234"

INIT_PROMT = dedent(
    """\
    Представь, что ты классификатор. Тебе необходимо проанализировать текст и определить тематику, 
    к которой он относится. В качестве ответа ты должен выдать 1 слово или 1 словосочетание, которое четко определяет
    тематику текста. Здесь важна именно сфера к которой относится текст: физика, математика, космос, литература и т.д
    """
)
