from importlib import reload
import powerfactory as pf
import sys
import input_file as input
import analysis
reload(input)

def main():
    #
    # INITIALISE SCRIPT
    #

    # Get the application object
    app = pf.GetApplication()
    # Enables the user to manually stop the script
    app.SetEnableUserBreak(1)
    app.ClearOutputWindow()
    # Turn the echo off (suppress output window messages)
    echo(app, off=True)

    # Store the initial feeder switch state
    switch_state = {}
    stored_switch_state = store_switch_state(app, switch_state, state=False)

    input_data = input.input()

    site_names = [key for key in input_data]
    app.PrintPlain(site_names)

    # Check the site names exist in Powerfactory
    site_name_check(app, site_names)
    # Convert site names to switch objects
    site_name_objs = site_name_convert(app, site_names)

    # From the site names, infer the feeder name
    feeder_name = get_fdr_name(app, site_name_objs)

    # Do a mesh feeder mesh_feeder_check
    if mesh_feeder_check(app, feeder_name):
        app.PrintPlain("Feeder is a mesh. Please radialise")
        app.PrintPlain("To run this script, please radialise the feeder")
        sys.exit(0)

    # Initialise output file
    output_file = {}
    for site_name in site_names:
        output_file[site_name] = [None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                              None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                              None, None, None]

    # For each of the feeder devices, identify all downstream nodes
    devices_terminals, devices_loads = get_downstream_objects(app, site_name_objs)

    # Update the output file for each device with dowsntream devices and upstreams devices
    output_file = us_ds_device(devices_terminals, output_file)

    section_loads = get_section_loads(app, devices_loads)
    device_max_load, device_max_trs = get_section_max_tr(section_loads)
    for site_name in site_names:
        output_file[site_name][28] = device_max_load[site_name]
    devices_sections = get_device_sections(app, devices_terminals)

    analysis.short_circuit(app, location=None, ppro=0, Format='Max', Type='Phase')
    for device, terminals in devices_sections.items():
        max_fl = 0
        for terminal in terminals:
            try:
                fault_level = terminal.GetAttribute('m:Ikss')
            except AttributeError:
                fault_level = 0
            if fault_level > max_fl:
                max_fl = fault_level
        output_file[device][23] = max_fl

    analysis.short_circuit(app, location=None, ppro=0, Format='Max', Type='Ground')
    for device, terminals in devices_sections.items():
        max_fl = 0
        for terminal in terminals:
            try:
                fault_level = terminal.GetAttribute('m:Ikss:A')
            except AttributeError:
                fault_level = 0
            if fault_level > max_fl:
                max_fl = fault_level
        output_file[device][24] = max_fl

    analysis.short_circuit(app, location=None, ppro=0, Format='Min', Type='Phase')
    for device, terminals in devices_sections.items():
        min_fl = 999
        for terminal in terminals:
            try:
                fault_level = terminal.GetAttribute('m:Ikss')
            except AttributeError:
                fault_level = 0
            if fault_level < min_fl:
                min_fl = fault_level
        output_file[device][25] = min_fl

    analysis.short_circuit(app, location=None, ppro=0, Format='Min', Type='Ground')
    for device, terminals in devices_sections.items():
        min_fl = 999
        for terminal in terminals:
            try:
                fault_level = terminal.GetAttribute('m:Ikss:A')
            except AttributeError:
                fault_level = 0
            if fault_level < min_fl:
                min_fl = fault_level
        output_file[device][26] = min_fl















    # Restore the echo
    echo(app, off=False)

    # script run successfully.


def echo(app, off: bool):
    """Supresses the printing of Warning and information messages to the Output.

    Usage: Echo(app) turns the echo off
           Echo(app, off = False) turns the echo back on
    """
    echo = app.GetFromStudyCase('ComEcho')
    if off:
        echo.iopt_err = True
        echo.iopt_wrng = False
        echo.iopt_info = False
        echo.Off()
    else:
        echo.On()


