from pathlib import Path
import pandas as pd
from typing import Any


def save_dataframe(app, study_type, gen_info: list, all_devices: list,
                   setting_report: dict, detailed_fls: list):
    """ saves the dataframe in the user directory.
    If the user is connected through citrix, the file should
    be saved local users PowerFactoryResults folder
    """
    import os
    import time

    date_string = time.strftime("%Y%m%d-%H%M%S")
    filename = 'Protection Study Results ' + date_string + ".xlsx"

    home_path = str(Path.home())
    save_path_1 = '\\\\client\\' + home_path[0] + '$' + home_path[2:] + '\\RelayCoordinationStudies'
    if Path(save_path_1).is_dir():
        # save the output file to the user's home directory
        filepath = os.path.join(save_path_1, filename)
        app.PrintPlain("Output file saved to " + filepath)
    else:
        # When running a local installation of PowerFactory
        save_path_2 = home_path + '\\RelayCoordinationStudies'
        filepath = os.path.join(save_path_2, filename)
        app.PrintPlain("Output file saved to " + filepath)

    feeder_name, study_type, grid_data_df, study_results, df_device_list = (
        format_results(study_type, gen_info, all_devices, setting_report, detailed_fls))

    #TODO: use Excel conditional formatting rules
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # General Information sheet
        grid_data_df.to_excel(writer, sheet_name='General Information', startrow=9, index=False)
        workbook = writer.book
        worksheet = workbook['General Information']
        worksheet['A1'] = feeder_name
        worksheet['A2'] = study_type
        worksheet['A4'] = 'Script Run Date'
        worksheet['A5'] = date_string
        worksheet['A8'] = 'External Grid Data:'

        # Study Results sheet
        study_results.to_excel(writer, sheet_name='Study Results', index=False)

        # Detailed fault levels sheet
        for i, device in df_device_list:
            count = i * 5 - 4
            device.to_excel(writer, sheet_name='Detailed fault levels', startrow=3, startcol=count)


def format_results(study_type, gen_info, all_devices, setting_report, detailed_fls):
    """

    :param study_type:
    :param gen_info:
    :param all_devices:
    :param setting_report:
    :param detailed_fls:
    :return:
    """

    # Format 'General Information' data
    instructs_lookup = {
        1: 'Full study (fault levels + relay coordination + grading diagram)',
        2: 'Fault level study only',
        3: 'Relay coordination study only',
        4: 'Create a grading diagram only',
        5: 'Line fuse study'
    }
    feeder_name = gen_info[0]
    study_type = instructs_lookup[study_type]
    grid_data = gen_info[1]
    grid_data_df = pd.DataFrame(grid_data)

    # Format 'Study Results' data
    formatted_dev = format_devices(all_devices)
    formatted_dev_pd = pd.DataFrame.from_dict(formatted_dev)
    formatted_dev_pd = formatted_dev_pd.set_index('Site Name').transpose()
    setting_report_pd = pd.DataFrame.from_dict(setting_report)
    study_results = pd.concat([formatted_dev_pd, setting_report_pd])
    study_results = study_results.fillna("")

    # Format 'Detailed fault levels' data
    pg_max_all, phase_max_all, pg_min_all, phase_min_all, section_loads, max_tr_pg_fls, max_tr_p_fls = detailed_fls
    device_list = [device for device in pg_max_all.keys]
    df_device_list = []
    for device in device_list:
        dev_dict = {
            'Max PG fault': pg_max_all[device],
            'Max 3P fault': phase_max_all[device],
            'Min PG fault': pg_min_all[device],
            'Min 2P fault': phase_min_all[device]
        }
        df = pd.DataFrame(dev_dict)
        df_device_list.append(df)
    # TODO: the above dataframes need to be sorted from largest fault level to smallest
    # TODO: output section_loads, max_tr_pg_fls, max_tr_p_fls variables

    return feeder_name, study_type, grid_data_df, study_results, df_device_list


def format_devices(all_devices: list) -> list[dict]:
    """

    :param all_devices:
    :return:
    """

    def check_att(dev, attribute):
        if hasattr(dev, attribute):
            return dev.attribute
        else:
            return ''

    device_list = []
    for device in all_devices:
        device_dic = {
            'Site Name': device.name,
            'Voltage (kV)': device.netdat.voltage,
            'Current split n:1': device.netdat.i_split,
            'DS capacity  (kVA)': device.netdat.ds_capacity,
            'Max 3p FL': device.netdat.max_3p_fl,
            'Max PG FL': device.netdat.max_pg_fl,
            'Min 2P FL': device.netdat.min_2p_fl,
            'Min PG FL': device.netdat.min_pg_fl,
            'Max DS TR (Site name)': device.netdat.tr_max_name,
            'Max TR size (kVA)': device.netdat.max_tr_size,
            'Max TR fuse': device.netdat.max_tr_fuse,
            'TR Max 3P ': device.netdat.tr_max_3p,
            'TR max PG': device.netdat.tr_max_pg,
            'DS devices': device.netdat.downstream_devices,
            'BU device': device.netdat.upstream_devices,
            'Device': device.manufacturer.__name__,
            'Status': device.relset.status,
            'CT saturation': check_att(device, 'ct.saturation'),
            'CT composite error': check_att(device, 'ct.ect'),
            'CT ratio': check_att(device, 'ct.ratio'),
            'load (A)': device.netdat.load,
            'Rating  (A)': device.netdat.rating,
            'OC pick up': check_att(device, 'relset.oc_pu'),
            'OC TMS': check_att(device, 'relset.oc_tms'),
            'OC Curve': check_att(device, 'relset.oc_curve'),
            'OC Hiset': check_att(device, 'relset.oc_hiset'),
            'OC Min time (s)': check_att(device, 'relset.oc_min_time'),
            'OC Hiset 2': check_att(device, 'relset.oc_hiset2'),
            'OC Min time 2 (s)': check_att(device, 'relset.oc_min_time2'),
            'EF pick up': check_att(device, 'relset.ef_pu'),
            'EF TMS': check_att(device, 'relset.ef_tms'),
            'EF Curve': check_att(device, 'relset.ef_curve'),
            'EF Hiset': check_att(device, 'relset.ef_hiset'),
            'EF Min time (s)': check_att(device, 'relset.ef_min_time'),
            'EF Hiset 2': check_att(device, 'relset.ef_hiset2'),
            'EF Min time 2 (s)': check_att(device, 'relset.ef_min_time2')
        }
        device_list.append(device_dic)

    return device_list
