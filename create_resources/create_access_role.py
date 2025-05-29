from akeyless import ApiException, CreateRole, SetRoleRule, AssocRoleAuthMethod

from configs.akeyless_config import write_error, AkeylessConfig
from configs.input_prompts import get_comma_delineated_input, create_multiple_choice_prompt

auth_methods = ["/cvs/iam/asm/authmethod/taylor/asd"]

rule_type_options = ['item-rule', 'auth-method-rule', 'role-rule']
permission_options = ['read', 'list', 'create', 'update', 'delete']


def set_deny_rules(config, role_name):
    deny_rules = {
        'role-rule': ['/cvs/iam/asm/roles/admin/asm-admin'],
        'item-rule': ['/cvs/iam/asm/keys/gateway/secretsmanager-gw-uat-dfckey'],
        'auth-method-rule': ['/cvs/iam/asm/authmethod/certs/gateway/*'],
    }
    permissions = ['deny']

    if role_name is None:
        role_name = get_comma_delineated_input("Role absolute path: ")

        prompt = "Select the numbers of the needed rule types (comma separated): "
        rule_types = create_multiple_choice_prompt(rule_type_options, prompt)

        for rule_type in rule_types:
            prompt = f"Type the paths to deny access to for {rule_type} (comma separated): "
            paths = get_comma_delineated_input(prompt)

            for path in paths:
                deny_rules[rule_type].append(path)

            prompt = "Select the numbers of the needed permissions (comma separated): "
            permissions = create_multiple_choice_prompt(permission_options, prompt)

    # Add deny rules to role
    for rule in deny_rules:
        for deny_path in deny_rules[rule]:
            body = SetRoleRule(capability=permissions, path=deny_path, rule_type=rule,
                               role_name=role_name, token=config.auth_token)
            config.api.set_role_rule(body)


def set_allow_rules(config, role_name, allow_path):
    allow_rules = {
        'role-rule': [],
        'item-rule': [],
        'auth-method-rule': [],
    }
    permissions = ["read", "list"]

    if allow_path is None:
        prompt = "Select the numbers of the rule types needed (comma separated): "
        rule_types = create_multiple_choice_prompt(rule_type_options, prompt)

        for rule_type in rule_types:
            prompt = f"Type the paths to allow access to for the {rule_type} (comma separated): "
            paths = get_comma_delineated_input(prompt)

            for path in paths:
                prompt = (f"Select the permissions needed for '{path}' (comma separated) "
                          f"or press enter for {permissions}:")
                new_permissions = create_multiple_choice_prompt(permission_options, prompt)
                if new_permissions:
                    permissions = new_permissions
                allow_rules[rule_type].append([path, permissions])

                body = SetRoleRule(capability=permissions, path=path, rule_type=rule_type,
                                   role_name=role_name, token=config.auth_token)
                config.api.set_role_rule(body)

    else:
        role_name = role_name
        allow_rules['item-rule'] = [allow_path]

        # Add allow rules to role
        for rule in allow_rules:
            for allow_path in allow_rules[rule]:
                body = SetRoleRule(capability=permissions, path=allow_path, rule_type=rule,
                                   role_name=role_name, token=config.auth_token)
                config.api.set_role_rule(body)


def add_auth_methods(config, role_name, auth_methods=None):
    if auth_methods is None:
        auth_methods = {}
        prompt = f"Type the Auth Method paths to attach to the Access Role '{role_name}' (comma separated): "
        response = get_comma_delineated_input(prompt)
        for val in response:
            if val == "/cvs/iam/asm/authmethod/oidc/pingid_sso_uat":
                prompt = f"Type the AD group names for the Sub Claims (comma separated): "
                groups = ",".join(get_comma_delineated_input(prompt))
                sub_claim = {"groups": groups}
                auth_methods["OIDC"] = {"auth_method_path": val, "sub_claims": sub_claim}
            else:
                auth_methods[val] = {"auth_method_path": val, "sub_claims": None}
    for auth_method in auth_methods:
        if auth_method == "OIDC":
            am_name = "/cvs/iam/asm/authmethod/oidc/pingid_sso_uat"
        else:
            am_name = auth_methods[auth_method]["auth_method_path"]
            auth_methods[auth_method]["sub_claims"] = None

        try:
            body = AssocRoleAuthMethod(role_name=role_name, am_name=am_name, token=config.auth_token,
                                       sub_claims=auth_methods[auth_method]["sub_claims"])
            config.api.assoc_role_auth_method(body)
        except ApiException as e:
            if e.status == 404:
                print("Auth Method not found. Please confirm path and try again. "
                      "Previous additions to the role persist and do not need to be repeated.")
            elif e.status != 409:
                print(e)
                continue


def set_auth_rules(config, role_path, allow_path, auth_methods):
    set_deny_rules(config, role_path)
    set_allow_rules(config, role_path, allow_path)
    add_auth_methods(config, role_path, auth_methods)


def create_akeyless_role(config, role_path):
    """
    Create a role in Akeyless

    :param config: Akeyless configuration for api and auth token
    :param role_path: Absolute path to auth method in akeyless
    """

    if role_path is None:
        role_path = input("Role absolute path: ")
        print("--" * 20)

    try:
        body = CreateRole(token=config.auth_token,
                          name=role_path,
                          description=f"Created by {config.engineer}. Script version: {config.version}."
                          )
        config.api.create_role(body)
        role_data = {
            "role_path": role_path,
            "is_new": True
        }
        return role_data
    except ApiException as e:
        msg = f"Role Path: {role_path}\n"
        write_error(e, msg)
        if e.status == 409:
            role_data = {
                "role_path": role_path,
                "is_new": False
            }
            return role_data
        print("something else occurred")
        print(f"e.status = {e.status}")
        return None


def choose_role_option(config, app_info=None, auth_methods=None):
    if app_info:
        line_of_business = app_info['line_of_business']
        app_team_name = app_info['app_team_name']
        itpm = app_info['itpm']
        secret_name = app_info['secret_name']
        path = f"/cvs/{line_of_business}/{app_team_name}-{itpm}/roles/{app_team_name}-{itpm}-read-all"
        allow_path = f"/cvs/{line_of_business}/{app_team_name}-{itpm}/secrets/*"
    else:
        path = None
        allow_path = None

    # Create role if it doesn't exist
    role_data = create_akeyless_role(config, path)
    set_auth_rules(config, role_data['role_path'], allow_path, auth_methods)

    return role_data


if __name__ == "__main__":
    akeyless_config = AkeylessConfig("../.env")

    choose_role_option(akeyless_config)
