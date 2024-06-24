"""
Pick-up generator functions:
oc_pick_up(relay)
"""

from input_files.input_file import grading_parameters


def pick_up(relay, f_type):
    """
    Calculates the required protection relay element pick-up.
    The function uses an RNG to set the relay pickup within a specified range dictated by upper and lower bounds. If the
    bounds overlap they are dynamically adjusted according to a priority list of constraints.
    :param relay:
    :param f_type:
    :return:
    """

    ####################################################################################################################
    # Formulate constraints
    ####################################################################################################################

    lower_bounds = pu_lower_bounds(relay, f_type)
    upper_bounds = pu_upper_bounds(relay, f_type)

    hard_lower_bound = lower_bounds['load_factor']
    hard_upper_bound = upper_bounds['oc_reach']

    if hard_upper_bound < hard_lower_bound:
        # Pick-up generation failed
        return [hard_lower_bound, hard_upper_bound]

    ################################################################################################################
    # Set RNG bounds and EF pickup according to constraint priority
    ################################################################################################################

    priority_dic = {
        "max_value": 8,
        "ef_pu": 7,
        "upstream_pu": 6,
        "pu_factor": 5,
        "rating_factor": 4,
        "bu_reach": 3,
        "pri_reach": 1
    }

    if f_type == 'EF':
        priority_dic["load_factor"] = 9
    else:
        priority_dic["load_factor"] = 2

    while max(lower_bounds.values()) > min(upper_bounds.values()):
        max_lower_bounds = [key for key in lower_bounds if lower_bounds[key] == max(lower_bounds.values())]
        min_upper_bounds = [key for key in upper_bounds if upper_bounds[key] == min(upper_bounds.values())]
        #find the key with the highest priority.
        highest_priority = 10
        for key in max_lower_bounds:
            priority = priority_dic[key]
            if priority < highest_priority:
                highest_priority = priority
        highest_priority_lower = [i for i in priority_dic if priority_dic[i] == highest_priority][0]

        highest_priority = 10
        for key in min_upper_bounds:
            priority = priority_dic[key]
            if priority < highest_priority:
                highest_priority = priority
        highest_priority_upper = [i for i in priority_dic if priority_dic[i] == highest_priority][0]

        # Compare with key with the highest priority from other bound.
        # Whichever of the two priorities is lower, jettison all related keys from that dictionary.
        if priority_dic[highest_priority_lower] > priority_dic[highest_priority_upper] and len(lower_bounds) != 1:
            del lower_bounds[highest_priority_lower]
        elif len(upper_bounds) != 1:
            del upper_bounds[highest_priority_upper]
        else:
            break

    return [max(lower_bounds.values()), min(upper_bounds.values())]


def pu_lower_bounds(relay, f_type):
    """

    :param relay:
    :param f_type:
    :return:
    """

    if f_type == 'OC':
        load_factor = relay.netdat.load * 1.1                   # 110% of forecast load current
    else:
        load_factor = 0

    if not relay.netdat.rating:
        rating_factor = 0                                   # This isn't a feeder relay
    else:
        rating_factor = relay.netdat.rating * 1.11          # 111% of feeder conductor 2HR rating.

    # Check if downstream relays exist (don't need to back up ds fuses):
    ds_relays = [device for device in relay.netdat.downstream_devices
                 if hasattr(device, 'cb_interrupt')]
    if not ds_relays:
        ds_pu_factor = 0
    else:
        # Create list of downstream device pickups.
        if f_type == 'EF':
            pick_ups = [device.relset.ef_pu for device in ds_relays]
        else:
            pick_ups = [device.relset.oc_pu for device in ds_relays]
        # Max pick-up of these devices.
        ds_pu_factor = max(pick_ups) * 1.1                     # 110% of downstream relay pick-up

    if f_type == 'OC' and relay.relset.ef_pu:
        ef_pu = relay.relset.ef_pu * 1.1                    # 110% of earth fault pick-up
    else:
        ef_pu = 10

    lower_bounds = {
        "load_factor": load_factor, "rating_factor": rating_factor, "pu_factor": ds_pu_factor, "ef_pu": ef_pu
    }

    return lower_bounds


def pu_upper_bounds(relay, f_type):
    """

    :param relay:
    :param f_type:
    :return:
    """

    # PU < mininium fault level / reach_factor
    if f_type == 'EF':
        min_fl = relay.netdat.min_2p_fl
    else:
        min_fl = relay.netdat.min_pg_fl
    pri_reach = min_fl / grading_parameters().pri_reach_factor

    # Check if upstream existing devices exist:
    exist_upstream_device = [device for device in relay.netdat.upstream_devices if device.relset.status == "Existing"]
    if not exist_upstream_device:
        upstream_pu = 9999
    else:
        # Min pick-up of these existing upstream devices.
        if f_type == 'EF':
            upstream_pu = min([device.relset.ef_pu for device in exist_upstream_device])
        else:
            upstream_pu = min([device.relset.oc_pu for device in exist_upstream_device])

    # Check if downstream relays exist (don't need to back up ds fuses):
    ds_relays = [device for device in relay.netdat.downstream_devices if hasattr(device, 'cb_interrupt')]
    if not ds_relays:
        bu_reach = 9999
    else:
        # Min fl of these devices.
        # Create list of downstream device min fault levels
        if f_type == 'EF':
            bu_min_fl = [device.netdat.min_pg_fl for device in ds_relays]
        else:
            bu_min_fl = [device.netdat.min_2p_fl for device in ds_relays]
        # PU < mininium back-up fault level / bu_reach_factor
        bu_reach = min(bu_min_fl) / grading_parameters().bu_reach_factor

    upper_bounds = {
        "pri_reach": pri_reach, "bu_reach": bu_reach, "upstream_pu": upstream_pu, "max_value": 3000
    }

    return upper_bounds

