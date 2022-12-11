import flask
import CTFd
import sys
import datetime
import time

from . import models
from . import kubernetes

def load(container_challenges):
    # Constants
    NAMESPACE_FORMAT = "chal-user-{chal}-{user}"
    # Initialize configuration route
    @container_challenges.route("/admin/container_challenges/configuration", methods=["POST", "GET"])
    @CTFd.utils.decorators.admins_only
    def configuration():
        if flask.request.method == "GET":
            # get current configuration
            config_data = flask.current_app.db.session.query(models.ContainerChallengeConfiguration)
            # Return final result
            return flask.templating.render_template("configuration.html", configs=config_data.all())
        if flask.request.method == "POST":
            # Temporary values
            username = flask.request.form["username"]
            password = flask.request.form["password"]
            url = flask.request.form["url"]
            image = flask.request.form["image"]
            # Create new configuration
            config = models.ContainerChallengeConfiguration(image=image, url=url ,username=username, password=password)
            # Add new configuration
            flask.current_app.db.session.query(models.ContainerChallengeConfiguration).delete()
            flask.current_app.db.session.add(config)
            flask.current_app.db.session.commit()
            # get current configuration
            config_data = flask.current_app.db.session.query(models.ContainerChallengeConfiguration)
            # Return final result
            return flask.templating.render_template("configuration.html", configs=config_data.all())
    # Initialize namespaces route
    @container_challenges.route("/admin/container_challenges/namespaces", methods=["GET"])
    @CTFd.utils.decorators.admins_only
    def namespaces():
        # Try to list namespaces
        namespace_listing = kubernetes.list_namespaces()
        if namespace_listing["status"] == False:
            error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
            error_suffix = "\n"
            sys.stdout.write(error_prefix + namespace_listing["result"] + error_suffix)
            return flask.templating.render_template("namespaces.html", namespaces=[])
        # Return final result
        return flask.templating.render_template("namespaces.html", namespaces=namespace_listing["result"])
    # Initialize namespace route
    @container_challenges.route("/container_challenges/namespace", methods=["GET", "POST", "DELETE"])
    def namespace():
        if flask.request.method == "GET":
            # Temporary values
            challenge_id = flask.request.args.get("challenge_id")
            user_id = flask.request.args.get("user_id")
            namespace_name = NAMESPACE_FORMAT.format(chal=challenge_id, user=user_id)
            # Try to list namespaces
            namespace_listing = kubernetes.list_namespaces()
            if namespace_listing["status"] == False:
                error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
                error_suffix = "\n"
                sys.stdout.write(error_prefix + namespace_listing["result"] + error_suffix)
                return "{}", 409
            # Try to find namespace
            for namespace in namespace_listing["result"]:
                if namespace.metadata.name == namespace_name:
                    return flask.jsonify(found="true"), 200
            # Return final result
            return flask.jsonify(found="false"), 200        
        if flask.request.method == "POST":
            # Temporary values
            challenge_id = flask.request.get_json()["challenge_id"]
            user_id = flask.request.get_json()["user_id"]
            namespace_name = NAMESPACE_FORMAT.format(chal=challenge_id, user=user_id)
            # Try to create namespace
            namespace_creation = kubernetes.create_namespace(namespace_name)
            if namespace_creation["status"] == False:
                error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
                error_suffix = "\n"
                sys.stdout.write(error_prefix + namespace_creation["result"] + error_suffix)
                return "{}", 409
            # Return final result
            return "{}", 200
        if flask.request.method == "DELETE":
            # Temporary values
            challenge_id = flask.request.get_json()["challenge_id"]
            user_id = flask.request.get_json()["user_id"]
            namespace_name = NAMESPACE_FORMAT.format(chal=challenge_id, user=user_id)
            current_epoch = int(time.time())
            # Try to list pods
            pod_listing = kubernetes.list_pods(namespace_name)
            if pod_listing["status"] == False:
                error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
                error_suffix = "\n"
                sys.stdout.write(error_prefix + pod_listing["result"] + error_suffix)
                return "{}", 409
            # Extract pod names
            pod_names = ""
            for pod in pod_listing["result"]["items"]:
                pod_names += pod["metadata"]["name"]
                pod_names += ","
            pod_names = pod_names[:-1]
            # Retrieve log
            statistics = flask.current_app.db.session.query(models.ContainerChallengeLog).filter_by(challenge_id=int(challenge_id), user_id=int(user_id)).first()
            # Check if logging
            if statistics:
                # Calculate seconds
                seconds = (current_epoch - statistics.start_epoch)
                # Log stop of challenge
                log_prefix = "[TRACK] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
                log_suffix = "\n"
                sys.stdout.write(log_prefix +
                        "challenge:\"" + challenge_id + "\" --- " +
                        "user:\"" + user_id + "\" --- " +
                        "namespace:\"" + namespace_name + "\" --- " +
                        "pods:\"" + pod_names + "\" --- " +
                        "seconds:\"" + str(seconds) + "\"" +
                        log_suffix)
                # Delete log
                flask.current_app.db.session.query(models.ContainerChallengeLog).filter_by(challenge_id=int(challenge_id), user_id=int(user_id)).delete()
                flask.current_app.db.session.commit()
            # Try to delete namespace
            namespace_deletion = kubernetes.delete_namespace(namespace_name)
            if namespace_deletion["status"] == False:
                error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
                error_suffix = "\n"
                sys.stdout.write(error_prefix + namespace_deletion["result"] + error_suffix)
                return "{}", 409
            # Return final result
            return "{}", 200
    # Initialize rbac route
    @container_challenges.route("/container_challenges/rbac", methods=["POST"])
    def rbac():
        # Validate configuration
        configuration = models.ContainerChallengeConfiguration.query.first()
        if not configuration:
            error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
            error_suffix = "\n"
            sys.stdout.write(error_prefix + "container challenge configuration is empty!" + error_suffix)
            return "{}", 409
        # Temporary values
        challenge_id = flask.request.get_json()["challenge_id"]
        user_id = flask.request.get_json()["user_id"]
        namespace_name = NAMESPACE_FORMAT.format(chal=challenge_id, user=user_id)
        # Try to create role
        role_creation = kubernetes.create_rbac(namespace_name)
        if role_creation["status"] == False:
            error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
            error_suffix = "\n"
            sys.stdout.write(error_prefix + role_creation["result"] + error_suffix)
            return "{}", 409
        # Try to create secret
        secret_creation = kubernetes.create_secret(configuration.url, configuration.username, configuration.password, namespace_name)
        if secret_creation["status"] == False:
            error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
            error_suffix = "\n"
            sys.stdout.write(error_prefix + secret_creation["result"] + error_suffix)
            return "{}", 409
        # Return final result
        return flask.jsonify(role_name=role_creation["result"]["service_account"]["metadata"]["name"]), 200
    # Initialize job route             
    @container_challenges.route("/container_challenges/job", methods=["POST"])
    def job():
        # Validate configuration
        configuration = models.ContainerChallengeConfiguration.query.first()
        if not configuration:
            error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
            error_suffix = "\n"
            sys.stdout.write(error_prefix + "container challenge configuration is empty!" + error_suffix)
            return "{}", 409
        # Temporary values
        challenge_id = flask.request.get_json()["challenge_id"]
        user_id = flask.request.get_json()["user_id"]
        role_name = flask.request.get_json()["role_name"]
        namespace_name = NAMESPACE_FORMAT.format(chal=challenge_id, user=user_id)
        challenge = flask.current_app.db.session.query(models.ContainerChallenge).filter_by(id=int(challenge_id)).one()
        job_name = challenge.name.lower().replace(" ", "-")
        compose_text = challenge.compose
        image = configuration.image
        # Try to create job
        job_object_creation = kubernetes.create_job_object(image, job_name, compose_text, role_name)
        job_creation = kubernetes.create_job(job_object_creation, namespace_name)
        if job_creation["status"] == False:
            error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
            error_suffix = "\n"
            sys.stdout.write(error_prefix + job_creation["result"] + error_suffix)
            return "{}", 409
        # Return final result
        return "{}", 200
    # Initialize info route
    @container_challenges.route("/container_challenges/info", methods=["GET"])
    def info():
        # Temporary values
        result = {}
        challenge_id = flask.request.args.get("challenge_id")
        user_id = flask.request.args.get("user_id")
        namespace_name = NAMESPACE_FORMAT.format(chal=challenge_id, user=user_id)
        current_epoch = int(time.time())
        # Try to list nodes
        node_listing = kubernetes.list_nodes()
        if node_listing["status"] == False:
            error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
            error_suffix = "\n"
            sys.stdout.write(error_prefix + node_listing["result"] + error_suffix)
            return "{}", 409
        # Try to list services
        service_listing = kubernetes.list_services(namespace_name)
        if service_listing["status"] == False:
            error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
            error_suffix = "\n"
            sys.stdout.write(error_prefix + service_listing["result"] + error_suffix)
            return "{}", 409
        # Retrieve log
        statistics = flask.current_app.db.session.query(models.ContainerChallengeLog).filter_by(challenge_id=int(challenge_id), user_id=int(user_id)).first()
        # Check if not logging
        if not statistics:
            # Try to list pods
            pod_listing = kubernetes.list_pods(namespace_name)
            if pod_listing["status"] == False:
                error_prefix = "[WARN] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
                error_suffix = "\n"
                sys.stdout.write(error_prefix + pod_listing["result"] + error_suffix)
                return "{}", 409
            # Extract pod names
            pod_names = ""
            for pod in pod_listing["result"]["items"]:
                pod_names += pod["metadata"]["name"]
                pod_names += ","
            pod_names = pod_names[:-1]
            # Save start time
            statistics = models.ContainerChallengeLog(challenge_id=int(challenge_id), user_id=int(user_id), start_epoch=current_epoch)
            flask.current_app.db.session.add(statistics)
            flask.current_app.db.session.commit()
            # Log start of challenge
            log_prefix = "[TRACK] [" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
            log_suffix = "\n"
            sys.stdout.write(log_prefix +
                            "challenge:\"" + challenge_id + "\" --- " +
                            "user:\"" + user_id + "\" --- " +
                            "namespace:\"" + namespace_name + "\" --- " +
                            "pods:\"" + pod_names + "\" --- " +
                            "seconds:\"0\"" +
                            log_suffix)
        # Determine challenge type
        challenge = flask.current_app.db.session.query(models.ContainerChallenge).filter_by(id=int(challenge_id)).one()
        if challenge.challenge_type == "web":
            # Add hyperlinks to result
            result["hyperlinks"] = []
            for service in service_listing["result"]["items"]:
                for node in node_listing["result"]["items"]:
                    url = node["metadata"]["name"] + ":" + str(service["spec"]["ports"][0]["nodePort"])
                    result["hyperlinks"].append({"name": service["metadata"]["name"], "url": url})
                    break
        else:
            # Add nodes to result
            result["nodes"] = []
            for node in node_listing["result"]["items"]:
                result["nodes"].append({"name": node["metadata"]["name"], "addresses": node["status"]["addresses"]})
            # Add services to result
            result["services"] = []
            for service in service_listing["result"]["items"]:
                result["services"].append({"name": service["metadata"]["name"], "clusterIP": service["spec"]["clusterIP"], "ports": service["spec"]["ports"]})
        # Return final result
        return flask.jsonify(result)