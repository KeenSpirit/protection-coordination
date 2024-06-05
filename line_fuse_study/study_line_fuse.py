"""
Get fault level data
Export fault level data to Fuse Selection Sheet Master V1.2 excel sheet
"""

import math
from relay_coordination import trip_time as tt
from input_files import fuse_inputs as fi
from input_files.input_file import GradingParameters


def line_fuse_study(all_devices) -> dict[str | float:dict[str | float: str]]:
    """
    String 'green'/'red' is appended to results to facilitate conditional formatting in Excel.
    :param all_devices:
    :return:
    """

    fuse_setting_report = {
        "Criteria:": [
            "Fuse downstream capacity x 25 (inrush withstand):",
            "Fuse max load x 6 (clp capability):",
            "Fuse max load x 3 (clp capability):",
            "Fuse min melt at 300s (load capability):",
            "Fuse downstream TR 3P % time (ds grading):",
            "Fuse downstream TR 2P % time (ds grading):",
            "Fuse downstream TR PG % time (ds grading):",
            "Fuse min 2P clear time:",
            "Fuse min PG clear time:",
            "Fuse upstream device 3P grading margin:",
            "Fuse upstream device PG grading margin:",
        ]
    }

    for device in all_devices:
        if hasattr(device, device.relset.rating):
            # It's a fuse
            if device.relset.status != 'Existing':
                # New settings required
                device_report = line_fuse(device)
            else:
                device_report = {device: ['', '', '', '', '', '']}
        else:
            device_report = {device: ['', '', '', '', '', '']}
        fuse_setting_report.update(device_report)

    return fuse_setting_report


def line_fuse(fuse):
    """

    :param fuse:
    :return:
    """

    df = fi.fuse_data()

    # Candidate fuses are the Energex standard EDO/MDO fuse sizes (as per Energex Technical Instruction TSD0019i)
    candidate_fuses = {'8T': 1, '16K': 2, '20K': 3, '25K': 4, '40K': 5, '50K': 6, '65K': 7, '80K': 8}

    best_score = 0
    best_fuses = []
    fuse_reports = {}
    # Get a list of best performing fuses
    for cand in candidate_fuses:
        inrush_score, inrush_vals = tr_inrush_capability(df, cand, fuse)
        clp_score, clp_vals = clp_capability(df, cand, fuse)
        load_score, load_vals = load_capability(df, cand, fuse)
        ds_grade_score, ds_grade_vals = ds_grade_capability(df, cand, fuse)
        min_fault_score, min_fault_vals = min_fault_capability(df, cand, fuse)
        us_grade_score, us_grade_vals = us_grade_capability(df, cand, fuse)
        fuse_score = inrush_score + clp_score + load_score + ds_grade_score + min_fault_score + us_grade_score
        if fuse_score == best_score:
            best_fuses.append(cand)
            fuse_reports[cand] = inrush_vals + clp_vals + load_vals + ds_grade_vals + min_fault_vals + us_grade_vals
            best_score = fuse_score
        elif fuse_score > best_score:
            best_fuses = [cand]
            fuse_reports[cand] = inrush_vals + clp_vals + load_vals + ds_grade_vals + min_fault_vals + us_grade_vals
            best_score = fuse_score

    best_fuse = None
    # Select the smallest best fuse
    if len(best_fuses) == 1:
        best_fuse = best_fuses[0]
    else:
        min_value = 9
        for fuse in best_fuses:
            value = candidate_fuses[fuse]
            if value < min_value:
                min_value = value
                best_fuse = fuse

    fuse.relset.rating = best_fuse

    return fuse_reports[best_fuse]


def tr_inrush_capability(df, cand, fuse):
    """
    Transformer inrush capability
    Check to ensure that the fuse can withstand the expected transformer inrush curnent
    Dictionary values for excel conditional formatting are created for future implementation
    :param df:
    :param fuse:
    :param fuse_check:
    :return:
    """

    score = 0

    withstand_25 = 25 * fuse.ds_capacity    # for 0.01s
    withstand_12 = 12 * fuse.ds_capacity    # for 0.1s

    # Min melting time (lookup)
    min_melt_25_with = tt.ip_fuse_time(df, cand, withstand_25, bound='Min')
    min_melt_12_with = tt.ip_fuse_time(df, cand, withstand_12, bound='Min')

    if min_melt_25_with > 0.01:
        score += 1
        min_melt_25 = {min_melt_25_with: 'green'}
    else:
        min_melt_25 = {min_melt_25_with: 'red'}

    if min_melt_12_with > 0.1:
        score += 1
        min_melt_12 = {min_melt_12_with: 'green'}
    else:
        min_melt_12 = {min_melt_12_with: 'red'}

    return score, [min_melt_25_with, min_melt_12_with]


def clp_capability(df, cand, fuse):
    """
    Cold load pickup capability
    :param df:
    :param fuse:
    :param fuse_check:
    :return:
    """
    score = 0
    max_load_x6 = fuse.netdat.load * 6
    max_load_x3 = fuse.netdat.load * 3

    # Min melting time (lookup)
    min_melt_load6 = tt.ip_fuse_time(df, cand, max_load_x6, bound='Min')
    min_melt_load3 = tt.ip_fuse_time(df, cand, max_load_x3, bound='Min')

    if min_melt_load6 > 1:
        score += 1
        min_melt_6 = {min_melt_load6: 'green'}
    else:
        min_melt_6 = {min_melt_load6: 'red'}

    if min_melt_load3 > 10:
        score += 1
        min_melt_3 = {min_melt_load3: 'green'}
    else:
        min_melt_3 = {min_melt_load3: 'red'}

    return score, [min_melt_load6, min_melt_load3]

