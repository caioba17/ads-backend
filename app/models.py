from app.utils.db_file import db

treino_exercicio = db.Table('treino_exercicio',
    db.Column('treino_id', db.Integer, db.ForeignKey('treino.id'), primary_key=True),
    db.Column('exercicio_id', db.Integer, db.ForeignKey('exercicios.id'), primary_key=True),
    db.Column('series', db.Integer),
    db.Column('repeticoes', db.Integer),
     db.Column('peso', db.Float)
)

usuario_treino = db.Table('usuario_treino',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('treino_id', db.Integer, db.ForeignKey('treino.id'), primary_key=True)
)

class Treino(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    intensidade = db.Column(db.String(50), nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    privacidade = db.Column(db.String(20), default='privado')
    exercicios = db.relationship('Exercicio', secondary=treino_exercicio, lazy='subquery',
                                 backref=db.backref('treinos', lazy=True))
    
    usuario = db.relationship('Usuario', backref='treinos')

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False) 
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    genero = db.Column(db.String(50))
    idade = db.Column(db.Integer)
    objetivo = db.Column(db.String(100))
    tipo_corpo = db.Column(db.String(50))
    meta_corpo = db.Column(db.String(100))
    motivacoes = db.Column(db.String(500))
    areas_alvo = db.Column(db.String(500))
    nivel_condicionamento = db.Column(db.String(50))
    local_treinamento = db.Column(db.String(100))
    altura = db.Column(db.Float)
    peso = db.Column(db.Float)
    meta_peso = db.Column(db.Float)

    favoritos = db.relationship('Treino', secondary=usuario_treino, lazy='subquery', backref=db.backref('favoritados_por', lazy=True))

class Exercicio(db.Model):
    __tablename__ = 'exercicios' 
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    categoria = db.Column(db.String(50))
    descricao = db.Column(db.String(500))
    equipamento = db.Column(db.String(100))
    dificuldade = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'equipamento': self.equipamento,
            'dificuldade': self.dificuldade
        }
    
class TreinoFinalizado(db.Model):
    __tablename__ = 'treinos_finalizados'
    id = db.Column(db.Integer, primary_key=True)
    treino_id = db.Column(db.Integer, db.ForeignKey('treino.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_finalizacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    total_time = db.Column(db.Integer)
    
    treino = db.relationship('Treino', backref=db.backref('finalizados', lazy=True))
    usuario = db.relationship('Usuario', backref=db.backref('finalizados', lazy=True))

    def __repr__(self):
        return f'<TreinoFinalizado {self.id}>'
    
class ExercicioTempo(db.Model):
    __tablename__ = 'exercicios_tempo'
    
    id = db.Column(db.Integer, primary_key=True)
    treino_finalizado_id = db.Column(db.Integer, db.ForeignKey('treinos_finalizados.id'), nullable=False)
    exercicio_id = db.Column(db.Integer, db.ForeignKey('exercicios.id'), nullable=False)
    tempo = db.Column(db.Integer)  # Tempo em segundos
    data_inicio = db.Column(db.DateTime, default=db.func.current_timestamp())
    data_fim = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    treino_finalizado = db.relationship('TreinoFinalizado', backref=db.backref('exercicios_tempo', lazy=True))
    exercicio = db.relationship('Exercicio', backref=db.backref('tempos', lazy=True))

    def __repr__(self):
        return f'<ExercicioTempo {self.id}, TreinoFinalizado {self.treino_finalizado_id}, Exercicio {self.exercicio_id}>'

    


    
