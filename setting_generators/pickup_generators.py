"""
Pick-up generator functions:
oc_pick_up(relay)
ef_pick_up(relay)
"""


def ef_pick_up(relay):
    """Calculates the required protection relay earth fault pick-up.
    The function uses an RNG to set the relay pickup within a specified range dictated by upper and lower bounds. If the
    bounds overlap they are dynamically adjusted according to a priority list of constraints.
    For improvement: These should be subject to an annealing schedule"""

    ####################################################################################################################
    # Formulate setting parameters based on inputs
    ####################################################################################################################

    load_factor = relay.netdat.load * 0.1                                  # >= 10% of max load
    ef_reach = relay.netdat.min_pg_fl / 2                                  # PU < mininium primary fault level / 2

    # Check if upstream existing devices exist:
    existing_upstream_ef = [device for device in relay.netdat.upstream_devices
                            if device.relset.status == "Existing"]
    if not existing_upstream_ef:
        upstream_ef = 9999
    else:
        # Min pick-up of these existing upstream devices.
        upstream_ef = min([device.relset.ef_pu for device in existing_upstream_ef])

    # Check if downstream devices exist:
    if not relay.netdat.downstream_devices:
        ef_pu_factor = 0
        ef_bu_reach = 9999
    else:
        # Create list of downstream device pickups.
        ef_pus = [device.relset.ef_pu for device in relay.netdat.downstream_devices]
        # Min pick-up of these devices.
        ef_pu_factor = max(ef_pus) * 1.1                        # 110% of downstream relay pick-up
        # Create list of downstream device min fault levels
        bu_pg_min = [device.netdat.min_pg_fl for device in relay.netdat.downstream_devices]
        ef_bu_reach = min(bu_pg_min) / 1.5                      # PU < minimum back-up fault level / 1.5

    ####################################################################################################################
    # List constraints from lowest to highest priority
    ####################################################################################################################

    hard_lower_bound = load_factor
    hard_upper_bound = ef_reach
    if hard_upper_bound < hard_lower_bound:
        # you need to use negative phase sequence protection
        raise Exception(f"load factor exceeds EF reach factor - {relay.name} EF element cannot grade properly")

    lower_bounds = {
        "load_factor": load_factor, "ef_pu_factor": ef_pu_factor, "min_value": 10
    }
    upper_bounds = {
        "ef_reach": ef_reach, "ef_bu_reach": ef_bu_reach, "upstream_ef": upstream_ef, "max_value": 2000
    }

    priority_dic = {
        "max_value": 7,
        "min_value": 6,
        "upstream_ef": 5,
        "ef_pu_factor": 4,
        "ef_bu_reach": 3,
        "load_factor": 2,
        "ef_reach": 1
    }

    ################################################################################################################
    # Set RNG bounds and EF pickup according to constraint priority
    ################################################################################################################

    while max(lower_bounds.values()) > min(upper_bounds.values()):
        max_lower_bounds = [key for key in lower_bounds if lower_bounds[key] == max(lower_bounds.values())]
        min_upper_bounds = [key for key in upper_bounds if upper_bounds[key] == min(upper_bounds.values())]
        #find the key with the highest priority.
        highest_priority = 9
        for key in max_lower_bounds:
            priority = priority_dic[key]
            if priority < highest_priority:
                highest_priority = priority
        highest_priority_lower = [i for i in priority_dic if priority_dic[i] == highest_priority][0]

        highest_priority = 9
        for key in min_upper_bounds:
            priority = priority_dic[key]
            if priority < highest_priority:
                highest_priority = priority
        highest_priority_upper = [i for i in priority_dic if priority_dic[i] == highest_priority][0]

        # compare with key with the highest priority from other bound.
        # Whichever of the two priotiries is lower, jettison all related keys from that dictionary.
        if priority_dic[highest_priority_lower] > priority_dic[highest_priority_upper] and len(lower_bounds) > 1:
            del lower_bounds[highest_priority_lower]
        elif len(upper_bounds) > 1:
            del upper_bounds[highest_priority_upper]
        else:
            break

    return [max(lower_bounds.values()), min(upper_bounds.values())]


