Akeyless Onboarding
=======
This repo is for use by the akeyless onboarding team to onboard application secrets into akeyless. It is meant to keep 
consistency for the addition of new secrets into Akeyless.

Pre-requisites
-----------
1. Install python version 3.12 or later
2. Install git

Initialization
-----------
1. Update the .env file with your variable values
2. In a command prompt on the machine, pip install the requirements.txt file
```
pip install -r requirements.txt
```

Running the Script:
-----------
The application is set out into multiple files.
- **create_azure_app_resources.py** 
  - to create an azure secret along with any auth method and automatically create a role connecting them together.
- **create_rotated_secret.py** 
  - to create a single or multiple rotated secrets of any type
- **create_auth_method.py** 
  - to create auth methods for an application to authenticate to Akeyless
- **create_access_role.py** 
  - to create an access role and connect it to an auth method and secret path

create_azure_app_resources.py
-----------

create_rotated_secret.py
-----------
create_auth_method.py
-----------
create_access_role.py
-----------