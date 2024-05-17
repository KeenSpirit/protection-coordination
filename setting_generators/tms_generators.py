"""
TMS generator functions:
ef_tms_exact(relay)
ef_tms_bounded(relay)
oc_tms_exact(relay)
oc_tms_bounded(relay)
"""

from random import uniform
import trip_time as tt
from inputs import input_file as input
from inputs import eql_fuse_data as fd




def ef_tms_exact(relay):
    """
    TMS must be greater than TMS of downstream curve.
    This function generates the optimal TMS based on the TMS of downstream device. No regard given for upstream devices.
     """

    # Provisional grading criteria (NPAG, p. 132)
    electro_m = ["Electro-mechanical", "electro-mechanical", 0.4]
    static = ["Static", "static", 0.35]
    digital_numeric = ["Digital", "digital", "Numeric", "numeric", 0.3]

    # Set minimum TMS so that curve grades with fuse curve by 100ms.
    relay.relset.ef_tms = relay.manufacturer.tms[0]
    t_relay = tt.ef_trip_time(relay, relay.netdat.tr_max_pg)
    ds_melting_time = fd.fuse_melting_time(relay.netdat.max_tr_fuse, relay.netdat.tr_max_pg)
    while t_relay < ds_melting_time + 0.1:
        relay.relset.ef_tms += relay.manufacturer.tms[2]
        t_relay = tt.ef_trip_time(relay, relay.netdat.tr_max_pg)
    min_tms = relay.relset.ef_tms

    # First check if the list of downstream devices is empty
    if not relay.netdat.downstream_devices:
        # Keep the relay TMS set to min grade above fuse
        tms_exact = min_tms
    # If not empty:
    else:
        # Get optimal TMS by evaluating (Req OP time / OP time @ TMS = 1).
        # Required operating time is based on fault level at either:
        # 1) maximum downstream fl, or
        # 2) maximum downstream hiset
        op_time_fault = {}
        for device in relay.netdat.downstream_devices:
            if device.relset.ef_hiset != "OFF":
                hs_op_time = tt.ef_trip_time(device, device.relset.ef_hiset-1)
                if device.manufacturer.technology in electro_m:
                    total_hs_time = hs_op_time + electro_m[-1]
                elif device.manufacturer.technology in static:
                    total_hs_time = hs_op_time + static[-1]
                else:
                    total_hs_time = hs_op_time + digital_numeric[-1]
                op_time_fault[total_hs_time] = device.relset.oc_hiset-1
            fl_op_time = tt.ef_trip_time(device, device.netdat.max_pg_fl)
            if device.manufacturer.technology in electro_m:
                total_fl_time = fl_op_time + electro_m[-1]
            elif device.manufacturer.technology in static:
                total_fl_time = fl_op_time + static[-1]
            else:
                total_fl_time = fl_op_time + digital_numeric[-1]
            op_time_fault[total_fl_time] = device.netdat.max_pg_fl
        op_times = list(op_time_fault.keys())
        fault_levels = list(op_time_fault.values())
        # The following is a list [associated fault level, slowest operating time]:
        max_op_fault = [fault_levels[op_times.index(max(op_times))], max(op_times)]

        relay.relset.ef_tms = 1
        relay_tms1 = tt.ef_trip_time(relay, max_op_fault[0])
        req_tms = max_op_fault[1] / relay_tms1

        tms_exact = relay.tms_converter(max(min_tms, req_tms))
    return tms_exact


