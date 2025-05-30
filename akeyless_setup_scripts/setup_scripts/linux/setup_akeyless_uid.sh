#!/bin/bash

# Get Env information
read -p 'What Environment is this running in? (PROD, UAT): ' ENV
user_dir="/root"

clean_up() {
  echo "Removing file $0"
  rm -- "$0"
  exit
}

if [ "${ENV^^}" == "PROD" ]; then
  gateway_url="https://api.secmgmt.cvshealth.com"
  akeyless_cli_url="https://cli.secmgmt.cvshealth.com"
  dns_url="vault.cvs.akeyless.io"
elif [ "${ENV^^}" == "UAT" ]; then
  gateway_url="https://api.secmgmt-uat.cvshealth.com"
  akeyless_cli_url="https://cli.secmgmt-uat.cvshealth.com"
  dns_url="vault.cvs.uat.akeyless.io"
else
  echo "Please enter a valid value. Valid values are PROD or UAT."
  exit
fi


# Check firewall access
echo "Checking Gateway connection status:"
# shellcheck disable=SC2034
response=$(curl -sLI --connect-timeout 3 "$gateway_url/status" -o /dev/null -w '%{http_code}\n')
exit_code=$?

# Handle any error
if [ "$exit_code" == 0 ]; then
    echo "Gateway connection successful!"
elif [ "$exit_code" == 28 ]; then
  echo "Connection timeout from script after 3 seconds."
  echo "You probably need to request firewall access to $gateway_url."
  echo -e "Try the following curl request if you believe this is an error: \n"
  # shellcheck disable=SC2028
  echo "curl -LI $gateway_url/status -o /dev/null -w '%{http_code}\n' -s;"
  echo -e "\n"
  exit
elif [ "$exit_code" == 6 ]; then
  echo "Error: Could not resolve host. Is the URL correct?"
  # shellcheck disable=SC2028
  echo "$gateway_url/status"
  exit
fi


# Install Akeyless CLI binary
if [ ! -f "$user_dir/akeyless" ] && [ ! -f "$user_dir/.akeyless/bin/akeyless" ]; then
  echo "Downloading Akeyless CLI from https://cli.secmgmt-uat.cvshealth.com/Akeyless_Artifacts/Linux/CLI/akeyless"
  curl -o akeyless "https://cli.secmgmt-uat.cvshealth.com/Akeyless_Artifacts/Linux/CLI/akeyless"
  echo "Akeyless CLI successfully downloaded!"
else
  echo "Akeyless CLI already downloaded"
fi


# Initialize Akeyless CLI
if [ -a "$user_dir/.akeyless" ]; then
  echo "Akeyless CLI already initialized"
else
  echo "Initializing Akeyless CLI"
  mkdir $user_dir/.akeyless
  echo "dns=\"$dns_url\"" > $user_dir/.akeyless/settings
  echo "Configured settings"
  mkdir $user_dir/.akeyless/bin
  mv ./akeyless $user_dir/.akeyless/bin
  echo "Moved akeyless executable to $user_dir/.akeyless/bin"
  chmod +x $user_dir/.akeyless/bin/akeyless
  echo "Initialization Successful"
fi


# Install universal identity script
if [ ! -f "./akeyless_universal_identity.sh" ]; then
  echo "Downloading akeyless_universal_identity.sh https://cli.secmgmt-uat.cvshealth.com/Akeyless_Artifacts/Linux/Universal_Identity/akeyless_universal_identity.sh"
  curl -o akeyless_universal_identity.sh "https://cli.secmgmt-uat.cvshealth.com/Akeyless_Artifacts/Linux/Universal_Identity/akeyless_universal_identity.sh"
  echo "akeyless_universal_identity.sh successfully downloaded!"
  # Add export AKEYLESS_GATEWAY_URL="<<URL>>" to line 10 of script
  sed -i "10i\export AKEYLESS_GATEWAY_URL=$akeyless_cli_url" akeyless_universal_identity.sh;
  # Change AKEYLESS_BIN variable to AKEYLESS_BIN="<<USER_DIR>>/.akeyless/bin/akeyless"
  sed -i "s|AKEYLESS_BIN=~/.akeyless/bin/akeyless|AKEYLESS_BIN=\"$user_dir/.akeyless/bin/akeyless\"|" akeyless_universal_identity.sh;
  # Change TOKEN_FILE=$HOME/.vault-token to TOKEN_FILE=$(pwd)/.vault-token
  sed -i 's/$HOME/$(pwd)/g' akeyless_universal_identity.sh;
  # Change CRON_JOB="* * * * * $USER /bin/bash $PWD/$THIS_EXEC rotate $TOKEN_FILE" to CRON_JOB="*/60 * * * * $USER /bin/bash $PWD/$THIS_EXEC rotate $TOKEN_FILE"
  sed -i '0,/*/s//*\/60/' akeyless_universal_identity.sh;
  # Change echo "* * * * * bash $PWD/$THIS_EXEC to echo "*/60 * * * * bash $PWD/$THIS_EXEC
  sed -i -z 's/*/*\/10/21' akeyless_universal_identity.sh;
  # Change [ ! -d ~/.akeyless ] to [ ! -d "<<USER_DIR>>/.akeyless" ]
  sed -i "s|\[ ! -d ~/.akeyless \]|[ ! -d "\"$user_dir/.akeyless\"" ]|" akeyless_universal_identity.sh
  echo "Updated akeyless_universal_identity.sh"
  chmod 755 ./akeyless_universal_identity.sh
  ./akeyless_universal_identity.sh init
else
  ./akeyless_universal_identity.sh init
fi

if [ -a ./.vault-token ]; then
  chmod 777 ./.vault-token
  echo ".vault-token permissions updated"
fi

chcon system_u:object_r:system_cron_spool_t:s0 /etc/cron.d/akeyless_universal_identity_rotator
echo "Cronjob user updated"

clean_up