def oc_pick_up(relay):
    """Calculates the required protection relay overcurrent pick-up.
    The function uses an RNG to set the relay pickup within a specified range dictated by upper and lower bounds. If the
    bounds overlap they are dynamically adjusted according to a priority list of constraints.
    For improvement: These should be subject to an annealing schedule using the best_settings list"""

    ####################################################################################################################
    # Formulate setting parameters based on inputs
    ####################################################################################################################

    load_factor = relay.netdat.load * 1.1                      # 110% of forecast load current

    if not relay.netdat.rating:
        rating_factor = 0                                       # This isn't a feeder relay
    else:
        rating_factor = relay.netdat.rating * 1.11            # 111% of feeder conductor 2HR rating.
    oc_reach = relay.netdat.min_2p_fl / 2                      # PU < minimium primary fault level / 2

    # Check if upstream existing devices exist:
    existing_upstream_oc = [device for device in relay.netdat.upstream_devices
                            if device.relset.status == "Existing"]
    if not existing_upstream_oc:
        upstream_oc = 9999
    else:
        # Min pick-up of these existing upstream devices.
        upstream_oc = min([device.relset.oc_pu for device in existing_upstream_oc])

    # Check if downstream devices exist:
    if not relay.netdat.downstream_devices:
        oc_pu_factor = 0
        oc_bu_reach = 9999
    else:
        # Create list of downstream device pickups.
        oc_pus = [device.relset.oc_pu for device in relay.netdat.downstream_devices]
        # Max pick-up of these devices.
        oc_pu_factor = max(oc_pus) * 1.1    # 110% of downstream relay pick-up
        # Create list of downstream device min fault levels
        bu_pp_min = [device.netdat.min_2p_fl for device in relay.netdat.downstream_devices]
        # PU < mininium back-up fault level / 1.5
        oc_bu_reach = min(bu_pp_min) / 1.5

    if relay.relset.ef_pu:
        ef_pu = relay.relset.ef_pu * 1.1    # 110% of earth fault pick-up
    else:
        ef_pu = 10

    ####################################################################################################################
    # List constraints
    ####################################################################################################################

    hard_lower_bound = load_factor
    hard_upper_bound = oc_reach
    if hard_upper_bound < hard_lower_bound:
        # you need to use negative phase sequence protection
        raise Exception(f"load factor exceeds OC reach factor - {relay.name} OC element cannot grade properly")

    lower_bounds = {
        "load_factor": load_factor, "rating_factor": rating_factor, "oc_pu_factor": oc_pu_factor, "ef_pu": ef_pu
    }
    upper_bounds = {
        "oc_reach": oc_reach, "oc_bu_reach": oc_bu_reach, "upstream_oc": upstream_oc, "max_value": 3000
    }

    ################################################################################################################
    # Set RNG bounds and EF pickup according to constraint priority
    ################################################################################################################

    priority_dic = {
        "max_value": 8,
        "ef_pu": 7,
        "upstream_oc": 6,
        "oc_pu_factor": 5,
        "rating_factor": 4,
        "oc_bu_reach": 3,
        "load_factor": 2,
        "oc_reach": 1
    }

    while max(lower_bounds.values()) > min(upper_bounds.values()):
        max_lower_bounds = [key for key in lower_bounds if lower_bounds[key] == max(lower_bounds.values())]
        min_upper_bounds = [key for key in upper_bounds if upper_bounds[key] == min(upper_bounds.values())]
        #find the key with the highest priority.
        highest_priority = 9
        for key in max_lower_bounds:
            priority = priority_dic[key]
            if priority < highest_priority:
                highest_priority = priority
        highest_priority_lower = [i for i in priority_dic if priority_dic[i] == highest_priority][0]

        highest_priority = 9
        for key in min_upper_bounds:
            priority = priority_dic[key]
            if priority < highest_priority:
                highest_priority = priority
        highest_priority_upper = [i for i in priority_dic if priority_dic[i] == highest_priority][0]

        # compare with key with highest priority from other bound.
        # Whichever of the two priotiries is lower, jettison all related keys from that dictionary.
        if priority_dic[highest_priority_lower] > priority_dic[highest_priority_upper] and len(lower_bounds) != 1:
            del lower_bounds[highest_priority_lower]
        elif len(upper_bounds) != 1:
            del upper_bounds[highest_priority_upper]
        else:
            break

    return [max(lower_bounds.values()), min(upper_bounds.values())]



