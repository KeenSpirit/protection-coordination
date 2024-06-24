from typing import Union, Any
from importlib import reload
import pandas as pd
from pathlib import Path
import device_data.eql_relay_data as re
import device_data.eql_fuse_data as fu
from device_data.eql_fuse_data import fuse_list
from input_files import lookup_tables as lt

reload(fu)


def get_input() -> tuple[list[Any], Any, dict]:
    """
    Get study instructions
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
    grad_param_pd = data['Grading Parameters']

    feeder_cell = instruction.at[9, 'INSTRUCTIONS:']
    instructions_cell = instruction.at[12, 'INSTRUCTIONS:']
    instructions = [feeder_cell, instructions_cell]
    inputs = inputs.loc[:, ~inputs.columns.str.contains('Unnamed|^$')]
    # Remove first column
    inputs = inputs.iloc[:, 1:]
    inputs = inputs.fillna("")
    # Transform dataframe into dictionary
    inputs = inputs.to_dict('list')
    grad_param = {}
    for n in [i for i in range(0, 5)] + [i for i in range(6, 12)] + [i for i in range(13, 16)]:
        grad_param[grad_param_pd.at[n, 'Parameter']] = grad_param_pd.at[n, 'Value']
    grad_param['Consider cold load pickup'] = lt.clp_lookup[grad_param['Consider cold load pickup']]
    grad_param['Enter feeder rating and load forecast manually'] = (
        lt.clp_lookup)[grad_param['Enter feeder rating and load forecast manually']]

    return instructions, inputs, grad_param


def update_devices(grad_param, inputs) -> list[Union[re.ProtectionRelay, fu.LineFuse]]:

    def split_string(object):
        if type(object) is str:
            return object.split(', ')
        else:
            return [None]

    all_devices = []
    for device, data in inputs.items():
        # If device is a relay:
        if 2 <= data[0] <= 26:
            parameters = [
                device, re.relay_lookup[data[0]],               # Device name
                grad_param['CB interrupt time']                 # CB interrupt time
            ]
            settings = [
                lt.status_lookup[data[1]],                      # Status
                data[19],                                       # OC pick up
                data[20],                                       # OC TMS
                lt.curve_lookup[data[21]],                      # OC Curve
                data[22],                                       # OC Hiset
                data[23],                                       # OC Min time (s)
                data[24],                                       # OC Hiset 2
                data[25],                                       # OC Min time 2 (s)
                data[26],                                       # EF pick up
                data[27],                                       # EF TMS
                lt.curve_lookup[data[28]],                      # EF Curve
                data[29],                                       # EF Hiset
                data[30],                                       # EF Min time (s)
                data[31],                                       # EF Hiset 2
                data[32]                                        # EF Min time 2 (s)
            ]
            network = [
                lt.voltage_lookup[data[2]],                     # Voltage (kV)
                data[3],                                        # Current split n:1
                '',                                             # Load
                '',                                             # Rating
                data[4],                                        # DS capacity  (kVA)
                data[5],                                        # Max 3p FL
                data[6],                                        # Max PG FL
                data[7],                                        # Min 2P FL
                data[8],                                       # Min PG FL
                data[9],                                       # Max DS TR (Site name)
                data[10],                                       # Max TR size (kVA)
                fuse_list[data[11]],                            # Max TR fuse
                data[12],                                       # TR Max 3P
                data[13],                                       # TR max PG
                split_string(data[14]),                         # DS devices
                split_string(data[15])                          # BU devices
            ]
            ct_data = [
                data[16],                                       # CT saturation
                data[17],                                       # CT composite error
                data[18]                                        # CT ratio
            ]
            new_relay = re.ProtectionRelay(parameters, settings, network, ct_data)
            all_devices.append(new_relay)
        # If device a fuse:
        else:  # data[0] > 26:
            parameters = [device]
            settings = [
                lt.status_lookup[data[1]],                      # Status
                lt.device_lookup[data[0]]                       # Fuse size
            ]
            network = [
                lt.voltage_lookup[data[2]],                     # Voltage (kV)
                data[3],                                        # Current split n:1
                '',                                             # Load
                '',                                             # Rating
                data[4],                                        # DS capacity  (kVA)
                data[5],                                        # Max 3p FL
                data[6],                                        # Max PG FL
                data[7],                                        # Min 2P FL
                data[8],                                       # Min PG FL
                data[9],                                       # Max DS TR (Site name)
                data[10],                                       # Max TR size (kVA)
                fuse_list[data[11]],                            # Max TR fuse
                data[12],                                       # TR Max 3P
                data[13],                                       # TR max PG
                split_string(data[14]),                         # DS devices
                split_string(data[15])                          # BU devices
            ]
            new_fuse = fu.LineFuse(parameters, settings, network)
            all_devices.append(new_fuse)

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
    return all_devices


class GradingParameters:
    """"""

    def __init__(self, grad_param):
        """Initialise attributes"""
        self.consider_clp: str = grad_param['Consider cold load pickup']
        self.pri_reach_factor = float(grad_param['Primary reach factor'])
        self.bu_reach_factor = float(grad_param['Back-up reach factor'])
        self.pri_slowest_clear = float(grad_param['Primary slowest clearing time (s)'])
        self.bu_slowest_clear = float(grad_param['Back-up slowest clearing time (s)'])
        self.mechanical_grading = float(grad_param['Electro-mechanical relay'])
        self.static_grading = float(grad_param['Static relay'])
        self.digital_grading = float(grad_param['Digital/numeric relay'])
        self.fuse_grading = float(grad_param['Fuse'])
        self.cb_interrupt = float(grad_param['CB interrupt time'])
        self.optimization_iter = int(grad_param['Relay coordination optimization iterations'])
        self.enter_load_rating: str = grad_param['Enter feeder rating and load forecast manually']
        self.feeder_load = float(grad_param['Forecast feeder load (A)'])
        self.feeder_rating = float(grad_param['Feeder rating (A)'])


def grading_parameters():
    _, _, grad_param = get_input()
    return GradingParameters(grad_param)
