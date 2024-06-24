import sys


def validate_data(app, instructions, inputs, grad_param):

    valid_1 = instructions_validation(app, instructions)
    valid_2 = input_validation(app, instructions, inputs)
    valid_3 = parameters_validation(app, instructions, grad_param)
    if not all({valid_1, valid_2, valid_3}):
        sys.exit()

def instructions_validation(app, instructions: list[str, int, bool]):

    feeder_name = instructions[0]
    valid = True

    if not isinstance(feeder_name, str) or len(feeder_name) < 2 or len(feeder_name) > 10:
        app.PrintPlain("The feeder name was not recognised")
        app.PrintPlain("Please check the feeder name in the Instructions sheet of the relay_coordination_input sheet and run "
              "the script again")
        valid = False

    study_type = instructions[1]
    if study_type == 1:
        app.PrintPlain("No study type selected from the relay_coordination_input_file.xlsm Instructions sheet")
        app.PrintPlain("Please review the Instructions sheet and run the script again")
        sys.exit()

    return valid


def input_validation(app, instructions: list[str, int, bool], inputs: dict):

    study_type = instructions[1]
    valid = True

    # Full study
    if study_type == 2:
        valid_1 = device_validation(app, inputs)
        valid_2 = relay_settings_val(app, inputs)
        valid_3 = ct_validation(app, inputs)
        if not all({valid_1, valid_2, valid_3}):
            valid = False

    # Fault level study only
    if study_type == 3:
        valid = True
        for device, data in inputs.items():
            if not isinstance(device, str):
                valid = _fail(app, f"Entered site name for {device} is not a string")

    # Relay coordination study only
    if study_type == 4:
        valid_1 = device_validation(app, inputs)
        valid_2 = network_validation(app, inputs)
        valid_3 = relay_settings_val(app, inputs)
        valid_4 = ct_validation(app, inputs)
        if not all({valid_1, valid_2, valid_3, valid_4}):
            valid = False

    # Grading diagram only
    if study_type == 5:
        valid_1 = device_validation(app, inputs)
        valid_2 = network_validation(app, inputs)
        valid_3 = relay_settings_val(app, inputs)
        valid_4 = ct_validation(app, inputs)
        if not all({valid_1, valid_2, valid_3, valid_4}):
            valid = False

    # Line Fuse Study
    if study_type == 6:
        valid_1 = device_validation(app, inputs)
        valid_2 = relay_settings_val(app, inputs)
        valid_3 = ct_validation(app, inputs)
        if not all({valid_1, valid_2, valid_3}):
            valid = False

    return valid


def device_validation(app, inputs):

    valid = True
    for device, data in inputs.items():
        if not isinstance(device, str):
            valid = _fail(app, f"Entered site name for {device} is not a string")
        if data[0] == "" or not (2 <= int(data[0]) <= 44):
            valid = _fail(app, f"No device type for {device} was entered in the Inputs sheet")
        if data[1] == "" or not (2 <= int(data[1]) <= 4):
            valid = _fail(app, f"No device status for {device} was entered in the Inputs sheet")
    return valid