def store_switch_state(app, switch_state: dict, state: bool) -> dict:
    """Store or restore the initial model switch state. If state = False, the initial switch state is stored.
    If state = True, the initial switch state is restored"""

    all_switches = app.GetCalcRelevantObjects('*.ElmCoup')

    if state:
        # Restore feeder switches to the initial state before ending script
        for switch in all_switches:
            switch.on_off = switch_state[switch]
    else:
        # Store the initial feeder switch state
        for switch in all_switches:
            switch_state[switch] = switch.on_off

    return switch_state


def mesh_feeder_check(app, obj: object) -> bool:
    """
    Check whether the line segment belongs to a meshed feeder or a radial feeder
    :param app:
    :param obj: object (line, feeder)
    :return: bool True = mesh feeder; False = radial feeder
    """

    all_grids = app.GetCalcRelevantObjects('*.ElmXnet')
    grids = [grid for grid in all_grids if grid.outserv == 0]
    # Do a topological search up- and downstream. If the external grid is found in both searches
    # this is a meshed feeder and will be excluded.
    if obj.GetClassName() == "ElmLne":
        if obj.bus1:
            cubicle = obj.bus1
        elif obj.bus2:
            cubicle = obj.bus2
        else:
            raise Exception("line has no terminal connections")
    else:
        cubicle = obj.obj_id
    down_devices = cubicle.GetAll(1, 0)
    up_devices = cubicle.GetAll(0, 0)
    if any(item in grids for item in down_devices) and any(item in grids for item in up_devices):
        return True
    else:
        return False


def site_name_check(app, site_names: list):

    breaker_switches = [switch.loc_name for switch in app.GetCalcRelevantObjects('*.ElmCoup')]
    switches = [switch.loc_name for switch in app.GetCalcRelevantObjects('*.StaSwitch')]
    all_switches = breaker_switches + switches

    script_exit = False
    for name in site_names:
        if name not in all_switches:
            app.PrintPlain(f"Device {name} was not found in the PowerFactory StaSwitch or ElmCoup switch lists")
            app.PrintPlain("Please check the device spelling and try again.")
            script_exit = True
    if script_exit:
        sys.exit(0)


def site_name_convert(app, site_names: list) -> list:


    breaker_switches = app.GetCalcRelevantObjects('*.ElmCoup')
    switches = app.GetCalcRelevantObjects('*.StaSwitch')
    all_switches = breaker_switches + switches

    site_name_objects = []
    for switch in all_switches:
        if switch.loc_name in site_names:
            site_name_objects.append(switch)

    return site_name_objects


def get_fdr_name(app, site_name_objs: dict) -> object:


    feeder_name = None
    netmod = app.GetProjectFolder('netmod')
    Elmfdrs = netmod.GetContents('*.ElmFeeder', True)
    active_feeders = [feeder for feeder in Elmfdrs if feeder.GetAll()]
    for feeder in active_feeders:
        fdr_name = feeder.loc_name
        feeder_switch = feeder.obj_id.obj_id
        feeder_switches = feeder.GetObjs('StaSwitch') + feeder_switch
        if (any(ele in feeder_switches for ele in site_name_objs) or
                any(ele.loc_name == fdr_name for ele in site_name_objs)):
            feeder_name = feeder
    if not feeder_name:
        app.PrintPlain(f"Feeder name was not found in PowerFactory")
        app.PrintPlain("Please check the device spelling and try again.")
        sys.exit(0)

    return feeder_name


