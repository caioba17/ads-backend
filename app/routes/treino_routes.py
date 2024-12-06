from flask import Blueprint, request, jsonify
from app.models import Treino, Exercicio, Usuario, TreinoFinalizado, treino_exercicio, ExercicioTempo
from app.utils.db_file import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import update

treino_routes = Blueprint('treino_routes', __name__)

@treino_routes.route('/treinos', methods=['GET'])
def listar_treinos():
    privacidade = request.args.get('privacidade', 'publico')
    treinos = Treino.query.filter_by(privacidade=privacidade).all();
    return jsonify([{'id': t.id, 'nome': t.nome, 'descricao': t.descricao, 'intensidade': t.intensidade} for t in treinos])

@treino_routes.route('/treino', methods=['POST'])
@jwt_required()
def criar_treino():
    usuario_atual = get_jwt_identity()
    data = request.get_json()

    nome = data.get('nome')
    descricao = data.get('descricao')
    intensidade = data.get('intensidade')
    privacidade = data.get('privacidade', 'privado')
    exercicios_data = data.get('exercicios')  # Exemplo: [{'id': 1, 'series': 3, 'repeticoes': 12}, ...]

    if not exercicios_data or not isinstance(exercicios_data, list):
        return jsonify({'error': 'Dados de exercícios inválidos ou não fornecidos'}), 400

    exercicios_ids = [ex['id'] for ex in exercicios_data]
    exercicios = Exercicio.query.filter(Exercicio.id.in_(exercicios_ids)).all()

    if not exercicios or len(exercicios) != len(exercicios_ids):
        return jsonify({'error': 'Um ou mais exercícios não foram encontrados'}), 404

    # Criação do treino
    novo_treino = Treino(nome=nome, descricao=descricao, intensidade=intensidade, privacidade=privacidade, usuario_id=usuario_atual)
    db.session.add(novo_treino)
    db.session.commit()  # Commit para gerar o ID do treino

    # Adiciona os exercícios com séries e repetições à tabela associativa
    for ex_data in exercicios_data:
        ex_id = ex_data['id']
        series = ex_data.get('series', 0)
        repeticoes = ex_data.get('repeticoes', 0)
        peso = ex_data.get('peso', 0)
        db.session.execute(
            treino_exercicio.insert().values(
                treino_id=novo_treino.id,  # O ID agora é garantido
                exercicio_id=ex_id,
                series=series,
                repeticoes=repeticoes,
                peso=peso
            )
        )

    db.session.commit()  # Commit final para salvar a associação

    usuario = Usuario.query.get(usuario_atual)
    
    if novo_treino not in usuario.favoritos:
        usuario.favoritos.append(novo_treino)
        db.session.commit()
    return jsonify({'mensagem': 'Treino criado com sucesso!'}), 201


@treino_routes.route('/treinos/pesquisa', methods=['GET'])
def pesquisar_treinos():
    query = request.args.get('query', '')

    treinos = Treino.query.filter(
        ((Treino.nome.ilike(f'%{query}%')) | 
        (Treino.descricao.ilike(f'%{query}%'))) &
        (Treino.privacidade == 'publico')
    ).all()

    return jsonify([{'id': t.id, 'nome': t.nome, 'descricao': t.descricao, 'intensidade': t.intensidade} for t in treinos])