def ef_tms_bounded(relay):
    """
    TMS must be greater than TMS of downstream curve.
    Idea for algorithm tuning:
    If a change in TMS value up (down) results in updating of best_total_trip, reduce the range of random number
    generation upwards (downwards). YOu can do a similar thing for pick up value.
    Alternatively, use temperature function to govern range of random number generation centred on the current
    best TMS
     """

    # Generated TMS is a random number between maximum downstream device tms or ds fuse grading and minimum upstream
    # existing device tms (rounded to 2 decimal places).
    # Set minimum TMS so that curve grades with fuse curve by 100ms.
    relay.relset.ef_tms = relay.manufacturer.tms[0]
    t_relay = tt.ef_trip_time(relay, relay.netdat.tr_max_pg)
    ds_melting_time = fd.fuse_melting_time(relay.netdat.max_tr_fuse, relay.netdat.tr_max_pg)
    while t_relay < ds_melting_time + 0.1:
        relay.relset.ef_tms += relay.manufacturer.tms[2]
        t_relay = tt.ef_trip_time(relay, relay.netdat.tr_max_pg)
    min_tms = relay.relset.ef_tms

    # First check if the list of downstream devices is empty
    if not relay.netdat.downstream_devices:
        # Keep the relay TMS set to min grade above fuse
        max_ds_ef_tms = min_tms
    # If not empty:
    else:
        ds_ef_tms = max([device.relset.ef_tms for device in relay.netdat.downstream_devices])
        max_ds_ef_tms = max(min_tms, relay.tms_converter_min(ds_ef_tms))

    # The upper bound of the TMS is the minimum of all upstream existing relay TMSs
    us_ef_exist_tms = [device.relset.ef_tms for device in relay.netdat.upstream_devices
                       if device.relset.status == "Existing"]
    if not us_ef_exist_tms:
        min_us_ef_tms = 1
    else:
        min_us_ef_tms = relay.tms_converter_max(min(us_ef_exist_tms))

    tms_bounded = [max_ds_ef_tms, min_us_ef_tms]

    return tms_bounded


def oc_tms_exact(relay):
    """
    TMS must be greater than TMS of downstream curve.
    This function generates the optimal TMS based on the TMS of downstream device. No regard given for upstream devices.
     """

    #Provisional grading criteria (NPAG, p. 132)
    electro_m = ["Electro-mechanical", "electro-mechanical", 0.4]
    static = ["Static", "static", 0.35]
    digital_numeric = ["Digital", "digital", "Numeric", "numeric", 0.3]

    # Set minimum TMS so that curve grades with fuse curve by 100ms.
    relay.relset.oc_tms = relay.manufacturer.tms[0]
    trip_relay = tt.oc_trip_time(relay, relay.netdat.tr_max_3p)
    ds_melting_time = fd.fuse_melting_time(relay.netdat.max_tr_fuse, relay.netdat.tr_max_3p)
    while trip_relay < ds_melting_time + 0.1:
        relay.relset.oc_tms += relay.manufacturer.tms[2]
        trip_relay = tt.oc_trip_time(relay, relay.netdat.tr_max_3p)

    if input.consider_clp:
        # If clp is greater than pick up, adjust the tms so curve lies no more than 0.2s below cold load pickup at 1s.
        # Don't worry about hiset - it has been set to at least 1.3 x clp
        if relay.relset.oc_pu < relay.netdat.get_clp():
            t_clp = tt.oc_trip_time(relay, relay.netdat.get_clp())
            while 1 - t_clp > 0.2:
                relay.relset.oc_tms += relay.manufacturer.tms[2]
                t_clp = tt.oc_trip_time(relay, relay.netdat.get_clp())

    min_tms = relay.relset.oc_tms

    # First check if the list of downstream devices is empty
    if not relay.netdat.downstream_devices:
        # Keep the relay TMS set to min grade above fuse
        tms_exact = min_tms
    # If not empty:
    else:
        # Get optimal TMS by evaluating (Req OP time / OP time @ TMS = 1).
        # Required operating time is based on fault level at either:
        # 1) maximum downstream fl, or
        # 2) maximum downstream hiset
        op_time_fault = {}
        for device in relay.netdat.downstream_devices:
            if device.relset.oc_hiset != "OFF":
                hiset_op_time = tt.oc_trip_time(device, device.relset.oc_hiset-1)
                if device.manufacturer.technology in electro_m:
                    total_hs_time = hiset_op_time + electro_m[-1]
                elif device.manufacturer.technology in static:
                    total_hs_time = hiset_op_time + static[-1]
                else:
                    total_hs_time = hiset_op_time + digital_numeric[-1]
                op_time_fault[total_hs_time] = device.relset.oc_hiset-1
            maxfl_op_time = tt.oc_trip_time(device, device.netdat.max_3p_fl)
            if device.manufacturer.technology in electro_m:
                total_fl_time = maxfl_op_time + electro_m[-1]
            elif device.manufacturer.technology in static:
                total_fl_time = maxfl_op_time + static[-1]
            else:
                total_fl_time = maxfl_op_time + digital_numeric[-1]
            op_time_fault[total_fl_time] = device.netdat.max_3p_fl
        op_times = list(op_time_fault.keys())                    # List of operating times
        fault_levels = list(op_time_fault.values())              # List of fault levels
        # The following is a list [associated fault level, slowest operating time]:
        max_op_fault = [fault_levels[op_times.index(max(op_times))], max(op_times)]

        relay.relset.oc_tms = 1
        op_time_tms1 = tt.oc_trip_time(relay, max_op_fault[0])
        req_tms = max_op_fault[1] / op_time_tms1
        tms_exact = relay.tms_converter(max(min_tms, req_tms))
    return tms_exact


