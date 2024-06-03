import shutil
import os
from pathlib import Path
import time
import xlwings as xw
import pandas as pd


curve_maps = {'SI': 2, 'VI': 3, 'EI': 4}
set_stat_maps = {'Existing': 1, 'Required': 2, 'New': 3}
relay_maps = {
            '_2TJM10': 2,
            '2TJM10': 2,
            'Argus_1': 3,
            'Argus_2': 4,
            'CDG11': 5,
            'CDG31': 6,
            'CDG66': 7,
            'KCEG': 8,
            'KCGG': 9,
            'Microtrip': 10,
            'NilStat': 11,
            'NOJA': 12,
            'NOJA_01': 12,
            'NOJA_10': 12,
            'CAPM2': 13,
            'CAPM4': 14,
            'CAPM5': 14,
            'ADVC2': 14,
            'ADVC3': 14,
            'P123': 15,
            'P142': 16,
            'P643': 17,
            'PBO': 18,
            'SEL351-1': 19,
            'SEL351_1': 19,
            'SEL351-6': 20,
            'SEL351_6': 20,
            'SEL351A': 21,
            'SPAJ140C': 22,
            'WHC07': 23,
            '1000_80A_Air': 27,
            '1000_80A_Oil': 28,
            '1500 air ins 100A SIBA Max': 29,
            '1500 air ins 100A SIBA Min': 30,
            '1500_100A_Air': 31,
            '1500_120A_oil': 32,
            '15Kmax': 33,
            '15TMax': 34,
            '15TMin': 35,
            '20Kmax': 36,
            '20Kmin': 37,
            '25Kmax': 38,
            '25Kmin': 39,
            '300_35.5A_Air': 40,
            '300_40_Oil': 41,
            '40Kmax': 42,
            '40Kmin': 43,
            '500_40A_Air': 44,
            '500_50A_Oil': 45,
            '50AKEBXO': 46,
            '50Kmax': 47,
            '50Kmin': 48,
            '65Kmax': 49,
            '65N': 50,
            '65Tmax': 51,
            '750_63A_Air': 52,
            '750_63A_Oil': 53,
            '80KMax': 54,
            '8Tmax': 55,
            '8Tmin': 56,
            'SilvEur_36SWG_2000/5': 57,
            'SilvEur_36SWG_3000/5': 58,
            'VIP30_140A': 59,
            'VIP30_170A': 60,
            'VIP30_200A': 61,
            'XWS250NJmax': 62,
            'XWS250NJmin': 63,
            }


def copy_excel_file(original_file, new_file):
    """

    :param original_file:
    :param new_file:
    :return:
    """

    # Copy the file using shutil to preserve macros
    shutil.copyfile(original_file, new_file)
    home_path = str(Path.home())
    old_path = f"E:\Python\_python_work\grading_diagrams\{new_file}"
    new_path = f"{home_path}\{new_file}"
    shutil.move(old_path, new_path)


def create_excel_files():
    """

    :return:
    """

    home_path = str(Path.home())

    date_string = time.strftime("%Y%m%d-%H%M%S")
    oc_relay_coordination = date_string + " OC Relay Grading Diagram.xlsm"
    ef_relay_coordination = date_string + " EF Relay Grading Diagram.xlsm"
    copy_excel_file(f'{home_path}/Relay Grading Template File.xlsm', oc_relay_coordination)
    copy_excel_file(f'{home_path}/Relay Grading Template File.xlsm', ef_relay_coordination)
    return oc_relay_coordination, ef_relay_coordination


