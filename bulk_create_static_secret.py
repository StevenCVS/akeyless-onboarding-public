from akeyless import ApiException, CreateSecret

from configs.akeyless_config import AkeylessConfig

# Required Values when run solo
env = "uat"  # UAT or PROD
business_unit = ""
app_name = "sp"
itpm = ""

is_bulk_load = False
# Set to True if building secret name with business_unit, app_name, and itpm values above
build_secret_name = False
bulk_load = [
    "/cvs/hcb/aarc-apm0015493/secrets/azure/sp-hcb-azurearc-nonprod",
    "/cvs/hcb/aarc-apm0015493/secrets/azure/sp-hcb-azurearc-nonprod2",
]


def input_values():
    application_id = input("Azure Application ID: ").strip().lower()
    secret_name = input("Secret Name: ").strip().lower()
    business_unit = input("Business Unit: ").strip().lower()
    app_name = input("App Name: ").strip().lower()
    itpm = input("ITPM Number (Optional - Press enter to skip): ").strip().lower()

    check = input(f"Are these values correct? (y/n):"
                  f"\n\t{application_id=}"
                  f"\n\t{secret_name=}"
                  f"\n\t{business_unit=}"
                  f"\n\t{app_name=}"
                  f"\n\t{itpm=}").lower()
    if check.lower() not in ["y", "yes", ""]:
        print("Exiting Program")
        exit()

    # Create secret path
    if itpm:
        secret = f"/cvs/{business_unit}/{app_name}-{itpm}/secrets/azure/{secret_name}"
    else:
        secret = f"/cvs/{business_unit}/{app_name}/secrets/azure/{secret_name}"

    return application_id, secret, business_unit, app_name, itpm


def new_static_secret():



    try:
        secret_type = input("What is the Secret Type? (Azure, AWS, GCP)")

        if secret_type.upper() == "AZURE":
            application_id, secret, business_unit, app_name, itpm = input_values()


            # Create rotated secret body
            body = CreateSecret(
                name=secret,
                target_name=target_name,
                authentication_credentials="use-target-creds",
                rotator_type="api-key",
                # application_id="d5d7953c-1209-4790-8be7-8185bbb3e795",
                application_id=application_id,
                rotation_interval=str(90),
                auto_rotate="True",
                tags=["Testing"],
                token=akeyless_config.auth_token
            )
        elif secret_type.upper() == "AWS":
            print(f"{secret_type.upper()} not yet configured")
            exit()
        elif secret_type.upper() == "GCP":
            print(f"{secret_type.upper()} not yet configured")
            exit()
        else:
            print("Invalid Secret Type")
            exit()

        # Create rotated secret
        akeyless_config.api.create_rotated_secret(body)

        return "Secret Successfully Created"
    except ApiException as e:
        if e.status != 409:
            print(e)
            return "Secret Already Exists"
        else:
            print(e)
            return "Error Creating Secret"
    except Exception as e:
        print(e)
        return "Error Creating Secret"


if __name__ == "__main__":
    print("start")

    # Set-up API and Auth
    akeyless_config = AkeylessConfig(env)
    print(akeyless_config.auth_token)

    # Create secret if it doesn't exist
    static_secret = new_static_secret()
    print(static_secret)


