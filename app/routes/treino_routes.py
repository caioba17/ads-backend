from flask import Blueprint, request, jsonify
from app.models import Treino, Exercicio, Usuario, TreinoFinalizado, treino_exercicio
from app.utils.db_file import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

treino_routes = Blueprint('treino_routes', __name__)

@treino_routes.route('/treinos', methods=['GET'])
def listar_treinos():
    treinos = Treino.query.all()
    return jsonify([{'id': t.id, 'nome': t.nome, 'descricao': t.descricao, 'intensidade': t.intensidade} for t in treinos])

@treino_routes.route('/treino', methods=['POST'])
@jwt_required()
def criar_treino():
    usuario_atual = get_jwt_identity()
    data = request.get_json()

    nome = data.get('nome')
    descricao = data.get('descricao')
    intensidade = data.get('intensidade')
    exercicios_data = data.get('exercicios')  # Exemplo: [{'id': 1, 'series': 3, 'repeticoes': 12}, ...]

    if not exercicios_data or not isinstance(exercicios_data, list):
        return jsonify({'error': 'Dados de exercícios inválidos ou não fornecidos'}), 400

    exercicios_ids = [ex['id'] for ex in exercicios_data]
    exercicios = Exercicio.query.filter(Exercicio.id.in_(exercicios_ids)).all()

    if not exercicios or len(exercicios) != len(exercicios_ids):
        return jsonify({'error': 'Um ou mais exercícios não foram encontrados'}), 404

    # Criação do treino
    novo_treino = Treino(nome=nome, descricao=descricao, intensidade=intensidade, usuario_id=usuario_atual)
    db.session.add(novo_treino)
    db.session.commit()  # Commit para gerar o ID do treino

    # Adiciona os exercícios com séries e repetições à tabela associativa
    for ex_data in exercicios_data:
        ex_id = ex_data['id']
        series = ex_data.get('series', 0)
        repeticoes = ex_data.get('repeticoes', 0)
        db.session.execute(
            treino_exercicio.insert().values(
                treino_id=novo_treino.id,  # O ID agora é garantido
                exercicio_id=ex_id,
                series=series,
                repeticoes=repeticoes
            )
        )

    db.session.commit()  # Commit final para salvar a associação
    return jsonify({'mensagem': 'Treino criado com sucesso!'}), 201


@treino_routes.route('/treinos/pesquisa', methods=['GET'])
def pesquisar_treinos():
    query = request.args.get('query', '')

    treinos = Treino.query.filter(
        (Treino.nome.ilike(f'%{query}%')) | 
        (Treino.descricao.ilike(f'%{query}%'))
    ).all()

    return jsonify([{'id': t.id, 'nome': t.nome, 'descricao': t.descricao, 'intensidade': t.intensidade} for t in treinos])

@treino_routes.route('/treinos/<int:treino_id>', methods=['GET'])
def get_treino(treino_id):
    treino = Treino.query.get(treino_id)
    if treino is None:
        return jsonify({'error': 'Treino não encontrado'}), 404

    # Busca os exercícios com as séries e repetições associadas ao treino
    treino_exercicios = db.session.query(
        treino_exercicio.c.exercicio_id,
        treino_exercicio.c.series,
        treino_exercicio.c.repeticoes,
        Exercicio.nome,
        Exercicio.descricao,
        Exercicio.categoria,
        Exercicio.equipamento
    ).join(Exercicio, Exercicio.id == treino_exercicio.c.exercicio_id) \
     .filter(treino_exercicio.c.treino_id == treino_id)

    exercicios_data = [
        {
            'nome': ex[3],  # Nome do exercício
            'descricao': ex[4],  # Descrição do exercício
            'categoria': ex[5],  # Categoria do exercício
            'equipamento': ex[6],  # Equipamento do exercício
            'series': ex[1],  # Séries do exercício
            'repeticoes': ex[2]  # Repetições do exercício
        }
        for ex in treino_exercicios
    ]

    return jsonify({
        'id': treino.id,
        'nome': treino.nome,
        'descricao': treino.descricao,
        'intensidade': treino.intensidade,
        'dataCriacao': treino.data_criacao,
        'exercicios': exercicios_data
    })

@treino_routes.route('/treinos/favoritar', methods=['POST'])
@jwt_required() 
def favoritar_treino():
    data = request.get_json()
    treino_id = data.get('treino_id') 
    
    usuario_id = get_jwt_identity() 
    
    usuario = Usuario.query.get(usuario_id)
    treino = Treino.query.get(treino_id)
    
    if not usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    if not treino:
        return jsonify({'error': 'Treino não encontrado'}), 404
    
    if treino not in usuario.favoritos:
        usuario.favoritos.append(treino)
        db.session.commit()
        return jsonify({'mensagem': 'Treino favoritado com sucesso!'}), 200
    else:
        return jsonify({'mensagem': 'Este treino já está nos favoritos.'}), 200

@treino_routes.route('/treinos/favoritos', methods=['GET'])
@jwt_required()  
def listar_favoritos():
    usuario_id = get_jwt_identity()  
    
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    favoritos = usuario.favoritos
    return jsonify([{'id': t.id, 'nome': t.nome, 'descricao': t.descricao, 'intensidade': t.intensidade} for t in favoritos]), 200