def load_capability(df, cand, fuse):
    """
    Max load current capability
    max load through MDO must be less equal or less than 80% of min melt current at 300s
    :param df:
    :param fuse:
    :param fuse_check:
    :return:
    """

    score = 0
    max_load = fuse.netdat.load

    min_melt_i_300s = tt.ip_fuse_current(df, cand, time=300, bound='Min')

    if max_load <= 0.8 * min_melt_i_300s:
        score += 1
        min_melt_300s = {min_melt_i_300s: 'green'}
    else:
        min_melt_300s = {min_melt_i_300s: 'red'}

    return score, [min_melt_i_300s]

def ds_grade_capability(df, cand, fuse):
    """
    Grade with largest downstream fuse with highest fault level
    EDO/MDO ratio must be equal or less than 75%
    :param df:
    :param fuse:
    :param fuse_check:
    :return:
    """
    score = 0
    # DS fuse fault level clearing time
    tr_max_2p = fuse.tr_max_3p * math.sqrt(3) / 2

    ds_fuse_clear_3p = tt.ip_fuse_time(df, cand, fuse.tr_max_3p, bound='Max')
    ds_fuse_clear_2p = tt.ip_fuse_time(df, cand, tr_max_2p, bound='Max')
    ds_fuse_clear_pg = tt.ip_fuse_time(df, cand, fuse.tr_max_pg, bound='Max')

    #MDO fuse minimum melt time at DS fuse max
    fuse_tr_max_2p = fuse.tr_max_3p * math.sqrt(3) / 2

    mdo_min_melt_3p = tt.ip_fuse_time(df, cand, fuse.tr_max_3p, bound='Min')
    mdo_min_melt_2p = tt.ip_fuse_time(df, cand, fuse_tr_max_2p, bound='Min')
    mdo_min_melt_pg = tt.ip_fuse_time(df, cand, fuse.tr_max_pg, bound='Min')

    ratio_3p = ds_fuse_clear_3p / mdo_min_melt_3p
    if ratio_3p <= 0.75:
        score += 1
        grade_3p = {ratio_3p: 'green'}
    else:
        grade_3p = {ratio_3p: 'red'}
    ratio_2P = ds_fuse_clear_2p / mdo_min_melt_2p
    if ratio_2P <= 0.75:
        score += 1
        grade_2p = {ratio_2P: 'green'}
    else:
        grade_2p = {ratio_2P: 'red'}
    ratio_pg = ds_fuse_clear_pg / mdo_min_melt_pg
    if ratio_pg <= 0.75:
        score += 1
        grade_pg = {ratio_pg: 'green'}
    else:
        grade_pg = {ratio_pg: 'red'}

    return score, [ratio_3p, ratio_2P, ratio_pg]


def min_fault_capability(df, cand, fuse):
    # Clear faults at end of spur

    score = 0
    slowest_clearing_time = 3

    # total clearing time at minimum fault level
    fuse_clear_2p = tt.ip_fuse_time(df, cand, fuse.min_2p_fl, bound='Max')
    fuse_clear_pg = tt.ip_fuse_time(df, cand, fuse.min_pg_fl, bound='Max')

    if fuse_clear_2p <= slowest_clearing_time:
        score += 5
        fault_2p = {fuse_clear_2p: 'green'}
    else:
        fault_2p = {fuse_clear_2p: 'red'}

    if fuse_clear_pg <= slowest_clearing_time:
        score += 5
        fault_pg = {fuse_clear_pg: 'green'}
    else:
        fault_pg = {fuse_clear_pg: 'red'}

    return score, [fuse_clear_2p, fuse_clear_pg]


def us_grade_capability(df, cand, fuse):
    """
    Grade with upstream protection
    Assumes that if there is upstream protection, it is a relay
    :param df:
    :param fuse:
    :param fuse_check:
    :return:
    """

    score = 0
    allowed_grading = GradingParameters.fuse_grading

    upstream_device = [fuse.upstream_devices][0]
    if not upstream_device:
        return score

    # total clearing time at maximum fault level
    fuse_clear_3p = tt.ip_fuse_time(df, cand, fuse.max_3p_fl, bound='Max')
    fuse_clear_pg = tt.ip_fuse_time(df, cand, fuse.max_pg_fl, bound='Max')

    # Upstream device trip time at max fuse fault current.
    try:
        us_tt_3p = tt.relay_trip_time(upstream_device, fuse.max_3p_fl, f_type='OC')
        us_tt_pg = tt.relay_trip_time(upstream_device, fuse.max_pg_fl, f_type='EF')
    except Exception:
        # If upstream device settings are unknown, return 0.
        return score

    fuse_grading_3p = us_tt_3p - fuse_clear_3p
    if fuse_grading_3p <= allowed_grading:
        score += 1
        grade_3p = {fuse_grading_3p: 'green'}
    else:
        grade_3p = {fuse_grading_3p: 'red'}
    fuse_grading_pg = us_tt_pg - fuse_clear_pg
    if fuse_grading_pg <= allowed_grading:
        score += 1
        grade_pg = {fuse_grading_pg: 'green'}
    else:
        grade_pg = {fuse_grading_pg: 'red'}

    return score, [fuse_grading_3p, fuse_grading_pg]

