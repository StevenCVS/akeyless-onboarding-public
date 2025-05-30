import os
from datetime import datetime, timezone

import akeyless  # run "pip install akeyless" to install
from akeyless_cloud_id import CloudId, __version__ as cloud_id_version  # run "pip install akeyless-cloud-id" to install


class AkeylessConnection:
    def __init__(self, access_id, secret_path):
        # NonProd URL
        self.base_url = "https://api.secmgmt-uat.cvshealth.com"
        # PROD URL
        # self.base_url = "https://api.secmgmt.cvshealth.com"
        self.api = self.setup_api()
        if access_id in ["p-...", "", None]:
            raise Exception("Access ID is not set. Please update the access_id variable at the bottom of the file.")
        if secret_path in ["...", "", None]:
            raise Exception("Secret path is not set. Please update the secret_path variable at the bottom of the file.")
        self.access_id = access_id
        self.secret_path = secret_path
        self.error_log_location = "./akeyless_error_logs"
        self.error_log_path = \
            f"{self.error_log_location}/UTC_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}.log"
        self.cloud_id = None
        self.auth_token = self.akeyless_auth()

    def log_error_for_akeyless(self, error, message):
        default_message = \
            f"Contact Akeyless Team for help. Provide above file if requested; Otherwise provide data below: \n"
        debug_info = \
            (f"Access ID: {self.access_id} \nSecret Path: {self.secret_path} \nURL: {self.base_url} \n"
             f"Python Version: {__import__('sys').version} \n"
             f"Akeyless Version: {akeyless.__version__} \nAkeyless Cloud ID Version: {cloud_id_version}\n"
             f"Cloud ID Token: {self.cloud_id} \n"
             f"Truncated Error Message: {message}")
        log = f"{'-' * 50}\n\n{message} \n{debug_info} \nError: \n{error} \n{'-' * 50}\n"

        try:
            print(f"\n{'-' * 50}\n")
            print(f"Error log written to {self.error_log_path}\n")
            print(f"{default_message}{debug_info}")
            print(f"\n{'-' * 50}\n")
            with open(self.error_log_path, "w") as f:
                f.write(log)
            exit()
        except FileNotFoundError:
            os.mkdir(self.error_log_location)
            self.log_error_for_akeyless(error, message)

    def setup_api(self):
        configuration = akeyless.Configuration(
            host=f"{self.base_url}"
        )

        api_client = akeyless.ApiClient(configuration)

        return akeyless.V2Api(api_client)

    def get_rotated_secret_data(self):
        # Payload to pull rotated secret value from Akeyless
        body = akeyless.RotatedSecretGetValue(name=self.secret_path, token=self.auth_token)

        # Make API call
        try:
            secret_data_response = self.api.rotated_secret_get_value(body)
        except Exception as e:
            err_msg = f"Error during pulling rotated secret data from Akeyless"
            self.log_error_for_akeyless(e, err_msg)

        return secret_data_response["value"]

    def akeyless_auth(self):
        # Generate Cloud ID based on provider
        cloud_id_generator = CloudId()
        self.cloud_id = cloud_id_generator.generate()

        # Payload to auth to Akeyless using AWS Cloud ID
        auth_body = akeyless.Auth(access_type="aws_iam", access_id=self.access_id, cloud_id=self.cloud_id)

        # Make API call
        try:
            auth_response = self.api.auth(auth_body)
        except Exception as e:
            err_msg = f"Error during auth to Akeyless while trying to connect to {self.base_url}"
            self.log_error_for_akeyless(e, err_msg)

        return auth_response.token


if __name__ == "__main__":
    # Update with your access_id and secret_path. These values should be pulled from an environment file
    access_id = "p-..."
    secret_path = "/cvs/..."

    # Auth to Akeyless and setup connection data
    akeyless_connection = AkeylessConnection(access_id, secret_path)

    # Pull rotated secret data from Akeyless
    secret_data = akeyless_connection.get_rotated_secret_data()
