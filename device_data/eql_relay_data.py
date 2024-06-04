"""
List of standard relays with their parameter data as per manufacturer specification.
The data is primarily used to determine protection device grading time.
For electromechanical relays, their earth fault effective setting is disproportionate to the relay characteristic curve
particularly at smaller values. See Table 9.4, p137, NPAG.
setting parameter limits are formatted as follows:  [min, max, step size, min2, max2, step size2]
"""

from dataclasses import dataclass
import math
from relay_coordination import trip_time as tt


class ProtectionRelay:
    """"""

    def __init__(self, parameters: list, settings: list, network: list, ct_data: list):
        """Initialise attributes"""
        self.name: str = parameters[0]
        self.manufacturer: object = parameters[1]
        self.cb_interrupt: float = parameters[2]
        self.relset: object = RelaySettings(settings)
        self.netdat: object = NetworkData(network)
        self.ct: object = RelayCT(ct_data)

    def pu_converter(self, old_value, f_type):
        """convert an existing element value into a new value that is valid for the pu step size
        element is either "OC" or "EF" """
        if f_type == "OC":
            if self.manufacturer.oc_pickup[2] < 1:
                step = self.manufacturer.oc_pickup[2] * self.ct.ratio
            else:
                step = self.manufacturer.oc_pickup[2]
        else:  # element = "EF"
            if self.manufacturer.ef_pickup[2] < 1:
                step = self.manufacturer.ef_pickup[2] * self.ct.ratio
            else:
                step = self.manufacturer.ef_pickup[2]
        return round((1 / step) * old_value) / (1 / step)

    def hiset_converter(self, old_value, element):
        """
        convert an existing oc into a new oc that is valid for the pu step size
        element is either "OC" or "EF"
        """
        if element == "OC":
            if self.manufacturer.oc_highset[3] == "ln":
                step = self.manufacturer.oc_highset[2] * self.ct.ratio
            elif self.manufacturer.oc_highset[3] == "pu":
                step = self.manufacturer.oc_highset[2] * self.relset.oc_pu
            else:
                # relay.manufacturer  step is amp:
                step = self.manufacturer.oc_highset[2]
        else:  # element = "EF"
            if self.manufacturer.ef_highset[3] == "ln":
                step = self.manufacturer.ef_highset[2] * self.ct.ratio
            elif self.manufacturer.ef_highset[3] == "pu":
                step = self.manufacturer.ef_highset[2] * self.relset.ef_pu
            else:
                # relay.manufacturer  step is amp:
                step = self.manufacturer.ef_highset[2]
        return round((1 / step) * old_value) / (1 / step)

    # The following functions convert an existing tms into a new tms that is valid for the relay settings
    def tms_converter_min(self, old_tms):
        new_tms = math.ceil((1 / self.manufacturer.tms[2]) * old_tms) / (1 / self.manufacturer.tms[2])
        return new_tms

    def tms_converter_max(self, old_tms):
        new_tms = math.floor((1 / self.manufacturer.tms[2]) * old_tms) / (1 / self.manufacturer.tms[2])
        return new_tms

    def tms_converter(self, old_tms):
        new_tms = round((1 / self.manufacturer.tms[2]) * old_tms) / (1 / self.manufacturer.tms[2])
        return new_tms

    def ef_setting_report(self):

        # TODO: Report any setting contraint violations
        primary_ef_reach = round(self.netdat.min_pg_fl / self.relset.ef_pu, 2)
        print(f"{self.name} primary ef reach factor: {primary_ef_reach}")
        if self.netdat.downstream_devices:
            ds_fl = min([device.netdat.min_pg_fl for device in self.netdat.downstream_devices])
            bu_ef_reach = round(ds_fl / self.relset.ef_pu, 2)
            print(f"{self.name} back-up ef reach factor: {bu_ef_reach}")
            grading_times = []
            for device in self.netdat.downstream_devices:
                # Create a list of fault levels over which to compare curves
                b = [a for a in range(device.netdat.min_pg_fl, device.netdat.max_pg_fl, 1)]
                for x in b:
                    # Append a single fault level grade time data point
                    grading_times.append(tt.relay_trip_time(self, x, f_type='EF') - tt.relay_trip_time(device, x, f_type='EF'))
            min_grade = round(min(grading_times), 3)
            print(f"{self.name} min ef grade time: {min_grade}")
        else:
            print(f"{self.name} has no downstream devices")

    def oc_setting_report(self):

        # TODO: Report any setting contraint violations
        primary_oc_reach = round(self.netdat.min_2p_fl / self.relset.oc_pu, 2)
        print(f"{self.name} primary oc reach factor: {primary_oc_reach}")
        if self.netdat.downstream_devices:
            ds_fl = min([device.netdat.min_2p_fl for device in self.netdat.downstream_devices])
            bu_oc_reach = round(ds_fl / self.relset.oc_pu, 2)
            print(f"{self.name} back-up oc reach factor: {bu_oc_reach}")
            grading_times = []
            for device in self.netdat.downstream_devices:
                # Create a list of fault levels over which to compare curves
                b = [a for a in range(device.netdat.min_2p_fl, device.netdat.max_3p_fl, 1)]
                for x in b:
                    # Append a single fault level grade time data point
                    grading_times.append(tt.relay_trip_time(self, x, f_type='EF') - tt.relay_trip_time(device, x, f_type='EF'))
            min_grade = round(min(grading_times), 3)
            print(f"{self.name} min oc grade time: {min_grade}")
        else:
            print(f"{self.name} has no downstream devices")


