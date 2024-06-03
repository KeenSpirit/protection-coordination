from input_files.fuse_inputs import fuse_data_1 as fd_1
from input_files.fuse_inputs import fuse_data_2 as fd_2


def curve_parameters(curve: str) -> tuple[float, float]:
    """

    :param curve:
    :return:
    """
    if curve == 'SI' or 'si':
        k = 0.14
        a = 0.02
    elif curve == "VI" or 'vi':
        k = 13.5
        a = 1
    else:
        # curve = EI
        k = 80
        a = 2
    return k, a


def relay_trip_time(relay, fault_level, f_type):
    """Calculate relay trip time
    """
    if f_type == 'EF':
        pu = relay.relset.ef_pu
        tms = relay.relset.ef_tms
        curve = relay.relset.ef_curve
        hiset = relay.relset.ef_hiset
        min_time = relay.relset.ef_min_time
        hiset_2 = relay.relset.ef_hiset2
        min_time2 = relay.relset.ef_min_time2
    else:
        pu = relay.relset.oc_pu
        tms = relay.relset.oc_tms
        curve = relay.relset.oc_curve
        hiset = relay.relset.oc_hiset
        min_time = relay.relset.oc_min_time
        hiset_2 = relay.relset.oc_hiset2
        min_time2 = relay.relset.oc_min_time2

    k, a = curve_parameters(curve)

    multiplier = fault_level / pu
    operate_time = (k * tms) / (multiplier ** a - 1)
    if operate_time <= 0:
        operate_time = 9999
    saturate_curve = (k * tms) / (relay.ct.saturation ** a - 1)

    # hisets off
    if hiset == "OFF":
        if multiplier > relay.ct.saturation:
            trip_time = saturate_curve
        else:
            trip_time = operate_time
    # hiset 1 on, fault level less than hiset 1, hiset 2 off
    elif fault_level < hiset and hiset_2 == "OFF":
        if multiplier > relay.ct.saturation:
            trip_time = saturate_curve
        else:
            trip_time = operate_time
    # hiset 1 on, fault level greater than hiset 1, hiset 2 off
    elif fault_level >= hiset and hiset_2 == "OFF":
        trip_time = min_time
    # hiset 1 on, hiset 2 on, fault level less than hiset 1
    elif fault_level < hiset:
        if multiplier > relay.ct.saturation:
            trip_time = saturate_curve
        else:
            trip_time = operate_time
    # hiset 1 on, hiset 2 on, fault level between hiset 1 and hiset 2
    elif hiset <= fault_level < hiset_2:
        trip_time = min_time
    # hiset 1 on, hiset 2 on, fault level greater than hiset 2
    else:
        trip_time = min_time2

    assert trip_time >= 0, (f"Trip time error: {relay.name}, "
                                        f"fault type: {f_type}, "
                                          f"fault level: {fault_level}, "
                                          f"trip time: {trip_time}, "
                                          f"hiset: {hiset}, "
                                          f"min time: {min_time},"
                                          f"hiset2: {hiset_2},"
                                          f"min_time2: {min_time2}")
    # assert trip_time > 0, f"Trip time error: {trip_time}"

    return trip_time


def ef_tms_solver(relay: object, grading_parameters: object, function: str) -> float:
    """
    Calculate tms associated with slowest permissible fault clearing time
    :param relay:
    :param grading_parameters:
    :param function:
    :return:
    """
    if function == 'primary':
        fault_level = relay.netdat.min_pg_fl
        op_time = grading_parameters.pri_slowest_clear
    else:
        if relay.netdat.downstream_devices:
            fault_level = min([device.netdat.min_pg_fl for device in relay.netdat.downstream_devices])
            op_time = grading_parameters.bu_slowest_clear
        else:
            return False

    k, a = curve_parameters(relay.relset.ef_curve)

    multiplier = fault_level / relay.relset.ef_pu
    tms = ((multiplier ** a - 1) * op_time) / k

    return tms


def oc_tms_solver(relay: object, grading_parameters: object, function: str) -> float:
    """
    Calculate tms associated with slowest permissible fault clearing time
    :param relay:
    :param grading_parameters:
    :param function:
    :return:
    """
    if function == 'primary':
        fault_level = relay.netdat.min_2p_fl
        op_time = grading_parameters.pri_slowest_clear
    else:
        if relay.netdat.downstream_devices:
            fault_level = min([device.netdat.min_2p_fl for device in relay.netdat.downstream_devices])
            op_time = grading_parameters.bu_slowest_clear
        else:
            return False

    k, a = curve_parameters(relay.relset.oc_curve)

    multiplier = fault_level / relay.relset.oc_pu
    tms = ((multiplier ** a - 1) * op_time) / k

    return tms


def fuse_melting_time(fuse_name: str, fault_current: float) -> float:
    """
    Interpolates the fuse melting time for a given fuse and fault current.
    :param df: grade_sheet_fuse_data()
    :param fuse_name: Name of the fuse.
    :param fault_current: Fault current for which to interpolate the melting time.
    :return: Interpolated fuse melting time.
    """

    # Extract the column index of the fuse
    fuse_index = fd_1.columns.get_loc(fuse_name)

    # Sort the DataFrame by the fault current column
    df_sorted = fd_1.sort_values(by=fd_1.columns[0])

    # Interpolate the melting time for the given fault current
    melting_time = df_sorted.iloc[:, [0, fuse_index]].interpolate(method='linear'). \
        loc[df_sorted.iloc[:, 0].searchsorted(fault_current)].iloc[1]

    return melting_time


def ip_fuse_time(fuse_name, current: float, bound:str) -> float:
    """
    Interpolates fuse time from given current
    :param fuse_name:
    :param current:
    :param bound:
    :return:
    """

    if bound == 'Min':
        i_col = f"{fuse_name}minI"
        time_col = f"{fuse_name}minT"
    else:
        i_col = f"{fuse_name}totI"
        time_col = f"{fuse_name}totT"

    # Ensure the DataFrame is sorted by i_col
    df = fd_2.sort_values(i_col).reset_index(drop=True)

    time_interp = False
    # Find the rows where x lies between y1 and y2

    for i in range(len(df) - 1):
        if df.loc[i, i_col] <= current <= df.loc[i + 1, i_col]:
            y1, y2 = df.loc[i, i_col], df.loc[i + 1, i_col]
            z1, z2 = df.loc[i, time_col], df.loc[i + 1, time_col]

            # Linear interpolation formula
            time_interp = z1 + (current - y1) * (z2 - z1) / (y2 - y1)

    return time_interp


def ip_fuse_current(fuse_name, time: float, bound: str) -> float:
    """
    Interpolates fuse current from given time
    :param fuse_name:
    :param time:
    :param bound:
    :return:
    """

    if bound == 'Min':
        i_col = f"{fuse_name}minI"
        time_col = f"{fuse_name}minT"
    else:
        i_col = f"{fuse_name}totI"
        time_col = f"{fuse_name}totT"

    # Ensure the DataFrame is sorted by i_col
    df = fd_2.sort_values(time_col).reset_index(drop=True)

    time_interp = False
    # Find the rows where x lies between y1 and y2

    for i in range(len(df) - 1):
        if df.loc[i, time_col] <= time <= df.loc[i + 1, time_col]:
            y1, y2 = df.loc[i, time_col], df.loc[i + 1, time_col]
            z1, z2 = df.loc[i, i_col], df.loc[i + 1, i_col]

            # Linear interpolation formula
            time_interp = z1 + (time - y1) * (z2 - z1) / (y2 - y1)

    return time_interp
