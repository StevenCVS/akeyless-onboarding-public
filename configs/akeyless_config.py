import datetime

from akeyless import ApiClient, Configuration, V2Api, Auth
import dotenv
import os

from configs.input_prompts import create_input_prompt

version = "1.2.0"
engineers = {
    "Taylor Slade": {
        "team": "build",
        "email": "taylor.slade2@cvshealth.com"
    },
    "SaiTeja Jami": {
        "team": "iam",
        "email": "saiteja.jami@cvshealth.com"
    },
    "Madhavi Kertipati": {
        "team": "build",
        "email": "madhavi.kertipati@cvshealth.com"
    },
    "Nandisha Mohan": {
        "team": "build",
        "email": "nandisha.mohan@cvshealth.com"
    },
    "Steven Sutton": {
        "team": "build",
        "email": "steven.sutton@cvshealth.com"
    },
    "Arun Vishwanath": {
        "team": "build",
        "email": "arun.vishwanath@cvshealth.com"
    }
}


def config_akeyless(environment):
    if environment in ["p", "prd"]:
        environment = "PROD"
    elif environment in ["u"]:
        environment = "UAT"
    elif environment in ["d"]:
        environment = "DEV"

    url = os.getenv(f"{environment.upper()}_LOAD_BALANCER_BASE_URL")
    api_access_id = os.getenv(f"{environment.upper()}_API_ACCESS_ID")
    api_access_key = os.getenv(f"{environment.upper()}_API_ACCESS_KEY")

    configuration = Configuration(
        host=url
    )

    api_client = ApiClient(configuration)
    api = V2Api(api_client)

    print(f"Authing to Akeyless {environment}")
    print("--" * 20)
    auth_token = auth_api_key(api, api_access_id, api_access_key)

    return api, auth_token


def auth_api_key(api, access_id, access_key) -> str:
    auth_body = Auth(
        access_id=access_id,
        access_key=access_key
    )
    auth_response = api.auth(auth_body)

    return auth_response.token


def write_error(error, message):
    print(datetime.datetime.now())
    print(f"An error occurred: {error}")
    try:
        with open("../errors.txt", "a") as f:
            f.write(message)
            f.write(f"Error: {error}\n")
    except FileNotFoundError:
        with open("../errors.txt", "w") as f:
            f.write(message)
            f.write(f"Error: {error}\n")


class AkeylessConfig:
    def __init__(self, env_file, is_testing: bool = False):
        dotenv.load_dotenv(env_file)
        env = os.getenv(f"ENV")
        if env in ["UAT", "PROD"]:
            self.env = env
        else:
            env_options = ["UAT", "PROD"]
            self.env = create_input_prompt(env_options, "Select a number for the environment:")

        self.api, self.auth_token = config_akeyless(self.env)
        self.version = version
        self.is_testing = is_testing
        self.engineer = os.getenv(f"DEFAULT_ENGINEER") or self.choose_engineer(env_file)
        self.engineer_email = engineers[self.engineer]["email"]
        self.default_bulk_load_location = os.getenv(f"DEFAULT_LOCATION_BULK_FILE") or None
        self.default_k8s_cert_location = os.getenv(f"DEFAULT_LOCATION_K8s_CERT_FILE") or None
        self.debug = os.getenv(f"DEBUG") or False
        if self.debug:
            print(self.auth_token)
        self.default_description = f"Created by {self.engineer}. Script version: {self.version}."
        self.tenant_id = "fabb61b8-3afe-4e75-b934-a47f782b8cd7"

        support_tag = f"support:{engineers[self.engineer]["team"]}-engineer:{self.engineer_email}"
        self.default_tags = ["csp:azure",
                             "type:service-account",
                             f"vaulted-by:automation-script:{self.version}",
                             support_tag]

    def choose_engineer(self, env_file):
        engineer_options = []
        for engineer in engineers:
            engineer_options.append(engineer)
        prompt = "Who is loading the secret? Select a number:\n"
        self.engineer = create_input_prompt(engineer_options, prompt)
        with open(env_file, "a") as f:
            f.write(f"\nDEFAULT_ENGINEER=\"{self.engineer}\"\n")
