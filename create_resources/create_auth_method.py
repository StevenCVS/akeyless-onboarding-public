from akeyless import (ApiException, CreateAuthMethodAzureAD, CreateAuthMethodUniversalIdentity, UidGenerateToken,
                      GatewayCreateK8SAuthConfig, AuthMethodCreateApiKey, AuthMethodCreateGcp, AuthMethodCreateAwsIam)
from configs.akeyless_config import write_error, AkeylessConfig
from configs.input_prompts import create_input_prompt, create_multiple_choice_prompt, get_comma_delineated_input, \
    get_input
from create_resources.create_access_role import add_auth_methods


def create_azure_ad_auth_method(config, auth_method_path):
    """
    Create an Azure AD auth method in Akeyless

    :param config: Akeyless configuration for api and auth token
    :param auth_method_path: Absolute path to auth method in akeyless
    # :param bound_resource_types: Typical value: VirtualMachines and/or UserManagedIdentity
    # :param bound_resource_names: Name of machine if resource type is VirtualMachines.
    # :param bound_sub_id: The Subscription ID of the Virtual Machine within Azure
    # :param bound_spid: The Object/Client ID in the Identity section of the Virtual Machine within Azure
    :return: auth_data: Dictionary with information about the Azure AD auth method
    """

    if auth_method_path is None:
        auth_method_path = input("Auth method path: ")
        print("--" * 20)

    bound_resource_names = []
    bound_sub_id = []
    bound_spid = []
    bound_resource_types =[]
    while bound_resource_names == [] and bound_sub_id == [] and bound_spid == []:
        print("At least one limitation is required to proceed.")

        bound_resource_types_options = ["VirtualMachines", "UserManagedIdentity"]
        prompt = "Select resource type limitation(s) (comma separated):"
        bound_resource_types = create_multiple_choice_prompt(bound_resource_types_options, prompt)

        for val in bound_resource_types:
            if val == bound_resource_types_options[0]:
                prompt = "Input Virtual Machine names (comma separated):"
                virtual_machines = get_comma_delineated_input(prompt)
                bound_resource_names.extend(virtual_machines)
            if val == bound_resource_types_options[1]:
                prompt = "Input User Managed Identity names (comma separated):"
                user_managed_identities = get_comma_delineated_input(prompt)
                bound_resource_names.extend(user_managed_identities)

        # prompt = "Input Subscription IDs:  (comma separated):\n"
        # bound_sub_id = get_comma_delineated_input(prompt)

        # prompt = "Input Object (principal) IDs:  (comma separated):\n"
        # bound_spid = get_comma_delineated_input(prompt)

    # Create rotated secret body
    body = CreateAuthMethodAzureAD(
        name=auth_method_path,
        description=config.default_description,
        bound_tenant_id=config.tenant_id,
        bound_resource_types=bound_resource_types,
        bound_resource_names=bound_resource_names,
        bound_sub_id=bound_sub_id,
        bound_spid=bound_spid,
        token=config.auth_token
    )

    try:
        response = config.api.create_auth_method_azure_ad(body)
        auth_data = {
            "access_id": response.access_id,
            "uid_token": None,
            "auth_method_path": auth_method_path,
            "is_new": True
        }
        return auth_data
    except ApiException as e:
        msg = f"Auth Path: {auth_method_path}\n"
        write_error(e, msg)
        if e.status == 409:
            auth_data = {
                "access_id": None,
                "uid_token": None,
                "auth_method_path": auth_method_path,
                "is_new": False
            }
            return auth_data
        return None


