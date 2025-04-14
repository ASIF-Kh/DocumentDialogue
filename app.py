import os
import logging
from flask import Flask
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
import markdown
# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
# Create the Flask app
app = Flask(__name__)
migrate = Migrate(app, db)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    if text:
        return Markup(text.replace('\n', '<br>'))
    
# Register 'markdown' as a custom Jinja2 filter
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text)



# Add datetime functions to templates
@app.context_processor
def utility_processor():
    from datetime import datetime
    return {
        'now': datetime.now
    }

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///docuchat.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Initialize the database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Import models and create database tables
with app.app_context():
    from models import User, Document, ChatSession  # noqa: F401
    db.create_all()

# Import and register blueprints
from routes.auth import auth_bp
from routes.document import document_bp
from routes.chat import chat_bp

app.register_blueprint(auth_bp)
app.register_blueprint(document_bp)
app.register_blueprint(chat_bp)

# Load user for login manager
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Root route
@app.route('/')
def index():
    from flask import render_template
    return render_template('index.html')
