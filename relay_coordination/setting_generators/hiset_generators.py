"""
Hiset generator functions:
oc_hiset_mintime(relay)
oc_hiset_2(relay, critical_fl)
ef_hiset_mintime(relay)
ef_hiset_2(relay, critical_fl)
"""

from relay_coordination import trip_time as tt
from device_data import eql_fuse_data as fd


def ef_hiset_mintime(relay):
    """
    Hiset must always be greater than 1.3 x cold load pickup
    Hiset may be either:
    - 1.3 * max fault level of downstream device (and min_time = 0.05), or
    - 1.3 * hiset of downstream device (and min_time = min time of downstream device + 0.3)
    """

    # Create scenario for no hiset setting
    hiset_scenarios = [["OFF", "OFF", "OFF", "OFF"]]

    # Check if there are any hisets by checking for integers of floats in the list of downstream hisets
    ds_hisets = [device.relset.ef_hiset for device in relay.netdat.downstream_devices]
    ds_hisets_on = [a for a in ds_hisets if type(a) is int or type(a) is float]

    ####################################################################################################################
    # If the relay has no hiset setting
    ####################################################################################################################
    electro_static = ["Electro-mechanical", "electro-mechanical", "Static", "static"]
    if not relay.manufacturer.oc_highset or relay.manufacturer.technology in electro_static:
        pass

    ####################################################################################################################
    # If relay has a hiset but there are no downstream devices,
    # grade hiset to be 1.3 x min_pg_fl
    ####################################################################################################################

    elif not relay.netdat.downstream_devices:
        critical_fl = relay.netdat.min_pg_fl
        if 1.3 * critical_fl < relay.netdat.max_pg_fl:
            ef_hiset = 1.3 * critical_fl
            # Set the hiset min time and hiset 2 (if any)
            new_scenario = ef_hiset_2(relay, ef_hiset, min_min_time=0)
            hiset_scenarios.append(new_scenario)

    ####################################################################################################################
    # If there are downstream devices but no downstream hisets,
    # set the relay hiset to be 1.3 x max ds fl
    ####################################################################################################################
    elif not ds_hisets_on:
        max_ds_max_fl = max([device.netdat.max_pg_fl for device in relay.netdat.downstream_devices])
        critical_fl = max(max_ds_max_fl, relay.netdat.min_pg_fl)
        if 1.3 * critical_fl < relay.netdat.max_pg_fl:
            ef_hiset = 1.3 * critical_fl
            # Set the hiset min time and hiset 2 (if any)
            new_scenario = ef_hiset_2(relay, ef_hiset, min_min_time=0)
            hiset_scenarios.append(new_scenario)

    ####################################################################################################################
    # There are downstream devices and at least some of them have hisets
    ####################################################################################################################
    else:
        new_scenarios = ef_hiset_ds(relay)
        if new_scenarios:
            hiset_scenarios = hiset_scenarios + new_scenarios

    # remove duplicates from hiset_scenarios list
    seen = set()
    hiset_scenarios_2 = []
    for sub_list in hiset_scenarios:
        sub_tuple = tuple(sub_list)
        if sub_tuple not in seen:
            hiset_scenarios_2.append(sub_list)
            seen.add(sub_tuple)

    return hiset_scenarios_2


def ef_hiset_ds(relay):
    """
    There are downstream devices and at least one of them has hisets.
    Methodology for selecting relay hiset:
    Solution space of possible relay hisets: [1.3 x max downstream hiset, 1.3 x each max downstream relay fault
    level exceeding the downstream hiset].
    Represent this as a list of hiset_scenarios = [[hiset, mintime, hiset2, mintime2], [...], ....]
    """

    max_pg_fl = relay.netdat.max_pg_fl

    ds_hisets = [device.relset.ef_hiset for device in relay.netdat.downstream_devices]
    ds_hisets_on = [a for a in ds_hisets if type(a) is int or type(a) is float]

    hiset_scenarios = []
    # Get max downstream hiset
    max_hiset = max(ds_hisets_on)

    # Create a dictionary = {ds_relay with max hiset: relay hiset,
    # ds_relay with max fl exceeding max hiset: max_fl of downstream relay, ...}
    max_fl_dic = {"max hiset relay": max_hiset}

    # for each ds device max fault level that exceeds this, calculate the ds device trip time at the critical_fl
    for device in relay.netdat.downstream_devices:
        if device.netdat.max_pg_fl > max_hiset:
            max_fl_dic[device] = device.netdat.max_pg_fl

    while max_fl_dic:
        new_hiset = min(max_fl_dic.values())
        if 1.3 * new_hiset > max_pg_fl:
            break
        new_relays = [key for key in max_fl_dic if max_fl_dic[key] == new_hiset]
        highest_min_time = 0

        # from the relays in this dictionary, find the relay with longest trip time at critical grade
        for device in max_fl_dic:
            if device == "max hiset relay":
                continue
            device_trip_time = tt.relay_trip_time(device, new_hiset, f_type ='EF')
            if device_trip_time > highest_min_time:
                highest_min_time = device_trip_time

        # New scenario:
        relay_hs = 1.3 * new_hiset
        new_scenario = ef_hiset_2(relay, relay_hs, highest_min_time)
        hiset_scenarios.append(new_scenario)

        # remove the max_hiset_relay from the max_fl_dic dictionary
        for relay in new_relays:
            del max_fl_dic[relay]

    return hiset_scenarios


