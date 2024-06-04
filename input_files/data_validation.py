
def instructions_validation(instructions: list[str, int, bool]):
    # TODO: Validate instructions data

    feeder_name = instructions[0]
    if type(feeder_name) != str:
        print("Error")

    study_type = instructions[1]
    if study_type == 1:
        print("No study type selected from the relay_coordination_input_file.xlsm Instructions sheet")
        print("Please review the Instructions sheet and run the script again")
        sys.exit()

    # check chrome version


    return instructions


def input_validation(inputs: dict):
    # TODO: Validate input data
    return inputs


def parameters_validation(grad_param: dict):
    # TODO: Validate input data
    return grad_param