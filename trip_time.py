
def ef_trip_time(relay, fault_level):
    """Calculate relay ef trip time
    """

    if relay.relset.ef_curve == 'SI' or 'si':
        k = 0.14
        a = 0.02
    elif relay.relset.ef_curve == "VI" or 'vi':
        k = 13.5
        a = 1
    else:
        # curve = EI
        k = 80
        a = 2

    multiplier = fault_level / relay.relset.ef_pu
    operate_time = (k * relay.relset.ef_tms) / (multiplier ** a - 1)
    if operate_time <= 0:
        operate_time = 9999
    saturate_curve = (k * relay.relset.ef_tms) / (relay.ct.saturation ** a - 1)

    # hisets off
    if relay.relset.ef_hiset == "OFF":
        if multiplier > relay.ct.saturation:
            trip_time = saturate_curve
        else:
            trip_time = operate_time
    # hiset 1 on, fault level less than hiset 1, hiset 2 off
    elif fault_level < relay.relset.ef_hiset and relay.relset.ef_hiset2 == "OFF":
        if multiplier > relay.ct.saturation:
            trip_time = saturate_curve
        else:
            trip_time = operate_time
    # hiset 1 on, fault level greater than hiset 1, hiset 2 off
    elif fault_level >= relay.relset.ef_hiset and relay.relset.ef_hiset2 == "OFF":
        trip_time = relay.relset.ef_min_time
    # hiset 1 on, hiset 2 on, fault level less than hiset 1
    elif fault_level < relay.relset.ef_hiset:
        if multiplier > relay.ct.saturation:
            trip_time = saturate_curve
        else:
            trip_time = operate_time
    # hiset 1 on, hiset 2 on, fault level between hiset 1 and hiset 2
    elif relay.relset.ef_hiset <= fault_level < relay.relset.ef_hiset2:
        trip_time = relay.relset.ef_min_time
    # hiset 1 on, hiset 2 on, fault level greater than hiset 2
    else:
        trip_time = relay.relset.ef_min_time2

    assert trip_time >= 0, (f"Trip time error: {relay.name}, "
                                          f"fault level: {fault_level}, "
                                          f"trip time: {trip_time}, "
                                          f"hiset: {relay.relset.ef_hiset}, "
                                          f"min time: {relay.relset.ef_min_time},"
                                          f"ef_hiset2: {relay.relset.ef_hiset2},"
                                          f"ef_min_time2: {relay.relset.ef_min_time2}")
    # assert trip_time > 0, f"Trip time error: {trip_time}"

    return trip_time


def oc_trip_time(relay, fault_level):
    """Calculate relay oc trip time
    """

    if relay.relset.oc_curve == 'SI' or 'si':
        k = 0.14
        a = 0.02
    elif relay.relset.oc_curve == "VI" or 'vi':
        k = 13.5
        a = 1
    else:
        # curve = EI
        k = 80
        a = 2

    multiplier = fault_level / relay.relset.oc_pu
    operate_time = (k * relay.relset.oc_tms) / (multiplier ** a - 1)
    if operate_time <= 0:
        operate_time = 9999
    saturate_curve = (k * relay.relset.oc_tms) / (relay.ct.saturation ** a - 1)

    # hisets off
    if relay.relset.oc_hiset == "OFF":
        if multiplier > relay.ct.saturation:
            trip_time = saturate_curve
        else:
            trip_time = operate_time
    # hiset 1 on, fault level less than hiset 1, hiset 2 off
    elif fault_level < relay.relset.oc_hiset and relay.relset.oc_hiset2 == "OFF":
        if multiplier > relay.ct.saturation:
            trip_time = saturate_curve
        else:
            trip_time = operate_time
    # hiset 1 on, fault level greater than hiset 1, hiset 2 off
    elif fault_level >= relay.relset.oc_hiset and relay.relset.oc_hiset2 == "OFF":
        trip_time = relay.relset.oc_min_time
    # hiset 1 on, hiset 2 on, fault level less than hiset 1
    elif fault_level < relay.relset.oc_hiset:
        if multiplier > relay.ct.saturation:
            trip_time = saturate_curve
        else:
            trip_time = operate_time
    # hiset 1 on, hiset 2 on, fault level between hiset 1 and hiset 2
    elif relay.relset.oc_hiset <= fault_level < relay.relset.oc_hiset2:
        trip_time = relay.relset.oc_min_time
    # hiset 1 on, hiset 2 on, fault level greater than hiset 2
    else:

        trip_time = relay.relset.oc_min_time2
    assert trip_time >= 0, (f"Trip time error: {relay.name}, "
                                          f"fault level: {fault_level}, "
                                          f"trip time: {trip_time}")
    # assert trip_time > 0, f"Trip time error: {trip_time}"

    return trip_time

