from inputs import eql_relay_data as re
import xlwings as xw
import pandas as pd

consider_clp = True

def input():
    """

    """
    path_ = ('E:\Python\_python_work\protection_coordination\inputs')

    Data = pd.read_excel(f'{path_}/input.xlsx', sheet_name='Data')
    # remove first column
    Data_1 = Data.iloc[:, 1:]
    Data_1 = Data_1.fillna("OFF")

    # Transform dataframe into dictionary
    Data_2 = Data_1.to_dict('list')

    def split_string(object):
        if type(object) == str:
            return object.split(', ')
        else:
            return [None]

    all_relays = []
    for relays in Data_2:
        relay = Data_2[relays]
        parameters = [relays, re.relay_lookup[relay[0]], relay[1]]
        settings = [relay[2], relay[3], relay[4], relay[5], relay[6], relay[7], relay[8], relay[9], relay[10],
                    relay[11], relay[12], relay[13], relay[14], relay[15], relay[16]]
        network = [relay[20], relay[21], relay[22], relay[23], relay[24], relay[25], relay[26], relay[27], relay[28],
                   relay[29], relay[30], split_string(relay[31]), split_string(relay[32])]
        ct_data = [relay[17], relay[18], relay[19]]

        new_relay = re.ProtectionRelay(parameters, settings, network, ct_data)
        all_relays.append(new_relay)

    # Add upstream and downstream relays. These can only be added after all relay objects are created
    for relay in all_relays:
        downstream_objects = []
        upstream_objects = []
        downstream_devices = relay.netdat.downstream_devices
        upstream_devices = relay.netdat.upstream_devices
        for relay_1 in all_relays:
            if relay_1.name in downstream_devices:
                downstream_objects.append(relay_1)
        relay.netdat.downstream_devices = downstream_objects
        for relay_2 in all_relays:
            if relay_2.name in upstream_devices:
                upstream_objects.append(relay_2)
        relay.netdat.upstream_devices = upstream_objects

    return all_relays

