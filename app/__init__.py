from flask import Flask

def creer_application():
    application = Flask(__name__)
    application.config.from_object("config.Config")

    from app.routes import main
    application.register_blueprint(main)

    return application