def get_downstream_objects(app, devices: list) -> tuple[dict, dict]:
    """

    :param app:
    :param devices:
    :return:
    """

    all_grids = app.GetCalcRelevantObjects('*.ElmXnet')
    grids = [grid for grid in all_grids if grid.outserv == 0]

    devices_terminals = {}
    devices_loads = {}
    for device in devices:
        # Convert device to its equivalent cubicle
        if device.GetClassName() == "ElmCoup":
            if device.bus1:
                cubicle = device.bus1
                device_term = cubicle.cterm
            elif device.bus2:
                cubicle = device.bus2
                device_term = cubicle.cterm
            else:
                raise Exception(f"Switch {device} has no terminal connections")
        else:
            cubicle = device.fold_id        # StaSwitch
            device_term = cubicle.cterm
        devices_terminals = {device: [device_term]}
        devices_loads[device] = []
        # Do a topological search of the device downstream ojects
        down_devices = cubicle.GetAll(1, 0)
        # If the external grid is in the downstream list, you're searching in the wrong direction
        if any(item in grids for item in down_devices):
            ds_objs_list = cubicle.GetAll(0, 0)
        else:
            ds_objs_list = down_devices
        for down_object in ds_objs_list:
            if down_object.GetClassName() == "ElmTerm":
                devices_terminals[device].append(down_object)
            if down_object.GetClassName() == "ElmLod":
                devices_loads[device].append(down_object)

    return devices_terminals, devices_loads



def us_ds_device(devices_terminals: dict, output_file: dict) -> dict:
    """
    Update the upstream device list and the downstream device list for devices in the output file
    :param devices_terminals:
    :param output_file:
    :return:
    """

    for device, terms in devices_terminals.items():
        # get a dictionary of device-terms that include the device in its list of terminals
        d_t_dic = {}
        for other_device, other_terms in devices_terminals.items():
            if other_device == device:
                continue
            if device in other_terms:
                d_t_dic[other_device] = other_terms
        # from this dictionary, the device with the shortest list of terminals is the backup device
        if d_t_dic:
            min_val = min([len(value) for key, value in d_t_dic.items()])
            bu_device = None
            for other_device, other_terms in d_t_dic.items():
                if len(other_terms) == min_val:
                    bu_device = other_device
            output_file[device][32] = [bu_device]
            output_file[bu_device][33].append(device)
    return output_file


def get_device_sections(app, devices_terminals: dict) -> dict:
    """For a dictionary of device: [terminals],determine the device sections"""

    devices_sections = {}
    short_iter = []
    while len(devices_terminals) > 0:
        # find the length of the shortest list of terminals for the given feeder.
        min_val = min([len(devices_terminals[ele]) for ele in devices_terminals])
        # find the shortest list by comparing list lengths to the length of the shortest list.
        for device, terminals in devices_terminals.items():
            if len(terminals) == min_val:
                shortest_list = device  # this is the key for the shortest list (ie name of PMR)
        # pop the shortest list dictionary from the dictionary
        short = devices_terminals.pop(shortest_list)
        shortest_section = list(set(short) - set(short_iter))

        # chop the device value from its section list so upstream section will include it in its list
        for n in range(min_val):
            try:
                shortest_list_object = app.GetCalcRelevantObjects(shortest_list + "_Term.ElmTerm")[0]
                if short[n] == shortest_list_object:
                    del short[n]
            except IndexError:
                continue

        short_iter = short_iter + short
        devices_sections[shortest_list] = shortest_section

    return devices_sections


def get_section_loads(app, devices_loads: dict) -> dict:
    section_loads = None
    return section_loads


def get_section_max_tr(section_loads: dict) -> tuple[dict, dict]:
    """

    :param app:
    :param section_loads:
    :return:
    """

    device_max_load = {}
    device_max_trs = {}
    for device, loads in section_loads.items():
        load_values = {load: load.Strat for load in loads}
        max_load_value = max(load_values.values())
        device_max_load[device] = max_load_value
        max_loads = [load for load in load_values if load_values[load] == max_load_value]
        # If there are multiple max loads, need to return all of them, so we can find the max load with highest fl.
        max_load_terminals = [load.bus1.cterm for load in max_loads]
        device_max_trs[device] = max_load_terminals

    return device_max_load, device_max_trs


# Python boilerplate
if __name__ == '__main__':
    main()