from input_files.input_file import instructions, all_devices
import load_rating_data as lrd

def get_load_rating():

    feeder = instructions[0]
    study_type = instructions[1]
    get_netplan = instructions[2]

    feeder_device = [device for device in all_devices if device.name == feeder][0]
    if get_netplan:
        rating_value, load_value = lrd.query_netplan()
        feeder_device.netdat.rating = rating_value
        feeder_device.netdat.load = load_value
    if study_type in {2, 4, 6}:
        feeder_util = feeder_device.netdat.load / feeder_device.netdat.ds_capacity
        for device in all_devices:
            device.netdat.load = device.netdat.ds_capacity * feeder_util
