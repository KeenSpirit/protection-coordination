import random
from random import uniform
from setting_generators import hiset_generators as hg
from setting_generators import pickup_generators as pg
from setting_generators import tms_generators as tg


def generate_ef_settings(relays, percentage):
    """Function that generates new setting parameters to evaluate, based on constraints therein."""

    grading_check = True
    for relay in relays:
        ef_bounds = pg.ef_pick_up(relay)
        pu_range = ef_bounds[1] - ef_bounds[0]
        current_setting = relay.relset.ef_pu
        # furthest_bound = distance from current (best) setting to furtherest bound
        # new setting is drawn from a uniform distribution centered on the current setting and bounded by a percentage
        # distance to the furthest_bound. This percentage distance decreases proportional to the iteration progress.
        # If current setting is outside oc_bounds, new_setting will be taken from a percentage distance from closest
        # bound to fatherest_bound.

        if ef_bounds[0] < current_setting < ef_bounds[1]:
            dist_min = abs(current_setting - ef_bounds[0])
            dist_max = abs(current_setting - ef_bounds[1])
            if dist_max > dist_min:
                furthest_dist = dist_max
            else:
                furthest_dist = dist_min
            new_distance = percentage * furthest_dist
            new_min_bound = max((current_setting - new_distance), ef_bounds[0])
            new_max_bound = min((current_setting + new_distance), ef_bounds[1])
            relay.relset.ef_pu = relay.pu_converter(uniform(new_min_bound, new_max_bound), "EF")
        elif current_setting < ef_bounds[0]:
            new_max_bound = ef_bounds[0] + (percentage * pu_range)
            relay.relset.ef_pu = relay.pu_converter(uniform(ef_bounds[0], new_max_bound), "EF")
            pass
        else:
            new_min_bound = ef_bounds[1] - (percentage * pu_range)
            relay.relset.ef_pu = relay.pu_converter(uniform(new_min_bound, ef_bounds[1]), "EF")

        if round(uniform(0, 1)) < percentage:
            # hiset setting for all iterations will be a random choice from scenarios
            ef_hiset_scenarios = hg.ef_hiset_mintime(relay)
            relay_settings = random.choice(ef_hiset_scenarios)
            relay.relset.ef_hiset = relay_settings[0]
            relay.relset.ef_min_time = relay_settings[1]
            relay.relset.ef_hiset2 = relay_settings[2]
            relay.relset.ef_min_time2 = relay_settings[3]
            # curve selection for all iterations will be a random choice from scenarios
            ef_curve_scenarios = ["SI", "VI", "EI"]
            relay.relset.ef_curve = random.choice(ef_curve_scenarios)
        else:
            # use existing (best) relay settings
            pass

        if round(uniform(0, 1)) > 0.5:
            ef_tms_exact = tg.ef_tms_exact(relay)
            relay.relset.ef_tms = relay.tms_converter(ef_tms_exact)
        else:
            ef_tms_bounded = tg.ef_tms_bounded(relay)
            # If lower bound is less than upper bound, take a random value between them.
            if ef_tms_bounded[0] < ef_tms_bounded[1]:
                tms_range = ef_tms_bounded[1] - ef_tms_bounded[0]
                current_setting = relay.relset.ef_tms
                # furthest_bound = distance from current (best) setting to furtherest bound
                # new setting is drawn from a uniform distribution centered on the current setting and bounded by a percentage
                # distance to the furthest_bound. This percentage distance decreases proportional to the iteration progress.
                # If tms setting is outside tms_bounds, new_setting will be taken from a percentage distance from closest
                # bound to fatherest_bound.

                if ef_tms_bounded[0] < current_setting < ef_tms_bounded[1]:
                    dist_min = abs(current_setting - ef_tms_bounded[0])
                    dist_max = abs(current_setting - ef_tms_bounded[1])
                    if dist_max > dist_min:
                        furthest_dist = dist_max
                    else:
                        furthest_dist = dist_min
                    new_distance = percentage * furthest_dist
                    new_min_bound = max((current_setting - new_distance), ef_tms_bounded[0])
                    new_max_bound = min((current_setting + new_distance), ef_tms_bounded[1])
                    relay.relset.ef_tms = relay.tms_converter(uniform(new_min_bound, new_max_bound))
                elif current_setting < ef_tms_bounded[0]:
                    new_max_bound = ef_tms_bounded[0] + (percentage * tms_range)
                    relay.relset.ef_tms = relay.tms_converter(uniform(ef_tms_bounded[0], new_max_bound))
                    pass
                else:
                    new_min_bound = ef_tms_bounded[1] - (percentage * tms_range)
                    relay.relset.ef_tms = relay.tms_converter(uniform(new_min_bound, ef_tms_bounded[1]))
            else:
                # The relay won't grade. Need to flag for constraint relaxation
                grading_check = False
                break
    return grading_check