def create_api_auth_method(config, auth_method_path):
    """
    Create an API Key auth method in Akeyless

    :param config: Akeyless configuration for api and auth token
    :param auth_method_path: Absolute path to auth method in akeyless
    :return: access_id, access_key: The generated Access ID and Access Key
    """

    if auth_method_path is None:
        auth_method_path = input("Auth method absolute path: ")
        print("--" * 20)

    # Create UID auth body
    body = AuthMethodCreateApiKey(
        name=auth_method_path,
        token=config.auth_token,
        description=config.default_description,
    )

    # Create auth method and token
    try:
        response = config.api.auth_method_create_api_key(body)
        access_id = response.access_id
        access_key = response.access_key

        auth_data = {
            "access_id": access_id,
            "uid_token": None,
            "access_key": access_key,
            "auth_method_path": auth_method_path,
            "is_new": True
        }

        print(f"Auth method path: {auth_data["auth_method_path"]}")
        print(f"Access ID: {auth_data["access_id"]}")
        print("--" * 20)

        return auth_data
    except ApiException as e:
        msg = f"Auth Path: {auth_method_path}\n"
        write_error(e, msg)
        if e.status == 409:
            auth_data = {
                "access_id": None,
                "uid_token": None,
                "access_key": None,
                "auth_method_path": auth_method_path,
                "is_new": False
            }
            return auth_data
        print("something else occurred")
        print(f"e.status = {e.status}")


def create_gcp_auth_method(config, auth_method_path):
    """
    Create a GCP auth method in Akeyless

    :param config: Akeyless configuration for api and auth token
    :param auth_method_path: Absolute path to auth method in akeyless
    :return: access_id: The generated Access ID
    """

    if auth_method_path is None:
        auth_method_path = input("Auth method absolute path: ")
        print("--" * 20)

    prompt = "Input the Google Project Names to allow access to (comma separated):"
    bound_projects = get_comma_delineated_input(prompt)

    gcp_type_options = ["IAM", "GCE"]
    prompt = "Select resource type limitation(s) (comma separated):"
    gcp_type = create_input_prompt(gcp_type_options, prompt)

    # Create UID auth body
    body = AuthMethodCreateGcp(
        name=auth_method_path,
        token=config.auth_token,
        description=config.default_description,
        bound_projects=bound_projects,
        type=gcp_type.lower(),
        audience="cvs.akeyless.io"
    )

    # Create auth method and token
    try:
        response = config.api.auth_method_create_gcp(body)
        access_id = response.access_id

        auth_data = {
            "access_id": access_id,
            "auth_method_path": auth_method_path,
            "is_new": True
        }

        print(f"Auth method path: {auth_data["auth_method_path"]}")
        print(f"Access ID: {auth_data["access_id"]}")
        print("--" * 20)

        return auth_data
    except ApiException as e:
        msg = f"Auth Path: {auth_method_path}\n"
        write_error(e, msg)
        if e.status == 409:
            auth_data = {
                "auth_method_path": auth_method_path,
                "is_new": False
            }
            return auth_data
        print("something else occurred")
        print(f"e.status = {e.status}")


def create_aws_auth_method(config, auth_method_path):
    """
    Create an AWS auth method in Akeyless

    :param config: Akeyless configuration for api and auth token
    :param auth_method_path: Absolute path to auth method in akeyless
    :return: access_id: The generated Access ID
    """

    if auth_method_path is None:
        auth_method_path = input("Auth method absolute path: ")
        print("--" * 20)

    prompt = "Input the AWS Account ID(s) to allow access to (comma separated):"
    bound_accounts = get_comma_delineated_input(prompt)

    # Create UID auth body
    body = AuthMethodCreateAwsIam(
        name=auth_method_path,
        token=config.auth_token,
        description=config.default_description,
        bound_aws_account_id=bound_accounts
    )

    # Create auth method and token
    try:
        response = config.api.auth_method_create_aws_iam(body)
        access_id = response.access_id

        auth_data = {
            "access_id": access_id,
            "auth_method_path": auth_method_path,
            "is_new": True
        }

        print(f"Auth method path: {auth_data["auth_method_path"]}")
        print(f"Access ID: {auth_data["access_id"]}")
        print("--" * 20)

        return auth_data
    except ApiException as e:
        msg = f"Auth Path: {auth_method_path}\n"
        write_error(e, msg)
        if e.status == 409:
            auth_data = {
                "auth_method_path": auth_method_path,
                "is_new": False
            }
            return auth_data
        print("something else occurred")
        print(f"e.status = {e.status}")