@treino_routes.route('/treinos/intensidade', methods=['GET'])
def get_treino_intensidade():
    intensidade = request.args.get('intensidade') 
    
    if intensidade:
        treinos = Treino.query.filter_by(intensidade=intensidade, privacidade='publico').all()
    else:
        treinos = Treino.query.filter_by(privacidade='publico').all()

    if not treinos:
        return jsonify({'message': 'Nenhum treino encontrado com essa intensidade e privacidade pública.'}), 404
    
    treinos_data = [{
        'id': treino.id,
        'nome': treino.nome,
        'descricao': treino.descricao,
        'intensidade': treino.intensidade,
    } for treino in treinos]

    return jsonify({'treinos': treinos_data}), 200
    
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
        Exercicio.equipamento,
        treino_exercicio.c.peso
    ).join(Exercicio, Exercicio.id == treino_exercicio.c.exercicio_id) \
     .filter(treino_exercicio.c.treino_id == treino_id)

    exercicios_data = [
        {
            'id': ex[0],
            'nome': ex[3],  # Nome do exercício
            'descricao': ex[4],  # Descrição do exercício
            'categoria': ex[5],  # Categoria do exercício
            'equipamento': ex[6],  # Equipamento do exercício
            'series': ex[1],  # Séries do exercício
            'repeticoes': ex[2],  # Repetições do exercício
            'peso': ex[7] #Peso do exercício
        }
        for ex in treino_exercicios
    ]

    return jsonify({
        'id': treino.id,
        'nome': treino.nome,
        'descricao': treino.descricao,
        'intensidade': treino.intensidade,
        'dataCriacao': treino.data_criacao,
        'privacidade': treino.privacidade,
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
    exercicios_tempos = data['exercicios_tempos']
    
    treino = Treino.query.get(treino_id)
    usuario = Usuario.query.get(usuario_id)
    
    if not treino:
        return jsonify({'error': 'Treino não encontrado'}), 404
    if not usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    treino_finalizado = TreinoFinalizado(treino_id=treino.id, usuario_id=usuario.id, total_time=total_time)
    db.session.add(treino_finalizado)
    db.session.commit()

    for item in exercicios_tempos:
        exercicio_tempo = ExercicioTempo(
            treino_finalizado_id = treino_finalizado.id,
            exercicio_id = item['exercicio_id'],
            tempo = item['tempo']
        )

        db.session.add(exercicio_tempo)

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
    
    response = []
    for tf in treinos_finalizados:
        treino_data = {
            'id': tf.id,
            'treino_id': tf.treino.id,
            'nome': tf.treino.nome,
            'descricao': tf.treino.descricao,
            'data_finalizacao': tf.data_finalizacao,
            'total_time': tf.total_time,
            'exercicios': []  # Lista de exercícios para este treino
        }

        # Buscar os tempos dos exercícios para o treino finalizado
        exercicios_tempos = db.session.query(ExercicioTempo).filter_by(treino_finalizado_id=tf.id).all()
        
        for et in exercicios_tempos:
            treino_data['exercicios'].append({
                'nome': et.exercicio.nome,
                'tempo': et.tempo  # Tempo do exercício em segundos
            })
        
        response.append(treino_data)
    
    return jsonify(response), 200


@treino_routes.route('/treinos/frequencia', methods=['GET'])
@jwt_required() 
def contar_frequencia_treinos():
    usuario_id = get_jwt_identity() 
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    treinos_finalizados = TreinoFinalizado.query.filter_by(usuario_id=usuario.id).all()
    
    # Estrutura para armazenar os dados agrupados por mês
    frequencia_por_mes = {}

    for tf in treinos_finalizados:
        data_finalizacao = tf.data_finalizacao
        if data_finalizacao:
            if isinstance(data_finalizacao, datetime):
                data = data_finalizacao
            else:
                try:
                    data = datetime.strptime(data_finalizacao, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    print(f"Erro ao converter data: {data_finalizacao}")
                    continue
            
            mes = data.strftime('%Y-%m')  # Exemplo: '2024-12'
            dia = data.day
            
            if mes not in frequencia_por_mes:
                frequencia_por_mes[mes] = {
                    '1-7': 0,
                    '8-15': 0,
                    '16-23': 0,
                    '24-31': 0
                }
            
            if 1 <= dia <= 7:
                frequencia_por_mes[mes]['1-7'] += 1
            elif 8 <= dia <= 15:
                frequencia_por_mes[mes]['8-15'] += 1
            elif 16 <= dia <= 23:
                frequencia_por_mes[mes]['16-23'] += 1
            elif 24 <= dia <= 31:
                frequencia_por_mes[mes]['24-31'] += 1

    # Formatação dos dados para o frontend
    dados_formatados = [
        {'mes': mes, 'frequencia': [{'label': intervalo, 'valor': contagem} for intervalo, contagem in intervalos.items()]}
        for mes, intervalos in frequencia_por_mes.items()
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
    treino.privacidade = data.get('privacidade', treino.privacidade)

    # Atualiza os exercícios associados (adicionar/atualizar/remover)
    exercicios_data = data.get('exercicios')  # Exemplo: [{'id': 1, 'series': 4, 'repeticoes': 10}, ...]
    if exercicios_data:
        if not isinstance(exercicios_data, list):
            return jsonify({'error': 'Dados de exercícios inválidos ou não fornecidos'}), 400

        # IDs dos exercícios recebidos na requisição
        novos_exercicios_ids = [ex['id'] for ex in exercicios_data if 'id' in ex]

        # IDs dos exercícios atualmente associados ao treino
        exercicios_associados = db.session.query(treino_exercicio.c.exercicio_id).filter_by(treino_id=treino.id).all()
        exercicios_associados_ids = [ex[0] for ex in exercicios_associados]

        # Exercícios a remover
        exercicios_a_remover = set(exercicios_associados_ids) - set(novos_exercicios_ids)
        if exercicios_a_remover:
            db.session.execute(
                treino_exercicio.delete().where(
                    treino_exercicio.c.treino_id == treino.id,
                    treino_exercicio.c.exercicio_id.in_(exercicios_a_remover)
                )
            )

        # Adicionar ou atualizar os exercícios fornecidos
        for ex_data in exercicios_data:
            ex_id = ex_data.get('id')
            series = ex_data.get('series', 0)
            repeticoes = ex_data.get('repeticoes', 0)
            peso = ex_data.get('peso', 0)

            if ex_id:
                # Atualiza ou cria a associação
                stmt = (
                    update(treino_exercicio)
                    .where(treino_exercicio.c.treino_id == treino.id)
                    .where(treino_exercicio.c.exercicio_id == ex_id)
                    .values(series=series, repeticoes=repeticoes, peso=peso)
                )
                result = db.session.execute(stmt)

                if result.rowcount == 0:
                    db.session.execute(
                        treino_exercicio.insert().values(
                            treino_id=treino.id,
                            exercicio_id=ex_id,
                            series=series,
                            repeticoes=repeticoes,
                            peso=peso
                        )
                    )

    # Commit final para salvar as alterações do treino
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f"Erro ao salvar o treino: {str(e)}"}), 500

    return jsonify({'mensagem': 'Treino atualizado com sucesso!'}), 200



