import sys
import load_rating_data.load_rating_data as lrd


def validate_data(instructions, inputs, grad_param):

    valid_1 = instructions_validation(instructions)
    valid_2 = input_validation(instructions, inputs)
    valid_3 = parameters_validation(instructions, grad_param)
    if not all({valid_1, valid_2, valid_3}):
        sys.exit()

def instructions_validation(instructions: list[str, int, bool]):
    # TODO: Validate instructions data

    feeder_name = instructions[0]
    valid = True

    if not isinstance(feeder_name, str) or len(feeder_name) < 2 or len(feeder_name) > 10:
        print("The feeder name was not recognised")
        print("Please check the feeder name in the Instructions sheet of the relay_coordination_input sheet and run "
              "the script again")
        valid = False

    study_type = instructions[1]
    if study_type == 1:
        print("No study type selected from the relay_coordination_input_file.xlsm Instructions sheet")
        print("Please review the Instructions sheet and run the script again")
        sys.exit()

    # check chrome version
    get_netplan = instructions[2]
    supported_chrome_versions = {'125.0.6422.113'}
    if study_type in {2, 4, 6} and get_netplan:
        chrome_version = lrd.get_chrome_version()
        if chrome_version not in supported_chrome_versions:
            print("The script could not access Netplan as the user's version of chrome is not supported")
            print(f"chrome versions supported: {supported_chrome_versions}")
            print(f"chrome version found: {chrome_version}")
            print("Please untick the relevant checkbox in the Instructions sheet of the relay_coordination_input file. "
                  "Then manually enter feeder and load data for the associated relay in the Inputs sheet.")
            valid = False
    return valid


def input_validation(instructions: list[str, int, bool], inputs: dict):

    study_type = instructions[1]
    valid = True

    # Full study
    if study_type == 2:
        valid_1 = device_validation(inputs)
        valid_2 = True
        if not instructions[2]:
            valid_2 = load_rating_val(inputs)
        valid_3 = relay_settings_val(inputs)
        valid_4 = ct_validation(inputs)
        if not all({valid_1, valid_2, valid_3, valid_4}):
            valid = False

    # Fault level study only
    if study_type == 3:
        valid = True
        for device, data in inputs.items():
            if not isinstance(device, int):
                valid = _fail(f"Entered site name for {device} is not a string")

    # Relay coordination study only
    if study_type == 4:
        valid_1 = device_validation(inputs)
        valid_2 = True
        if not instructions[2]:
            valid_2 = load_rating_val(inputs)
        valid_3 = network_validation(inputs)
        valid_4 = relay_settings_val(inputs)
        valid_5 = ct_validation(inputs)
        if not all({valid_1, valid_2, valid_3, valid_4, valid_5}):
            valid = False

    # Grading diagram only
    if study_type == 5:
        valid_1 = device_validation(inputs)
        valid_2 = network_validation(inputs)
        valid_3 = relay_settings_val(inputs)
        valid_4 = ct_validation(inputs)
        if not all({valid_1, valid_2, valid_3, valid_4}):
            valid = False

    # Line Fuse Study
    if study_type == 6:
        valid_1 = device_validation(inputs)
        valid_2 = True
        if not instructions[2]:
            valid_2 = load_rating_val(inputs)
        valid_3 = relay_settings_val(inputs)
        valid_4 = ct_validation(inputs)
        if not all({valid_1, valid_2, valid_3, valid_4}):
            valid = False

    return valid


def device_validation(inputs):

    valid = True
    for device, data in inputs.items():
        if not isinstance(device, int):
            valid = _fail(f"Entered site name for {device} is not a string")
        if data[0] == "" or data[0] not in {range(2,45)}:
            valid = _fail(f"No device type for {device} was entered in the Inputs sheet")
        if data[1] == "" or data[0] not in {range(2,5)}:
            valid = _fail(f"No device status for {device} was entered in the Inputs sheet")
    return valid


def load_rating_val(inputs):

    valid = True
    for device, data in inputs.items():
        if data[4] != "" or not isinstance(data[4], float):
            valid = _fail(f"Entered Load for {device} is not in the correct format.")
        if data[5] != "" or not isinstance(data[5], float):
            valid = _fail(f"Entered Rating for {device} is not in the correct format.")
    return valid

def relay_settings_val(inputs):

    valid = True
    for device, data in inputs.items():
        if data[0] in {range(2,26)}:
            # It's a relay
            if not isinstance(data[21], float):
                valid = _fail(f"Entered OC pickup value for {device} is not a number.")
            if not isinstance(data[22], float):
                valid = _fail(f"Entered TMS value for {device} is not a number.")
            if data[23] not in {range(2,5)}:
                valid = _fail(f"OC curve type for {device} not selected")
            if data[24] != "" or not isinstance(data[24], float):
                valid = _fail(f"Entered OC Hiset value for {device} is not in the correct format.")
            if data[25] != "" or not isinstance(data[25], float):
                valid = _fail(f"Entered OC Min time value for {device} is not in the correct format.")
            if data[26] != "" or not isinstance(data[26], float):
                valid = _fail(f"Entered OC Hiset 2 value for {device} is not in the correct format.")
            if data[27] != "" or not isinstance(data[27], float):
                valid = _fail(f"Entered OC Min time 2 value for {device} is not in the correct format.")
            if data[28] != "" or not isinstance(data[28], float):
                valid = _fail(f"Entered EF pickup value value for {device} is not in the correct format.")
            if data[29] != "" or not isinstance(data[29], float):
                valid = _fail(f"Entered EF TMS value for {device} is not in the correct format.")
            if data[30] not in {range(1,5)}:
                pass
            if data[31] != "" or not isinstance(data[31], float):
                valid = _fail(f"Entered EF Hiset value for {device} is not in the correct format.")
            if data[32] != "" or not isinstance(data[32], float):
                valid = _fail(f"Entered EF Min time value for {device} is not in the correct format.")
            if data[33] != "" or not isinstance(data[33], float):
                valid = _fail(f"Entered EF Hiset 2 value for {device} is not in the correct format.")
            if data[34] != "" or not isinstance(data[34], float):
                valid = _fail(f"Entered EF Min time 2 value for {device} is not in the correct format.")
    return valid


