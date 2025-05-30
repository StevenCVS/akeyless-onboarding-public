import os
from datetime import datetime, timezone

import akeyless  # run "pip install akeyless" to install


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
        self.token_file = "./.vault-token"
        self.uid_token = None
        self.read_uid_token_value()
        self.auth_token = self.akeyless_auth()

    def log_error_for_akeyless(self, error, message):
        default_message = \
            f"Contact Akeyless Team for help. Provide above file if requested; Otherwise provide data below: \n"
        debug_info = \
            (f"Access ID: {self.access_id} \nSecret Path: {self.secret_path} \nURL: {self.base_url} \n"
             f"Python Version: {__import__('sys').version} \n"
             f"Akeyless Version: {akeyless.__version__} \n"
             f"Token File Path: {self.token_file} \nUID Token: {self.uid_token} \n"
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

    def read_uid_token_value(self):
        # Uid token value needs to be put into a file in the same directory as the script
        try:
            with open(self.token_file, "r") as f:
                self.uid_token = f.read()
        except FileNotFoundError:
            with (open(self.token_file, "w") as f):
                self.uid_token = \
                    input(f"Enter your UID token provided by the Akeyless team for Access ID {self.access_id}:\n")
                self.write_uid_token_value()

    def write_uid_token_value(self):
        # Write the new uid token value into the location in the variable token_file
        with open(self.token_file, "w") as f:
            f.write(self.uid_token)

    def rotate_uid_token(self):
        # Payload to rotate UID token
        body = akeyless.UidRotateToken(uid_token=self.uid_token)

        # Make API call
        try:
            rotate_uid_token_response = self.api.uid_rotate_token(body)
        except Exception as e:
            err_msg = f"Error during UID token rotation in Akeyless"
            self.log_error_for_akeyless(e, err_msg)

        self.uid_token = rotate_uid_token_response.token

        self.write_uid_token_value()

    def akeyless_auth(self):
        # Payload to auth using UID token to Akeyless
        auth_body = \
            akeyless.Auth(access_type="universal_identity", access_id=self.access_id, uid_token=self.uid_token)

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

    # NOT REQUIRED - FOR EDUCATIONAL PURPOSES OF HOW TO ROTATE THE UID TOKEN VIA THE SCRIPT
    # THIS IS NORMALLY TAKEN CARE OF OUTSIDE OF THE SCRIPT VIA A CRONJOB OR WINDOWS TASK SCHEDULER
    # Rotate UID token
    akeyless_connection.rotate_uid_token()
