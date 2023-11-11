from flask import Blueprint

blueprint = Blueprint("health", __name__)

@blueprint.route("/public/health")
def status():
    return "<p>🤖 Server Running...</p>"