def oc_tms_bounded(relay):
    """
    TMS must be greater than TMS of downstream curve.
    Idea for algorithm tuning:
    If a change in TMS value up (down) results in updating of best_total_trip, reduce the range of random number
    generation upwards (downwards). YOu can do a similar thing for pick up value.
    Alternatively, use temperature function to govern range of random number generation centred on the current
    best TMS
     """

    # Generated TMS is a random number between maximum downstream device tms or ds fuse grading and minimum upstream
    # existing device tms (rounded to 2 decimal places).
    # Set minimum TMS so that curve grades with fuse curve by 100ms.
    relay.relset.oc_tms = relay.manufacturer.tms[0]
    t_relay = tt.oc_trip_time(relay, relay.netdat.tr_max_3p)
    ds_melting_time = fd.fuse_melting_time(relay.netdat.max_tr_fuse, relay.netdat.tr_max_3p)
    while t_relay < ds_melting_time + 0.1:
        relay.relset.oc_tms += relay.manufacturer.tms[2]
        t_relay = tt.oc_trip_time(relay, relay.netdat.tr_max_3p)

    if input.consider_clp:
        # If clp is greater than pick up, adjust the tms so curve lies no more than 0.2s below cold load pickup at 1s.
        # Don't worry about hiset - it has been set to at least 1.3 x clp
        if relay.relset.oc_pu < relay.netdat.get_clp():
            t_clp = tt.oc_trip_time(relay, relay.netdat.get_clp())
            while 1 - t_clp > 0.2:
                relay.relset.oc_tms += relay.manufacturer.tms[2]
                t_clp = tt.oc_trip_time(relay, relay.netdat.get_clp())

    min_tms = relay.relset.oc_tms

    # First check if the list of downstream devices is empty
    if not relay.netdat.downstream_devices:
        # Keep the relay TMS set to min grade above fuse
        min_tms_2 = min_tms
    # If not empty:
    else:
        # TMS lower bound of max((TMS to grade above ds fuse), max(downstream relay TMSs)
        ds_tms = max([device.relset.oc_tms for device in relay.netdat.downstream_devices])
        # Take ceiling to convert TMS to value appropriate to the relay
        min_tms_2 = max(min_tms, relay.tms_converter_min(ds_tms))

    # The upper bound of the TMS is the minimum of all upstream existing relay TMSs
    us_oc_exist_tms = [device.relset.oc_tms for device in relay.netdat.upstream_devices
                       if device.relset.status == "Existing"]

    if not us_oc_exist_tms:
        max_tms = 1
    else:
        max_tms = relay.tms_converter_max(min(us_oc_exist_tms))

    tms_bounded = [min_tms_2, max_tms]

    return tms_bounded