def ef_hiset_2(relay, ef_hiset, min_min_time):
    """
    Calculates relay hiset min time and hiset 2settings.
    Ensures hiset always grades over downstream fuse and inrush
    min_min_time is the minimum value that min_time is allowed to be set at (due to constraints listed outside this
    function)
    Returns a scenario [hiset, min_time, hiset2, min_time2]
    """

    if ef_hiset <= relay.netdat.tr_max_pg:
        ds_melting_time = fd.fuse_melting_time(relay.netdat.max_tr_fuse, ef_hiset)
        fuse_min_time = ds_melting_time + 0.1
    else:
        fuse_min_time = 0
    # Ensure hiset min time grades over fuse
    min_time = max(0.05, fuse_min_time, min_min_time)
    if relay.netdat.downstream_devices:
        max_ds_fl = max([device.netdat.max_pg_fl for device in relay.netdat.downstream_devices])
        ef_hiset2 = 1.3 * max_ds_fl
        if (ef_hiset < ef_hiset2 < relay.netdat.max_pg_fl
                and relay.manufacturer.ef_hiset2):
            ef_hiset2 = ef_hiset2
            ef_min_time2 = 0.05
        else:
            ef_hiset2 = "OFF"
            ef_min_time2 = "OFF"
    else:
        ef_hiset2 = "OFF"
        ef_min_time2 = "OFF"

    hiset_scenario = [ef_hiset, min_time, ef_hiset2, ef_min_time2]

    return hiset_scenario


def oc_hiset_mintime(relay):
    """
    Hiset must always be greater than 1.3 x cold load pickup and max tr fault level
    Hiset may be either:
    - 1.3 * max fault level of downstream device (and min_time = 0.05), or
    - 1.3 * hiset of downstream device (and min_time = min time of downstream device + grade time)
    """

    # Create scenario for no hiset setting
    hiset_scenarios = [["OFF", "OFF", "OFF", "OFF"]]

    # Check if there are any downstream hisets by checking for integers of floats in the list of downstream hisets
    ds_hisets = [device.relset.oc_hiset for device in relay.netdat.downstream_devices]
    ds_hisets_on = [a for a in ds_hisets if type(a) is int or type(a) is float]

    ####################################################################################################################
    # If the relay has no hiset setting
    ####################################################################################################################
    electro_static = ["Electro-mechanical", "electro-mechanical", "Static", "static"]
    if not relay.manufacturer.oc_highset or relay.manufacturer.technology in electro_static:
        pass

    ####################################################################################################################
    # If relay has a hiset but there are no downstream devices,
    # grade hiset to be 1.3 x max(min_2p_fl, clp)
    ####################################################################################################################
    elif not relay.netdat.downstream_devices:
        critical_fl = max(relay.netdat.get_clp(), relay.netdat.min_2p_fl)
        if 1.3 * critical_fl < relay.netdat.max_3p_fl:
            oc_hiset = 1.3 * critical_fl
            # Set the hiset min time and hiset 2 (if any)
            new_scenario = oc_hiset_2(relay, oc_hiset, min_min_time=0)
            hiset_scenarios.append(new_scenario)

    ####################################################################################################################
    # If there are downstream devices but no downstream hisets,
    # set the relay hiset to be 1.3 x max(max ds fl, relay clp)
    ####################################################################################################################
    elif not ds_hisets_on:
        max_ds_max_fl = max([device.netdat.max_3p_fl for device in relay.netdat.downstream_devices])
        critical_fl = max(max_ds_max_fl, relay.netdat.get_clp(), relay.netdat.min_2p_fl)
        if 1.3 * critical_fl < relay.netdat.max_3p_fl:
            oc_hiset = 1.3 * critical_fl
            # Set the hiset min time and hiset 2 (if any)
            new_scenario = oc_hiset_2(relay, oc_hiset, min_min_time=0)
            hiset_scenarios.append(new_scenario)

    ####################################################################################################################
    # There are downstream devices and at least some of them have hisets
    ####################################################################################################################
    else:
        new_scenarios = oc_hiset_ds(relay)
        if new_scenarios:
            hiset_scenarios = hiset_scenarios + new_scenarios

    # remove duplicates from hiset_scenarios list
    seen = set()
    hiset_scenarios_2 = []
    for sub_list in hiset_scenarios:
        sub_tuple = tuple(sub_list)
        if sub_tuple not in seen:
            hiset_scenarios_2.append(sub_list)
            seen.add(sub_tuple)

    return hiset_scenarios_2


