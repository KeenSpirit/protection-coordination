"""
The PowerFactory Ergon library lists fuse sizes and melting curves, but doesn't link this to transformer size.
Transfer the information from "TSD0013i - RMU fuse selection guide" and "TSD0019i HV and LV fuse selection guide" to
CSV files.
Creeate a lookup function that matches the fuse size from Powerfactory with the transformer size as per the csv file.
Create a context manager using the with statement
"""


import math


class LineFuse:
    """"""

    def __init__(self, parameters: list, settings: list, network: list):
        """Initialise attributes"""
        self.name: str = parameters[0]
        self.relset: object = RelaySettings(settings)
        self.netdat: object = NetworkData(network)


class RelaySettings:
    """"""

    def __init__(self, settings: list):
        """Initialise attributes"""

        self.status: str = settings[0]
        self.rating: str = settings[1]


class NetworkData:
    """"""

    def __init__(self, network: list):
        """
        Initialise attributes
        """
        self.voltage: float = network[0]
        self.i_split: int = network[1]              # Current split n:1
        self.load: float = network[2]
        self.rating: float = network[3]             # Section conductor 2HR rating.
        self.ds_capacity: float = network[4]        # Units (A)
        self.max_3p_fl: float = network[5]
        self.max_pg_fl: float = network[6]
        self.min_2p_fl: float = network[7]
        self.min_pg_fl: float = network[8]
        self.tr_max_name: str = network[9]           # Max size downstream transformer site name
        self.max_tr_size: int = network[10]
        self.max_tr_fuse: str = network[11]
        self.tr_max_3p: float = network[12]
        self.tr_max_pg: float = network[13]
        self.downstream_devices: list = network[14]   # List of only downstream devices backed up by this relay
        self.upstream_devices: list = network[15]     # List of only upstream device that backs up this relay

        # Data validation
        # if self.min_2p_fl < self.tr_max_3p < self.max_3p_fl is False:
        #     raise Exception("Phase fault level data error")
        # elif self.min_pg_fl < self.tr_max_pg < self.max_pg_fl is False:
        #     raise Exception("Ground fault level data error")
        # elif 10 < self.max_tr_size < 2000 is False:
        #     raise Exception("Transformer data error")
        # elif 0 < self.load < self.ds_capacity is False:
        #     raise Exception("Load data error")

    def cnvrt_to_11kv(self, value):
        new_value = (self.voltage / 11) * value
        return new_value

    def trnsp_pg_stardelta(self, value):
        """Transpose P-G fault from 11kV to HV of a star-delta transformer"""

        new_value = (value * (11/self.voltage))/math.sqrt(3)
        return new_value

    def trnsp_2p_stardelta(self, value):
        """Transpose 2-P fault from 11kV to HV of a star-delta transformer"""

        new_value = (value/(2/math.sqrt(3))) * (11/self.voltage)
        return new_value

    def trnsp_3p_stardelta(self, value):
        """Transpose 3-P fault from 11kV to HV of a star-delta transformer"""

        new_value = (self.voltage / 11) * value
        return new_value

    def get_clp(self):
        """Calculate relay cold load pickup."""

        clp = self.load * 6
        return clp

    def get_inrush(self):
        """Calculate maximum transformer inrush on section."""

        inrush = self.ds_capacity * 12
        return inrush


fuse_list = {
    '': None,
    1: 'None',
    2: 'Unknown fuse',
    3: '1000_80A_Air',
    4: '1000_80A_Oil',
    5: '1500 air ins 100A SIBA Max',
    6: '1500 air ins 100A SIBA Min',
    7: '1500_100A_Air',
    8: '1500_120A_oil',
    9: '15Kmax',
    10: '15TMax',
    11: '15TMin',
    12: '20Kmax',
    13: '20Kmin',
    14: '25Kmax',
    15: '25Kmin',
    16: '300_35.5A_Air',
    17: '300_40_Oil',
    18: '40Kmax',
    19: '40Kmin',
    20: '500_40A_Air',
    21: '500_50A_Oil',
    22: '50AKEBXO',
    23: '50Kmax',
    24: '50Kmin',
    25: '65Kmax',
    26: '65N',
    27: '65Tmax',
    28: '750_63A_Air',
    29: '750_63A_Oil',
    30: '80KMax',
    31: '8Tmax',
    32: '8Tmin',
    33: 'SilvEur_36SWG_2000/5',
    34: 'SilvEur_36SWG_3000/5',
    35: 'VIP30_140A',
    36: 'VIP30_170A',
    37: 'VIP30_200A',
    38: 'XWS250NJmax',
    39: 'XWS250NJmin',
}


def get_fuse_size(dist_tr: dict[str:int]) -> str:
    """
    Estimated fuse size of 11kV distribution transformer.
    Pole transformer fuses are based on data from Energex Technical Instruction TSD0019i.
    RMU fuses types (i.e. air or oil) cannot be inferred without user input. They are assumed to be air insulated with
    the proviso that the user should verify the output.
    SWER fuses not currently handled.
    :param dist_tr:
    :return:
    """

    SWER_f_sizes = {
        10: '3K',
        25: '3K'
    }

    pole_fuse_sizes = {
        10: '8T',
        15: '8T',
        25: '8T',
        50: '8T',
        63: '8T',
        100: '16K',
        200: '20K',
        300: '25K',
        315: '25K',
        500: '40K',
        750: '50K',
        1000: '65K',
        1500: '80K',
    }

    rmu_fuse_sizes = {
        300: '300_35.5A_Air',
        315: '300_35.5A_Air',
        500: '500_40A_Air',
        750: '750_63A_Air',
        1000: '1000_80A_Air',
        1500: '1500_100A_Air'
    }

    fuse_size = None
    for tr, rating in dist_tr.items():
        try:
            if tr[:2] == "SP":
                fuse_size = pole_fuse_sizes[rating]
            else:
                fuse_size = rmu_fuse_sizes[rating]
        except IndexError:
            fuse_size = 'unknown'

    return fuse_size






