import kubernetes
import base64

def initialize():
    # Try to initialize kubernetes SDK
    try:
        kubernetes.config.load_incluster_config()
    except kubernetes.config.ConfigException:
        try:
            kubernetes.config.load_kube_config()
        except kubernetes.config.ConfigException:
            return {
                "status": False,
                "result": "cannot initialize Python Kubernetes SDK!"
            }
    # Return final result
    return {
        "status": True,
        "result": None
    }

def create_namespace(namespace_name):
    # Try to create namespace
    try:
        namespace = kubernetes.client.V1Namespace(metadata=kubernetes.client.V1ObjectMeta(name=namespace_name))
        kubernetes.client.CoreV1Api().create_namespace(namespace)
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Return final result
    return {
        "status": True,
        "result": None
    }

def create_rbac(namespace_name):
    # Temporary values
    service_account = kubernetes.client.V1ServiceAccount()
    service_account.metadata = kubernetes.client.V1ObjectMeta(generate_name="deploy")
    # Try to create service account in namespace
    try:
        service_account = kubernetes.client.CoreV1Api().create_namespaced_service_account(namespace_name, service_account)
        service_account = kubernetes.client.ApiClient().sanitize_for_serialization(service_account)
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Create rules
    rules = [
        kubernetes.client.V1PolicyRule([""],
            resources=["pods", "services", "deployments", "secrets"],
            verbs=["get", "list", "create", "delete", "deletecollection", "update", "watch", "patch"]),
        kubernetes.client.V1PolicyRule(["apps"],
            resources=["deployments"],
            verbs=["get", "list", "create", "delete", "deletecollection", "update", "watch", "patch"]),
        client.V1PolicyRule(["networking.k8s.io"], 
            resources=["networkpolicies"], 
            verbs=["get", "list", "create", "delete", "deletecollection", "update", "watch", "patch"])
    ]
    # Create role
    role = kubernetes.client.V1Role(rules=rules)
    role.metadata = kubernetes.client.V1ObjectMeta(namespace=namespace_name, generate_name="deploy")
    # Try to create role in namespace
    try:
        role = kubernetes.client.RbacAuthorizationV1Api().create_namespaced_role(namespace_name, role)
        role = kubernetes.client.ApiClient().sanitize_for_serialization(role)
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Create role binding
    role_binding = kubernetes.client.V1RoleBinding(
        metadata=kubernetes.client.V1ObjectMeta(namespace=namespace_name, generate_name="deploy"),
        subjects=[kubernetes.client.V1Subject(name=service_account["metadata"]["name"], kind="ServiceAccount", api_group="")],
        role_ref=kubernetes.client.V1RoleRef(kind="Role", api_group="rbac.authorization.k8s.io", name=role["metadata"]["name"]))
    # Try to create role binding in namespace
    try:
        role_binding = kubernetes.client.RbacAuthorizationV1Api().create_namespaced_role_binding(namespace=namespace_name, body=role_binding)
        role_binding = kubernetes.client.ApiClient().sanitize_for_serialization(role_binding)
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Return final result
    return {
        "status": True,
        "result": {
            "role": role,
            "service_account": service_account,
            "role_binding": role_binding
        }
    }

