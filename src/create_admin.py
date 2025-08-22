
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.models.user import db, User
from flask import Flask

# Ajuste o nome do arquivo do banco de dados conforme necessário
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'app.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Defina aqui o usuário e senha do admin
ADMIN_USERNAME = 'RafaelPinho'
ADMIN_PASSWORD = '@21314100'

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username=ADMIN_USERNAME).first():
        admin = User(username=ADMIN_USERNAME, role='admin')
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f'Usuário admin criado: {ADMIN_USERNAME} / {ADMIN_PASSWORD}')
    else:
        print('Usuário admin já existe.')
