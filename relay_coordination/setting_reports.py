import trip_time as tt
from relay_coord import iterations, grading_check_iter


def ef_report(best_relays):
    """

    :param best_relays:
    :return:
    """

    ef_setting_report = {
        "Criteria:": [
            "Downstream device earth fault minimum grading:",
            "Downstream max fuse earth fault minimum grading:",
            "Primary earth fault reach factor:",
            "Back-up earth fault reach factor:",
            "Earth fault fault slowest trip time:"
        ]
    }

    for relay in best_relays:
        # grading with all downstream relays

        # Check if downstream devices exist:
        if not relay.netdat.downstream_devices:
            ds_grading = "No downstream devices"
        else:
            for device in relay.netdat.downstream_devices:
                # Create a list of fault levels over which to compare curves
                b = [a for a in range(device.netdat.min_pg_fl, device.netdat.max_pg_fl, 1)]
                min_grading = 999
                for x in b:
                    trip_relay_1 = tt.relay_trip_time(device, x, f_type='EF')
                    trip_relay_2 = tt.relay_trip_time(relay, x, f_type='EF')
                    grading_time_d = trip_relay_2 - trip_relay_1
                    if grading_time_d < min_grading:
                        min_grading = round(grading_time_d, 3)
                ds_grading = min_grading

        # grading with downstream max fuse
        tr_max_pg = relay.netdat.tr_max_pg
        ds_melting_time = tt.fuse_melting_time(relay.netdat.max_tr_fuse, tr_max_pg)
        trip_relay = tt.relay_trip_time(relay, tr_max_pg, f_type='EF')
        fuse_grading_time = round(trip_relay - ds_melting_time, 3)
        max_fuse_grading = fuse_grading_time

        # reach factor
        primary_ef_reach = round(relay.netdat.min_pg_fl / relay.relset.ef_pu, 2)
        if relay.netdat.downstream_devices:
            ds_fl = min([device.netdat.min_pg_fl for device in relay.netdat.downstream_devices])
            bu_ef_reach = round(ds_fl / relay.relset.ef_pu, 2)
            bu_reach_factor = bu_ef_reach
        else:
            bu_reach_factor = "No downstream devices"

        # relay slowest operating time
        b = [a for a in range(relay.netdat.min_pg_fl, relay.netdat.max_pg_fl, 1)]
        slowest_trip = 0
        for x in b:
            trip_relay = tt.relay_trip_time(relay, x, f_type='EF')
            if trip_relay > slowest_trip:
                slowest_trip = round(trip_relay, 3)
        slowest_operate = slowest_trip

        ef_setting_report[relay.name] = [
            ds_grading, max_fuse_grading, primary_ef_reach, bu_reach_factor, slowest_operate
        ]

    return ef_setting_report


def oc_report(best_relays):
    """

    :param best_relays:
    :return:
    """

    oc_setting_report = {
        "Criteria:": [
            "Downstream device overcurrent minimum grading:",
            "Downstream max fuse 2 phase minimum grading:",
            "Trip time at inrush current:",
            "Primary overcurrent reach factor:",
            "Back-up overcurrent reach factor:",
            "Overcurrent pick up exceeds load factor (x1.1)?",
            "Overcurrent pick up exceeds rating factor (x1.1)?",
            "Overcurrent fault slowest trip time:"
        ]
    }

    for relay in best_relays:
        # grading with all downstream relays

        # Check if downstream devices exist:
        if not relay.netdat.downstream_devices:
            ds_grading = "No downstream devices"
        else:
            for device in relay.netdat.downstream_devices:
                # Create a list of fault levels over which to compare curves
                b = [a for a in range(device.netdat.min_2p_fl, device.netdat.max_3p_fl, 1)]
                min_grading = 999
                for x in b:
                    trip_relay_1 = tt.relay_trip_time(device, x, f_type='OC')
                    trip_relay_2 = tt.relay_trip_time(relay, x, f_type='OC')
                    grading_time_d = trip_relay_2 - trip_relay_1
                    if grading_time_d < min_grading:
                        min_grading = round(grading_time_d, 3)
                ds_grading = min_grading

        # grading with downstream max fuse
        tr_max_3p = relay.netdat.tr_max_3p
        ds_melting_time = tt.fuse_melting_time(relay.netdat.max_tr_fuse, tr_max_3p)
        trip_relay = tt.relay_trip_time(relay, tr_max_3p, f_type='OC')
        fuse_grading_time = round(trip_relay - ds_melting_time, 3)
        max_fuse_grading = fuse_grading_time

        # grading with inrush
        inrush = relay.netdat.get_inrush()
        if inrush > relay.netdat.max_3p_fl:
            trip_inrush = round(tt.relay_trip_time(relay, relay.netdat.max_3p_fl, f_type='OC'), 3)
        else:
            trip_inrush = round(tt.relay_trip_time(relay, inrush, f_type='OC'), 3)

        # reach factor
        primary_oc_reach = round(relay.netdat.min_2p_fl / relay.relset.oc_pu, 2)
        if relay.netdat.downstream_devices:
            ds_fl = min([device.netdat.min_2p_fl for device in relay.netdat.downstream_devices])
            bu_oc_reach = round(ds_fl / relay.relset.oc_pu, 2)
            bu_reach_factor = bu_oc_reach
        else:
            bu_reach_factor = "No downstream devices"

        # load factor
        load_factor = relay.netdat.load * 1.1
        if relay.relset.oc_pu > load_factor:
            l_f = "Yes"
        elif relay.netdat.load > 0:
            l_f = "No"
        else:
            l_f = "Load unknown"

        # feeder relay rating factor
        rating_factor = relay.netdat.rating * 1.11  # 111% of feeder conductor 2HR rating.
        if not relay.netdat.rating:
            r_f = "Rating factor unknown"
        elif relay.relset.oc_pu > rating_factor:
            r_f = "Yes"
        else:
            r_f = "No"

        # relay slowest operating time
        b = [a for a in range(relay.netdat.min_2p_fl, relay.netdat.max_3p_fl, 1)]
        slowest_trip = 0
        for x in b:
            trip_relay = tt.relay_trip_time(relay, x, f_type='OC')
            if trip_relay > slowest_trip:
                slowest_trip = round(trip_relay, 3)
        slowest_operate = slowest_trip

        oc_setting_report[relay.name] = [
            ds_grading, max_fuse_grading, trip_inrush, primary_oc_reach, bu_reach_factor, l_f, r_f, slowest_operate
        ]
    return oc_setting_report


