from flask import Blueprint, request, jsonify
from app.models import Usuario, Treino
from app.utils.db_file import db
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity

usuario_routes = Blueprint('usuario_routes', __name__)
bcrypt = Bcrypt()

@usuario_routes.route('/cadastro', methods=['POST'])
def cadastro_usuario():
    data = request.get_json()
    
    usuario_existente = Usuario.query.filter_by(email=data['email']).first()
    if usuario_existente:
        return jsonify({'mensagem': 'Usuário já existe!'}), 400

    senha_hash = bcrypt.generate_password_hash(data['senha']).decode('utf-8')

    novo_usuario = Usuario(
        nome=data['nome'],
        email=data['email'],
        senha=senha_hash
    )
    db.session.add(novo_usuario)
    db.session.commit()

    return jsonify({'mensagem': 'Usuário criado com sucesso!'}), 201

@usuario_routes.route('/login', methods=['POST'])
def login_usuario():
    data = request.get_json()
    usuario = Usuario.query.filter_by(email=data['email']).first()

    if not usuario or not bcrypt.check_password_hash(usuario.senha, data['senha']):
        return jsonify({'mensagem': 'E-mail ou senha inválidos!'}), 401

    access_token = create_access_token(identity=usuario.id)
    
    print("Token gerado:", access_token)

    return jsonify({
        'mensagem': 'Login bem-sucedido!',
        'token': access_token 
    }), 200

@usuario_routes.route('/atualizar-perfil', methods=['POST'])
@jwt_required()
def atualizar_perfil():
    current_user = get_jwt_identity() 
    usuario = Usuario.query.filter_by(id=current_user).first()

    if not usuario:
        return jsonify({"error": "Usuário não encontrado"}), 404

    data = request.get_json()

    usuario.genero = data.get('genero', usuario.genero)
    usuario.idade = data.get('idade', usuario.idade)
    usuario.objetivo = data.get('objetivo', usuario.objetivo)
    usuario.tipo_corpo = data.get('tipo_corpo', usuario.tipo_corpo)
    usuario.meta_corpo = data.get('meta_corpo', usuario.meta_corpo)
    usuario.motivacoes = data.get('motivacoes', usuario.motivacoes)
    usuario.areas_alvo = data.get('areas_alvo', usuario.areas_alvo)
    usuario.nivel_condicionamento = data.get('nivel_condicionamento', usuario.nivel_condicionamento)
    usuario.local_treinamento = data.get('local_treinamento', usuario.local_treinamento)
    usuario.altura = data.get('altura', usuario.altura)
    usuario.peso = data.get('peso', usuario.peso)
    usuario.meta_peso = data.get('meta_peso', usuario.meta_peso)

    db.session.commit()

    return jsonify({"message": "Perfil atualizado com sucesso!"}), 200

@usuario_routes.route('/validar/<int:treino_id>', methods=['POST'])
@jwt_required()
def validar_usuario(treino_id):
    usuario_id = get_jwt_identity()

    treino = Treino.query.get(treino_id)
    if treino is None:
        return jsonify({'error': 'Treino não encontrado'}), 404
    
    if treino.usuario_id != usuario_id:
        return jsonify({'error': 'Você não tem permissão para editar este treino'}), 403
    else:
        return jsonify({'mensagem': 'Acesso autorizado para editar treino!'}), 200
    



