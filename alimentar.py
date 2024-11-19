from flask import Flask
from app.utils.db_file import db
from app.models import Exercicio
import requests
from datetime import datetime

app = Flask(__name__)

# Configure the app with the database URI (adjust for your DB)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:GOHsTtNTFUpXUfdZTmQYzZxZgyixWVGc@junction.proxy.rlwy.net:50339/railway'  # Ajuste conforme seu banco de dados
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the db instance with the app
db.init_app(app)


@app.route('/alimentar_exercicios')
def alimentar_exercicios():
    # Requisição para a API ExerciseDB
    url = "https://exercisedb.p.rapidapi.com/exercises"
    querystring = {"limit":"0","offset":"0"}
    headers = {
        'x-rapidapi-key': "dc4eadccaamsh989ba4fab96604dp11faf9jsn8a092f9da256",
        'x-rapidapi-host': "exercisedb.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        exercises = response.json()
        
        # Itera sobre os exercícios e insere no banco de dados
        for ex_data in exercises:
            exercicio = Exercicio(
                nome=ex_data['name'],
                tipo=ex_data.get('bodyPart'),  # Adaptação do campo para "tipo"
                categoria=ex_data.get('target'),  # Alvo do exercício como "categoria"
                descricao=ex_data.get('gifUrl'),  # Pode ser modificado se houver descrição
                equipamento=ex_data.get('equipment'),
                dificuldade="N/A"  # Defina a dificuldade se disponível, ou use um valor padrão
            )
            db.session.add(exercicio)
        
        db.session.commit()
        return "exercícios inseridos com sucesso!"
    else:
        return f"Erro ao acessar a API: {response.status_code}"


@app.route('/atualizar_exercicios')
def atualizar_exercicios():
    # Requisição para a API ExerciseDB
    url = "https://exercisedb.p.rapidapi.com/exercises"
    querystring = {"limit":"0","offset":"0"}
    headers = {
        'x-rapidapi-key': "dc4eadccaamsh989ba4fab96604dp11faf9jsn8a092f9da256",
        'x-rapidapi-host': "exercisedb.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        exercises = response.json()

        # Atualizar os exercícios no banco de dados
        for ex_data in exercises:
            exercicio = Exercicio.query.filter_by(nome=ex_data['name']).first()  # Encontre o exercício pelo nome
            if exercicio:
                exercicio.descricao = ex_data.get('gifUrl')  # Atualize o gifUrl
                db.session.commit()

        return "Exercícios atualizados com sucesso!"
    else:
        return f"Erro ao acessar a API: {response.status_code}"
        



# Apenas uma execução do Flask (fora das rotas)
if __name__ == "__main__":
    app.run(debug=True)