def relay_settings(workbook, input, output, fault_type: str):
    """

    :param workbook:
    :param input:
    :param output:
    :param fault_type:
    :return:
    """

    relay_voltage = 11

    if len(output) > 11:
        raise Exception("More relays (> 10) than can fit in workbook")

    relay_sheets = [
        'Relay 1', 'Relay 2', 'Relay 3', 'Relay 4', 'Relay 5', 'Relay 6', 'Relay 7', 'Relay 8', 'Relay 9', 'Relay 10'
    ]

    if fault_type == 'OC':
        n = 3
        m = 21
        earth_fault_curve = False
    else:
        n = 10  # type == 'EF'
        m = 22
        earth_fault_curve = True
    count = 0
    for relay, data in output.items():
        print(f'updating {relay}')
        if relay == "Unnamed: 0":
            continue
        set_stat_string = set_stat_maps[data[2]]
        out_curve_string = curve_maps[data[n + 2]]
        if data[0][:4] in ['NOJA', 'CAPM', 'ADVC']:
            ct_pri = 2000
            ct_sec = 1
        else:
            ct_pri = data[33] * 5
            ct_sec = 5

        relay_sheet = relay_sheets[count]
        sheet = workbook.sheets[relay_sheet]
        sheet.range((5, 2)).value = relay                               # Sheet name
        sheet.range((16, 6)).value = True                               # Pickup Confirmed
        sheet.range((5, 6)).value = earth_fault_curve                   # Earth fault curve
        sheet.range((6, 2)).value = relay_voltage                       # Voltage
        sheet.range((7, 2)).value = ct_pri                              # Primary CT turns
        sheet.range((7, 4)).value = ct_sec                                   # Secondary CT turns
        sheet.range((8, 2)).value = data[n]                             # Element pick-up
        sheet.range((10, 2)).value = data[n+1]                          # Element TMS
        sheet.range((13, 2)).value = data[n+3]                          # Hiset
        sheet.range((14, 2)).value = data[n+4]                          # Min time
        # sheet.range((16, 2)).value = None                             # Definite time
        sheet.range((20, 2)).value = 4                                  # Finish curve at (sec)
        sheet.range((21, 2)).value = round((data[m] * 1.3)/5)*5         # Finish curve at (A)
        sheet.range((23, 2)).value = set_stat_string                    # Setting status
        sheet.range((25, 2)).value = data[n+5]                          # 2nd hiset
        sheet.range((26, 2)).value = data[n+6]                          # 2nd min time
        # sheet.range((28, 2)).value = None                             # Lowest Current
        # sheet.range((29, 2)).value = None                             # Lowest Operating Time
        sheet.range((3, 7)).value = count + 1                           # Curve colour"""
        sheet.range((4, 2)).value = relay_maps[data[0]]                 # Relay name
        sheet.range((11, 2)).value = out_curve_string                   # Curve type
        try:
            sheet.name = relay
        except:
            pass
        count += 1

    """count = 0
    for relay, data in output.items():
        if relay == "Unnamed: 0":
            continue
        print(relay_sheets[count])
        print(relay)
        relay_sheet = relay_sheets[count]
        try:
            sheet = workbook.sheets[relay_sheet]
            sheet.name = relay
        except:
            pass
        count += 1"""

    refresh_curves = 'Sheet3.RefreshCurves_Click'
    workbook.macro(refresh_curves).run()

    workbook.save()

    # Existing settings
    # Curve type
    """for relay, data in input.items():
        if relay == " name":
            continue
        in_curve_string = curve_maps[data[n + 2]]
        if data[2] == 'Existing':
            relay_sheet = relay_sheets[count]
            sheet = workbook.sheets[relay_sheet]
            
            sheet.range((35, 4)).value = data[19]*5                     # Primary CT turns
            sheet.range((36, 2)).value = 5                              # Secondary CT turns
            sheet.range((36, 2)).value = data[n]                        # Element pick-up
            sheet.range((38, 2)).value = data[n+1]                      # Element TMS
            sheet.range((39, 2)).value = in_curve_string                # Curve type
            sheet.range((40, 2)).value = data[n+3]                      # Hiset
            sheet.range((41, 2)).value = data[n+4]                      # Min time
            sheet.range((42, 2)).value = data[n+5]                      # 2nd hiset
            sheet.range((43, 2)).value = data[n+6]                      # 2nd min time
            # sheet.range((44, 2)).value = relay_maps[data[0]]          # Lowest Operating Time

    workbook.save()
    workbook.close()
    """
    # TODO: Grading Times
    # Get downstream relay with lowest min fault level
    """def split_string(object):
        if type(object) == str:
            return object.split(', ')
        else:
            return [None]

    ds_relays = split_string(data[31])
    min_fl = 999
    min_relay = {}
    if ds_relays:
        for ds_relay in ds_relays:
            datas = output[ds_relay]
            relay_min_fl = datas[j]
            if relay_min_fl < min_fl:
                min_fl = relay_min_fl
                min_relay = {ds_relay: relay_min_fl}
    sheet.cell(column=9, row=7, value=)                         # relay fl
    sheet.cell(column=2, row=23, value=)                        # Setting status
    sheet.cell(column=2, row=25, value=)                       # 2nd hiset
    sheet.cell(column=2, row=26, value=)                       # 2nd min time"""

    # TODO: Set Substation/Feeder name, Reference Voltage, Graph Starting Current


