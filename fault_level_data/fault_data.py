from importlib import reload
from typing import Dict

import sys
import analysis
from device_data import eql_fuse_data as fu
import floating_terminals as ft


def fault_study(app, all_devices: list[object], feeder: str) -> tuple[list, list, list]:
    """

    :param all_devices:
    :return:
    """

    app.SetEnableUserBreak(1)
    app.ClearOutputWindow()
    # Turn the echo off (suppress output window messages)
    echo(app, off=True)

    site_names = [device.name for device in all_devices]
    app.PrintPlain(site_names)

    # Check the site names exist in Powerfactory
    site_name_check(app, site_names)
    # Convert site names to switch objects
    site_name_objs = site_name_convert(app, site_names)

    # From the site names, infer the feeder name
    feeder_name = get_fdr_name(app, feeder)

    # Do a mesh feeder mesh_feeder_check
    if mesh_feeder_check(app, feeder_name):
        app.PrintPlain("Feeder is a mesh. Please radialise")
        app.PrintPlain("To run this script, please radialise the feeder")
        sys.exit(0)

    # For each of the feeder devices, identify all downstream nodes
    devices_terminals, devices_loads = get_downstream_objects(app, site_name_objs)

    # Update all devices with the lists of downstream devices and upstreams devices
    all_devices = us_ds_device(devices_terminals, all_devices)

    section_loads = get_device_sections(devices_loads)
    device_max_load, device_max_trs = get_section_max_tr(section_loads)

    devices_sections = get_device_sections(devices_terminals)
    floating_terms = ft.get_floating_terminals(feeder_name, devices_sections)

    analysis.short_circuit(app, location=None, ppro=0, bound='Max', f_type='Ground')
    pg_max_first_pass = terminal_fls(devices_sections, f_type='Ground')
    pg_max_all = append_floating_terms(app, pg_max_first_pass, floating_terms, bound='Max', f_type='Ground')
    sect_pg_max = sect_fl_bound(pg_max_all, bound='Max')

    max_tr_pg_fls = terminal_fls(device_max_trs, f_type='Ground')
    sect_tr_pg_max = sect_fl_bound(max_tr_pg_fls, bound='Max')

    analysis.short_circuit(app, location=None, ppro=0, bound='Max', f_type='Phase')
    phase_max_first_pass = terminal_fls(devices_sections, f_type='Phase')
    phase_max_all = append_floating_terms(app, phase_max_first_pass, floating_terms, bound='Max', f_type='Phase')
    sect_phase_max = sect_fl_bound(phase_max_all, bound='Max')

    max_tr_p_fls = terminal_fls(device_max_trs, f_type='Phase')
    sect_tr_phase_max = sect_fl_bound(max_tr_p_fls, bound='Max')

    analysis.short_circuit(app, location=None, ppro=0, bound='Min', f_type='Ground')
    pg_min_first_pass = terminal_fls(devices_sections, f_type='Ground')
    pg_min_all = append_floating_terms(app, pg_min_first_pass, floating_terms, bound='Min', f_type='Ground')
    sect_pg_min = sect_fl_bound(pg_min_all, bound='Min')

    analysis.short_circuit(app, location=None, ppro=0, bound='Min', f_type='Phase')
    phase_min_first_pass = terminal_fls(devices_sections, f_type='Phase')
    phase_min_all = append_floating_terms(app, phase_min_first_pass, floating_terms, bound='Min', f_type='Phase')
    sect_phase_min = sect_fl_bound(phase_min_all, bound='Max')

    # Load device fault level data into their respective objects
    for device, term in sect_pg_max.items():
        dev_obj = pf_to_obj(device, all_devices)
        dev_obj.netdat.max_pg_fl = device[term]
    for device, term in sect_phase_max.items():
        dev_obj = pf_to_obj(device, all_devices)
        dev_obj.netdat.max_3p_fl = device[term]
    for device, term in sect_pg_min.items():
        dev_obj = pf_to_obj(device, all_devices)
        dev_obj.netdat.min_pg_fl = device[term]
    for device, term in sect_phase_min.items():
        dev_obj = pf_to_obj(device, all_devices)
        dev_obj.netdat.min_2p_fl = device[term]

    # Update device transformer data
    for device, term in sect_tr_pg_max.items():
        dev_obj = pf_to_obj(device, all_devices)
        dev_obj.netdat.tr_max_name = term.loc_name
        dev_obj.netdat.tr_max_pg = device[term]
    for device, term in sect_tr_phase_max.items():
        dev_obj = pf_to_obj(device, all_devices)
        dev_obj.netdat.tr_max_3p = device[term]
    for device in all_devices:
        device.netdat.max_tr_size = device_max_load[device.name]
        device.netdat.max_tr_fuse = fu.get_fuse_size({device.netdat.tr_max_name: device.netdat.max_tr_size})

    # package general information
    gen_info = [feeder_name.loc_name, get_grid_data(app)]
    # package detailed fl data
    detailed_fls = [pg_max_all, phase_max_all, pg_min_all, phase_min_all, section_loads, max_tr_pg_fls, max_tr_p_fls]

    # Restore the echo
    echo(app, off=False)

    return gen_info, all_devices, detailed_fls


