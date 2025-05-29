from configs.akeyless_config import AkeylessConfig
from configs.input_prompts import create_multiple_choice_prompt


if __name__ == "__main__":
    # Set-up API and Auth
    akeyless_config = AkeylessConfig(".env")

    script_options = ["Create Secret(s)", "Create Auth Method(s)", "Create Access Role(s)",
                      "Delete Secret(s)", "Delete Auth Method(s)", "Delete Access Role(s)"]
    prompt = "Select the numbers of what you would like to do: \n"

    create_multiple_choice_prompt(script_options, prompt)
