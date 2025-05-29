import unittest
from unittest import skip

from configs.akeyless_config import AkeylessConfig
from configs.input_prompts import get_comma_delineated_input
from create_resources.create_access_role import create_akeyless_role
from create_resources.create_rotated_secret import azure_bulk_load
from akeyless import DeleteItems, DeleteRoles, DeleteAuthMethods


class AllTests(unittest.TestCase):
    @classmethod
    # Executed once at the start before any tests in this class
    def setUpClass(cls):
        cls.config = AkeylessConfig(".env", True)
        cls.role_path = "/cvs/iam/asm-ITPM0123456789/roles/script_test_role"
        cls.secret_data = []

    # Executed once before each test in this class
    def setUp(self):
        pass

    def test_create_azure_rotated_secrets(self):
        response, app_info = azure_bulk_load(self.config, self.secret_data)
        self.assertEqual("asm", app_info['app_team_name'])
        self.assertEqual("f00913c3-0a8b-48a4-b9f6-30ed61626622", app_info['app_id'])
        self.assertEqual("iam", app_info['line_of_business'])
        self.assertEqual("ITPM0123456789", app_info['itpm'])
        self.assertEqual("/cvs/iam/asm-ITPM0123456789/secrets/azure/script_test_azure_secret", response[0])
        self.assertEqual("/cvs/iam/asm-ITPM0123456789/secrets/azure/script_test_azure_secret_2", response[1])

    def cleanup_create_azure_rotated_secrets(self):
        body = DeleteItems(
            item=[
                "/cvs/iam/asm-ITPM0123456789/secrets/azure/script_test_azure_secret",
                "/cvs/iam/asm-ITPM0123456789/secrets/azure/script_test_azure_secret_2"
            ],
            token=self.config.auth_token
        )
        response = self.config.api.delete_items(body)
        if response.failed_deleted_items is not None:
            return response.failed_deleted_items

    def test_create_access_role(self):
        role_data = create_akeyless_role(self.config, self.role_path)
        self.assertEqual(True, role_data['is_new'])
        self.assertEqual("/cvs/iam/asm-ITPM0123456789/roles/script_test_role", role_data['role_path'])
        pass

    def cleanup_create_access_role(self):
        body = DeleteItems(
            item=[
                "/cvs/iam/asm-ITPM0123456789/roles/script_test_role"
            ],
            token=self.config.auth_token
        )
        response = self.config.api.delete_items(body)
        if response.failed_deleted_items is not None:
            return response.failed_deleted_items

    @staticmethod
    @skip
    def test_inputs():
        out = get_comma_delineated_input("input something:")

    @classmethod
    def tearDownClass(cls):
        errors = {
            "delete_secrets_error": {},
            "delete_role_error": {},
            "delete_auth_methods_error": {},
        }
        # Catch errors during deleting test secrets
        errors["delete_secrets_error"]["azure"] = cls.cleanup_create_azure_rotated_secrets(cls)

        # Catch errors during deleting test role
        errors["delete_role_error"]["role"] = cls.cleanup_create_access_role(cls)

        # Catch errors during deleting test auth methods
        # errors["delete_auth_methods_error"] = cls.(cls)

        for val in errors:
            if errors[val] is not None:
                raise Exception(errors)

