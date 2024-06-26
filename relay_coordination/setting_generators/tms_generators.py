"""
TMS generator functions:
ef_tms_exact(relay)
ef_tms_bounded(relay)
oc_tms_exact(relay)
oc_tms_bounded(relay)
"""

from input_files.input_file import grading_parameters
from relay_coordination import trip_time as tt


def ef_tms_exact(relay):
    """
    TMS must be greater than TMS of downstream curve.
    This function generates the optimal TMS based on the TMS of downstream device. No regard given for upstream devices.
     """

    f_type = 'EF'

    # Set minimum TMS so that curve grades with fuse curve.
    relay.relset.ef_tms = relay.manufacturer.tms[0]
    t_relay = tt.relay_trip_time(relay, relay.netdat.tr_max_pg, f_type)
    ds_melting_time = tt.fuse_melting_time(relay.netdat.max_tr_fuse, relay.netdat.tr_max_pg)
    while t_relay < ds_melting_time + grading_parameters().fuse_grading:
        relay.relset.ef_tms += relay.manufacturer.tms[2]
        t_relay = tt.relay_trip_time(relay, relay.netdat.tr_max_pg, f_type)
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
            if hasattr(device, 'cb_interrupt'):
                # DS device is a relay
                if device.relset.ef_hiset != "OFF":
                    hs_op_time = tt.relay_trip_time(device, device.relset.ef_hiset-1, f_type)
                    if device.manufacturer.technology == "Electro-mechanical":
                        total_hs_time = hs_op_time + grading_parameters().mechanical_grading
                    elif device.manufacturer.technology == "Static":
                        total_hs_time = hs_op_time + grading_parameters().static_grading
                    else:
                        total_hs_time = hs_op_time + grading_parameters().digital_grading
                    op_time_fault[total_hs_time] = device.relset.oc_hiset-1
                fl_op_time = tt.relay_trip_time(device, device.netdat.max_pg_fl, f_type)
                if device.manufacturer.technology == "Electro-mechanical":
                    total_fl_time = fl_op_time + grading_parameters().mechanical_grading
                elif device.manufacturer.technology == "Static":
                    total_fl_time = fl_op_time + grading_parameters().static_grading
                else:
                    total_fl_time = fl_op_time + grading_parameters().digital_grading
                op_time_fault[total_fl_time] = device.netdat.max_pg_fl
            else:
                # DS device is a fuse
                total_fl_time = (tt.fuse_melting_time(device.relset.rating, device.netdat.max_pg_fl)
                                 + grading_parameters().fuse_grading)
                op_time_fault[total_fl_time] = device.netdat.max_pg_fl
        op_times = list(op_time_fault.keys())
        fault_levels = list(op_time_fault.values())
        # The following is a list [associated fault level, slowest operating time]:
        max_op_fault = [fault_levels[op_times.index(max(op_times))], max(op_times)]

        relay.relset.ef_tms = 1
        relay_tms1 = tt.relay_trip_time(relay, max_op_fault[0], f_type)
        req_tms = max_op_fault[1] / relay_tms1

        tms_exact = relay.tms_converter(max(min_tms, req_tms))
    return tms_exact


