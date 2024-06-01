""" Two types of grading margin may be calculated: Grading with nominal margin depending on the technology type,
 and exact grading margins with parameters specific to the relay and fault level"""

from input_files.input_file import GradingParameters
import trip_time as tt

def ef_grade_time(relay):
    """Grade time with all downstream devices and with upstream devices having existing settings is calculated"""

    # Provisional grading criteria (NPAG, p. 132)
    electro_m = ["Electro-mechanical", "electro-mechanical", GradingParameters().mechanical_grading]
    static = ["Static", "static", GradingParameters().static_grading]
    digital_numeric = ["Digital", "digital", "Numeric", "numeric", GradingParameters().digital_grading]

    grading_eval = []
    # For each relay in the downstream list:
    # Check if downstream devices exist:
    if not relay.netdat.downstream_devices:
        grading_eval.append(True)
    else:
        for device in relay.netdat.downstream_devices:
            # Create a list of fault levels over which to compare curves
            b = [a for a in range(device.netdat.min_pg_fl, device.netdat.max_pg_fl, 1)]
            for x in b:
                trip_relay_1 = tt.relay_trip_time(device, x, f_type='EF')
                trip_relay_2 = tt.relay_trip_time(relay, x, f_type='EF')
                grading_time_d = trip_relay_2 - trip_relay_1
                # Evaluate downstream grading against relay technology
                if device.manufacturer.technology in electro_m:
                    if grading_time_d >= electro_m[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                elif device.manufacturer.technology in static:
                    if grading_time_d >= static[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                elif device.manufacturer.technology in digital_numeric:
                    if grading_time_d >= digital_numeric[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                else:
                    raise NameError('Relay technology input in incorrect format')

    # Create a list of upstream devices with existing settings
    existing_upstream_ef = [device for device in relay.netdat.upstream_devices if device.relset.status == "Existing"]
    if not existing_upstream_ef:
        pass
    else:
        for device in existing_upstream_ef:
            # Create a list of fault levels over which to compare curves
            b = [a for a in range(relay.netdat.min_pg_fl, relay.netdat.max_pg_fl, 1)]
            # For each fault level, calculate the grading time
            for x in b:
                trip_relay_1 = tt.relay_trip_time(relay, x, f_type='EF')
                trip_relay_2 = tt.relay_trip_time(device, x, f_type='EF')
                grading_time_u = trip_relay_2 - trip_relay_1
                if relay.manufacturer.technology in electro_m:
                    if grading_time_u >= electro_m[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                elif relay.manufacturer.technology in static:
                    if grading_time_u >= static[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                elif relay.manufacturer.technology in digital_numeric:
                    if grading_time_u >= digital_numeric[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                else:
                    raise NameError('Relay technology input in incorrect format')

    grading_eval_all = all(grading_eval)

    return grading_eval_all


def oc_grade_time(relay):
    """Grade time with all downstream devices and with upstream devices having existing settings is calculated
    """

    #Provisional grading criteria (NPAG, p. 132)
    electro_m = ["Electro-mechanical", "electro-mechanical", GradingParameters().mechanical_grading]
    static = ["Static", "static", GradingParameters().static_grading]
    digital_numeric = ["Digital", "digital", "Numeric", "numeric", GradingParameters().digital_grading]

    grading_eval = []
    # For each relay in the downstream list:
    # Check if downstream devices exist:
    if not relay.netdat.downstream_devices:
        grading_eval.append(True)
    else:
        for device in relay.netdat.downstream_devices:
            # Create a list of fault levels over which to compare curves
            b = [a for a in range(device.netdat.min_2p_fl, device.netdat.max_3p_fl, 1)]
            for x in b:
                trip_relay_1 = tt.relay_trip_time(device, x, f_type='OC')
                trip_relay_2 = tt.relay_trip_time(relay, x, f_type='OC')
                grading_time_d = trip_relay_2 - trip_relay_1
                # Evaluate downstream grading against relay technology
                if device.manufacturer.technology in electro_m:
                    if grading_time_d >= electro_m[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                elif device.manufacturer.technology in static:
                    if grading_time_d >= static[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                elif device.manufacturer.technology in digital_numeric:
                    if grading_time_d >= digital_numeric[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)

                else:
                    raise NameError('Relay technology input in incorrect format')

    # Create a list of upstream devices with existing settings (there should be max of 1...)
    existing_upstream_oc = [device for device in relay.netdat.upstream_devices if device.relset.status == "Existing"]
    if existing_upstream_oc:
        for device in existing_upstream_oc:
            # Create a list of fault levels over which to compare curves
            b = [a for a in range(relay.netdat.min_2p_fl, relay.netdat.max_3p_fl, 1)]
            # For each fault level, calculate the grading time
            for x in b:
                trip_relay_1 = tt.relay_trip_time(relay, x, f_type='OC')
                trip_relay_2 = tt.relay_trip_time(device, x, f_type='OC')
                grading_time_u = trip_relay_2 - trip_relay_1
                if relay.manufacturer.technology in electro_m:
                    if grading_time_u >= electro_m[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                elif relay.manufacturer.technology in static:
                    if grading_time_u >= static[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                elif relay.manufacturer.technology in digital_numeric:
                    if grading_time_u >= digital_numeric[-1]:
                        grading_eval.append(True)
                    else:
                        grading_eval.append(False)
                else:
                    raise NameError('Relay technology input in incorrect format')

    # If all grading points measures equal True, return a True result. Else return a False result.
    grading_eval_all = all(grading_eval)

    return grading_eval_all


def ef_grading_exact(relay):
    """ Calculate the relay required grading margin with a downstream relay (across the whole characteristic).

    Where relays of different technologies are used, the time appropriate to the technology of the downstream relay
    should be used (NPAG, p 132).

    Note: Use of a fixed grading margin is only appropriate at high fault levels. At lower levels, with longer
    operating times, the permitted error specified in IEC 60255 may exceed the fixed grading margin (NPAG, p 131).

    er = relay timing error(%) of downstream relay. Relay error index is quoted by manufacturer
    ect = maximum CT ratio error (%) of downstream relay. Equal to CT composite error.
    (It can be shown that the time error for a class 10P CT will result in a max timing error of less than 10% for
    currents between about 3 and 20 times the current setting - being 9% at 3x setting and 4% at 20 times setting
    (QUT PESTC EEP211 p 124).)
    t = operating time of downstream relay (s)
    tcb = CB interrupting time(varies depending on oil CB or vacuum CB and fault current to be interrupted)
    See manufacturer for details. Does PowerFactory give the CB manufacturer?
    to = relay overshoot of downstream relay(s)
    ts = safety margin (s)
    """

    grading_eval = []
    # For each relay in the downstream list:
    # Check if downstream devices exist:
    if not relay.netdat.downstream_devices:
        grading_eval.append(True)
    else:
        for device in relay.netdat.downstream_devices:
            # Create a list of fault levels over which to compare curves
            b = [a for a in range(device.netdat.min_pg_fl, device.netdat.max_pg_fl, 1)]
            for x in b:
                t_device = tt.relay_trip_time(device, x, f_type='EF')
                t_relay = tt.relay_trip_time(relay, x, f_type='EF')
                grading_actual = t_relay - t_device
                grading_required = (((2 * device.manufacturer.timing_error + device.ct.ect) / 100) * t_device
                                    + device.cb_interrupt + device.manufacturer.overshoot
                                    + device.manufacturer.safety_margin)
                if grading_actual >= grading_required:
                    grading_eval.append(True)
                else:
                    grading_eval.append(False)

    # Create a list of upstream devices with existing settings (there should be max of 1...)
    existing_upstream_ef = [device for device in relay.netdat.upstream_devices if
                            device.relset.status == "Existing"]
    if not existing_upstream_ef:
        pass
    else:
        for device in existing_upstream_ef:
            # Create a list of fault levels over which to compare curves
            b = [a for a in range(relay.netdat.min_pg_fl, relay.netdat.max_pg_fl, 1)]
            # For each fault level, calculate the grading time
            for x in b:
                trip_relay_1 = tt.relay_trip_time(relay, x, f_type='EF')
                trip_relay_2 = tt.relay_trip_time(device, x, f_type='EF')
                grading_time_u = trip_relay_2 - trip_relay_1
                grading_required = (((2 * relay.manufacturer.timing_error + relay.ct.ect) / 100) * trip_relay_1
                                    + relay.cb_interrupt + relay.manufacturer.overshoot
                                    + relay.manufacturer.safety_margin)
                if grading_time_u >= grading_required:
                    grading_eval.append(True)
                else:
                    grading_eval.append(False)

    # If all grading point evaluations equal True, return a True result. Else return a False result.
    grading_eval_all = all(grading_eval)
    return grading_eval_all


def oc_grading_exact(relay):
    """
    Calculate the relay required grading margin with a downstream relay (across the whole characteristic).
    """

    grading_eval = []
    # For each relay in the downstream list:
    # Check if downstream devices exist:
    if not relay.netdat.downstream_devices:
        grading_eval.append(True)
    else:
        for device in relay.netdat.downstream_devices:
            # Create a list of fault levels over which to compare curves
            b = [a for a in range(device.netdat.min_2p_fl, device.netdat.max_3p_fl, 1)]
            for x in b:
                t_ds_device = tt.relay_trip_time(device, x, f_type='OC')
                t_relay = tt.relay_trip_time(relay, x, f_type='OC')
                grading_actual = t_relay - t_ds_device
                grading_required = (((2 * device.manufacturer.timing_error + device.ct.ect) / 100) * t_ds_device
                                    + device.cb_interrupt + device.manufacturer.overshoot
                                    + device.manufacturer.safety_margin)
                if grading_actual >= grading_required:
                    grading_eval.append(True)
                else:
                    grading_eval.append(False)

    # Create a list of upstream devices with existing settings (there should be max of 1...)
    existing_upstream_oc = [device for device in relay.netdat.upstream_devices if device.relset.status == "Existing"]
    if not existing_upstream_oc:
        pass
    else:
        for device in existing_upstream_oc:
            # Create a list of fault levels over which to compare curves
            b = [a for a in range(relay.netdat.min_2p_fl, relay.netdat.max_3p_fl, 1)]
            # For each fault level, calculate the grading time
            for x in b:
                trip_relay_1 = tt.relay_trip_time(relay, x, f_type='OC')
                trip_relay_2 = tt.relay_trip_time(device, x, f_type='OC')
                grading_time_u = trip_relay_2 - trip_relay_1
                grading_required = (((2 * relay.manufacturer.timing_error + relay.ct.ect) / 100) * trip_relay_1
                                    + relay.cb_interrupt + relay.manufacturer.overshoot
                                    + relay.manufacturer.safety_margin)
                if grading_time_u >= grading_required:
                    grading_eval.append(True)
                else:
                    grading_eval.append(False)

    # If all grading point evaluations equal True, return a True result. Else return a False result.
    grading_eval_all = all(grading_eval)
    return grading_eval_all