class RelaySettings:
    """"""

    def __init__(self, settings: list):
        """Initialise attributes"""

        self.status: str = settings[0]
        self.oc_pu: float = settings[1]
        self.oc_tms: float = settings[2]
        self.oc_curve: str = settings[3]
        self.oc_hiset: float = settings[4]
        self.oc_min_time: float = settings[5]
        self.oc_hiset2: float = settings[6]
        self.oc_min_time2: float = settings[7]
        self.ef_pu: float = settings[8]
        self.ef_tms: float = settings[9]
        self.ef_curve: str = settings[10]
        self.ef_hiset: float = settings[11]
        self.ef_min_time: float = settings[12]
        self.ef_hiset2: float = settings[13]
        self.ef_min_time2: float = settings[14]

        # Data validation
        if self.status not in ["Existing", "existing", "Required", "required", "New", "new"]:
            raise Exception("Relay status data error")


class NetworkData:
    """"""

    def __init__(self, network: list):
        """
        Initialise attributes
        """
        self.voltage: float = network[0]
        self.i_split: int = network[1]       # Current split n:1
        self.load: float = network[3]          # Would this be the five year 10% POE peak load?
        self.rating: float = network[2]        # Section conductor 2HR rating. If 0, this isn't a feeder relay
        self.ds_capacity: float = network[4]   # Units (A)
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
        if self.min_2p_fl < self.tr_max_3p < self.max_3p_fl is False:
            raise Exception("Phase fault level data error")
        elif self.min_pg_fl < self.tr_max_pg < self.max_pg_fl is False:
            raise Exception("Ground fault level data error")
        elif 10 < self.max_tr_size < 1500 is False:
            raise Exception("Transformer data error")
        elif 0 < self.load < self.ds_capacity is False:
            raise Exception("Load data error")

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


class RelayCT:
    """"""

    def __init__(self, ct_data: list):
        """
        saturation: Relay CT saturation factor
        ect: Maximum CT ratio error (%). Equal to CT composite error.
        ratio: CT ratio
        """
        self.saturation: float = ct_data[0]
        self.ect: float = ct_data[1]
        self.ratio: float = ct_data[2]


