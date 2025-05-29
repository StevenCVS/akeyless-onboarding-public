from create_resources.create_access_role import choose_role_option
from create_resources.create_rotated_secret import choose_secret_option
from create_resources.create_auth_method import choose_auth_option
from configs.akeyless_config import AkeylessConfig

if __name__ == "__main__":
    # Set-up API and Auth
    akeyless_config = AkeylessConfig(".env")

    created_rotated_secrets, app_info = choose_secret_option(akeyless_config, True)

    created_auth_methods = choose_auth_option(akeyless_config, app_info)

    created_access_roles = choose_role_option(akeyless_config, app_info, created_auth_methods)

    if created_rotated_secrets is not None:
        print("Created secrets: ")
        print("\tSecret paths:")
        for secret in created_rotated_secrets:
            print(f"\t\t{secret}")

    if created_auth_methods is not None:
        print("Created auth methods: ")
        for auth_method in created_auth_methods:
            access_id = created_auth_methods[auth_method].get("access_id", None)
            access_key = created_auth_methods[auth_method].get("access_key", None)
            uid_token = created_auth_methods[auth_method].get("uid_token", None)
            auth_method_path = created_auth_methods[auth_method].get("auth_method_path", None)
            is_new = created_auth_methods[auth_method].get("is_new", None)

            print(f"\t{auth_method}:")
            if auth_method != "OIDC":
                if is_new:
                    if access_id is not None:
                        print(f"\t\tAccess ID: {access_id}")
                    if uid_token is not None:
                        print(f"\t\tUID Token: {uid_token}")
                    if access_key is not None:
                        print(f"\t\tAPI Access Key: {access_key}")
                else:
                    print(f"\t\tAlready exists: {auth_method_path}")
            else:
                groups = created_auth_methods['OIDC']['sub_claims']['groups']
                print(f"\t\tOIDC access added with sub claims: 'groups={groups}' to the role "
                      f"'{created_access_roles.get("role_path", None)}'")

    if created_access_roles is not None:
        print("Created roles: ")
        print("\tRole paths:")
        role_path = created_access_roles.get("role_path", None)
        is_new = created_access_roles.get("is_new", None)

        if is_new:
            print(f"\t\t{role_path}")
        else:
            print(f"\t\tAlready exists: {role_path}")

