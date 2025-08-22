from src.models.tool import db, ToolInstance
from src.main import app

with app.app_context():
    recusadas = ToolInstance.query.filter_by(status='Recusada').all()
    if not recusadas:
        print('Nenhuma ferramenta com status Recusada.')
    else:
        for ti in recusadas:
            print(f"Ferramenta: {ti.tool.name if ti.tool else 'N/A'}, Quantidade: {ti.quantity}")
