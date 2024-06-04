"""
fault_level_study
relay_coordination_study
line fuse study
grading_diagram
"""

import time
import sys
import powerfactory as pf
from input_files import input_file
from load_rating_data import device_load_rating as dlr
from fault_level_data import fault_data
from relay_coordination import relay_coord as rc
from grading_diagram import grading_diagrams as gd
from line_fuse_study import study_line_fuse as slf
import save_dataframe as save


def main():
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

    # Load the data from the input file into the relay classes.
    instructions, all_devices, grading_parameters = input_file.get_input()
    feeder = instructions[0]
    study_type = instructions[1]
    app = pf.GetApplication()

    # Assess what type of study is required.
    if study_type == 1:
        print("No study type selected from the relay_coordination_input_file.xlsm Instructions sheet")
        print("Please review the Instructions sheet and run the script again")
        sys.exit()
    elif study_type == 2:
        print("User has selected a full study (fault levels + relay coordination + grading diagram)")
        gen_info, all_devices, detailed_fls = fault_data.fault_study(app, all_devices, feeder)
        dlr.get_load_rating()
        all_devices, setting_report = rc.relay_coordination(all_devices)
        gd.create_diagrams(all_devices)
    elif study_type == 3:
        print("User has selected a fault level study only")
        setting_report = None
        gen_info, all_devices, detailed_fls = fault_data.fault_study(app, all_devices, feeder)
    elif study_type == 4:
        print("User has selected a relay coordination study only")
        gen_info, detailed_fls = None, None
        dlr.get_load_rating()
        all_devices, setting_report = rc.relay_coordination(all_devices)
    elif study_type == 5:
        print("User has selected Create a Grading diagram only")
        gen_info, detailed_fls, setting_report = None, None, None
        gd.create_diagrams(all_devices)
    else:
        print("User has selected a line fuse study")
        dlr.get_load_rating()
        gen_info, detailed_fls = None, None
        setting_report = slf.line_fuse_study(all_devices)

    save.save_dataframe(app, study_type, gen_info, all_devices, setting_report, detailed_fls)


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    run_time = round(end - start, 6)
    print(f"Script run time: {run_time} seconds")