def ef_tms_bounded(relay):
    """
    TMS must be greater than TMS of downstream curve.
     """

    f_type = 'EF'

    # Generated TMS is a random number between maximum downstream device tms or ds fuse grading and minimum upstream
    # existing device tms (rounded to 2 decimal places).
    # Set minimum TMS so that curve grades with fuse curve by 100ms.
    relay.relset.ef_tms = relay.manufacturer.tms[0]
    t_relay = tt.relay_trip_time(relay, relay.netdat.tr_max_pg, f_type)
    tr_melting_time = tt.fuse_melting_time(relay.netdat.max_tr_fuse, relay.netdat.tr_max_pg)
    if relay.netdat.downstream_devices:
        ds_fuses = [device for device in relay.netdat.downstream_devices if not hasattr(device, 'cb_interrupt')]
        mdo_melt_time = max(tt.fuse_melting_time(device.relset.rating, device.netdat.max_pg_fl) for device in ds_fuses)
    else:
        mdo_melt_time = 0
    ds_melt_time = max(tr_melting_time, mdo_melt_time)
    while t_relay < ds_melt_time + grading_parameters().fuse_grading:
        relay.relset.ef_tms += relay.manufacturer.tms[2]
        t_relay = tt.relay_trip_time(relay, relay.netdat.tr_max_pg, f_type)
    min_tms = relay.relset.ef_tms

    # First check if the list of downstream relays is empty
    ds_relays = [device for device in relay.netdat.downstream_devices if hasattr(device, 'cb_interrupt')]
    if ds_relays:
        ds_ef_tms = max([device.relset.ef_tms for device in ds_relays])
        max_ds_ef_tms = max(min_tms, relay.tms_converter_min(ds_ef_tms))
    else:
        max_ds_ef_tms = min_tms

    # The upper bound of the TMS is the minimum of the following:
    # 1) All upstream existing relay TMSs
    # 2) TMS corresponding to the slowest permissible clearing time
    us_ef_exist_tms = [device.relset.ef_tms for device in relay.netdat.upstream_devices
                       if device.relset.status == "Existing"]
    max_bu_tms = tt.tms_solver(relay, f_type, function='backup')
    max_pri_tms = tt.tms_solver(relay, f_type, function='primary')

    if not us_ef_exist_tms:
        min_us_ef_tms = 1
    else:
        min_us_ef_tms = min(us_ef_exist_tms)
    if not max_bu_tms:
        max_bu_tms = 1
    if not max_pri_tms:
        max_pri_tms = 1
    upper_bound_ef_tms = relay.tms_converter_max(min(min_us_ef_tms, max_bu_tms, max_pri_tms))

    tms_bounded = [max_ds_ef_tms, upper_bound_ef_tms]

    return tms_bounded


def oc_tms_exact(relay):
    """
    TMS must be greater than TMS of downstream curve.
    This function generates the optimal TMS based on the TMS of downstream device. No regard given for upstream devices.
     """

    f_type = 'OC'

    # Set minimum TMS so that curve grades with fuse curve by 100ms.
    relay.relset.oc_tms = relay.manufacturer.tms[0]
    trip_relay = tt.relay_trip_time(relay, relay.netdat.tr_max_3p, f_type)
    ds_melting_time = tt.fuse_melting_time(relay.netdat.max_tr_fuse, relay.netdat.tr_max_3p)
    while trip_relay < ds_melting_time + grading_parameters().fuse_grading:
        relay.relset.oc_tms += relay.manufacturer.tms[2]
        trip_relay = tt.relay_trip_time(relay, relay.netdat.tr_max_3p, f_type)

    if grading_parameters().consider_clp == "Yes":
        # If clp is greater than pick up, adjust the tms so curve lies no more than 0.2s below cold load pickup at 1s.
        # Don't worry about hiset - it has been set to at least 1.3 x clp
        if relay.relset.oc_pu < relay.netdat.get_clp():
            t_clp = tt.relay_trip_time(relay, relay.netdat.get_clp(), f_type)
            while 1 - t_clp > 0.2:
                relay.relset.oc_tms += relay.manufacturer.tms[2]
                t_clp = tt.relay_trip_time(relay, relay.netdat.get_clp(), f_type)

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
            if hasattr(device, 'cb_interrupt'):
                # DS device is a relay
                if device.relset.oc_hiset != "OFF":
                    hiset_op_time = tt.relay_trip_time(device, device.relset.oc_hiset-1, f_type)
                    if device.manufacturer.technology == "Electro-mechanical":
                        total_hs_time = hiset_op_time + grading_parameters().mechanical_grading
                    elif device.manufacturer.technology == "Static":
                        total_hs_time = hiset_op_time + grading_parameters().static_grading
                    else:
                        total_hs_time = hiset_op_time + grading_parameters().digital_grading
                    op_time_fault[total_hs_time] = device.relset.oc_hiset-1
                maxfl_op_time = tt.relay_trip_time(device, device.netdat.max_3p_fl, f_type)
                if device.manufacturer.technology == "Electro-mechanical":
                    total_fl_time = maxfl_op_time + grading_parameters().mechanical_grading
                elif device.manufacturer.technology == "Static":
                    total_fl_time = maxfl_op_time + grading_parameters().static_grading
                else:
                    total_fl_time = maxfl_op_time + grading_parameters().digital_grading
                op_time_fault[total_fl_time] = device.netdat.max_3p_fl
            else:
                # DS device is a fuse
                total_fl_time = (tt.fuse_melting_time(device.relset.rating, device.netdat.max_3p_fl)
                                 + grading_parameters().fuse_grading)
                op_time_fault[total_fl_time] = device.netdat.max_3p_fl
        op_times = list(op_time_fault.keys())                    # List of operating times
        fault_levels = list(op_time_fault.values())              # List of fault levels
        # The following is a list [associated fault level, slowest operating time]:
        max_op_fault = [fault_levels[op_times.index(max(op_times))], max(op_times)]

        relay.relset.oc_tms = 1
        op_time_tms1 = tt.relay_trip_time(relay, max_op_fault[0], f_type)
        req_tms = max_op_fault[1] / op_time_tms1
        tms_exact = relay.tms_converter(max(min_tms, req_tms))
    return tms_exact