def network_validation(inputs):

    valid = True
    for device, data in inputs.items():
        if not isinstance(data[6], float):
            valid = _fail(f"Entered DS capacity value for {device} is not in the correct format.")
        if not isinstance(data[7], float):
            valid = _fail(f"Entered Max 3p FL value for {device} is not in the correct format.")
        if not isinstance(data[8], float):
            valid = _fail(f"Entered Max PG FL value for {device} is not in the correct format.")
        if not isinstance(data[9], float):
            valid = _fail(f"Entered Min 2P FL value for {device} is not in the correct format.")
        if not isinstance(data[10], float):
            valid = _fail(f"Entered Min PG FL value for {device} is not in the correct format.")
        if not isinstance(data[11], str):
            valid = _fail(f"Entered Max DS TR (Site name) for {device} is not in the correct format.")
        if not isinstance(data[12], float):
            valid = _fail(f"Entered Max TR size (kVA) for {device} is not in the correct format.")
        if data[13] not in {range(1,39)}:
            valid = _fail(f"Entered Max TR fuse value for {device} is not in the correct format.")
        if not isinstance(data[14], float):
            valid = _fail(f"Entered TR Max 3P value for {device} is not in the correct format.")
        if not isinstance(data[15], float):
            valid = _fail(f"Entered TR max PG value for {device} is not in the correct format.")
        if not isinstance(data[16], str):
            valid = _fail(f"Entered DS devices value for {device} is not in the correct format.")
        if not isinstance(data[17], str):
            valid = _fail(f"Entered BU device value for {device} is not in the correct format.")
    return valid


def ct_validation(inputs):

    valid = True
    for device, data in inputs.items():
        if data[0] in {range(2,26)}:
            # It's a relay
            if not isinstance(data[18], float):
                valid = _fail(f"Entered CT saturation value for {device} is not in the correct format.")
            if not isinstance(data[19], float):
                valid = _fail(f"Entered CT composite error value for {device} is not in the correct format.")
            if not isinstance(data[20], float):
                valid = _fail(f"Entered CT ratio value for {device} is not in the correct format.")
    return valid


def parameters_validation(instructions, grad_param: dict):

    study_type = instructions[1]

    valid = True
    # Full study
    if study_type in {2, 4}:
        for data in grad_param.values():
            if not isinstance(data[4], float):
                valid = _fail(f"Primary reach factor is not in the correct format.")
            elif data[4] < 1 or data[4] > 10:
                valid = _fail(f"Primary reach factor is out of bounds (1, 10).")
            if not isinstance(data[5], float):
                valid = _fail(f"Back-up reach factor is not in the correct format.")
            elif data[5] < 1 or data[5] > 10:
                valid = _fail(f"Back-up reach factor is out of bounds (1, 10).")
            if not isinstance(data[6], float):
                valid = _fail(f"Primary slowest clearing time is not in the correct format.")
            elif data[6] < 0.1 or data[6] > 10:
                valid = _fail(f"Primary slowest clearing time is out of bounds (0.1, 10).")
            if not isinstance(data[7], float):
                valid = _fail(f"Back-up slowest clearing time is not in the correct format.")
            elif data[7] < 0.1 or data[7] > 10:
                valid = _fail(f"Back-up slowest clearing time is out of bounds (0.1, 10).")
            if not isinstance(data[8], float):
                valid = _fail(f"Grading margin for mechanical is not in the correct format.")
            elif data[8] < -1 or data[8] > 10:
                valid = _fail(f"Grading margin for mechanical relays is out of bounds (-1, 10).")
            if not isinstance(data[9], float):
                valid = _fail(f"Grading margin for static relays is not in the correct format.")
            elif data[9] < -1 or data[9] > 10:
                valid = _fail(f"Grading margin for static relays is out of bounds (-1, 10).")
            if not isinstance(data[10], float):
                valid = _fail(f"Grading margin for digital relays is not in the correct format.")
            elif data[10] < -1 or data[10] > 10:
                valid = _fail(f"Grading margin for digital relays is out of bounds (-1, 10).")
            if not isinstance(data[12], float):
                print(f"CB interrupt time is not in the correct format.")
                valid = _fail(f"Grading margin for fuses is not in the correct format.")
            elif data[12] < 0 or data[12] > 10:
                print(f"CB interrupt time is out of bounds (0, 10).")
                valid = _fail(f"Grading margin for fuses is not in the correct format.")
            if not isinstance(data[13], float):
                valid = _fail(f"Relay coordination optimization iterations is not in the correct format.")
            elif data[13] < 1 or data[13] > 1000000:
                valid = _fail(f"Relay coordination optimization iterations is out of bounds (1, 1,000,000).")

    if study_type in {2, 4, 6}:
        for data in grad_param.values():
            if not isinstance(data[11], float):
                valid = _fail(f"Grading margin for fuses is not in the correct format.")
            elif data[11] < -1 or data[11] > 10:
                valid = _fail(f"Grading margin for fuses is out of bounds (-1, 10).")
    return valid


def _fail(message):
    print(message)
    return False