def relay_settings_val(app, inputs):

    valid = True
    for device, data in inputs.items():
        if int(data[0]) in {range(2,26)}:
            # It's a relay
            if not isinstance(data[19], float):
                valid = _fail(app, f"Entered OC pickup value for {device} is not a number.")
            if not isinstance(data[20], float):
                valid = _fail(app, f"Entered TMS value for {device} is not a number.")
            if int(data[21]) not in {range(2,5)}:
                valid = _fail(app, f"OC curve type for {device} not selected")
            if data[22] != "" or not isinstance(data[24], float):
                valid = _fail(app, f"Entered OC Hiset value for {device} is not in the correct format.")
            if data[23] != "" or not isinstance(data[25], float):
                valid = _fail(app, f"Entered OC Min time value for {device} is not in the correct format.")
            if data[24] != "" or not isinstance(data[26], float):
                valid = _fail(app, f"Entered OC Hiset 2 value for {device} is not in the correct format.")
            if data[25] != "" or not isinstance(data[27], float):
                valid = _fail(app, f"Entered OC Min time 2 value for {device} is not in the correct format.")
            if data[26] != "" or not isinstance(data[28], float):
                valid = _fail(app, f"Entered EF pickup value value for {device} is not in the correct format.")
            if data[27] != "" or not isinstance(data[29], float):
                valid = _fail(app, f"Entered EF TMS value for {device} is not in the correct format.")
            if int(data[28]) not in {range(1,5)}:
                pass
            if data[29] != "" or not isinstance(data[31], float):
                valid = _fail(app, f"Entered EF Hiset value for {device} is not in the correct format.")
            if data[30] != "" or not isinstance(data[32], float):
                valid = _fail(app, f"Entered EF Min time value for {device} is not in the correct format.")
            if data[31] != "" or not isinstance(data[33], float):
                valid = _fail(app, f"Entered EF Hiset 2 value for {device} is not in the correct format.")
            if data[32] != "" or not isinstance(data[34], float):
                valid = _fail(app, f"Entered EF Min time 2 value for {device} is not in the correct format.")
    return valid


def network_validation(app, inputs):

    valid = True
    for device, data in inputs.items():
        if not isinstance(data[4], float):
            valid = _fail(app, f"Entered DS capacity value for {device} is not in the correct format.")
        if not isinstance(data[5], float):
            valid = _fail(app, f"Entered Max 3p FL value for {device} is not in the correct format.")
        if not isinstance(data[6], float):
            valid = _fail(app, f"Entered Max PG FL value for {device} is not in the correct format.")
        if not isinstance(data[7], float):
            valid = _fail(app, f"Entered Min 2P FL value for {device} is not in the correct format.")
        if not isinstance(data[8], float):
            valid = _fail(app, f"Entered Min PG FL value for {device} is not in the correct format.")
        if not isinstance(data[9], str):
            valid = _fail(app, f"Entered Max DS TR (Site name) for {device} is not in the correct format.")
        if not isinstance(data[10], float):
            valid = _fail(app, f"Entered Max TR size (kVA) for {device} is not in the correct format.")
        if not isinstance(data[11], float):
            valid = _fail(app, f"Entered Max TR fuse value for {device} is not in the correct format.")
        if not isinstance(data[12], float):
            valid = _fail(app, f"Entered TR Max 3P value for {device} is not in the correct format.")
        if not isinstance(data[13], float):
            valid = _fail(app, f"Entered TR max PG value for {device} is not in the correct format.")
        if not isinstance(data[14], str):
            valid = _fail(app, f"Entered DS devices value for {device} is not in the correct format.")
        if not isinstance(data[15], str):
            valid = _fail(app, f"Entered BU device value for {device} is not in the correct format.")
    return valid


def ct_validation(app, inputs):

    valid = True
    for device, data in inputs.items():
        if int(data[0]) in {range(2,26)}:
            # It's a relay
            if not isinstance(data[16], float):
                valid = _fail(app, f"Entered CT saturation value for {device} is not in the correct format.")
            if not isinstance(data[17], float):
                valid = _fail(app, f"Entered CT composite error value for {device} is not in the correct format.")
            if not isinstance(data[18], float):
                valid = _fail(app, f"Entered CT ratio value for {device} is not in the correct format.")
    return valid


