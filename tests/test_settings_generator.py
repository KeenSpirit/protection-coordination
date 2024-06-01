from random import uniform
import time
import unittest
import settings_generator as sg
import matplotlib.pylab as plt
from relay_coordination import trip_time as tt
from inputs import input_file


start = time.time()

def main():

    relays = input_file.inputs()
    print(relays)

    # print("Initial relay settings:")
    # for relay in relays:
    #     print(vars(relay.relset))

    # print("Initial relay settings:")
    # plot_results_oc(relays)
    # plot_results_ef(relays)


    generate_oc_settings(relays)
    # generate_ef_settings(relays)

    print("New relay settings:")
    for relay in relays:
        print(vars(relay.relset))
 
    plot_results(relays, "OC")
    # plot_results(relays, "EF")


def generate_oc_settings(relays):
    """Function that generates new setting parameters to evaluate, based on constraints therein."""

    for relay in relays:
        sg.oc_pick_up(relay)
        sg.oc_hiset_mintime(relay)
        sg.curve_type(relay)
        # Half the time, generate an exact TMS. Otherwise generate a bounded TMS.
        if round(uniform(0, 1)) <= 0.5:
            sg.oc_tms_exact(relay)
        else:
            sg.oc_tms_bounded(relay)

def generate_ef_settings(relays):
    """Function that generates new setting parameters to evaluate, based on constraints therein."""

    for relay in relays:
        sg.ef_pick_up(relay)
        sg.ef_hiset_mintime(relay)
        sg.curve_type(relay)
        # Half the time, generate an exact TMS. Otherwise generate a bounded TMS.
        if round(uniform(0, 1)) <= 0.5:
            sg.ef_tms_exact(relay)
        else:
            sg.ef_tms_bounded(relay)


def plot_results(relays, ele_type):
    """
    relay 1 = blue
    relay 2 = green
    relay 3 = red
    relay 4 = cyan
    relay 5 = magenta
    relay 6 = yellow
    relay 7 = black
    relay 8 = white
    """
    colours = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    i = 0
    for relay in relays:
        if ele_type == "OC" or "oc":
            x1 = [x for x in list(range(int(round(relay.relset.oc_pu,0)) + 1, 5001))]
            y1 = [tt.oc_trip_time(relay, x) for x in x1]
        else:
            x1 = [x for x in list(range(int(round(relay.relset.ef_pu, 0)) + 1, 5001))]
            y1 = [tt.ef_trip_time(relay, x) for x in x1]

        plt.plot(x1, y1, colours[i], label=ele_type + " " + relay.name)
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


class TestGenerator(unittest.TestCase):

    def __init__(self, relay):
        self.relay = relay

    def test_pu(self):
        sg.oc_pick_up(self.relay)
        self.assertTrue(self.relay.relset.oc_pu > max(80, load_factor, rating_factor, oc_pu_factor), 'OC PU constraint violation')
        self.assertTrue(self.relay.relset.oc_pu < min(oc_reach, oc_bu_reach, upstream_oc), 'OC PU constraint violation')

    def test_hiset(self):
        sg.oc_hiset_mintime(self.relay)

    def test_tms_exact(self):
        sg.oc_tms_exact(self.relay)

    def test_tms_bounded(self):
        sg.ef_tms_bounded(self.relay)

if __name__ == '__main__':
    # main()