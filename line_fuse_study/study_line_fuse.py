"""
Get fault level data
Export fault level data to Fuse Selection Sheet Master V1.2 excel sheet
"""

import math
from relay_coordination import trip_time as tt
from input_files import fuse_inputs as fi
from input_files.input_file import GradingParameters


def line_fuse_study(all_devices):
    """

    :param all_devices:
    :return:
    """

    for device in all_devices:
        #TODO: determine which devices require a fuse study



def line_fuse(fuse):
    """

    :param fuse:
    :return:
    """

    df = fi.fuse_data()

    # Candidate fuses are the Energex standard EDO/MDO fuse sizes (as per Energex Technical Instruction TSD0019i)
    candidate_fuses = {'8T': 1, '16K': 2, '20K': 3, '25K': 4, '40K': 5, '50K': 6, '65K': 7, '80K':8}

    best_score = 0
    best_fuses = []
    # Get a list of best performing fuses
    for cand in candidate_fuses:
        fuse_score = tr_inrush_capability(df, cand, fuse)
        fuse_score += clp_capability(df, cand, fuse)
        fuse_score += load_capability(df, cand, fuse)
        fuse_score += ds_grade_capability(df, cand, fuse)
        fuse_score += min_fault_capability(df, cand, fuse)
        fuse_score += us_grade_capability(df, cand, fuse)
        if fuse_score == best_score:
            best_fuses.append(cand)
            best_score = fuse_score
        elif fuse_score > best_score:
            best_fuses = [cand]
            best_score = fuse_score

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


    # TODO: Create fuse study report and append it to the study results dataframe
    fuse_study_report(best_fuse)


def tr_inrush_capability(df, cand, fuse):
    """
    Transformer inrush capability
    Check to ensure that the fuse can withstand the expected transformer inrush curnent
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

    if min_melt_12_with > 0.1:
        score += 1

    return score


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

    if min_melt_load3 > 10:
        score += 1

    return score

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

    return score

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

    if ds_fuse_clear_3p / mdo_min_melt_3p <= 0.75:
        score += 1

    if ds_fuse_clear_2p / mdo_min_melt_2p <= 0.75:
        score += 1

    if ds_fuse_clear_pg / mdo_min_melt_pg <= 0.75:
        score += 1

    return score


def min_fault_capability(df, cand, fuse):
    # Clear faults at end of spur

    score = 0
    slowest_clearing_time = 3

    # total clearing time at minimum fault level
    fuse_clear_2p = tt.ip_fuse_time(df, cand, fuse.min_2p_fl, bound='Max')
    fuse_clear_pg = tt.ip_fuse_time(df, cand, fuse.min_pg_fl, bound='Max')

    if fuse_clear_2p <= slowest_clearing_time:
        score += 5

    if fuse_clear_pg <= slowest_clearing_time:
        score += 5

    return score


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
    fuse_grading = GradingParameters.fuse_grading

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

    if (us_tt_3p - fuse_clear_3p) <= fuse_grading:
        score += 1

    if (us_tt_pg - fuse_clear_pg) <= fuse_grading:
        score += 1

    return score


def fuse_study_report(best_fuse):

    pass