def parameters_validation(app, instructions, grad_param: dict):

    study_type = instructions[1]

    valid = True
    # Full study
    if study_type in {2, 4}:
        data = list(grad_param.values())
        if not isinstance(data[1], float):
            valid = _fail(app, f"Primary reach factor is not in the correct format.")
        elif data[1] < 1 or data[1] > 10:
            valid = _fail(app, f"Primary reach factor is out of bounds (1, 10).")
        if not isinstance(data[2], float):
            valid = _fail(app, f"Back-up reach factor is not in the correct format.")
        elif data[2] < 1 or data[2] > 10:
            valid = _fail(app, f"Back-up reach factor is out of bounds (1, 10).")
        if not isinstance(data[3], float):
            valid = _fail(app, f"Primary slowest clearing time is not in the correct format.")
        elif data[3] < 0.1 or data[3] > 10:
            valid = _fail(f"Primary slowest clearing time is out of bounds (0.1, 10).")
        if not isinstance(data[4], float):
            valid = _fail(app, f"Back-up slowest clearing time is not in the correct format.")
        elif data[4] < 0.1 or data[4] > 10:
            valid = _fail(app, f"Back-up slowest clearing time is out of bounds (0.1, 10).")
        if not isinstance(data[5], float):
            valid = _fail(app, f"Grading margin for mechanical is not in the correct format.")
        elif data[5] < -1 or data[5] > 10:
            valid = _fail(app, f"Grading margin for mechanical relays is out of bounds (-1, 10).")
        if not isinstance(data[6], float):
            valid = _fail(app, f"Grading margin for static relays is not in the correct format.")
        elif data[6] < -1 or data[6] > 10:
            valid = _fail(app, f"Grading margin for static relays is out of bounds (-1, 10).")
        if not isinstance(data[7], float):
            valid = _fail(app, f"Grading margin for digital relays is not in the correct format.")
        elif data[7] < -1 or data[7] > 10:
            valid = _fail(app, f"Grading margin for digital relays is out of bounds (-1, 10).")
        if not isinstance(data[8], float):
            valid = _fail(app, f"Grading margin for fuse is not in the correct format.")
        elif data[8] < -1 or data[8] > 10:
            valid = _fail(app, f"Grading margin for fuse is out of bounds (-1, 10).")
        if not isinstance(data[9], float):
            print(f"CB interrupt time is not in the correct format.")
            valid = _fail(app, f"Grading margin for fuses is not in the correct format.")
        elif data[9] < 0 or data[9] > 10:
            print(f"CB interrupt time is out of bounds (0, 10).")
            valid = _fail(app, f"Grading margin for fuses is not in the correct format.")
        if not isinstance(data[10], float):
            valid = _fail(app, f"Relay coordination optimization iterations is not in the correct format.")
        elif data[13] < 1 or data[10] > 1000000:
            valid = _fail(app, f"Relay coordination optimization iterations is out of bounds (1, 1,000,000).")
        if not isinstance(data[12], float):
            valid = _fail(app, f"Entered feeder load is not in the correct format.")
        elif data[12] < 1 or data[12] > 1000000:
            valid = _fail(app, f"Entered feeder load is out of bounds (1, 1,000,000).")
        if not isinstance(data[13], float):
            valid = _fail(app, f"Entered feeder rating is not in the correct format.")
        elif data[13] < 1 or data[13] > 1000000:
            valid = _fail(app, f"Entered feeder ratings is out of bounds (1, 1,000,000).")


    if study_type in {2, 4, 6}:
        data = list(grad_param.values())
        if not isinstance(data[8], float):
            valid = _fail(app, f"Grading margin for fuses is not in the correct format.")
        elif data[8] < -1 or data[8] > 10:
            valid = _fail(app, f"Grading margin for fuses is out of bounds (-1, 10).")
        if not isinstance(data[13], float):
            valid = _fail(app, f"Entered feeder rating is not in the correct format.")
        elif data[13] < 1 or data[13] > 1000000:
            valid = _fail(app, f"Entered feeder ratings is out of bounds (1, 1,000,000).")
    return valid


def _fail(app, message):
    app.PrintPlain(message)
    return False


# def get_chrome_version():
#
#     import winreg as reg
#
#     try:
#         reg_path = r"SOFTWARE\Google\Chrome\BLBeacon"
#         key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path)
#         version, _ = reg.QueryValueEx(key, "version")
#         return version
#     except Exception as e:
#         return None