def echo(app, off: bool):
    """
    Suppresses the printing of Warning and information messages to the Output.
    :param app:
    :param off: boolean state turns toggles the echo on and off
    """
    echo = app.GetFromStudyCase('ComEcho')
    if off:
        echo.iopt_err = True
        echo.iopt_wrng = False
        echo.iopt_info = False
        echo.Off()
    else:
        echo.On()


def store_switch_state(app, switch_state: Dict[object:int], state: bool) -> Dict[object:int]:
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


def get_grid_data(app) -> list[Dict[str:float]]:
    """
    PowerFactory model external grid data read to put in a pd.DataFrame
    :param app:
    :return:
    """

    all_grids = app.GetCalcRelevantObjects('*.ElmXnet')
    grids = [grid for grid in all_grids if grid.outserv == 0]

    grid_data = []
    for grid in grids:
        grid_data.append({grid.loc_name: ['3-P fault level (A):', 'R/X:', 'Z2/Z1:', 'X0/X1:', 'R0/X0:']})
        grid_data.append({'Maximum': [
            round(grid.GetAttribute('ikss'), 3),
            round(grid.GetAttribute('rntxn'), 8),
            round(grid.GetAttribute('z2tz1'), 8),
            round(grid.GetAttribute('x0tx1'), 8),
            round(grid.GetAttribute('r0tx0'), 8)
        ]})
        grid_data.append({'Minimum': [
            round(grid.GetAttribute('ikssmin'), 3),
            round(grid.GetAttribute('rntxnmin'), 8),
            round(grid.GetAttribute('z2tz1min'), 8),
            round(grid.GetAttribute('x0tx1min'), 8),
            round(grid.GetAttribute('r0tx0min'), 8)
        ]})
    return grid_data


def pf_to_obj(pf_obj: object, all_devices: list[object]) -> object:
    """ Convert a PowerFactory device object to the relevant script object"""

    device_name = pf_obj.loc_name
    for script_obj in all_devices:
        if script_obj.name == device_name:
            return script_obj
    return False


def site_name_check(app, site_names: list[str]):
    """
    Check the site names exist in Powerfactory
    :param app:
    :param site_names:
    :return:
    """

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


def site_name_convert(app, site_names: list[str]) -> list[object]:
    """
    Convert site names to PowerFactory switch objects
    :param app:
    :param site_names:
    :return:
    """

    breaker_switches = app.GetCalcRelevantObjects('*.ElmCoup')
    switches = app.GetCalcRelevantObjects('*.StaSwitch')
    all_switches = breaker_switches + switches

    site_name_objects = []
    for switch in all_switches:
        if switch.loc_name in site_names:
            site_name_objects.append(switch)

    return site_name_objects


def get_fdr_name(app, feeder: str) -> object:
    """

    :param app:
    :param feeder:
    :return:
    """

    feeder_name = None
    netmod = app.GetProjectFolder('netmod')
    Elmfdrs = netmod.GetContents('*.ElmFeeder', True)
    active_feeders = [feeder for feeder in Elmfdrs if feeder.GetAll()]
    for active_feeder in active_feeders:
        if feeder in active_feeder.loc_name:
            feeder_name = active_feeder
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


