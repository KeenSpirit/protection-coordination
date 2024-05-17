"""

"""

import time
import copy
import sys
import pandas as pd
import trip_time as tt
from setting_generators import generate_settings as gs
import grading_margins as gm
from inputs import input_file
import save_dataframe as save
import setting_reports as sr


# Set iterations of optimisation routine
iterations = 100
# The grading_check_iter variable denotes how many times the script will attempt to generate relay settings that
# conform to grading constraints before aborting
grading_check_iter = 1000


def main():
    """"""

    relays = input_file.input()

    ####################################################################################################################
    # Run optimization routine:
    ####################################################################################################################
    print("Running optimization routine")

    best_total_trip_ef, best_settings_ef = best_ef_relays(relays)
    best_total_trip_oc, best_settings_oc = best_oc_relays(relays)
    print(f"best_total_trip_ef: {best_total_trip_ef} seconds")
    print(f"best_total_trip_oc: {best_total_trip_oc} seconds")

    ef_setting_report = sr.ef_report(best_settings_oc)
    oc_setting_report = sr.oc_report(best_settings_oc)
    ef_setting_report = pd.DataFrame.from_dict(ef_setting_report)
    oc_setting_report = pd.DataFrame.from_dict(oc_setting_report)
    setting_report = pd.concat([ef_setting_report, oc_setting_report])
    new_list = []
    for relay in best_settings_oc:
        relay_network_data = relay.netdat
        ds_devices = []
        if relay_network_data.downstream_devices:
            for ds_relay in relay.netdat.downstream_devices:
                ds_devices.append(ds_relay.name)
        relay_network_data.downstream_devices = ds_devices
        us_devices = []
        if relay.netdat.upstream_devices:
            for us_relay in relay_network_data.upstream_devices:
                us_devices.append(us_relay.name)
        relay_network_data.upstream_devices = us_devices
        head = {'relay': relay.name, 'manufacturer': relay.manufacturer.__name__, "cb_interrupt": relay.cb_interrupt}
        relay_0 = {**head, **vars(relay.relset), **vars(relay.ct), **vars(relay.netdat)}
        new_list.append(relay_0)
    result = pd.DataFrame.from_dict(new_list)
    result_2 = result.set_index('relay').transpose()
    date_string = time.strftime("%Y%m%d-%H%M%S")
    filename = date_string + ' ' + 'Relay Coordination Results'
    save.save_dataframe(result_2, setting_report, filename)


def best_ef_relays(relays):
    """"""

    best_total_trip = 1000000
    best_relays = []
    # a, b, c are parameters indicating whether a solution has converged under specified constraints. When reaching a
    # threshold value, this triggers formulation of new solutions under less stringent constraints.
    a, b, c, d = 0, 0, 0, 0
    for n in range(0, iterations):
        print(f"EF settings iteration {n+1} of {iterations}")
        percentage = 1 - (n/iterations)
        # Generate new relay settings under constraints
        a, b, c, d = check_ef_settings(relays, a, b, c, d, percentage)
        if d == grading_check_iter and iterations == 1:
            print("EF grading not achieved. Attempt manual solution")
            sys.exit()

        total_trip_time = ef_objective_function(relays)
        if total_trip_time < best_total_trip:
            best_total_trip = round(total_trip_time, 2)
            best_relays = copy.deepcopy(relays)
        relays = best_relays
        if n == iterations:
            if a == grading_check_iter:
                print(f"EF Grading with existing settings not achieved using nominal margins after {n} iterations.")
            if b == grading_check_iter:
                print(f"EF Grading with existing settings not achieved using exact margins after {n} iterations.")
            if c == grading_check_iter:
                print(f"EF Grading with new settings not achieved using nominal margins after {n} iterations.")
        if d == grading_check_iter:
            print(f"EF grading not achieved after {n} iterations.")
            break

    return best_total_trip, best_relays


def best_oc_relays(relays):
    """"""

    best_total_trip = 999999
    best_relays = []
    # a, b, c are parameters indicating whether a solution has converged under specified constraints. They prevent new
    # iterations from attempting solutions that couldn't converge in prior iterations.
    a, b, c, d = 0, 0, 0, 0
    for n in range(0, iterations):
        print(f"OC settings iteration {n+1} of {iterations}")
        percentage = n / iterations
        # Generate new relay settings under constraints
        a, b, c, d = check_oc_settings(relays, a, b, c, d, percentage)
        if d == grading_check_iter and iterations == 1:
            print("OC grading not achieved. Attempt manual solution")
            sys.exit()

        total_trip_time = oc_objective_function(relays)
        if total_trip_time < best_total_trip:
            best_total_trip = round(total_trip_time, 2)
            best_relays = copy.deepcopy(relays)
        relays = best_relays
        if n == iterations:
            if a == grading_check_iter:
                print(f"OC Grading with existing settings not achieved using nominal margins after {n} iterations.")
            if b == grading_check_iter:
                print(f"OC Grading with existing settings not achieved using exact margins after {n} iterations.")
            if c == grading_check_iter:
                print(f"OC Grading with new settings not achieved using nominal margins after {n} iterations.")
        if d == grading_check_iter:
            print(f"OC grading not achieved after {n} iterations.")
            break

    return best_total_trip, best_relays