@treino_routes.route('/treinos/desfavoritar', methods=['POST'])
@jwt_required()  
def desfavoritar_treino():
    try:
        data = request.get_json()
        treino_id = data.get('treino_id')  
        usuario_id = get_jwt_identity()  

        usuario = Usuario.query.get(usuario_id)
        treino = Treino.query.get(treino_id)

        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        if not treino:
            return jsonify({'error': 'Treino não encontrado'}), 404

        if treino in usuario.favoritos:
            usuario.favoritos.remove(treino) 
            db.session.commit()
            return jsonify({'mensagem': 'Treino removido dos favoritos com sucesso!'}), 200
        else:
            return jsonify({'mensagem': 'Este treino não está nos favoritos.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
    
@treino_routes.route('/treinos/finalizar', methods=['POST'])
@jwt_required() 
def finalizar_treino():
    data = request.get_json()
    treino_id = data.get('treino_id')  
    usuario_id = get_jwt_identity()
    total_time = data.get('total_time')
    
    treino = Treino.query.get(treino_id)
    usuario = Usuario.query.get(usuario_id)
    
    if not treino:
        return jsonify({'error': 'Treino não encontrado'}), 404
    if not usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    treino_finalizado = TreinoFinalizado(treino_id=treino.id, usuario_id=usuario.id, total_time=total_time)
    db.session.add(treino_finalizado)
    db.session.commit()
    
    return jsonify({'mensagem': 'Treino finalizado com sucesso!'}), 200

@treino_routes.route('/treinos/finalizados', methods=['GET'])
@jwt_required() 
def listar_treinos_finalizados():
    usuario_id = get_jwt_identity()  
    
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    treinos_finalizados = TreinoFinalizado.query.filter_by(usuario_id=usuario.id).all()
    
    return jsonify([{
        'id': tf.id,
        'treino_id': tf.treino.id,
        'nome': tf.treino.nome,
        'descricao': tf.treino.descricao,
        'data_finalizacao': tf.data_finalizacao,
        'total_time': tf.total_time
    } for tf in treinos_finalizados]), 200

@treino_routes.route('/treinos/frequencia', methods=['GET'])
@jwt_required() 
def contar_frequencia_treinos():
    usuario_id = get_jwt_identity() 
    
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    treinos_finalizados = TreinoFinalizado.query.filter_by(usuario_id=usuario.id).all()
    
    intervalos = {
        '1-7': 0,
        '8-15': 0,
        '16-23': 0,
        '24-31': 0
    }

    for tf in treinos_finalizados:
        data_finalizacao = tf.data_finalizacao
        if data_finalizacao:
            if isinstance(data_finalizacao, datetime):
                day = data_finalizacao.day  
            else:
                try:
                    data_finalizacao = datetime.strptime(data_finalizacao, "%Y-%m-%d %H:%M:%S")
                    day = data_finalizacao.day
                except ValueError:
                    print(f"Erro ao converter data: {data_finalizacao}")
                    continue

            if 1 <= day <= 7:
                intervalos['1-7'] += 1
            elif 8 <= day <= 15:
                intervalos['8-15'] += 1
            elif 16 <= day <= 23:
                intervalos['16-23'] += 1
            elif 24 <= day <= 31:
                intervalos['24-31'] += 1

    dados_formatados = [
        {'label': intervalo, 'valor': contagem} 
        for intervalo, contagem in intervalos.items()
    ]

    return jsonify(dados_formatados), 200

@treino_routes.route('/treinos/editar/<int:treino_id>', methods=['PUT'])
@jwt_required()
def alterar_treino(treino_id):
    data = request.get_json()
    usuario_id = get_jwt_identity()
    
    # Verifica se o treino existe
    treino = Treino.query.get(treino_id)
    if treino is None:
        return jsonify({'error': 'Treino não encontrado'}), 404

    # Verifica se o usuário é dono do treino
    if treino.usuario_id != usuario_id:
        return jsonify({'error': 'Acesso negado: você não tem permissão para editar este treino'}), 403

    # Atualiza os dados do treino
    treino.nome = data.get('nome', treino.nome)
    treino.descricao = data.get('descricao', treino.descricao)
    treino.intensidade = data.get('intensidade', treino.intensidade)

    # Atualiza os exercícios associados
    exercicios_data = data.get('exercicios')  # Exemplo: [{'id': 1, 'series': 4, 'repeticoes': 10}, ...]

    if exercicios_data:
        if not isinstance(exercicios_data, list):
            return jsonify({'error': 'Dados de exercícios inválidos ou não fornecidos'}), 400

        # Verifica se todos os itens têm a chave 'id'
        try:
            exercicios_ids = [ex['id'] for ex in exercicios_data if 'id' in ex]
        except KeyError as e:
            return jsonify({'error': f"Erro nos dados do exercício: {str(e)}"}), 400

        # Busca os exercícios no banco
        exercicios = Exercicio.query.filter(Exercicio.id.in_(exercicios_ids)).all()

        if not exercicios or len(exercicios) != len(exercicios_ids):
            return jsonify({'error': 'Um ou mais exercícios não foram encontrados'}), 404

        # Remove associações antigas do treino
        db.session.execute(
            treino_exercicio.delete().where(treino_exercicio.c.treino_id == treino.id)
        )
        
        # Cria novas associações com séries e repetições atualizadas
        for ex_data in exercicios_data:
            ex_id = ex_data.get('id')
            series = ex_data.get('series', 0)
            repeticoes = ex_data.get('repeticoes', 0)
            if ex_id:  # Verifica se o ID é válido antes de continuar
                db.session.execute(
                    treino_exercicio.insert().values(
                        treino_id=treino.id,
                        exercicio_id=ex_id,
                        series=series,
                        repeticoes=repeticoes
                    )
                )


    # Commit final para salvar alterações
    db.session.commit()
    return jsonify({'mensagem': 'Treino atualizado com sucesso!'}), 200