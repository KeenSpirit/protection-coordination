"""
fault_level_study
relay_coordination_study
line fuse study
grading_diagram
"""

from importlib import reload
import time
import sys
import powerfactory as pf
from helper_funcs.script_helper import *
from input_files import input_file, data_validation as dv
from load_rating_data import device_load_rating as dlr
from fault_level_data import fault_data
from relay_coordination import relay_coord as rc
from grading_diagram import grading_diagrams as gd
from line_fuse_study import study_line_fuse as slf
import save_dataframe as save

reload(fault_data)
reload(input_file)
reload(save)
reload(dlr)
reload(rc)
reload(dv)

def main(app):
    """

    All documents are stored and saved to home/RelayCoordinationStudies
    Input file (template):
    - Relay data input sheet

    New Excel file created:
    - Protection Study Results
    New Excel files created:
    - EF grading_diagram
    - OC grading_diagram
    """

    # Retrieve data from the input file
    instructions, inputs, grad_param = input_file.get_input()
    # Validate all input data
    dv.validate_data(app, instructions, inputs, grad_param)
    feeder = instructions[0]
    study_type = instructions[1]

    # Load the data into the device classes.
    all_devices = input_file.update_devices(grad_param, inputs)

    # Assess the type of study required.
    if study_type == 1:
        app.PrintPlain("No study type selected from the relay_coordination_input_file.xlsm Instructions sheet")
        app.PrintPlain("Please review the Instructions sheet and run the script again")
        sys.exit()
    elif study_type == 2:
        app.PrintPlain("User has selected a full study (fault levels & relay coordination & grading diagram)")
        gen_info, all_devices, detailed_fls = fault_data.fault_study(app, all_devices, feeder)
        dlr.get_load_rating(app, all_devices, instructions, grad_param)
        all_devices, setting_report = rc.relay_coordination(all_devices)
        gd.create_diagrams(all_devices)
    elif study_type == 3:
        app.PrintPlain("User has selected a fault level study only")
        setting_report = None
        gen_info, all_devices, detailed_fls = fault_data.fault_study(app, all_devices, feeder)
    elif study_type == 4:
        app.PrintPlain("User has selected a relay coordination study only")
        gen_info, detailed_fls = None, None
        dlr.get_load_rating(all_devices, instructions, grad_param)
        all_devices, setting_report = rc.relay_coordination(all_devices)
    elif study_type == 5:
        app.PrintPlain("User has selected to create a grading diagram only")
        gen_info, detailed_fls, setting_report = None, None, None
        gd.create_diagrams(all_devices)
    else:
        app.PrintPlain("User has selected a line fuse study")
        dlr.get_load_rating(all_devices, instructions, grad_param)
        gen_info, detailed_fls = None, None
        setting_report = slf.line_fuse_study(all_devices)

    save.save_dataframe(app, study_type, gen_info, all_devices, setting_report, detailed_fls)


if __name__ == '__main__':
    start = time.time()

    app = pf.GetApplication()
    app.SetEnableUserBreak(1)
    app.ClearOutputWindow()

    with project_manager(app):
        main(app)

    end = time.time()
    run_time = round(end - start, 6)
    app.PrintPlain(f"Script run time: {run_time} seconds")