def check_ef_settings(relays, a, b, c, d, percentage):
    """
    The test_iter variable counts the number of times newly generated settings violate the grading rules.
    If the generated settings violate the grading rules too many times, the grading rules are relaxed, and the process
    is repeated.
    Reaching successive parameter iteration thresholds triggers the following constraint modifications:
    a) Relax grading from 0.3s to the most exact grading margins
    b) Keep nominal grading rules but include relays with existing settings to the list of relays with modifiable
    settings
    c) Combine Steps 1 & 2
    d) Grading not achieved. Attempt manual solution
    Relay CLP clearance up from 0.2s?
    Grading of upstream relays takes precedence over grading of downstream relays?
    Others...
    """

    new_relays = [relay for relay in relays if relay.relset.status in ["New", "Required"]]
    existing_relays = [relay for relay in relays if relay.relset.status == "Existing"]
    test_iter = 10000

    grading_check = [False]
    while not all(grading_check) and a < test_iter:
        # Generate new input variables, subject to their own constraints
        grading_check = [gs.generate_ef_settings(new_relays, percentage)]
        # Calculate grading time constraint to assess whether inputs need to be regenerated
        grading_check.extend([gm.ef_grade_time(relay) for relay in new_relays])
        a += 1
        assert a <= test_iter, "script stuck in ef loop 1"

    # violation handling
    grading_check = [False]
    if a == test_iter:
        print("EF Grading with existing settings not achieved using nominal margins.")
        # use code for oc_grading_exact(relay)
        while not all(grading_check) and b < test_iter:
            # Generate new input variables, subject to their own constraints
            grading_check = [gs.generate_ef_settings(new_relays, percentage)]
            # Calculate grading time constraint to assess whether inputs need to be regenerated
            grading_check.extend([gm.ef_grading_exact(relay) for relay in new_relays])
            b += 1
            assert b <= test_iter, "script stuck in ef loop 2"

    # start adding relays from the existing_relays list in to the new_relays list. from the existing_relays list,
    # first add the relay with the lowest netdat.max_pg_fl, and re-run the assessment loop. Keep adding relays to the
    # new_relay list if the assessment loop keeps returning False
    if b == test_iter:
        print("EF Grading with existing settings not achieved using exact margins.")
    if existing_relays and a == test_iter and b == test_iter:
        grading_check = [False]
        while (existing_relays and not all(grading_check)) and c < test_iter:
            min_pg = min([relay.netdat.max_pg_fl for relay in existing_relays])
            for relay in existing_relays:
                if relay.netdat.max_pg_fl == min_pg:
                    existing_relays.remove(relay)
                    new_relays.append(relay)
                    relay.relset.status = "Required"
            c_1 = 0
            while not all(grading_check) and c_1 < test_iter:
                if not existing_relays:
                    c_1 = test_iter
                    break
                # Generate new input variables, subject to their own constraints
                grading_check = [gs.generate_ef_settings(new_relays, percentage)]
                # Calculate grading time constraint to assess whether inputs need to be regenerated
                grading_check.extend([gm.ef_grade_time(relay) for relay in new_relays])
                c_1 += 1
                assert c_1 <= test_iter, "script stuck in ef loop 3"
            c += 1
            assert c <= test_iter, "script stuck in ef loop 4"
    elif b == grading_check_iter:
    # There are no existing relays
        return a, b, c, d

    # Attempt grading with all relay settings available and the most exact grading margins
    if a == test_iter and b == test_iter and c == test_iter:
        print("EF Grading with new settings not achieved using nominal margins.")
        # use code for oc_grading_exact(relay)
        while not all(grading_check) and d < test_iter:
            # Generate new input variables, subject to their own constraints
            grading_check = [gs.generate_ef_settings(new_relays, percentage)]
            # Calculate grading time constraint to assess whether inputs need to be regenerated
            grading_check.extend([gm.ef_grading_exact(relay) for relay in new_relays])
            d += 1
            assert d <= test_iter, "script stuck in ef loop 5"

    return a, b, c, d


