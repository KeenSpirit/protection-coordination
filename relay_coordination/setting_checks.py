"""
The first iteration of the optimization routine (percentage = 1) will set the triggers which define paramerters
used to generate settings. Subsequent iterations will generate settings based on these triggers.

The test_iter variable counts the number of times newly generated settings violate the grading rules.
If the generated settings violate the grading rules too many times, the grading rules are relaxed via triggers,
and the process is repeated.
Reaching successive parameter iteration thresholds triggers the following constraint modifications:
a) Relax grading from nominal to the most exact grading margins
b) Keep nominal grading rules but include feeder relays with existing settings to the list of relays with modifiable
settings
c) Combine Steps 1 & 2
d) Relax fuse grading by -0.15s
e) Add any substation relays to the list of relays with modifiable settings
f) Increase relay slowest permissible clearing time
g) Grading not achieved. Attempt manual solution
"""

# TODO: Is there some way to assess why generated settings failed to grade, and if so, modify contraints in a more
#  targetted manner?
# TODO: Think about an optimization algorithm that optimizes one relay at a time.


from input_files.input_file import grading_parameters
from relay_coordination.setting_generators import generate_settings as gs
from relay_coordination import grading_margins as gm


# The grading_check_iter variable denotes how many times the script will attempt to generate relay settings that
# conform to grading constraints before aborting

grading_check_iter = grading_parameters().optimization_iter * 10

def check_settings(relays: list, triggers: list, percentage: float, f_type: str):
    """

    :param relays:
    :param triggers:
    :param percentage:
    :param f_type:
    :return:
    """

    new_relays = [relay for relay in relays if relay.relset.status in ["New", "Required"]]
    # Relays are sorted so that downstream relay settings are generated first
    new_relays = sorted(new_relays, key=lambda x: x.netdat.max_pg_fl)
    exist_feed_relays = [relay for relay in relays if relay.relset.status == "Existing" and relay.net.dat.i_split == 1]
    sub_bu_relays = [relay for relay in relays if relay.relset.status == "Existing" and relay.net.dat.i_split > 1]

    a, b, c, d, e, f, g = triggers
    if percentage < 1:
        if ((a == grading_check_iter and b < grading_check_iter)
                or (c == grading_check_iter and d < grading_check_iter)
                or (d == grading_check_iter and e < grading_check_iter)
                or (d == grading_check_iter and f < grading_check_iter)
                or f == grading_check_iter):
            g = generate_settings(new_relays, percentage, f_type, eval_type='Exact')
        else:
            g = generate_settings(new_relays, percentage, f_type, eval_type='Nominal')
        triggers = [a, b, c, d, e, f, g]
        return triggers

    a = generate_settings(new_relays, percentage, f_type, eval_type='Nominal')

    # Relax grading from 0.3s to the most exact grading margins
    if a == grading_check_iter:
        b = generate_settings(new_relays, percentage, f_type, eval_type='Exact')

    # Start adding relays from the existing_relays list in to the new_relays list. From the existing_relays list,
    # first add the relay with the lowest netdat.max_pg_fl, and re-run the assessment loop. Keep adding relays to the
    # new_relay list if the assessment loop keeps returning False
    if exist_feed_relays and a == b == grading_check_iter:
        grading_check = [False]
        c_1 = grading_check_iter
        while (exist_feed_relays and not all(grading_check)) and c_1 == grading_check_iter and c < grading_check_iter:
            min_pg = min([relay.netdat.max_pg_fl for relay in exist_feed_relays])
            for relay in exist_feed_relays:
                if relay.netdat.max_pg_fl == min_pg:
                    exist_feed_relays.remove(relay)
                    new_relays.append(relay)
                    relay.relset.status = "Required"
            new_relays = sorted(new_relays, key=lambda x: x.netdat.max_pg_fl)
            c_1 = generate_settings(new_relays, percentage, f_type, eval_type='Nominal')
            c += 1
    elif a == b == grading_check_iter:
        # There are no relays with existing settings. Skip the next trigger as it is identical to the b trigger loop.
        c == d == grading_check_iter

    # Attempt grading with all relay settings available and the most exact grading margins
    if a == b == c == grading_check_iter:
        d = generate_settings(new_relays, percentage, f_type, eval_type='Exact')

    # Relax fuse grading
    if a == b == c == d == grading_check_iter:
        grading_parameters().fuse_grading -= 0.15
        e = generate_settings(new_relays, percentage, f_type, eval_type='Exact')

    # Add substation bu relays to new_relays list
    if a == b == c == d == e == grading_check_iter:
        for relay in sub_bu_relays:
            relay.relset.status = "Required"
            new_relays.append(relay)
        f = generate_settings(new_relays, percentage, f_type, eval_type='Exact')

    # Relax permissible slowest primary and backup clearing times
    if a == b == c == d == e == f == grading_check_iter:
        grading_parameters().pri_slowest_clear += 1
        grading_parameters().bu_slowest_clear += 1
        g = generate_settings(new_relays, percentage, f_type, eval_type='Exact')

    triggers = [a, b, c, d, e, f, g]
    return triggers


def generate_settings(relays: list, percentage: float, f_type: str, eval_type: str):
    """
    Attempt to generate device settings that conform to grading checks. n attempts are permitted.
    :param relays:
    :param percentage: Setting variable analogous to temperature coefficient
    :param f_type: 'EF', 'OC'
    :param eval_type: 'Nominal', 'Exact'
    :return:
    """
    n = 0 
    grading_check = [False]
    while not all(grading_check) and n < grading_check_iter:
        if f_type == 'EF':
            grading_check = [gs.generate_ef_settings(relays, percentage)]
            grading_check.extend([gm.eval_grade_time(relay, f_type, eval_type) for relay in relays])
        elif f_type == 'OC':
            grading_check = [gs.generate_oc_settings(relays, percentage)]
            grading_check.extend([gm.eval_grade_time(relay, f_type, eval_type) for relay in relays])
        n += 1
    return n
