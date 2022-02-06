from kubernetes import client, config, watch
from os import path
from pathlib import Path
import sys


def create_namespace(api_instance, namespace):
    try:
        namespace = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=namespace))
        api_instance.create_namespace(namespace)
        return_object = {
            "status": True,
            "code": 201,
            "items": {
                "namespace": namespace
            }
        }
        return return_object

    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e),
            "detail": namespace
        }
        return return_object


def create_docker_secret(api_instance, encoded_secret, namespace):
    data = {}
    data[".dockerconfigjson"] = encoded_secret
    secret = client.V1Secret(metadata=client.V1ObjectMeta(
        name="private-registry"), type="kubernetes.io/dockerconfigjson", data=data)
    try:
        api_instance.create_namespaced_secret(namespace=namespace, body=secret)
    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e),
            "detail": secret
        }
        return return_object
    try:
        service_accounts = api_instance.list_namespaced_service_account(
            namespace)
        service_account = ""
        for i in range(0, len(service_accounts.items)):
            if service_accounts.items[i].metadata.name == "default":
                service_account = service_accounts.items[i]
        service_account.image_pull_secrets = [
            client.V1ObjectReference(name=secret.metadata.name)]
        updated_service_account = api_instance.patch_namespaced_service_account(
            name=service_account.metadata.name, namespace=namespace, body=service_account)
        return_object = {
            "status": True,
            "code": 201,
            "items": {
                "secret": secret,
                "service_account": updated_service_account
            }
        }
        return return_object
    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e)
        }
        return return_object


def create_job_object(job_name, compose, compose_file, image, san):
    # Create environment for container
    env_list = []
    env_list.append(client.V1EnvVar(name="ENCODED", value=compose))
    env_list.append(client.V1EnvVar(name="FILE", value=compose_file))

    # Create and configure a container section
    container = client.V1Container(
        name=job_name,
        image=image,
        env=env_list)

    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(),
        spec=client.V1PodSpec(service_account_name=san, restart_policy="Never", containers=[container]))

    # Create the specification of deployment
    spec = client.V1JobSpec(
        template=template,
        backoff_limit=3)

    # Instantiate the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name),
        spec=spec)

    return job


def create_rbac(api_client, core_v1, rbac_v1, namespace):
    service_account = client.V1ServiceAccount()
    service_account.metadata = client.V1ObjectMeta(
        generate_name="deploy"
    )

    try:
        api_response = core_v1.create_namespaced_service_account(
            namespace, service_account)
        service_account = api_client.sanitize_for_serialization(api_response)
    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e),
            "detail": service_account
        }
        return return_object

    rules = [
        client.V1PolicyRule([""], resources=["pods", "services", "deployments", "secrets"], verbs=[
                            "get", "list", "create", "delete", "deletecollection", "update", "watch", "patch"], ),
        client.V1PolicyRule(["apps"], resources=["deployments"],
                            verbs=["get", "list", "create", "delete", "deletecollection", "update", "watch", "patch"], ),
        client.V1PolicyRule(["networking.k8s.io"], resources=["networkpolicies"], 
                            verbs=["get", "list", "create", "delete", "deletecollection", "update", "watch", "patch"], )
    ]
    role = client.V1Role(rules=rules)
    role.metadata = client.V1ObjectMeta(namespace=namespace,
                                        generate_name="deploy")
    try:
        # Create role in namespace of player
        api_response = rbac_v1.create_namespaced_role(namespace, role)
        role = api_client.sanitize_for_serialization(api_response)
    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e),
            "detail": role
        }
        return return_object

    role_binding = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(namespace=namespace,
                                     generate_name="deploy"),
        subjects=[client.V1Subject(
            name=service_account['metadata']['name'], kind="ServiceAccount", api_group="")],
        role_ref=client.V1RoleRef(kind="Role", api_group="rbac.authorization.k8s.io",
                                  name=role['metadata']['name']))
    try:
        # Create rolebinding in namespace of player with deployment job
        api_response = rbac_v1.create_namespaced_role_binding(namespace=namespace,
                                                              body=role_binding)
        role_binding = api_client.sanitize_for_serialization(api_response)
    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e),
            "detail": role_binding
        }
        return return_object

    return_object = {
        "status": True,
        "code": 201,
        "items": {
            "role": role,
            "service_account": service_account,
            "role_binding": role_binding
        }
    }
    return return_object


def create_job(api_instance, job, namespace):
    try:
        # Create Job
        api_instance.create_namespaced_job(
            body=job,
            namespace=namespace)

        # Watch Job until it succeeds
        w = watch.Watch()
        for event in w.stream(func=api_instance.list_namespaced_job, namespace=namespace):
            o = event['object']
            if o.status.succeeded:
                w.stop()
                return_object = {
                    "status": True,
                    "code": 201,
                    "items": {
                        "job": job
                    }
                }
                return return_object
            if o.status.failed:
                w.stop()
                return_object = {
                    "status": False,
                    "message": "Cannot fulfill job description.",
                    "detail": job
                }
                return return_object

    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e),
            "detail": job
        }
        return return_object


def delete_all(api_instance, namespace):
    try:
        # Delete namespace which will delete everything related to the namespace and the namespace itself.
        api_instance.delete_namespace(namespace)
        return_object = {
            "status": True,
            "code": 204,
        }
        return return_object

    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e)
        }
        return return_object


def list_nodes(api_client, api_instance):
    try:
        api_response = api_instance.list_node(pretty=True)
        nodes = api_client.sanitize_for_serialization(api_response)
        return_object = {
            "status": True,
            "code": 200,
            "items": {
                "nodes": nodes
            }
        }
        return return_object

    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e),
        }
        return return_object


def list_services(api_client, api_instance, namespace):
    try:
        api_response = api_instance.list_namespaced_service(
            namespace, pretty=True)
        services = api_client.sanitize_for_serialization(api_response)
        return_object = {
            "status": True,
            "code": 200,
            "items": {
                "services": services
            }
        }
        return return_object

    except Exception as e:
        return_object = {
            "status": False,
            "message": str(e),
        }
        return return_object
