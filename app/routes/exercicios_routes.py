from flask import Blueprint, request, jsonify
from app.models import Exercicio  
from app.utils.db_file import db

exercicios_routes = Blueprint('exercicios_routes', __name__)

@exercicios_routes.route('/exercicios', methods=['GET'])
def get_exercicios():
    tipo = request.args.get('tipo') 
    
    if tipo:
        exercicios = Exercicio.query.filter_by(tipo=tipo).all()
    
    return jsonify([exercicio.to_dict() for exercicio in exercicios])