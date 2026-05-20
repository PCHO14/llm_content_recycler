from rutube_transcriber.database import init_db

from llm_content_recylcer.css import CSS
from llm_content_recylcer.web_gui import DB_PATH, build_app


if __name__ == "__main__":
    init_db(DB_PATH)
    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=True,
        css=CSS
    )
