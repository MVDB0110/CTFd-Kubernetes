import flask
import collections
import CTFd
import sys
import datetime

from .code import models
from .code import routes
from .code import kubernetes

def load(app):
    # Create database tables
    app.db.create_all()
    # Register challenge type
    CTFd.plugins.challenges.CHALLENGE_CLASSES["container"] = models.ContainerChallengeType
    # Register plugin assets
    CTFd.plugins.register_plugin_assets_directory(app, base_path="/plugins/container_challenges/assets/")
    # Initialize Python Kubernetes SDK
    initialization = kubernetes.initialize()
    if initialization["status"] == False:
        error_prefix = "[ERROR] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
        error_suffix = "\n"
        sys.stderr.write(error_prefix + initialization["result"] + error_suffix)
        sys.exit(1)
    # Add pages to frontend
    Menu = collections.namedtuple("Menu", ["title", "route"])
    app.admin_plugin_menu_bar.append(Menu(title="CC Namespaces", route="/admin/container_challenges/namespaces"))
    app.admin_plugin_menu_bar.append(Menu(title="CC Configuration", route="/admin/container_challenges/configuration"))
    # Initialize Flask blueprint
    container_challenges = flask.Blueprint("container_challenges", __name__, template_folder="templates", static_folder="assets")
    # Initialize routes
    routes.load(container_challenges)
    # Register Flask blueprint
    app.register_blueprint(container_challenges)