def us_ds_device(devices_terminals: dict, all_devices: list[object]) -> list:
    """

    :param devices_terminals:
    :param all_devices:
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
            dev_obj = pf_to_obj(device, all_devices)
            if dev_obj:
                dev_obj.netdat.upstream_devices.append(bu_device)
                dev_obj.netdat.downstream_devices.append(device)
    return all_devices


def get_device_sections(devices_terms: Dict[object:list[object]]) -> Dict[object:list[object]]:
    """
    For a dictionary of device: [terminals],determine the device sections
    :param devices_terminals:
    :return:
    """

    # Sort the keys by the length of their lists in descending order
    sorted_keys = sorted(devices_terms, key=lambda k: len(devices_terms[k]), reverse=True)

    # Iterate over the sorted keys
    for i, key1 in enumerate(sorted_keys):
        for key2 in sorted_keys[i + 1:]:
            set1 = set(devices_terms[key1])
            set2 = set(devices_terms[key2])

            # Find common elements except the key of the shorter list (key2)
            common_elements = set1 & set2 - {key2}

            # Remove common elements from the longer list (key1's list)
            devices_terms[key1] = [elem for elem in devices_terms[key1] if elem not in common_elements]

    return devices_terms


def get_section_max_tr(section_loads: Dict[object:object]) -> tuple[Dict[str:float], Dict[object:object]]:
    """

    :param app:
    :param section_loads:
    :return:
    device_max_load = {'device': str, ...}
    device_max_trs = {device.switch: [term1, term2...], ..}
    """

    device_max_load = {}
    device_max_trs = {}
    for device, loads in section_loads.items():
        load_values = {load: load.Strat for load in loads}
        max_load_value = max(load_values.values())
        device_max_load[device.loc_name] = max_load_value
        max_loads = [load for load in load_values if load_values[load] == max_load_value]
        # If there are multiple max loads, need to return all of them, so we can find the max load with highest fl.
        max_load_terms = [load.bus1.cterm for load in max_loads]
        device_max_trs[device] = max_load_terms

    return device_max_load, device_max_trs


def terminal_fls(devices_sections: Dict[object:object], f_type: str) -> Dict[object:Dict[object:float]]:
    """

    :param devices_sections:
    :param type:
    :return:
    """

    # Map fault type to terminal attribute
    type_att = {'spgf': 'm:Ikss:A', '3psc': 'm:Ikss', '2psc': 'm:Ikss:B'}
    attribute = type_att[f_type]

    results_all = {}
    for device, terminals in devices_sections.items():
        results_all[device] = {}
        for terminal in terminals:
            if terminal.HasAttribute(attribute):
                results_all[device][terminal] = round(terminal.GetAttribute(attribute), 3)
            else:
                results_all[device][terminal] = 0

    return results_all


def sect_fl_bound(results_all: Dict[object:Dict[object:float]], bound: str) -> Dict[object:float]:
    """

    :param results_all:
    :param bound: 'Min', 'Max'.
    :return:
    """

    sect_bound = {}
    for device, terms in results_all.items():
        sect_bound[device] = {}
        non_zero_terms = {term: fl for term, fl in terms.items() if fl != 0}
        if not non_zero_terms:
            sect_bound[device] = 'no terminations'
            continue
        if bound == 'Min':
            min_term = min(non_zero_terms, key=non_zero_terms.get)
            sect_bound[device] = {min_term: non_zero_terms[min_term]}
        elif bound == 'Max':
            max_term = max(non_zero_terms, key=non_zero_terms.get)
            sect_bound[device] = {max_term: non_zero_terms[max_term]}

    return sect_bound


def append_floating_terms(app, results_all: Dict[object:Dict[object:float]],
                          floating_terms: Dict[object:Dict[object:float]], bound: str, f_type: str):
    """

    :param app:
    :param results_all:
    :param floating_terms:
    :param bound: 'Max', 'Min'
    :param f_type: 'Phase', 'Ground'
    :return:
    """

    for device, lines in floating_terms.items():
        for line, term in lines.items():
            if line.bus1.cterm == term:
                ppro = 1
            else:
                ppro = 99
            analysis.short_circuit(app, location=line, ppro=ppro, bound=bound, f_type=f_type)
            line_current = analysis.get_line_current(line)
            results_all[device].update({term: line_current})

    return results_all