def check_oc_settings(relays, a, b, c, d, percentage):
    """
    The test_iter variable counts the number of times newly generated settings violate the grading rules.
    If the generated settings violate the grading rules too many times, the grading rules are relaxed, and the process
    is repeated.
    Reaching successive parameter iteration thresholds triggers the following constraint modifications:
    a) Relax grading from 0.3s to the most exact grading margins
    b) Keep nominal grading rules but include relays with existing settings to the list of relays with modifiable
    settings
    c) Combine Steps 1 & 2
    d) Grading not achieved. Break loop.
    Relay CLP clearance up from 0.2s?
    Grading of upstream relays takes precedence over grading of downstream relays?
    Others...
    """

    new_relays = [relay for relay in relays if relay.relset.status in ["New", "Required"]]
    # Relays are sorted so that downstream relay settings are generated first
    new_relays = sorted(new_relays, key=lambda x: x.netdat.max_pg_fl)
    existing_relays = [relay for relay in relays if relay.relset.status == "Existing"]

    grading_check = [False]
    while not all(grading_check) and a < grading_check_iter:
        # Generate new input variables, subject to their own constraints
        grading_check = [gs.generate_oc_settings(new_relays, percentage)]
        # Calculate grading time constraint to assess whether inputs need to be regenerated
        grading_check.extend([gm.oc_grade_time(relay) for relay in new_relays])
        a += 1
        assert a <= grading_check_iter, "script stuck in oc loop 1"

    # violation handling
    grading_check = [False]
    if a == grading_check_iter:
        # Use code for oc_grading_exact(relay)
        while not all(grading_check) and b < grading_check_iter:
            # Generate new input variables, subject to their own constraints
            grading_check = [gs.generate_oc_settings(new_relays, percentage)]
            # Calculate grading time constraint to assess whether inputs need to be regenerated
            grading_check.extend([gm.oc_grade_time(relay) for relay in new_relays])
            b += 1
            assert b <= grading_check_iter, "script stuck in oc loop 2"

    # start adding relays from the existing_relays list in to the new_relays list. from the existing_relays list,
    # first add the relay with the lowest netdat.max_pg_fl, and re-run the assessment loop. Keep adding relays to the
    # new_relay list if the assessment loop keeps returning False
    if existing_relays and b == grading_check_iter:
        grading_check = [False]
        while (existing_relays and not all(grading_check)) and c < grading_check_iter:
            min_pg = min([relay.netdat.max_pg_fl for relay in existing_relays])
            for relay in existing_relays:
                if relay.netdat.max_pg_fl == min_pg:
                    existing_relays.remove(relay)
                    new_relays.append(relay)
                    relay.relset.status = "Required"
            c_1 = 0
            new_relays = sorted(new_relays, key=lambda x: x.netdat.max_pg_fl)
            while not all(grading_check) and c_1 < grading_check_iter:
                if not existing_relays:
                    c_1 = grading_check_iter
                    break
                # Generate new input variables, subject to their own constraints
                grading_check = [gs.generate_oc_settings(new_relays, percentage)]
                # Calculate grading time constraint to assess whether inputs need to be regenerated
                grading_check.extend([gm.oc_grade_time(relay) for relay in new_relays])
                c_1 += 1
                assert c_1 <= grading_check_iter, "script stuck in oc loop 3"
            c += 1
            assert c <= grading_check_iter, "script stuck in oc loop 4"
    elif b == grading_check_iter:
        # There are no existing relays
        return a, b, c, d

    # Attempt grading with all relay settings available and the most exact grading margins
    if c == grading_check_iter:
        # Use code for oc_grading_exact(relay)
        while not all(grading_check) and d < grading_check_iter:
            # Generate new input variables, subject to their own constraints
            grading_check = [gs.generate_oc_settings(new_relays, percentage)]
            # Calculate grading time constraint to assess whether inputs need to be regenerated
            grading_check.extend([gm.oc_grade_time(relay) for relay in new_relays])
            d += 1
            assert d <= grading_check_iter, "script stuck in oc loop 5"

    return a, b, c, d


def ef_objective_function(relays):
    """
    Minimize total trip time for all relays across all fault levels.
    Input variable is a list of ProtectionRelay classes
    """

    total_trip_time = 0
    for relay in relays:
        total_time = 0
        for x in range(relay.netdat.min_pg_fl, relay.netdat.max_pg_fl, 1):
            total_time += tt.ef_trip_time(relay, x)
        total_trip_time += total_time

    return total_trip_time


def oc_objective_function(relays):
    """
    Minimize total trip time for all relays across all fault levels.
    Input variable is a list of ProtectionRelay classes
    """

    total_trip_time = 0
    for relay in relays:
        total_time = 0
        for x in range(relay.netdat.min_2p_fl, relay.netdat.max_3p_fl, 1):
            total_time += tt.oc_trip_time(relay, x)
        total_trip_time += total_time

    return total_trip_time


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    run_time = round(end - start, 6)
    print(f"Script run time: {run_time} seconds")