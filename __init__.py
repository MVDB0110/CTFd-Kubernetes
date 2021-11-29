from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.plugins import register_plugin_assets_directory
from flask.templating import render_template
from kubernetes import client, config
from flask import Blueprint, request, url_for, send_file, jsonify, abort
from CTFd.utils.decorators import admins_only
import os
import time
import base64
from .models import KubernetesChallenge, KubernetesChallengeType, KubernetesConfig
from .functions import create_namespace, create_job_object, create_job, delete_all, list_nodes, list_services, create_rbac, create_docker_secret
from collections import namedtuple
import json


# Init Kubernetes Python SDK
try:
    config.load_incluster_config()
except config.ConfigException:
    try:
        config.load_kube_config()
    except config.ConfigException:
        raise Exception("Could not configure kubernetes python client")

core_v1 = client.CoreV1Api()
batch_v1 = client.BatchV1Api()
api_client = client.ApiClient()
rbac_v1 = client.RbacAuthorizationV1Api()
prefix = "ctf-user-"
retry_attempts = 3

Menu = namedtuple("Menu", ["title", "route"])


def load(app):
    app.db.create_all()
    kubernetes = Blueprint('kubernetes', __name__,
                           template_folder='templates', static_folder='assets')

    config_list = [
        {
            "name": "Namespaces",
            "route": "/admin/kubernetes/namespaces"
        },
        {
            "name": "Cluster",
            "route": "/admin/kubernetes/config"
        }
    ]

    for item in config_list:
        config = Menu(title=item['name'], route=item['route'])
        app.admin_plugin_menu_bar.append(config)
        
    config = KubernetesConfig.query.order_by(
            KubernetesConfig.id.desc()).first()

    if config is None:
        q = KubernetesConfig(
                image='ghcr.io/mvdb0110/ctfd-kubernetes-container:master', secret='eyJhdXRocyI6IHt9fQ==')
        app.db.session.add(q)
        app.db.session.commit()

    @kubernetes.route("/admin/kubernetes/config", methods=["POST", "GET"])
    @admins_only
    def kubernetes_config():
        if request.method == "POST":
            q = KubernetesConfig(
                image=request.form['image'], secret=request.form['secret'])
            app.db.session.add(q)
            app.db.session.commit()
        config = KubernetesConfig.query.order_by(
            KubernetesConfig.id.desc()).first()
        return render_template("plugin-config.html", config=config)

    @kubernetes.route("/admin/kubernetes/namespaces", methods=["POST", "GET"])
    @admins_only
    def kubernetes_namespaces():
        response = core_v1.list_namespace()
        namespaces = response.items
        return render_template("namespaces.html", namespaces=namespaces)

    @kubernetes.route("/kubernetes/deploy/namespace", methods=["POST"])
    def deploy_namespace():
        # Get data
        data = request.form or request.get_json()

        # Configuration values
        namespace = prefix + str(data['user_id']) + '-' + str(data['challenge_id'])


       # Create namespace
        retries = retry_attempts
        while retries > 0:
            creation_namespace = create_namespace(core_v1, namespace)
            if creation_namespace['status'] is True:
                break
            else:
                delete_all(core_v1, namespace)
                time.sleep(30)
                retries -= 1
                continue
        if creation_namespace['status'] is True:
            return jsonify({"status": creation_namespace['status']}), 201
        else:
            return api_client.sanitize_for_serialization(creation_namespace), 409


    @kubernetes.route("/kubernetes/deploy/rbac", methods=["POST"])
    def deploy_rbac():
        # Get data
        data = request.form or request.get_json()
        config = KubernetesConfig.query.order_by(
            KubernetesConfig.id.desc()).first()

        # Configuration values
        namespace = prefix + str(data['user_id']) + '-' + str(data['challenge_id'])


        retries = retry_attempts
        while retries > 0:
            role_creation = create_rbac(
                api_client, core_v1, rbac_v1, namespace)
            docker_secret_creation = create_docker_secret(
                core_v1, config.secret, namespace)
            if role_creation['status'] is True and docker_secret_creation['status'] is True:
                break
            else:
                time.sleep(30)
                retries -= 1
                continue

        if role_creation['status'] is True and docker_secret_creation['status'] is True:
            return jsonify({"role_name": role_creation['items']['service_account']['metadata']['name']}), 201
        else:
            return {"role": api_client.sanitize_for_serialization(role_creation), "secret": api_client.sanitize_for_serialization(docker_secret_creation)}, 409

    @kubernetes.route("/kubernetes/deploy/job", methods=["POST"])
    def deploy_job():
        # Get data
        data = request.form or request.get_json()
        config = KubernetesConfig.query.order_by(
            KubernetesConfig.id.desc()).first()

        # Configuration values
        challenge_id = str(data['challenge_id'])
        role_name = str(data['role_name'])
        namespace = prefix + str(data['user_id']) + '-' + str(data['challenge_id'])
        challenge_name = app.db.session.query(
            KubernetesChallenge.name).filter_by(id=challenge_id).scalar()
        challenge_name = challenge_name.lower()
        compose = app.db.session.query(
            KubernetesChallenge.compose).filter_by(id=challenge_id).scalar()
        job_name = str(challenge_name).replace(" ", "-")
        compose_file = str(job_name) + ".yml"

        retries = retry_attempts
        while retries > 0:
            completion_job = create_job(batch_v1, create_job_object(
                job_name, compose, compose_file, config.image, role_name), namespace)
            if completion_job['status'] is True:
                break
            else:
                time.sleep(30)
                retries -= 1
                continue
        
        if completion_job['status'] is True:
            return jsonify({"status": completion_job['status']}), 201
        else:
            return api_client.sanitize_for_serialization(completion_job), 409

    @kubernetes.route("/kubernetes/deploy/info", methods=["POST"])
    def deploy_info():
        # Get data
        data = request.form or request.get_json()

        # Configuration values
        namespace = prefix + str(data['user_id']) + '-' + str(data['challenge_id'])


        # Get all services
        retries = retry_attempts
        while retries > 0:
            api_response = list_services(
                api_client, core_v1, namespace)
            if api_response['status'] is True:
                break
            else:
                time.sleep(30)
                retries -= 1
                continue

        info = {}
        if api_response['status'] is True:
            info['services'] = []
            # Append Name, ClusterIP and Ports from services in namespace
            for service in api_response['items']['services']['items']:
                info['services'].append({"name": service['metadata']['name'],
                                            "clusterIP": service['spec']['clusterIP'], "ports": service['spec']['ports']})
        else:
            info['services'] = api_response

        # Get all cluster nodes
        retries = retry_attempts
        while retries > 0:
            api_response = list_nodes(api_client, core_v1)
            if api_response['status'] is True:
                break
            else:
                time.sleep(30)
                retries -= 1
                continue

        if api_response['status'] is True:
            info['nodes'] = []
            # Append Name and addresses of nodes
            for node in api_response['items']['nodes']['items']:
                info['nodes'].append(
                    {"name": node['metadata']['name'], "addresses": node['status']['addresses']})
        else:
            info['nodes'] = api_response

        return jsonify(info)

    @kubernetes.route("/kubernetes/destroy", methods=["POST"])
    def undeploy():
        # Get data
        data = request.form or request.get_json()

        # Configuration values
        namespace = prefix + str(data['user_id']) + '-' + str(data['challenge_id'])

        retries = retry_attempts
        while retries > 0:
            deletion = delete_all(core_v1, namespace)
            if deletion['status'] is True:
                break
            else:
                time.sleep(30)
                retries -= 1
                continue

        return jsonify(deletion)

    CHALLENGE_CLASSES["kubedefault"] = KubernetesChallengeType
    register_plugin_assets_directory(
        app, base_path="/plugins/kubernetes/assets/")
    app.register_blueprint(kubernetes)