def oc_hiset_ds(relay):
    """
    There are downstream devices and at least one of them has hisets
    Methodology for selecting relay hiset:
    Solution space of possible relay hisets: [1.3 x max downstream hiset, 1.3 x each max downstream relay fault
    level exceeding the downstream hiset].
    Represent this as a list of hiset_scenarios = [[hiset, mintime, hiset2, mintime2], [...], ....]
    """

    max_3p_fl = relay.netdat.max_3p_fl

    ds_hisets = [device.relset.oc_hiset for device in relay.netdat.downstream_devices]
    ds_hisets_on = [a for a in ds_hisets if type(a) is int or type(a) is float]

    hiset_scenarios = []
    # Get max downstream hiset
    max_hiset = max(ds_hisets_on)

    # Create a dictionary = {ds_relay with max hiset: relay hiset,
    # ds_relay with max fl exceeding max hiset: max_fl of downstream relay, ...}
    max_fl_dic = {"max hiset relay": max_hiset}

    # for each ds device max fault level that exceeds this, calculate the ds device trip time at the critical_fl
    for device in relay.netdat.downstream_devices:
        if device.netdat.max_3p_fl > max_hiset:
            max_fl_dic[device] = device.netdat.max_3p_fl

    while max_fl_dic:
        new_hiset = min(max_fl_dic.values())
        if 1.3 * new_hiset > max_3p_fl:
            break
        new_relays = [key for key in max_fl_dic if max_fl_dic[key] == new_hiset]
        highest_min_time = 0

        # from the relays in this dictionary, find the relay with largest trip time at critical grade
        for device in max_fl_dic:
            if device == "max hiset relay":
                continue
            device_trip_time = tt.relay_trip_time(device, new_hiset, f_type ='OC')
            if device_trip_time > highest_min_time:
                highest_min_time = device_trip_time

        # New scenario:
        relay_hs = 1.3 * new_hiset
        new_scenario = oc_hiset_2(relay, relay_hs, highest_min_time)
        hiset_scenarios.append(new_scenario)

        # remove the max_hiset_relay from the max_fl_dic dictionary
        for relay in new_relays:
            del max_fl_dic[relay]

    return hiset_scenarios


def oc_hiset_2(relay, oc_hiset, min_min_time):
    """
    Calculates relay hiset min time and hiset 2settings.
    Ensures hiset always grades over downstream fuse and inrush
    min_min_time is the minimum value that min_time is allowed to be set at (due to constraints listed outside this
    function)
    Returns a scenario [hiset, min_time, hiset2, min_time2]
    """

    if oc_hiset <= relay.netdat.tr_max_3p:
        ds_melting_time = fd.fuse_melting_time(relay.netdat.max_tr_fuse, oc_hiset)
        fuse_min_time = ds_melting_time + 0.1
    else:
        fuse_min_time = 0
    # Ensure hiset min time grades 0.05 over inrush and over fuse
    # Set the hiset2 if applicable
    if oc_hiset > 1.3 * relay.netdat.get_inrush():
        min_time = max(0.05, fuse_min_time, min_min_time)
        oc_hiset2 = "OFF"
        oc_min_time2 = "OFF"
    else:
        min_time = max(0.15, fuse_min_time, min_min_time)
        if relay.netdat.downstream_devices:
            max_ds_fl = max([device.netdat.max_3p_fl for device in relay.netdat.downstream_devices])
        else:
            max_ds_fl = 0
        oc_hiset2 = 1.3 * (max(max_ds_fl, relay.netdat.get_inrush()))
        if (oc_hiset < oc_hiset2 < relay.netdat.max_3p_fl
                and relay.manufacturer.oc_hiset2):
            oc_hiset2 = oc_hiset2
            oc_min_time2 = 0.05
        else:
            oc_hiset2 = "OFF"
            oc_min_time2 = "OFF"

    return [oc_hiset, min_time, oc_hiset2, oc_min_time2]



