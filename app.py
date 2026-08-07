from flask import Flask, render_template
from models.models import init_db

# Import semua Blueprint rute
from routes.scraping_routes import scraping_bp
from routes.history_routes import history_bp
from routes.export_routes import export_bp
from routes.extraction_routes import extraction_bp
from routes.chat_routes import chat_bp
app = Flask(__name__)

# Inisialisasi Database
init_db()

# Daftarkan Blueprint ke Flask
app.register_blueprint(scraping_bp)
app.register_blueprint(history_bp)
app.register_blueprint(export_bp)
app.register_blueprint(extraction_bp)
app.register_blueprint(chat_bp)

# Rute untuk merender halaman antarmuka utama (HTML)
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)