def triggers_report(ef_triggers, oc_triggers, failed_ef, failed_oc):


    ef_a, ef_b, ef_c, ef_d, ef_e, ef_f, ef_g = ef_triggers
    ef_notes = []
    if ef_a == grading_check_iter:
        ef_report_a = "EF grading was altered from nominal margins to exact margins"
        ef_notes.append(ef_report_a)
    if ef_b == grading_check_iter:
        ef_report_b = "Existing feeder relay EF settings were change to 'Required'"
        ef_notes.append(ef_report_b)
    if ef_d == grading_check_iter:
        ef_report_d = "EF fuse grading margins were reduced by 0.15s"
        ef_notes.append(ef_report_d)
    if ef_e == grading_check_iter:
        ef_report_e = "existing substation relay EF settings were change to 'Required'"
        ef_notes.append(ef_report_e)
    if ef_f == grading_check_iter:
        ef_report_f = "Slowest permissible primary and backup clearing times were increased by 1s"
        ef_notes.append(ef_report_f)
    ef_report_g = f"There were {failed_ef} failed EF setting interations out of a total of {iterations}"
    ef_notes.append(ef_report_g)

    trigger_report_ef = {"EF Setting Notes": ef_notes}

    oc_a, oc_b, oc_c, oc_d, oc_e, oc_f, oc_g = oc_triggers
    oc_notes = []
    if oc_a == grading_check_iter:
        oc_report_a = "OC grading was altered from nominal margins to exact margins"
        oc_notes.append(oc_report_a)
    if ef_b == grading_check_iter:
        oc_report_b = "Existing feeder relay OC settings were change to 'Required'"
        oc_notes.append(oc_report_b)
    if ef_d == grading_check_iter:
        oc_report_d = "OC fuse grading margins were reduced by 0.15s"
        oc_notes.append(oc_report_d)
    if ef_e == grading_check_iter:
        oc_report_e = "existing substation relay OC settings were change to 'Required'"
        oc_notes.append(oc_report_e)
    if ef_f == grading_check_iter:
        oc_report_f = "Slowest permissible primary and backup clearing times were increased by 1s"
        oc_notes.append(oc_report_f)
    oc_report_g = f"There were {failed_oc} failed OC setting interations out of a total of {iterations}"
    oc_notes.append(oc_report_g)

    trigger_report_oc = {"OC Setting Notes": oc_notes}

    return {**trigger_report_ef, **trigger_report_oc}


def print_results(best_settings_ef, best_settings_oc, best_total_trip_oc, best_total_trip_ef):
    """
    DEPRECATED
    Prints results to the console output window
    """

    # Print results
    print("Optimized relay settings:")
    for best_relay in best_settings_oc:
        print(vars(best_relay.relset))
    for relay in best_settings_oc:
        relay.oc_setting_report()
        relay.ef_setting_report()
    print(f"Total oc trip time: {best_total_trip_oc} seconds")
    print(f"Total ef trip time: {best_total_trip_ef} seconds")

    # Plot results
    plot_results(best_settings_ef, "EF")
    plot_results(best_settings_oc, "OC")


def plot_results(relays, f_type):
    """
    DEPRECATED
    relay 1 = blue
    relay 2 = green
    relay 3 = red
    relay 4 = cyan
    relay 5 = magenta
    relay 6 = yellow
    relay 7 = black
    relay 8 = white
    """
    import matplotlib.pylab as plt

    colours = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    i = 0
    for relay in relays:
        if f_type == "OC":
            x1 = [x for x in list(range(int(round(relay.relset.oc_pu,0)) + 1, 5001))]
            y1 = [relay_trip_time(relay, x, f_type) for x in x1]
        else:
            x1 = [x for x in list(range(int(round(relay.relset.ef_pu, 0)) + 1, 5001))]
            y1 = [relay_trip_time(relay, x, f_type) for x in x1]

        plt.plot(x1, y1, colours[i], label=f_type + " " + relay.name)
        plt.legend(loc="upper right")
        if i in range(0, 7):
            i += 1
        else:
            i = 0
    plt.title('Relay coordination curves')
    plt.xlabel('Fault current')
    plt.ylabel('Time')
    plt.axis([0, 5000, 0, 5])
    plt.show()

