import os
from datetime import datetime, timezone
import requests
import json

# Update with your access_id and secret_path. These values should be pulled from an environment file
# NonProd URL
base_url = "https://api.secmgmt-uat.cvshealth.com"
# PROD URL
# base_url = "https://api.secmgmt.cvshealth.com"
access_id = "p-..."
secret_path = "/cvs/..."
error_log_location = "./akeyless_error_logs"
error_log_path = f"{error_log_location}/UTC_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}.log"
headers = {
    "accept": "application/json",
    "content-type": "application/json"
}


def log_error_for_akeyless(error, message):
    default_message = \
        f"Contact Akeyless Team for help. Provide above file if requested; Otherwise provide data below: \n"
    debug_info = \
        (f"Access ID: {access_id} \nSecret Path: {secret_path} \nURL: {base_url} \n"
         f"Python Version: {__import__('sys').version} \n"
         f"Token File Path: {token_file} \nUID Token: {uid_token} \n"
         f"Truncated Error Message: {message}")
    log = f"{'-' * 50}\n\n{message} \n{debug_info} \nError: \n{error} \n{'-' * 50}\n"

    try:
        print(f"\n{'-' * 50}\n")
        print(f"Error log written to {error_log_path}\n")
        print(f"{default_message}{debug_info}")
        print(f"\n{'-' * 50}\n")
        with open(error_log_path, "w") as f:
            f.write(log)
        exit()
    except FileNotFoundError:
        os.mkdir(error_log_location)
        log_error_for_akeyless(error, message)


def get_rotated_secret_data(auth_token, secret_path):
    global headers

    # Payload to pull rotated secret value from Akeyless
    payload = {
        "names": secret_path,
        "token": auth_token
    }

    # Make API call
    secret_data_response = requests.post(f"{base_url}/get-rotated-secret-value",
                                         json=payload,
                                         headers=headers)
    status_code = secret_data_response.status_code
    if status_code != 200:
        err_msg = f"Error during pulling rotated secret data from Akeyless with status code {status_code}"
        log_error_for_akeyless(secret_data_response.text, err_msg)

    return json.loads(secret_data_response.text)


def read_uid_token_value(token_file):
    # Uid token value needs to be put into a file in the same directory as the script
    try:
        with open(token_file, "r") as f:
            uid_token = f.read()
            return uid_token
    except FileNotFoundError:
        with open(token_file, "w") as f:
            uid_token = input(f"Enter your UID token provided by the Akeyless team for Access ID {access_id}:\n")
            write_uid_token_value(token_file, uid_token)
            return uid_token


def write_uid_token_value(token_file, new_uid_token):
    # Write the new uid token value into the location in the variable token_file
    with open(token_file, "w") as f:
        f.write(new_uid_token)


def rotate_uid_token(uid_token):
    global headers
    global token_file

    # Payload to rotate UID token
    rotate_uid_token_payload = {
        "uid-token": uid_token
    }

    # Make API call
    rotate_uid_token_response = requests.post(f"{base_url}/uid-rotate-token",
                                              json=rotate_uid_token_payload,
                                              headers=headers)
    status_code = rotate_uid_token_response.status_code
    if status_code != 200:
        err_msg = f"Error during UID token rotation in Akeyless with status code {status_code}"
        log_error_for_akeyless(rotate_uid_token_response.text, err_msg)

    new_uid_token = json.loads(rotate_uid_token_response.text)['token']

    write_uid_token_value(token_file, new_uid_token)


def akeyless_auth(uid_token):
    global headers

    # Payload to auth using UID token to Akeyless
    auth_payload = {
        "access-type": "universal_identity",
        "uid_token": uid_token,
        "access-id": access_id
    }

    # Make API call
    try:
        auth_response = requests.post(f"{base_url}/auth",
                                      json=auth_payload,
                                      headers=headers)
    except requests.exceptions.SSLError as e:
        err_msg = f"Error during auth to Akeyless while trying to connect to {base_url}"
        log_error_for_akeyless(e, err_msg)

    status_code = auth_response.status_code
    if status_code != 200:
        err_msg = f"Error during auth to Akeyless with status code {status_code}"
        log_error_for_akeyless(auth_response.text, err_msg)

    # Token used in get-rotated-secret-value call
    auth_token = json.loads(auth_response.text)['token']

    return auth_token


if __name__ == "__main__":
    # Check that the needed variables are set
    if access_id in ["p-...", "", None]:
        raise Exception("Access ID is not set. Please update the access_id variable at the top of the file.")
    if secret_path in ["/cvs/...", "", None]:
        raise Exception("Secret path is not set. Please update the secret_path variable at the top of the file.")

    # Reads the value of the UID token stored in the token_file variable
    token_file = "./.vault-token"
    uid_token = read_uid_token_value(token_file)

    # Auth to Akeyless
    auth_token = akeyless_auth(uid_token)

    # Pull rotated secret data from Akeyless
    secret_data = get_rotated_secret_data(auth_token, secret_path)

    # NOT REQUIRED - FOR EDUCATIONAL PURPOSES OF HOW TO ROTATE THE UID TOKEN VIA THE SCRIPT
    # THIS IS NORMALLY TAKEN CARE OF OUTSIDE OF THE SCRIPT VIA A CRONJOB OR WINDOWS TASK SCHEDULER
    # Rotate UID token
    rotate_uid_token(uid_token)
