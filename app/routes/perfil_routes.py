from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Usuario

perfil_routes = Blueprint('perfil_routes', __name__)

@perfil_routes.route('/perfil', methods=['GET'])
@jwt_required() 
def perfil_usuario():
    usuario_id = get_jwt_identity()  
    print(f"ID do usuário do token: {usuario_id}")
    usuario = Usuario.query.get(usuario_id)  

    if not usuario:
        print(f"Usuário não encontrado no banco de dados para o ID: {usuario_id}")  
        return jsonify({'mensagem': 'Usuário não encontrado!'}), 404

    return jsonify({
        'nome': usuario.nome,
        'email': usuario.email,
        'genero': usuario.genero,
        'idade': usuario.idade,
        'objetivo': usuario.objetivo,
        'tipo_corpo': usuario.tipo_corpo,
        'meta_corpo': usuario.meta_corpo,
        'motivacoes': usuario.motivacoes,
        'areas_alvo': usuario.areas_alvo,
        'nivel_condicionamento': usuario.nivel_condicionamento,
        'local_treinamento': usuario.local_treinamento,
        'altura': usuario.altura,
        'peso': usuario.peso,
        'meta_peso': usuario.meta_peso
        
    }), 200