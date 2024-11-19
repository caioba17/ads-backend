import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave_secreta'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:GOHsTtNTFUpXUfdZTmQYzZxZgyixWVGc@junction.proxy.rlwy.net:50339/railway'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'chave'
