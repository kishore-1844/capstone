"""Development entry point. Run with: python run.py"""

from datetime import date

from flask import Flask

from backend.database import init_db
from backend.routes import main
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    init_db(app.config["DATABASE_PATH"])
    app.register_blueprint(main)

    @app.context_processor
    def template_context():
        today = date.today()
        return {"now_label": today.strftime("%b %d, %Y"),
                "today_label": today.strftime("%A, %B %d, %Y"),
                "today": today.isoformat()}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