def create_k8s_auth_method(config, auth_method_path):
    """
    Create a K8s auth method in Akeyless

    :param config: Akeyless configuration for api and auth token
    :param auth_method_path: Absolute path to auth method in akeyless
    :return: auth_data: Dictionary with information about the K8s auth method
    """

    if auth_method_path is None:
        auth_method_path = input("Auth method path: ")
        print("--" * 20)

    k8s_cluster_api_types_options = ["Native K8s", "Rancher (WIP)"]
    prompt = "Select K8s cluster api type:\n"
    k8s_cluster_api_type = create_input_prompt(k8s_cluster_api_types_options, prompt)

    cluster_api_endpoint = None
    cluster_ca_cert = None
    cluster_bearer_token = None

    match k8s_cluster_api_type:
        case "Native K8s":
            while not cluster_api_endpoint:
                prompt = "Input K8s cluster api endpoint:\n"
                cluster_api_endpoint = input(prompt)
            while not cluster_ca_cert:
                if not config.default_k8s_cert_location:
                    prompt = "Input K8s cluster ca certificate file location:\n"
                    cluster_ca_cert_file = input(prompt)
                else:
                    cluster_ca_cert_file = config.default_k8s_cert_location
                start = "-----BEGIN CERTIFICATE-----"
                end = "-----END CERTIFICATE-----"
                try:
                    with open(cluster_ca_cert_file, "r") as f:
                        cluster_ca_cert = f.read()
                    if not cluster_ca_cert.startswith(start) or not cluster_ca_cert.endswith(end):
                        print(
                            f"Invalid value. It should start with \"{start}\" and end with \"{end}\". It could be "
                            f"an encoded certificate.")
                        cluster_ca_cert = None
                except FileNotFoundError:
                    print(f"Invalid value. It should start with \"{start}\" and end with \"{end}\". It could be an "
                          f"encoded certificate.")
                    cluster_ca_cert = None

            while not cluster_bearer_token:
                prompt = "Input K8s service account token:\n"
                cluster_bearer_token = input(prompt)
                start = "ey"
                if not cluster_bearer_token.startswith(start):
                    print(f"Invalid value. It should start with {start}. It could be an encoded token.")
                    cluster_bearer_token = None
            exit()
        case "Rancher":
            pass

    # Create K8s auth body
    body = GatewayCreateK8SAuthConfig(
        name=auth_method_path,
        description=config.default_description,
        cluster_api_type=k8s_cluster_api_type,
        k8s_auth_type="token",
        k8s_host=cluster_api_endpoint,
        k8s_ca_cert=cluster_ca_cert,
        token_reviewer_jwt=cluster_bearer_token,
        token=config.auth_token
    )

    try:
        response = config.api.gateway_create_k8s_auth_config(body)
        auth_data = {
            "access_id": response.access_id,
            "uid_token": None,
            "auth_method_path": auth_method_path,
            "is_new": True
        }
        return auth_data
    except ApiException as e:
        msg = f"Auth Path: {auth_method_path}\n"
        write_error(e, msg)
        if e.status == 409:
            auth_data = {
                "access_id": None,
                "uid_token": None,
                "auth_method_path": auth_method_path,
                "is_new": False
            }
            return auth_data
        return None


