import sys
from typing import Tuple, List, Any

import pandas as pd
from pathlib import Path
from device_data import eql_relay_data as re
from device_data import eql_fuse_data as fu
from device_data.eql_fuse_data import LineFuse, fuse_list
from device_data.eql_relay_data import ProtectionRelay

status_lookup = {1: False, 2: 'Existing', 3: 'Required', 4: 'New'}

voltage_lookup = {1: False, 2: 11, 3: 33, 4: 110}

curve_lookup = {1: False, 2: "SI", 3: "VI", 4: "EI"}

device_lookup = {
    1: False,
    2: '2TJM10',
    3: 'Argus 1',
    4: 'Argus 2',
    5: 'CDG11',
    6: 'CDG31',
    7: 'CDG66',
    8: 'KCEG',
    9: 'KCGG',
    10: 'NOJA RC01',
    11: 'NOJA RC10',
    12: 'CAPM2',
    13: 'CAPM4',
    14: 'CAPM5',
    15: 'ADVC2',
    16: 'ADVC3',
    17: 'P123',
    18: 'P142',
    19: 'P643',
    20: 'SEL351-1',
    21: 'SEL351-6',
    22: 'SEL351A',
    23: 'SPAJ140C',
    24: 'REF615',
    25: 'RED615',
    26: 'WHC07',
    27: 'Unknown fuse',
    28: '8Tmax',
    29: '8Tmin',
    30: '15Kmax',
    31: '15TMax',
    32: '15TMin',
    33: '20Kmax',
    34: '20Kmin',
    35: '25Kmax',
    36: '25Kmin',
    37: '40Kmax',
    38: '40Kmin',
    39: '50Kmax',
    40: '50Kmin',
    41: '65Kmax',
    42: '65N',
    43: '65Tmax',
    44: '80KMax',
}


def get_input() -> tuple[list[Any], list[ProtectionRelay | LineFuse], dict]:
    """
    Get study instructions
    Load input data into relay classes
    """

    user = Path.home().name
    basepath = Path('//client/c$/LocalData') / user

    if basepath.exists():
        clientpath = basepath / Path('RelayCoordinationStudies')
    else:
        clientpath = Path('c:/LocalData') / user / Path('RelayCoordinationStudies')

    sheet_names = ['Instructions', 'Inputs', 'Grading Parameters']
    data = pd.read_excel(
        f'{clientpath}/relay_coordination_input_file.xlsm', sheet_name=sheet_names, engine='openpyxl'
    )
    instruction = data['Instructions']
    inputs = data['Inputs']
    grad_param = data['Grading Parameters']

    feeder_cell = instruction.at[11, 'B']
    instructions_cell = instruction.at[14, 'B']
    netplan_cell = instruction.at[18, 'B']
    instructions = [feeder_cell, instructions_cell, netplan_cell]

    inputs = inputs.loc[:, ~inputs.columns.str.contains('Unnamed|^$')]
    # Remove first column
    inputs = inputs.iloc[:, 1:]
    inputs = inputs.fillna("")
    # Transform dataframe into dictionary
    inputs = inputs.to_dict('list')

    grad_param = grad_param.loc[:, ~grad_param.columns.str.contains('Unnamed|^$')]
    # remove first column
    grad_param = grad_param.iloc[:, 1:]
    grad_param = grad_param.fillna("")
    # Transform dataframe into dictionary
    grad_param = grad_param.to_dict('list')

    def split_string(object):
        if type(object) == str:
            return object.split(', ')
        else:
            return [None]

    all_devices = []
    for device, data in inputs.items():
        # If device is a relay:
        if 2 <= data[0] <= 26:
            parameters = [device, re.relay_lookup[data[0]], grad_param['CB interrupt time']]
            settings = [status_lookup[data[1]], data[21], data[22], curve_lookup[data[23]], data[24], data[25],
                        data[26], data[27], data[28], data[29], curve_lookup[data[30]], data[31], data[32], data[33],
                        data[34]]
            network = [voltage_lookup[data[2]], data[3], data[22], data[21], data[23], data[24], data[25], data[26],
                       data[27], data[28], data[29], data[30], data[31], split_string(data[32]), split_string(data[33])]
            ct_data = [data[18], data[19], data[20]]
            new_relay = re.ProtectionRelay(parameters, settings, network, ct_data)
            all_devices.append(new_relay)
        # If device a fuse:
        elif data[0] > 26:
            parameters = [device]
            settings = [status_lookup[data[1]], device_lookup[data[0]]]
            network = [voltage_lookup[data[2]], data[3], data[22], data[21], data[23], data[24], data[25], data[26],
                       data[27], data[28], data[29], data[30], data[31], split_string(data[32]), split_string(data[33])]
            new_fuse = fu.LineFuse(parameters, settings, network)
            all_devices.append(new_fuse)
        else:
            print("A device value is missing from the relay_coordination_input_file.xlsm Inputs sheet (row 2)")
            print("Please review the input file and run the script again")
            sys.exit()

    # Add upstream and downstream device. These can only be added after all device objects are created
    for device in all_devices:
        downstream_objects = []
        upstream_objects = []
        downstream_devices = device.netdat.downstream_devices
        upstream_devices = device.netdat.upstream_devices
        for relay_1 in all_devices:
            if relay_1.name in downstream_devices:
                downstream_objects.append(relay_1)
        device.netdat.downstream_devices = downstream_objects
        for relay_2 in all_devices:
            if relay_2.name in upstream_devices:
                upstream_objects.append(relay_2)
        device.netdat.upstream_devices = upstream_objects

    return instructions, all_devices, grad_param


instructions, all_devices, grad_param = get_input()

class GradingParameters:
    """"""

    def __init__(self):
        """Initialise attributes"""
        self.feeder_rat_per: str = grad_param['Feeder rating period']
        self.forecast_years_poe = float(grad_param['Load forecast years POE'])
        self.forecast_years = float(grad_param['Load forecast years'])
        self.consider_clp: str = grad_param['Consider cold load pickup']
        self.pri_reach_factor = float(grad_param['Primary reach factor'])
        self.bu_reach_factor = float(grad_param['Back-up reach factor'])
        self.pri_slowest_clear = float(grad_param['Primary slowest clearing time (ms)'])
        self.bu_slowest_clear = float(grad_param['Back-up slowest clearing time (ms)'])
        self.mechanical_grading = float(grad_param['Electro-mechanical relay'])
        self.static_grading = float(grad_param['Static relay'])
        self.digital_grading = float(grad_param['Digital/numeric relay'])
        self.fuse_grading = float(grad_param['Fuse'])
        self.cb_interrupt = float(grad_param['CB interrupt time'])
        self.optimization_iter = int(grad_param['Relay coordination optimization iterations'])


