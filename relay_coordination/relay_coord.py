"""

"""

import copy
from input_files.input_file import GradingParameters
import trip_time as tt
import setting_checks as sc
import setting_reports as sr
from line_fuse_study import study_line_fuse as slf

# Set iterations of optimisation routine
iterations = GradingParameters().optimization_iter
# The grading_check_iter variable denotes how many times the script will attempt to generate relay settings that
# conform to grading constraints before aborting
grading_check_iter = iterations * 10


def relay_coordination(all_devices: list) -> tuple[list[object], dict]:
    """

    :param all_devices:
    :return:
    """

    fuse_setting_report = slf.line_fuse_study(all_devices)
    print("Running optimization routine")
    best_total_trip_ef, best_settings_ef, ef_triggers, failed_ef = best_relays(all_devices, f_type='EF')
    best_total_trip_oc, best_settings, oc_triggers, failed_oc = best_relays(all_devices, f_type='OC')
    print_results(best_total_trip_ef, ef_triggers, best_total_trip_oc, oc_triggers, failed_ef, failed_oc)

    ef_setting_report = sr.ef_report(best_settings, ef_triggers)
    oc_setting_report = sr.oc_report(best_settings, oc_triggers)
    setting_report = {**ef_setting_report, **oc_setting_report, **fuse_setting_report}
    # Change upstream devices and downstream devices from objects to strings for output file
    for device in best_settings:
        relay_network_data = device.netdat
        ds_devices = []
        if relay_network_data.downstream_devices:
            for ds_relay in device.netdat.downstream_devices:
                ds_devices.append(ds_relay.name)
        relay_network_data.downstream_devices = ds_devices
        us_devices = []
        if device.netdat.upstream_devices:
            for us_relay in relay_network_data.upstream_devices:
                us_devices.append(us_relay.name)
        relay_network_data.upstream_devices = us_devices

    return best_settings, setting_report


def best_relays(all_devices: list[object], f_type: str) -> tuple[float, list, list, int]:
    """

    :param all_devices:
    :param f_type:
    :return:
    """

    # Assess relays
    relays = [device for device in all_devices if hasattr(device, device.cb_interrupt)]

    best_total_trip = 1000000
    best_relays = []
    # Triggers are parameters indicating whether a solution has failed to converge under specified constraints.
    # When reaching a threshold value, this triggers formulation of new solutions under less stringent constraints.
    triggers = [0, 0, 0, 0, 0]
    failed_iter = 0
    for n in range(0, iterations):
        print(f"{f_type} settings iteration {n + 1} of {iterations}")
        # percentage is a variable that behaves similar to temperature in simulated annealing. It progressively
        # restricts bounds on setting parameter generation to converge on the best settings.
        percentage = 1 - (n / iterations)
        # Generate new relay settings under constraints
        triggers = sc.check_settings(relays, triggers, percentage, f_type)
        if triggers[4] == grading_check_iter:
            # Iteration failed to generate permissible settings
            failed_iter += 1
            continue
        total_trip_time = objective_function(relays, f_type)
        if total_trip_time < best_total_trip:
            best_total_trip = round(total_trip_time, 2)
            best_relays = copy.deepcopy(relays)
        relays = best_relays
    # If slowest clearing time was changed, revert the change.
    if triggers[3] == grading_check_iter or triggers[4] == grading_check_iter:
        GradingParameters().pri_slowest_clear -= 1
        GradingParameters().bu_slowest_clear -= 1

    return best_total_trip, best_relays, triggers, failed_iter


def objective_function(relays: list[object], f_type: str) -> float:
    """
    Calculate total trip time for all relays across all fault levels.
    :param relays:
    :param f_type: "EF", "OC".
    :return:
    """

    total_trip_time = 0
    for relay in relays:
        total_time = 0
        if f_type == 'EF':
            min_fl = relay.netdat.min_pg_fl
            max_fl = relay.netdat.max_pg_fl
        else:
            min_fl = relay.netdat.min_2p_fl
            max_fl = relay.netdat.max_3p_fl
        for x in range(min_fl, max_fl, 1):
            total_time += tt.relay_trip_time(relay, x,  f_type)
        total_trip_time += total_time

    return total_trip_time


def print_results(
        best_total_trip_ef: float,
        ef_triggers: list,
        best_total_trip_oc: float,
        oc_triggers: list,
        failed_ef: int,
        failed_oc: int
):
    """

    :param best_total_trip_ef:
    :param ef_triggers:
    :param best_total_trip_oc:
    :param oc_triggers:
    :return:

    """
    print(f"There were {failed_ef} failed EF iterations out of a total of {iterations} attempts")
    if ef_triggers[0] == grading_check_iter:
        print(f"EF Grading with existing settings not achieved using nominal margins.")
    if ef_triggers[1] == grading_check_iter:
        print(f"EF Grading with existing settings not achieved using exact margins.")
    if ef_triggers[2] == grading_check_iter:
        print(f"EF Grading with new settings not achieved using nominal margins.")
    if ef_triggers[3] == grading_check_iter:
        print(f"EF Grading with new settings not achieved using nominal margins "
              f"and relaxed clearing time after {iterations} iterations.")
    if ef_triggers[4] == grading_check_iter:
        print(f"EF grading not achieved after {iterations} iterations.")
    print(f"There were {failed_oc} failed OC iterations out of a total of {iterations} attempts")
    if oc_triggers[0] == grading_check_iter:
        print(f"OC Grading with existing settings not achieved using nominal margins.")
    if oc_triggers[1] == grading_check_iter:
        print(f"OC Grading with existing settings not achieved using exact margins.")
    if oc_triggers[2] == grading_check_iter:
        print(f"OC Grading with new settings not achieved using nominal margins.")
    if oc_triggers[3] == grading_check_iter:
        print(f"OC Grading with new settings not achieved using nominal margins and relaxed clearing time.")
    if oc_triggers[4] == grading_check_iter:
        print(f"OC grading not achieved after {iterations} iterations.")
    print(f"best_total_trip_oc: {best_total_trip_oc} seconds")
    print(f"best_total_trip_ef: {best_total_trip_ef} seconds")
    print(f"best_total_trip_oc: {best_total_trip_oc} seconds")