def create_uid_auth_method(config, auth_method_path):
    """
    Create a UID Token auth method in Akeyless

    :param config: Akeyless configuration for api and auth token
    :param auth_method_path: Absolute path to auth method in akeyless
    :return: access_id, uid_token: The generated Access ID and UID token
    """

    if auth_method_path is None:
        auth_method_path = input("Auth method absolute path: ")
        print("--" * 20)

    # Create UID auth body
    body = CreateAuthMethodUniversalIdentity(
        name=auth_method_path,
        token=config.auth_token,
        description=config.default_description,
        ttl=4320
    )

    # Generate UID Token body
    body2 = UidGenerateToken(
        auth_method_name=auth_method_path,
        token=config.auth_token
    )

    # Create auth method and token
    try:
        response = config.api.create_auth_method_universal_identity(body)
        access_id = response.access_id

        response = config.api.uid_generate_token(body2)
        uid_token = response.token

        auth_data = {
            "access_id": access_id,
            "uid_token": uid_token,
            "auth_method_path": auth_method_path,
            "is_new": True
        }

        print(f"Auth method path: {auth_data["auth_method_path"]}")
        print(f"Access ID: {auth_data["access_id"]}")
        print(f"UID Token: {auth_data["uid_token"]}")
        print("--" * 20)

        return auth_data
    except ApiException as e:
        if e.status == 409:
            auth_data = {
                "auth_method_path": auth_method_path,
                "is_new": False
            }
            return auth_data
        else:
            msg = f"Auth Path: {auth_method_path}\n"
            write_error(e, msg)
            print("something else occurred")
            print(f"e.status = {e.status}")


def choose_auth_option(config, app_info):
    auth_options = ["Azure-AD", "GCP", "AWS", "K8s (WIP)", "UID", "API-Key", "OIDC"]
    prompt = "Select a number for the auth method types needed (comma separated):\n"
    auth_methods = create_multiple_choice_prompt(auth_options, prompt)

    auth_method_data = {}

    for value in auth_methods:
        if app_info:
            line_of_business = app_info['line_of_business']
            app_team_name = app_info['app_team_name']
            itpm = app_info['itpm']
            secret_name = app_info['secret_name']
            path = (f"/cvs/{line_of_business}/{app_team_name}-{itpm}/authmethod/{value.lower()}/{app_team_name}-{itpm}-"
                    f"{value.lower()}")
        else:
            path = None

        data = {
            value: {}
        }

        match value:
            case "Azure-AD":
                auth = create_azure_ad_auth_method(config, path)
                if auth is not None:
                    data[value].update(auth)
                    auth_method_data.update(data)
            case "GCP":
                auth = create_gcp_auth_method(config, path)
                if auth is not None:
                    data[value].update(auth)
                    auth_method_data.update(data)
            case "AWS":
                auth = create_aws_auth_method(config, path)
                if auth is not None:
                    data[value].update(auth)
                    auth_method_data.update(data)
            case "K8s (WIP)":
                auth = create_k8s_auth_method(config, path)
                if auth is not None:
                    data[value].update(auth)
                    auth_method_data.update(data)
            case "UID":
                auth = create_uid_auth_method(config, path)
                if auth is not None:
                    data[value].update(auth)
                    auth_method_data.update(data)
            case "API-Key":
                auth = create_api_auth_method(config, path)
                if auth is not None:
                    data[value].update(auth)
                    auth_method_data.update(data)
            case "OIDC":
                prompt = f"Type the AD group names to add to the Sub Claims (comma separated): "
                groups = ",".join(get_comma_delineated_input(prompt))
                sub_claim = {"groups": groups}
                auth = {
                    "auth_method_path": "/cvs/iam/asm/authmethod/oidc/pingid_sso_uat",
                    "is_new": False,
                    "sub_claims": sub_claim
                }
                if path is None:
                    prompt = f"Type the absolute path of the role this will be attached to: "
                    path = get_input(prompt)
                    auth_method = {"OIDC": auth}
                    add_auth_methods(config, path, auth_method)
                data[value].update(auth)
                auth_method_data.update(data)
            case _:
                print(f"Option is not currently supported.")

    return auth_method_data


if __name__ == "__main__":
    akeyless_config = AkeylessConfig("../.env")

    auth = choose_auth_option(akeyless_config, None)