@dataclass
class _2TJM10:
    """OC and EF values not confirmed"""
    technology = "Electro-mechanical"
    timing_error = 7.5
    overshoot = 0.05
    safety_margin = 0.1
    tms = (0.05, 1, 0.025)
    oc_lowset = (0.1, 10, 0.01)
    oc_pickup = (0.1, 10, 0.01)
    oc_highset = False
    oc_min_time = False
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (0.1, 10, 0.01)
    ef_pickup = (0.1, 10, 0.01)
    ef_highset = False
    ef_min_time = False
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class ADVC2:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 2, 0.01)
    oc_lowset = (1, 10, 0.1)
    oc_pickup = (10, 1260, 1)
    oc_highset = (1, 30, 0.1, "pu")
    oc_min_time = (0.01, 100, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (1, 10, 0.1)
    ef_pickup = (10, 1260, 1)
    ef_highset = (1, 30, 0.1, "pu")
    ef_min_time = (0.01, 100, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class ADVC3:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 2, 0.01)
    oc_lowset = (1, 10, 0.1)
    oc_pickup = (10, 1260, 1)
    oc_highset = (1, 30, 0.1, "pu")
    oc_min_time = (0.01, 100, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (1, 10, 0.1)
    ef_pickup = (10, 1260, 1)
    ef_highset = (1, 30, 0.1, "pu")
    ef_min_time = (0.01, 100, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class CAPM2:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 2, 0.01)
    oc_lowset = (1, 10, 0.1)
    oc_pickup = (10, 1260, 1)
    oc_highset = (1, 30, 0.1, "pu")
    oc_min_time = (0, 2, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (1, 10, 0.1)
    ef_pickup = (10, 1260, 1)
    ef_highset = (1, 30, 0.1, "pu")
    ef_min_time = (0, 2, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class CAPM4:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 2, 0.01)
    oc_lowset = (1, 10, 0.1)
    oc_pickup = (10, 1260, 1)
    oc_highset = (1, 30, 0.1, "pu")
    oc_min_time = (0, 2, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (1, 10, 0.1)
    ef_pickup = (10, 1260, 1)
    ef_highset = (1, 30, 0.1, "pu")
    ef_min_time = (0, 2, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class CAPM5:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 2, 0.01)
    oc_lowset = (1, 10, 0.1)
    oc_pickup = (10, 1260, 1)
    oc_highset = (1, 30, 0.1, "pu")
    oc_min_time = (0.01, 100, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (1, 10, 0.1)
    ef_pickup = (10, 1260, 1)
    ef_highset = (1, 30, 0.1, "pu")
    ef_min_time = (0.01, 100, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class Argus_1:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.025, 1.6, 0.025)
    oc_lowset = (0.1, 2.5, 0.05)
    oc_pickup = (0.1, 2.5, 0.05)
    oc_highset = (0.1, 2.5, 0.05, 2.5, 52.5, 0.5, "ln")
    oc_min_time = (0, 20, 0.01)
    oc_highset_2 = (0.1, 2.5, 0.05, 2.5, 52.5, 0.5, "ln")
    oc_min_time2 = (0, 20, 0.01)
    ef_lowset = (0.1, 2.5, 0.05)
    ef_pickup = (0.1, 2.5, 0.05)
    ef_highset = (0.1, 2.5, 0.05, 2.5, 52.5, 0.5, "ln")
    ef_min_time = (0, 20, 0.01)
    ef_highset_2 = (0.1, 2.5, 0.05, 2.5, 52.5, 0.5, "ln")
    ef_min_time2 = (0, 20, 0.01)


@dataclass
class Argus_2:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.025, 1.6, 0.025)
    oc_lowset = (0.1, 2.5, 0.05)
    oc_pickup = (0.1, 2.5, 0.05)
    oc_highset = (0.1, 2.5, 0.05, 2.5, 53.5, 0.5, "ln")
    oc_min_time = (0, 20, 0.01)
    oc_highset_2 = (0.1, 2.5, 0.05, 2.5, 53.5, 0.5, "ln")
    oc_min_time2 = (0, 20, 0.01)
    ef_lowset = (0.1, 2.5, 0.05)
    ef_pickup = (0.1, 2.5, 0.05)
    ef_highset = (0.1, 2.5, 0.05, 2.5, 53.5, 0.5, "ln")
    ef_min_time = (0, 20, 0.01)
    ef_highset_2 = (0.1, 2.5, 0.05, 2.5, 53.5, 0.5, "ln")
    ef_min_time2 = (0, 20, 0.01)


@dataclass
class CDG11:
    """OC and EF values not confirmed"""
    technology = "Electro-mechanical"
    timing_error = 7.5
    overshoot = 0.05
    safety_margin = 0.1
    tms = (0.05, 1, 0.025)
    oc_lowset = (0.1, 10, 0.01)
    oc_pickup = (0.1, 10, 0.01)
    oc_highset = False
    oc_min_time = False
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (0.1, 10, 0.01)
    ef_pickup = (0.1, 10, 0.01)
    ef_highset = False
    ef_min_time = False
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class CDG31:
    """OC and EF values not confirmed"""
    technology = "Electro-mechanical"
    timing_error = 7.5
    overshoot = 0.05
    safety_margin = 0.1
    tms = (0.05, 1, 0.025)
    oc_lowset = (0.1, 10, 0.01)
    oc_pickup = (0.1, 10, 0.01)
    oc_highset = False
    oc_min_time = False
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (0.1, 10, 0.01)
    ef_pickup = (0.1, 10, 0.01)
    ef_highset = False
    ef_min_time = False
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class CDG66:
    """OC and EF values not confirmed"""
    technology = "Electro-mechanical"
    timing_error = 7.5
    overshoot = 0.05
    safety_margin = 0.1
    tms = (0.05, 1, 0.025)
    oc_lowset = (0.1, 10, 0.01)
    oc_pickup = (0.1, 10, 0.01)
    oc_highset = False
    oc_min_time = False
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (0.1, 10, 0.01)
    ef_pickup = (0.1, 10, 0.01)
    ef_highset = False
    ef_min_time = False
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class KCEG:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.025, 1.5, 0.025)
    oc_lowset = (12, 1920, 6)
    oc_pickup = (48, 1920, 6)
    oc_highset = (48, 19200, 6, "amp")
    oc_min_time = (0, 100, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (3, 480, 1.5)
    ef_pickup = (3, 480, 1.5)
    ef_highset = (3, 4800, 1.5, "amp")
    ef_min_time = (0, 100, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class KCGG:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.025, 1.5, 0.025)
    oc_lowset = (12, 1920, 6)
    oc_pickup = (48, 1920, 6)
    oc_highset = (48, 19200, 6, "amp")
    oc_min_time = (0, 100, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (3, 480, 1.5)
    ef_pickup = (3, 480, 1.5)
    ef_highset = (3, 4800, 1.5, "amp")
    ef_min_time = (0, 100, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class NOJA_01:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 10, 0.01)
    oc_lowset = (1, 20, 0.01)
    oc_pickup = (3, 1280, 1)
    oc_highset = (3, 16000, 1, "amp")
    oc_min_time = (0, 2, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (1, 20, 0.01)
    ef_pickup = (3, 1280, 1)
    ef_highset = (3, 16000, 1, "amp")
    ef_min_time = (0, 2, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class NOJA_10:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 10, 0.01)
    oc_lowset = (1, 20, 0.01)
    oc_pickup = (3, 1280, 1)
    oc_highset = (3, 16000, 1, "amp")
    oc_min_time = (0, 2, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (1, 20, 0.01)
    ef_pickup = (3, 1280, 1)
    ef_highset = (3, 16000, 1, "amp")
    ef_min_time = (0, 2, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class P123:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.025, 1.5, 0.001)
    oc_lowset = (0.5, 40, 0.05)
    oc_pickup = (0.05, 25, 0.01)
    oc_highset = (0.5, 40, 0.05, "ln")
    oc_min_time = (0, 150, 0.01)
    oc_highset_2 = (0.5, 40, 0.05, "ln")
    oc_min_time2 = (0, 150, 0.01)
    ef_lowset = False
    ef_pickup = (0.01, 2, 0.005)
    ef_highset = (0.01, 8, 0.005, "ln")
    ef_min_time = (0, 150, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class P142:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.025, 1.2, 0.005)
    oc_lowset = (0.08, 4, 0.01)
    oc_pickup = (0.08, 4, 0.01)
    oc_highset = (0.08, 32, 0.01, "ln")
    oc_min_time = (0, 100, 0.01)
    oc_highset_2 = (0.08, 32, 0.01, "ln")
    oc_min_time2 = (0, 100, 0.01)
    ef_lowset = (0.08, 4, 0.01)
    ef_pickup = (0.08, 4, 0.01)
    ef_highset = (0.08, 32, 0.01, "ln")
    ef_min_time = (0, 200, 0.01)
    ef_highset_2 = (0.08, 32, 0.01, "ln")
    ef_min_time2 = (0, 200, 0.01)


@dataclass
class P643:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.025, 1.2, 0.005)
    oc_lowset = (0.08, 32, 0.01)
    oc_pickup = (0.08, 4, 0.01)
    oc_highset = (0.08, 32, 0.01, "ln")
    oc_min_time = (0, 100, 0.01)
    oc_highset_2 = (0.08, 32, 0.01, "ln")
    oc_min_time2 = (0, 100, 0.01)
    ef_lowset = (0.08, 32, 0.01)
    ef_pickup = (0.08, 4, 0.01)
    ef_highset = (0.08, 32, 0.01, "ln")
    ef_min_time = (0, 100, 0.01)
    ef_highset_2 = (0.08, 32, 0.01, "ln")
    ef_min_time2 = (0, 100, 0.01)


@dataclass
class SEL351_1:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 1, 0.01)
    oc_lowset = False
    oc_pickup = (0.25, 16, 0.01)
    oc_highset = (0.25, 100, 0.01, "ln")
    oc_min_time = (0, 320, 0.005)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = False
    ef_pickup = (0.1, 16, 0.01)
    ef_highset = (0.25, 100, 0.01, "ln")
    ef_min_time = (0, 320, 0.005)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class SEL351_6:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 1, 0.01)
    oc_lowset = False
    oc_pickup = (0.25, 16, 0.01)
    oc_highset = (0.25, 100, 0.01, "ln")
    oc_min_time = (0, 320, 0.005)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = False
    ef_pickup = (0.1, 16, 0.01)
    ef_highset = (0.25, 100, 0.01, "ln")
    ef_min_time = (0, 320, 0.005)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class SEL351A:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 1, 0.01)
    oc_lowset = ()
    oc_pickup = (0.25, 16, 0.01)
    oc_highset = (0.25, 100, 0.01, "ln")
    oc_min_time = (0, 320, 0.005)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = ()
    ef_pickup = (0.1, 16, 0.01)
    ef_highset = (0.25, 100, 0.01, "ln")
    ef_min_time = (0, 320, 0.005)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class SPAJ140C:
    """"""
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 1, 0.01)
    oc_lowset = (0.5, 5, 0.01)
    oc_pickup = (0.5, 5, 0.01)
    oc_highset = (0.5, 40, 0.01, "ln")
    oc_min_time = (0.04, 300, 0.001)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (0.1, 0.8, 0.01)
    ef_pickup = (0.1, 0.8, 0.01)
    ef_highset = (0.1, 10, 0.01, "ln")
    ef_min_time = (0.05, 300, 0.001)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class WHC07:
    """OC and EF values not confirmed"""
    technology = "Electro-mechanical"
    timing_error = 7.5
    overshoot = 0.05
    safety_margin = 0.1
    tms_min = 0.5
    tms_step = 11
    tms_max = 0.5
    tms = (0.5, 11, 0.5)
    oc_lowset = (0.1, 10, 0.01)
    oc_pickup = (0.1, 10, 0.01)
    oc_highset = (0.1, 10, 0.01, "ln")
    oc_min_time = (0.1, 10, 0.01)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = (0.1, 10, 0.01)
    ef_pickup = (0.1, 10, 0.01)
    ef_highset = (0.1, 10, 0.01, "ln")
    ef_min_time = (0.1, 10, 0.01)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class REF615:
    """"""
    # TODO: Values not confirmed
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 1, 0.01)
    oc_lowset = False
    oc_pickup = (0.25, 16, 0.01)
    oc_highset = (0.25, 100, 0.01, "ln")
    oc_min_time = (0, 320, 0.005)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = False
    ef_pickup = (0.1, 16, 0.01)
    ef_highset = (0.25, 100, 0.01, "ln")
    ef_min_time = (0, 320, 0.005)
    ef_highset_2 = False
    ef_min_time2 = False


@dataclass
class RED615:
    """"""
    # TODO: Values not confirmed
    technology = "Digital"
    timing_error = 5
    overshoot = 0.02
    safety_margin = 0.03
    tms = (0.05, 1, 0.01)
    oc_lowset = False
    oc_pickup = (0.25, 16, 0.01)
    oc_highset = (0.25, 100, 0.01, "ln")
    oc_min_time = (0, 320, 0.005)
    oc_highset_2 = False
    oc_min_time2 = False
    ef_lowset = False
    ef_pickup = (0.1, 16, 0.01)
    ef_highset = (0.25, 100, 0.01, "ln")
    ef_min_time = (0, 320, 0.005)
    ef_highset_2 = False
    ef_min_time2 = False

# This dictionary is used in the input file to map the relay input by the user to the relay dataclasses above
relay_lookup = {
    1: None,
    2: _2TJM10,
    3: Argus_1,
    4: Argus_2,
    5: CDG11,
    6: CDG31,
    7: CDG66,
    8: KCEG,
    9: KCGG,
    10: NOJA_01,
    11: NOJA_10,
    12: CAPM2,
    13: CAPM4,
    14: CAPM5,
    15: ADVC2,
    16: ADVC3,
    17: P123,
    18: P142,
    19: P643,
    20: SEL351_1,
    21: SEL351_6,
    22: SEL351A,
    23: SPAJ140C,
    24: WHC07,
    25: REF615,
    26: RED615
}
