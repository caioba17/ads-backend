from flask import Flask
from app.config import Config
from app.utils.db_file import db
from flask_cors import CORS
from flask_jwt_extended import JWTManager


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_object(Config)
    jwt = JWTManager(app)
    db.init_app(app)

    # Registrar rotas
    from app.routes.usuario_routes import usuario_routes
    from app.routes.treino_routes import treino_routes
    from app.routes.exercicios_routes import exercicios_routes
    from app.routes.perfil_routes import perfil_routes
    
    app.register_blueprint(treino_routes)
    app.register_blueprint(usuario_routes)
    app.register_blueprint(exercicios_routes)
    app.register_blueprint(perfil_routes)

    with app.app_context():
        db.create_all()

    return app