def create_secret(url, username, password, namespace_name):
    # Compose secret
    raw_auth = username + ":" + password
    enc_auth = base64.b64encode(raw_auth.encode("ascii")).decode("ascii")
    raw_secret = "{\"auths\": {\"%s\": {\"username\": \"%s\", \"password\": \"%s\", \"email\": \"\", \"auth\": \"%s\"}}}" % (url, username, password, enc_auth)
    enc_secret = base64.b64encode(raw_secret.encode("ascii")).decode("ascii")
    # Create secret
    secret_data = {}
    secret_data[".dockerconfigjson"] = enc_secret
    secret = kubernetes.client.V1Secret(
        metadata=kubernetes.client.V1ObjectMeta(name="private-registry"),
        type="kubernetes.io/dockerconfigjson",
        data=secret_data)
    # Try to create secret in namespace
    try:
        kubernetes.client.CoreV1Api().create_namespaced_secret(namespace=namespace_name, body=secret)
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Try to patch service account in namespace
    try:
        service_accounts = kubernetes.client.CoreV1Api().list_namespaced_service_account(namespace_name)
        service_account = ""
        for i in range(0, len(service_accounts.items)):
            if service_accounts.items[i].metadata.name == "default":
                service_account = service_accounts.items[i]
        service_account.image_pull_secrets = [kubernetes.client.V1ObjectReference(name=secret.metadata.name)]
        kubernetes.client.CoreV1Api().patch_namespaced_service_account(
            name=service_account.metadata.name,
            namespace=namespace_name,
            body=service_account)
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Return final result
    return {
        "status": True,
        "result": None
    }

def create_job_object(image, job_name, compose_text, role_name):
    # Create container
    env_list = []
    env_list.append(kubernetes.client.V1EnvVar(name="ENCODED", value=base64.b64encode(compose_text.encode("ascii")).decode("ascii")))
    env_list.append(kubernetes.client.V1EnvVar(name="FILE", value=str(job_name + ".yml")))
    container = kubernetes.client.V1Container(name=job_name, image=image, env=env_list)
    # Create job spec
    spec_template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(),
        spec=kubernetes.client.V1PodSpec(service_account_name=role_name, restart_policy="Never", containers=[container]))
    spec = kubernetes.client.V1JobSpec(template=spec_template, backoff_limit=3)
    # Create job object
    job_object = kubernetes.client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=kubernetes.client.V1ObjectMeta(name=job_name),
        spec=spec)
    # Return final result
    return job_object

def create_job(job, namespace_name):
    # Try to create job in namespace
    try:
        kubernetes.client.BatchV1Api().create_namespaced_job(body=job, namespace=namespace_name)
        watch = kubernetes.watch.Watch()
        for event in watch.stream(func=kubernetes.client.BatchV1Api().list_namespaced_job, namespace=namespace_name):
            o = event["object"]
            if o.status.succeeded:
                watch.stop()
                return {
                    "status": True,
                    "result": None
                }
            elif o.status.failed:
                watch.stop()
                return {
                    "status": False,
                    "result": "cannot fulfill job description while trying to create Kubernetes job!"
                }
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }

def list_namespaces():
    # Try to list namespaces
    try:
        namespaces = kubernetes.client.CoreV1Api().list_namespace()
        namespaces = namespaces.items
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Return final result
    return {
        "status": True,
        "result": namespaces
    }

def list_nodes():
    # Try to list nodes
    try:
        nodes = kubernetes.client.CoreV1Api().list_node(pretty=True)
        nodes = kubernetes.client.ApiClient().sanitize_for_serialization(nodes)
    except Exception as e:
         return {
            "status": False,
            "result": str(e)
        }
    # Return final result
    return {
        "status": True,
        "result": nodes
    }

def list_services(namespace_name):
    # Try to list services
    try:
        services = kubernetes.client.CoreV1Api().list_namespaced_service(namespace_name, pretty=True)
        services = kubernetes.client.ApiClient().sanitize_for_serialization(services)
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Return final result
    return {
        "status": True,
        "result": services
    }

def list_pods(namespace_name):
    # Try to list pods
    try:
        pods = kubernetes.client.CoreV1Api().list_namespaced_pod(namespace_name, pretty=True)
        pods = kubernetes.client.ApiClient().sanitize_for_serialization(pods)
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Return final result
    return {
        "status": True,
        "result": pods
    }

def delete_namespace(namespace_name):
    # Try to delete namespace
    try:
        kubernetes.client.CoreV1Api().delete_namespace(namespace_name)
    except Exception as e:
        return {
            "status": False,
            "result": str(e)
        }
    # Return final result
    return {
        "status": True,
        "result": None
    }