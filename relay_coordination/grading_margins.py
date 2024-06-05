""" Two types of grading margin may be calculated: Grading with nominal margin depending on the technology type,
 and exact grading margins with parameters specific to the relay and fault level"""

from input_files.input_file import GradingParameters
import trip_time as tt


def eval_grade_time(relay: object, f_type: str, eval_type: str) -> list[bool]:
    """
    Calculate the relay required grading margin with a downstream relay (across the whole characteristic)
    :param relay:
    :param f_type:
    :param eval_type: 'Nominal', 'Exact'
    :return:
    If eval_type is 'Nominal':
    Where relays of different technologies are used, the time appropriate to the technology of the downstream relay
    should be used (NPAG, p 132).

    Use of a fixed grading margin is only appropriate at high fault levels. At lower levels, with longer
    operating times, the permitted error specified in IEC 60255 may exceed the fixed grading margin (NPAG, p 131).
    Hence, we also specify an exact grading margin, eval_type = 'Exact'.

    if eval_type is 'Exact':
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
        for ds_device in relay.netdat.downstream_devices:
            grading_eval.extend(_grade_time(ds_device, relay, f_type, eval_type))

    # Create a list of upstream devices with existing settings
    existing_upstream = [device for device in relay.netdat.upstream_devices if device.relset.status == "Existing"]
    if not existing_upstream:
        pass
    else:
        for us_device in existing_upstream:
            grading_eval.extend(_grade_time(relay, us_device, f_type, eval_type))

    grading_eval_all = all(grading_eval)

    return grading_eval_all


def _grade_time(ds_device: object, us_device: object, f_type: str, eval_type: str) -> list[bool]:
    """

    :param ds_device:
    :param us_device:
    :param f_type:
    :param eval_type: 'Nominal', 'Exact'
    :return:
    """

    eval = []
    # Create a list of fault levels over which to compare curves
    min_fl, max_fl = _min_max_fl(ds_device, f_type)
    b = [a for a in range(min_fl, max_fl, 1)]
    for x in b:
        if hasattr(ds_device, ds_device.cb_interrupt):
            trip_ds_device = tt.relay_trip_time(ds_device, x, f_type)
        else:
            trip_ds_device = tt.fuse_melting_time(ds_device.relset.rating, x)
        trip_us_device = tt.relay_trip_time(us_device, x, f_type)
        grading_actual = trip_us_device - trip_ds_device
        # Evaluate downstream grading against device technology
        eval.append(_grading_eval(ds_device, trip_ds_device, grading_actual, eval_type))

    return eval


def _grading_eval(device: object, device_trip: float, grading_actual: float, eval_type: str) -> bool:
    """

    :param device:
    :param device_trip:
    :param grading_actual:
    :param eval_type:
    :return:
    """

    if hasattr(device, device.cb_interrupt):
        if eval_type == 'Exact':
            grading_required = (((2 * device.manufacturer.timing_error + device.ct.ect) / 100) * device_trip
                                + device.cb_interrupt + device.manufacturer.overshoot
                                + device.manufacturer.safety_margin)
        elif device.manufacturer.technology == "Electro-mechanical":
            grading_required = GradingParameters().mechanical_grading
        elif device.manufacturer.technology == "Static":
            grading_required = GradingParameters().static_grading
        else:                       # device.manufacturer.technology == "Digital"
            grading_required = GradingParameters().digital_grading
    else:
        grading_required = GradingParameters().fuse_grading

    if grading_actual >= grading_required:
        eval = True
    else:
        eval = False

    return eval


def _min_max_fl(device: object, f_type: str) -> tuple[float, float]:
    if f_type == 'EF':
        min_fl = device.netdat.min_pg_fl
        max_fl = device.netdat.max_pg_fl
    else:
        min_fl = device.netdat.min_2p_fl
        max_fl = device.netdat.max_3p_fl
    return min_fl, max_fl