def faults_sheet(workbook, output, fault_type: str):
    """

    :param workbook:
    :param input:
    :param output:
    :param fault_type:
    :return:
    """

    print("Adding faults to grading diagram")
    faults = workbook.sheets["Faults"]

    if fault_type == 'OC':
        n = 21
        max_string = " 3P max"
        min_string = " 2P min"
    else:
        n = 22  # type == 'EF'
        max_string = " PG max"
        min_string = " PG min"

    next_row = 3
    count = 1

    for relay, data in output.items():
        if relay == "Unnamed: 0":
            continue
        faults.range((next_row, 2)).value = f"{relay} {max_string}"
        faults.range((next_row + 1, 2)).value = data[n]                                 # Fault type name
        faults.range((next_row + 1, 4)).value = 5                                       # Time
        #faults.range((next_row, 7)).value = count                                       # Colour
        faults.range((next_row + 1, 7)).value = count + 1                               # Relay

        faults.range((next_row + 4, 2)).value = f"{relay} {min_string}"                 # Fault type name
        faults.range((next_row + 5, 2)).value = data[n+2]                               # Fault current
        faults.range((next_row + 5, 4)).value = 5                                       # Time
        #faults.range((next_row + 4, 7)).value = count                                   # Colour
        faults.range((next_row + 5, 7)).value = count + 1                               # Relay
        next_row += 8
        count += 1

    workbook.save()
    workbook.close()


def create_diagrams(all_devices):
    """
    relay_grading_template: Excel relay grading template file. Normally stored on network drive.
    input_file: Excel file of data io_template_files created by user. Stored in user's home directory
    Relay Coordination Results: Excel file produced by the relay coordination program. Stored in user's home directory
    Relay Grading Diagram
    """

    app = xw.App(visible=True)

    oc_relay_coordination, ef_relay_coordination = create_excel_files()

    inputs_path = ('E:\Python\_python_work\protection_coordination\inputs')
    output_path = (str(Path.home()))

    input_dataframe = pd.read_excel(f'{inputs_path}/input.xlsx', sheet_name='Data')
    input_file = input_dataframe.to_dict('list')
    output_dataframe = pd.read_excel(f'{output_path}/Relay Coordination Results.xlsx', sheet_name='Results')
    output_dataframe.replace('OFF', '', inplace=True)
    output_file = output_dataframe.to_dict('list')

    ef_workbook = xw.Book(f'{output_path}/{ef_relay_coordination}')
    # oc_workbook = xw.Book(f'{output_path}/{oc_relay_coordination}')

    #relay_settings(ef_workbook, input_file, output_file, "EF")
    # relay_settings(oc_workbook, input_file, output_file, "OC")

    faults_sheet(ef_workbook, output_file, "EF")
    # faults_sheet(oc_workbook, output_file, "OC")

    # Close Excel
    app.quit()


if __name__ == '__main__':
    main()