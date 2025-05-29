import csv
from akeyless import ApiException, CreateRotatedSecret
from configs.akeyless_config import AkeylessConfig, write_error
from configs.input_prompts import create_input_prompt


def input_values(application_id="", tags="", description="", itpm="", app_team_name="", line_of_business="", secret_name=""):
    while application_id == "":
        application_id = input("Azure Application ID: ").strip().lower()
    while secret_name == "":
        secret_name = input("Secret Name: ").strip().lower()
    while line_of_business == "":
        line_of_business = input("Line of Business: ").strip().lower()
    while app_team_name == "":
        app_team_name = input("Team Name: ").lower().split(" ")

        # Remove whitespace from every item
        app_team_name = [item.strip() for item in app_team_name if item.strip() not in [None, ""]]

        # Join items with hyphen separating them
        app_team_name = "-".join(app_team_name)
    while itpm == "":
        itpm = input("ITPM Number: ").strip().lower()
    while tags in ["", [], [""]]:
        tags = input("Tags (comma separated list): ").lower().split(',')

    # Remove whitespace from every item
    tags = [item.strip() for item in tags if item.strip() not in [None, ""]]

    return application_id, secret_name, line_of_business, app_team_name, itpm, description, tags


def azure_load(config, secret=None):
    if secret is None:
        application_id, secret_name, line_of_business, app_team_name, itpm, description, tags = input_values()
        tags.extend(config.default_tags)

        # Create secret path
        secret_path = f"/cvs/{line_of_business}/{app_team_name}-{itpm}/secrets/azure/{secret_name}"
    else:
        if secret[1].strip() == "":
            secret_name = secret[2]
            line_of_business = secret[3]
            app_team_name = secret[4]
            itpm = secret[5]
            secret_path = f"/cvs/{line_of_business}/{app_team_name}-{itpm}/secrets/azure/{secret_name}"
        else:
            secret_path = f"{secret[1]}"
            line_of_business = secret_path.split("/")[2]
            app_team_name = secret_path.split("/")[3].split("-")[0]
            itpm = secret_path.split("/")[3].split("-")[1]
            secret_name = secret_path.split("/")[6]

        description = secret[6]
        application_id = secret[7]
        tags = [f"owner1:{secret[8]}", f"owner2:{secret[9]}"]
        tags.extend(config.default_tags)
        if secret[10] not in [None, ""]:
            tags.append(f"owner3:{secret[10]}")

    if description.strip() == "":
        description = (f"Default description - This secret belongs to the azure app {app_team_name.upper()}; App ID: "
                       f"{application_id}. For support please contact {config.engineer_email}. Script version: {config.version}.")

    if not config.is_testing:
        check = input(f"Are these values correct? (y/n):\n"
                      f"\t{application_id=}\n"
                      f"\t{secret_name=}\n"
                      f"\t{line_of_business=}\n"
                      f"\t{app_team_name=}\n"
                      f"\t{itpm=}\n"
                      f"\t{description=}\n"
                      f"\t{tags=}\n")
        print("--" * 20)
        if check.lower() not in ["y", "ys", "ye", "es", "yes", ""]:
            print("Exiting Program")
            exit()

    loaded_path = add_rotated_secret(config, secret_path, application_id, tags, description)

    app_info = {
        "app_team_name": app_team_name,
        "app_id": application_id,
        "line_of_business": line_of_business,
        "tags": tags,
        "itpm": itpm,
        "secret_name": secret_name
    }

    return loaded_path, app_info


def add_rotated_secret(config, secret_path, application_id, tags, description):
    body = create_body(config, secret_path, application_id, tags, description)

    try:
        config.api.create_rotated_secret(body)
        print(f"Successfully loaded {secret_path}")
        print("--" * 20)
        return secret_path
    except ApiException as e:
        if "Status 409 Conflict" in e.body:
            print(f"The secret {secret_path} already exists")
            print("--" * 20)
            return secret_path
        else:
            msg = f"Secret Path: {secret_path}\n"
            write_error(e, msg)


def azure_bulk_load(config, secret_data):
    if config.default_bulk_load_location:
        bulk_load_csv = config.default_bulk_load_location
    else:
        bulk_load_csv = input(f"Input the absolute path of the csv file to upload: ").strip()
        print("--" * 20)
    with open(bulk_load_csv, "r") as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)
        for secret in csv_reader:
            response, app_info = azure_load(config, secret)
            if response is not None:
                secret_data.append(response)
    return secret_data, app_info


def choose_secret_option(config, load_script):
    load_options = ["Single Secret Load", "Bulk Secret Load"]
    prompt = "Select a number for the load type:\n"
    load_type = create_input_prompt(load_options, prompt)

    secret_data = []
    app_info = None

    match load_type:
        case "Single Secret Load":
            response, app_info = azure_load(config)
            if response is not None:
                secret_data.append(response)
        case "Bulk Secret Load":
            response, app_info = azure_bulk_load(config, secret_data)
        case _:
            print(f"Option {load_type} is not currently supported.")

    if load_script:
        return secret_data, app_info
    else:
        return secret_data


def create_body(config, secret_path, application_id, tags, description):
    # Choose target azure environment
    if config.env.upper() == "PROD":
        target_name = "/cvs/iam/asm/target/azure/ar-enterprise-asm-prod"
    elif config.env.upper() == "UAT":
        target_name = "/cvs/iam/asm/target/azure/ar-enterprise-asm-uat"
    else:
        target_name = "/Azure AD/Azure Target"

    # Create rotated secret body
    body = CreateRotatedSecret(
        name=secret_path,
        target_name=target_name,
        description=description,
        authentication_credentials="use-target-creds",
        rotator_type="api-key",
        # application_id="d5d7953c-1209-4790-8be7-8185bbb3e795",
        application_id=application_id,
        rotation_interval=str(90),
        auto_rotate="True",
        tags=tags,
        token=config.auth_token,
        rotate_after_disconnect="True"
    )
    return body


if __name__ == "__main__":
    # Set-up API and Auth
    akeyless_config = AkeylessConfig()
    # print(akeyless_config.auth_token)

    choose_secret_option(akeyless_config, False)