def oc_tms_bounded(relay):
    """
    TMS must be greater than TMS of downstream curve.
    Alternatively, use temperature function to govern range of random number generation centred on the current
    best TMS
     """

    f_type = 'OC'

    # Generated TMS is a random number between maximum downstream device tms or ds fuse grading and minimum upstream
    # existing device tms (rounded to 2 decimal places).
    # Set minimum TMS so that curve grades with fuse curve by 100ms.
    relay.relset.oc_tms = relay.manufacturer.tms[0]
    t_relay = tt.relay_trip_time(relay, relay.netdat.tr_max_3p, f_type)
    tr_melting_time = tt.fuse_melting_time(relay.netdat.max_tr_fuse, relay.netdat.tr_max_3p)
    if relay.netdat.downstream_devices:
        ds_fuses = [device for device in relay.netdat.downstream_devices if not hasattr(device, device.cb_interrupt)]
        mdo_melt_time = max(tt.fuse_melting_time(device.relset.rating, device.netdat.max_3p_fl) for device in ds_fuses)
    else:
        mdo_melt_time = 0
    ds_melt_time = max(tr_melting_time, mdo_melt_time)
    while t_relay < ds_melt_time + grading_parameters().fuse_grading:
        relay.relset.oc_tms += relay.manufacturer.tms[2]
        t_relay = tt.relay_trip_time(relay, relay.netdat.tr_max_3p, f_type)

    if grading_parameters().consider_clp == "Yes":
        # If clp is greater than pick up, adjust the tms so curve lies no more than 0.2s below cold load pickup at 1s.
        # Don't worry about hiset - it has been set to at least 1.3 x clp
        if relay.relset.oc_pu < relay.netdat.get_clp():
            t_clp = tt.relay_trip_time(relay, relay.netdat.get_clp(), f_type)
            while 1 - t_clp > 0.2:
                relay.relset.oc_tms += relay.manufacturer.tms[2]
                t_clp = tt.relay_trip_time(relay, relay.netdat.get_clp(), f_type)

    min_tms = relay.relset.oc_tms

    # First check if the list of downstream relays is empty
    ds_relays = [device for device in relay.netdat.downstream_devices if hasattr(device, device.cb_interrupt)]
    if ds_relays:
        ds_oc_tms = max([device.relset.oc_tms for device in ds_relays])
        lower_bound_tms = max(min_tms, relay.tms_converter_min(ds_oc_tms))
    else:
        lower_bound_tms = min_tms

    # The upper bound of the TMS is the minimum of the following:
    # 1) All upstream existing relay TMSs
    # 2) TMS corresponding to the slowest permissible clearing time
    us_oc_exist_tms = [device.relset.oc_tms for device in relay.netdat.upstream_devices
                       if device.relset.status == "Existing"]
    max_bu_tms = tt.tms_solver(relay, f_type, function='backup')
    max_pri_tms = tt.tms_solver(relay, f_type, function='primary')

    if not us_oc_exist_tms:
        min_us_oc_tms = 1
    else:
        min_us_oc_tms = min(us_oc_exist_tms)
    if not max_bu_tms:
        max_bu_tms = 1
    if not max_pri_tms:
        max_pri_tms = 1
    # Ignore upstream TMS if it is lower than downstream tms:
    if lower_bound_tms > min_us_oc_tms:
        min_us_oc_tms = 1
    upper_bound_oc_tms = relay.tms_converter_max(min(min_us_oc_tms, max_bu_tms, max_pri_tms))

    tms_bounded = [lower_bound_tms, upper_bound_oc_tms]

    return tms_bounded
