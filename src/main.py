import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# ✅ Agora os models não têm mais db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.tools import tools_bp  # Certifique-se que tools_bp está definido em tools.py
from src.routes.assignments import assignments_bp
from src.routes.transfers import transfers_bp
from src.routes.returns import returns_bp
from src.routes.reports import reports_bp

# -------------------------
# 🔧 Configuração da aplicação Flask
# -------------------------
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'

# Enable CORS for all routes
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

# -------------------------
# 🔧 Registro das rotas
# -------------------------
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tools_bp, url_prefix='/api/tools')
app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
app.register_blueprint(transfers_bp, url_prefix='/api/transfers')
app.register_blueprint(returns_bp, url_prefix='/api/returns')
app.register_blueprint(reports_bp, url_prefix='/api/reports')

# -------------------------
# 🔧 Rotas para servir frontend (Vercel ou build local)
# -------------------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    # ✅ Flask roda no Render sem problema
    app.run(host='0.0.0.0', port=5000, debug=True)