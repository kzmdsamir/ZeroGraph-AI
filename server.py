"""
ZeroGraph AI — KZSAMIR Workstation Pro Server
Flask Web Server hosting the 100% air-gapped operational audit engine & single-page application.
Developer: kzsamir
"""

import logging
import os
from flask import Flask, render_template, send_from_directory

from config import Config
from database.connection import close_all
from database.migrate import migrate

# Import API blueprints
from api.analysis import analysis_bp
from api.evidence import evidence_bp
from api.findings import findings_bp
from api.actions import actions_bp
from api.risks import risks_bp, system_bp
from api.export import export_bp, settings_bp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# Register Blueprints
app.register_blueprint(analysis_bp)
app.register_blueprint(evidence_bp)
app.register_blueprint(findings_bp)
app.register_blueprint(actions_bp)
app.register_blueprint(risks_bp)
app.register_blueprint(system_bp)
app.register_blueprint(export_bp)
app.register_blueprint(settings_bp)


@app.route("/")
def index():
    """Render Single Page Application shell."""
    return render_template("index.html")


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Clean up thread-local DB connections."""
    close_all()


def init_app():
    """Ensure database schema and migrations are initialized on startup."""
    logger.info("Initializing ZeroGraph AI Server...")
    if not os.path.exists(Config.ZEROGRAPH_DB_PATH):
        logger.info("Database not found. Executing migration from knowledge_graph.db...")
        migrate()


if __name__ == "__main__":
    init_app()
    logger.info("🚀 Starting ZeroGraph AI Server on http://%s:%s", Config.HOST, Config.PORT)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
