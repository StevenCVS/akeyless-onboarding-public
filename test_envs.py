import akeyless
import os

from akeyless import ApiException
from dotenv import load_dotenv
import time
from functools import wraps

# Load environment variables
load_dotenv("C:\\Users\\c795950\\AppData\\Roaming\\JetBrains\\PyCharm2023.3\\scratches\\.env")

# envs = ["UAT", "PROD"]
envs = ["PROD"]
# envs = ["UAT"]
# envs = ["DEV"]
test_static_secret = os.getenv("TEST_STATIC_SECRET")
test_rotated_secret = os.getenv("TEST_ROTATED_SECRET")
DEBUG = True


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Completed in {total_time:.4f} seconds')
        return result
    return timeit_wrapper


def auth_api_key(api, access_id, access_key) -> str:
    auth_body = akeyless.Auth(
        access_id=access_id,
        access_key=access_key
    )
    auth_response = api.auth(auth_body)

    return auth_response.token


def auth_uid(api, access_id, token) -> str:
    auth_body = akeyless.Auth(
        access_type="universal_identity",
        access_id=access_id,
        uid_token=token
    )
    auth_response = api.auth(auth_body)
    return auth_response.token


@timeit
def create_static_secret(api, name, token, errors: list):
    body = akeyless.CreateSecret(name=name,
                                 value="test secret",
                                 description="test secret made from python sdk",
                                 token=token)

    try:
        api.create_secret(body)
    except ApiException as e:
        if e.status == 409:
            pass
        else:
            print(e)
            errors.append(e)
    except Exception as e:
        print(e)
        errors.append(e)


@timeit
def create_rotated_secret(api, name, token, env, errors: list):
    if env == "PROD":
        target_name = "/cvs/iam/asm/target/azure/ar-enterprise-asm-prod"
    elif env == "UAT":
        target_name = "/cvs/iam/asm/target/azure/ar-enterprise-asm-uat"
    else:
        target_name = "/Azure AD/Azure Target"
    body = akeyless.CreateRotatedSecret(
        name=name,
        target_name=target_name,
        authentication_credentials="use-target-creds",
        rotator_type="api-key",
        application_id="d5d7953c-1209-4790-8be7-8185bbb3e795",
        rotation_interval=str(90),
        auto_rotate="True",
        tags=["Environment Testing"],
        token=token
    )
    try:
        api.create_rotated_secret(body)
    except ApiException as e:
        if e.status == 409:
            pass
        else:
            print(e)
            errors.append(e)
    except Exception as e:
        print(e)
        errors.append(e)


@timeit
def get_static_secret(api, name, token, errors: list):
    body = akeyless.GetSecretValue(names=[name], token=token)
    try:
        api.get_secret_value(body)
    except Exception as e:
        print(e)
        errors.append(e)


@timeit
def get_rotated_secret(api, name, token, errors: list):
    body = akeyless.RotatedSecretGetValue(name=name, token=token)
    try:
        api.rotated_secret_get_value(body)
    except Exception as e:
        print(e)
        errors.append(e)


@timeit
def delete_static_secret(api, name, token, errors: list):
    body = akeyless.DeleteItem(name=name, token=token)
    try:
        api.delete_item(body)
    except Exception as e:
        print(e)
        errors.append(e)


@timeit
def delete_rotated_secret(api, name, token, errors: list):
    body = akeyless.DeleteItem(name=name, token=token)
    try:
        api.delete_item(body)
    except Exception as e:
        print(e)
        errors.append(e)

@timeit
def auth(url, api, api_access_id, api_access_key):
    # Api_key login test
    try:
        if DEBUG:
            print(f"Authenticating to Akeyless @ {url}")
        else:
            print(url)
        auth_token = auth_api_key(api, api_access_id, api_access_key)
        return auth_token
    except Exception as e:
        print(e)
        # return e



@timeit
def main():
    global time
    api_access_id = os.getenv(f"{env}_API_ACCESS_ID")
    api_access_key = os.getenv(f"{env}_API_ACCESS_KEY")
    uid_token = os.getenv(f"{env}_UID_TOKEN")
    base_url_list = os.getenv(f"{env}_BASE_URL_LIST").split(",")
    errors = []

    print(f"Running tests against {env}")
    for url in base_url_list:
        configuration = akeyless.Configuration(
            host=url
        )

        # Akeyless api setup
        api_client = akeyless.ApiClient(configuration)
        api = akeyless.V2Api(api_client)

        # url = "https://api.cvs.uat.akeyless.io"
        auth_token = auth(url, api, api_access_id, api_access_key)

        if DEBUG:
            print(f"Creating static secret... ", end="")
        create_static_secret(api, test_static_secret, auth_token, errors)

        if DEBUG:
            print(f"Creating rotated secret... ", end="")
        create_rotated_secret(api, test_rotated_secret, auth_token, env, errors)

        if DEBUG:
            print(f"Retrieving static secret... ", end="")
        get_static_secret(api, test_static_secret, auth_token, errors)

        if DEBUG:
            print(f"Retrieving rotated secret... ", end="")
        get_rotated_secret(api, test_rotated_secret, auth_token, errors)

        if DEBUG:
            print(f"Deleting static secret... ", end="")
        delete_static_secret(api, test_static_secret, auth_token, errors)

        if DEBUG:
            print(f"Deleting rotated secret... ", end="")
        delete_rotated_secret(api, test_rotated_secret, auth_token, errors)

    if not errors:
        print("All URLs passed")


if __name__ == "__main__":
    for env in envs:
        main()


 