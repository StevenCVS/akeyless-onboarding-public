def create_multiple_choice_prompt(options, prompt="Select options (comma-separated numbers): ") -> list:
    """
    Presents a list of options to the user and allows them to select multiple options by entering comma-separated numbers.

    Args:
        options: A list of strings representing the available options.
        prompt: The prompt to display to the user.

    Returns:
        A list of strings representing the selected options, or an empty list if the input is invalid.
    """

    while True:
        try:
            message = prompt + "\n"
            message += ''.join([f'{i + 1}: {n}\n' for i, n in enumerate(options)])
            user_input = input(message)
            selected_indices = [int(x.strip()) - 1 for x in user_input.split(',') if x.strip()]
            if all(0 <= i < len(options) for i in selected_indices):
                print("--" * 20)
                return [options[i] for i in selected_indices]
            else:
                print("Invalid input. Please enter comma-separated numbers corresponding to the options.")
        except ValueError:
            print("Invalid input. Please enter comma-separated numbers.")
        except EOFError:
            return []


def get_comma_delineated_input(prompt, output="") -> list:
    while output in ["", []]:
        output = input(f"{prompt}\n").split(",")
        # Remove whitespace from every item
        output = [item.strip() for item in output if item.strip() not in [None, ""]]
    print("--" * 20)
    return output


def get_input(prompt) -> str:
    """
    Creates a prompt for the user. The user types a value in response to the prompt. The returned output value is the
    value input by the user, stripped of whitespace number selected by the user. This will loop until a value is input.

    Args:
        prompt: The question that is asked to the user

    Returns:
        The string stripped of whitespace characters.
    """

    output = ""
    while output in [""]:
        output = input(prompt).strip()
    print("--" * 20)
    return output


def create_input_prompt(user_options: list, prompt: str) -> str:
    """
    Creates a prompt for the user with options from the list passed into the function. The user selects a single number
    that corresponds to the value they wish to select. The returned output value is the option of the corresponding
    number selected by the user. This will loop until a value is input.

    Args:
        user_options: Options for the user to choose from. Only one option is allowed.
        prompt: The question that is asked to the user

    Returns:
        The option that was mapped to the numerical value assigned to it
    """
    value = ""
    while value == "":
        message = f"{prompt}\n"
        message += ''.join([f'{i + 1}: {n}\n' for i, n in enumerate(user_options)])
        option_num: str = input(message)
        if option_num == '':
            value = user_options[0]
            print("--" * 20)
        elif option_num.isnumeric():
            if int(option_num) > len(user_options):
                print(
                    f'Invalid option. Please enter a whole number. Valid options are between 1 and {len(user_options)}')
                print(f'Input value was "{option_num}"')
                print("--" * 20)
            else:
                value = user_options[int(option_num) - 1]
                print("--" * 20)
        else:
            print(
                f'Invalid option. Please enter a whole number. Valid options are between 1 and {len(user_options)}')
            print(f'Input value was "{option_num}"')
            print("--" * 20)

    return value