def generate_oc_settings(relays, percentage):
    """Function that generates new setting parameters to evaluate, based on constraints therein."""

    grading_check = True
    for relay in relays:
        oc_bounds = pg.oc_pick_up(relay)
        pu_range = oc_bounds[1] - oc_bounds[0]
        current_setting = relay.relset.oc_pu
        # furthest_bound = distance from current (best) setting to furtherest bound
        # new setting is drawn from a uniform distribution centered on the current setting and bounded by a percentage
        # distance to the furthest_bound. This percentage distance decreases proportional to the iteration progress.
        # If current setting is outside oc_bounds, new_setting will be taken from a percentage distance from closest
        # bound to fatherest_bound.

        if oc_bounds[0] < current_setting < oc_bounds[1]:
            dist_min = abs(current_setting - oc_bounds[0])
            dist_max = abs(current_setting - oc_bounds[1])
            if dist_max > dist_min:
                furthest_dist = dist_max
            else:
                furthest_dist = dist_min
            new_distance = percentage * furthest_dist
            new_min_bound = max((current_setting - new_distance), oc_bounds[0])
            new_max_bound = min((current_setting + new_distance), oc_bounds[1])
            relay.relset.oc_pu = relay.pu_converter(uniform(new_min_bound, new_max_bound), "OC")
        elif current_setting < oc_bounds[0]:
            new_max_bound = oc_bounds[0] + (percentage * pu_range)
            relay.relset.oc_pu = relay.pu_converter(uniform(oc_bounds[0], new_max_bound), "OC")
            pass
        else:
            new_min_bound = oc_bounds[1] - (percentage * pu_range)
            relay.relset.oc_pu = relay.pu_converter(uniform(new_min_bound, oc_bounds[1]), "OC")

        if round(uniform(0, 1)) < percentage:
            # hiset setting for all iterations will be a random choice from scenarios
            oc_hiset_scenarios = hg.oc_hiset_mintime(relay)
            relay_settings = random.choice(oc_hiset_scenarios)
            relay.relset.oc_hiset = relay_settings[0]
            relay.relset.oc_hiset_min_time = relay_settings[1]
            relay.relset.oc_hiset2 = relay_settings[2]
            relay.relset.oc_min_time2 = relay_settings[3]
            # curve selection for all iterations will be a random choice from scenarios
            oc_curve_scenarios = ["SI", "VI", "EI"]
            relay.relset.oc_curve = random.choice(oc_curve_scenarios)
        else:
            # use existing (best) relay settings
            pass

        if round(uniform(0, 1)) > 0.5:
            oc_tms_exact = tg.oc_tms_exact(relay)
            relay.relset.oc_tms = relay.tms_converter(oc_tms_exact)
        else:
            oc_tms_bounded = tg.oc_tms_bounded(relay)
            # If lower bound is less than upper bound, take a random value between them.
            if oc_tms_bounded[0] < oc_tms_bounded[1]:
                tms_range = oc_tms_bounded[1] - oc_tms_bounded[0]
                current_setting = relay.relset.oc_tms
                # furthest_bound = distance from current (best) setting to furtherest bound
                # new setting is drawn from a uniform distribution centered on the current setting and bounded by a percentage
                # distance to the furthest_bound. This percentage distance decreases proportional to the iteration progress.
                # If tms setting is outside tms_bounds, new_setting will be taken from a percentage distance from closest
                # bound to fatherest_bound.

                if oc_tms_bounded[0] < current_setting < oc_tms_bounded[1]:
                    dist_min = abs(current_setting - oc_tms_bounded[0])
                    dist_max = abs(current_setting - oc_tms_bounded[1])
                    if dist_max > dist_min:
                        furthest_dist = dist_max
                    else:
                        furthest_dist = dist_min
                    new_distance = percentage * furthest_dist
                    new_min_bound = max((current_setting - new_distance), oc_tms_bounded[0])
                    new_max_bound = min((current_setting + new_distance), oc_tms_bounded[1])
                    relay.relset.oc_tms = relay.tms_converter(uniform(new_min_bound, new_max_bound))
                elif current_setting < oc_tms_bounded[0]:
                    new_max_bound = oc_tms_bounded[0] + (percentage * tms_range)
                    relay.relset.oc_tms = relay.tms_converter(uniform(oc_tms_bounded[0], new_max_bound))
                    pass
                else:
                    new_min_bound = oc_tms_bounded[1] - (percentage * tms_range)
                    relay.relset.oc_tms = relay.tms_converter(uniform(new_min_bound, oc_tms_bounded[1]))
            else:
                # The relay won't grade. Need to flag for constraint relaxation
                grading_check = False
                break
    return grading_check



