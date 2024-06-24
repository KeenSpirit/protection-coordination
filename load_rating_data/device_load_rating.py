import sys
from importlib import reload
import load_rating_data.load_rating_data as lrd
from input_files import data_inputs as di
reload(lrd)

def get_load_rating(app, all_devices, instructions, grad_param):


    df = di.netplan_extract()

    feeder = instructions[0]
    study_type = instructions[1]
    get_netplan = grad_param['Enter feeder rating and load forecast manually']

    feeder_device = [device for device in all_devices if device.name == feeder][0]
    if get_netplan == 'No':
        rating_sd = df.loc[df['Feeder'] == feeder, 'Rating SD']
        rating_sn = df.loc[df['Feeder'] == feeder, 'Rating SN']
        max_load = df.loc[df['Feeder'] == feeder, 'Maximum load']
        if rating_sd.empty or rating_sd.empty or rating_sd.empty:
            app.PrintPlain("Feeder load and rating data could not be retrieved from Netplan. "
                           "Please untick the 'Obtain feeder rating data from Netplan' check box in the Instruction tab "
                           "of the input file and manually enter the feeder load and rating data in the Grading "
                           "Parameters sheet")
            sys.exit(0)
        rating_value = min(rating_sd.values[0], rating_sn.values[0])
        load_value = max_load.values[0]
        if isinstance(rating_value, float):
            feeder_device.netdat.rating = rating_value
        if isinstance(load_value, float):
            feeder_device.netdat.load = load_value
    if study_type in {2, 4, 6}:
        if feeder_device.netdat.ds_capacity > 0:
            feeder_util = feeder_device.netdat.load / feeder_device.netdat.ds_capacity
        else:
            feeder_util = 0
        for device in all_devices:
            device.netdat.load = device.netdat.ds_capacity * feeder_util

