from importlib import reload

import sys
import math
sys.path.append(r"\\Ecasd01\WksMgmt\PowerFactory\ScriptsDEV\PowerFactoryTyping")
import powerfactorytyping as pft
from fault_level_data import analysis, floating_terminals as ft
from device_data import eql_fuse_data as fu


def fault_study(app, all_devices: list[object], feeder: str) -> tuple[list, list, list]:
    """

    :param all_devices:
    :return:
    """

    # Convert site names to cubicle and terminal objects
    site_names = [device.name for device in all_devices]
    site_name_map, unknown_sites = site_name_convert(app, site_names)
    unknown_sites_warning(app, unknown_sites)

    # From the site names, infer the feeder name
    feeder_name = get_fdr_name(app, feeder)

    # Do a mesh feeder mesh_feeder_check
    if mesh_feeder_check(app, feeder_name):
        app.PrintPlain("Feeder is a mesh. Please radialise")
        app.PrintPlain("To run this script, please radialise the feeder")
        sys.exit(0)

    # For each of the feeder devices, identify all downstream nodes
    devices_terminals, devices_loads = get_downstream_objects(app, site_name_map)
    # Update all devices with the lists of downstream devices and upstreams devices
    all_devices = us_ds_device(devices_terminals, site_name_map, all_devices)

    ds_capacity = get_ds_capacity(devices_loads)
    section_loads = get_device_sections(devices_loads)
    device_max_load, device_max_trs = get_section_max_tr(section_loads)
    devices_sections = get_device_sections(devices_terminals)
    floating_terms = ft.get_floating_terminals(feeder_name, devices_sections)

    bound = 'Max'
    f_type = 'Ground'
    analysis.short_circuit(app, bound, f_type)
    # Max transformer data
    max_tr_pg_fls = terminal_fls(device_max_trs, bound, f_type)
    sect_tr_pg_max = sect_fl_bound(max_tr_pg_fls, bound)
    # Terminal data
    pg_max_first_pass = terminal_fls(devices_sections, bound, f_type)
    pg_max_all = append_floating_terms(app, pg_max_first_pass, floating_terms, bound, f_type)
    sect_pg_max = sect_fl_bound(pg_max_all, bound)

    f_type = 'Phase'
    analysis.short_circuit(app, bound, f_type)
    # Max transformer data
    max_tr_p_fls = terminal_fls(device_max_trs, bound, f_type)
    sect_tr_phase_max = sect_fl_bound(max_tr_p_fls, bound)
    # Terminal data
    phase_max_first_pass = terminal_fls(devices_sections, bound, f_type)
    phase_max_all = append_floating_terms(app, phase_max_first_pass, floating_terms, bound, f_type)
    sect_phase_max = sect_fl_bound(phase_max_all, bound)

    bound = 'Min'
    f_type = 'Ground'
    analysis.short_circuit(app, bound, f_type)
    pg_min_first_pass = terminal_fls(devices_sections, bound, f_type)
    pg_min_all = append_floating_terms(app, pg_min_first_pass, floating_terms, bound, f_type)
    sect_pg_min = sect_fl_bound(pg_min_all, bound)

    f_type = 'Phase'
    analysis.short_circuit(app, bound, f_type)
    phase_min_first_pass = terminal_fls(devices_sections, bound, f_type)
    phase_min_all = append_floating_terms(app, phase_min_first_pass, floating_terms, bound, f_type)
    sect_phase_min = sect_fl_bound(phase_min_all, bound)

    # Load device fault level data into their respective objects
    for device, term in ds_capacity.items():
        dev_obj = pf_to_obj(site_name_map, device, all_devices)
        dev_obj.netdat.ds_capacity = round(term)
    for device, term in sect_pg_max.items():
        dev_obj = pf_to_obj(site_name_map, device, all_devices)
        (dev_obj.netdat.max_pg_fl,) = term.values()
    for device, term in sect_phase_max.items():
        dev_obj = pf_to_obj(site_name_map, device, all_devices)
        (dev_obj.netdat.max_3p_fl,) = term.values()
    for device, term in sect_pg_min.items():
        dev_obj = pf_to_obj(site_name_map, device, all_devices)
        (dev_obj.netdat.min_pg_fl,) = term.values()
    for device, term in sect_phase_min.items():
        dev_obj = pf_to_obj(site_name_map, device, all_devices)
        (dev_obj.netdat.min_2p_fl,) = term.values()

    # Update device transformer data
    for device, term in sect_tr_pg_max.items():
        dev_obj = pf_to_obj(site_name_map, device, all_devices)
        (load_term,) = term.keys()
        dev_obj.netdat.tr_max_name = load_term.loc_name
        (dev_obj.netdat.tr_max_pg,) = term.values()
    for device, term in sect_tr_phase_max.items():
        dev_obj = pf_to_obj(site_name_map, device, all_devices)
        (dev_obj.netdat.tr_max_3p,) = term.values()
    for device in all_devices:
        pf_device = [key for key in device_max_load.keys() if device.name in key][0]
        device.netdat.max_tr_size = round(device_max_load[pf_device])
        device.netdat.max_tr_fuse = fu.get_fuse_size({device.netdat.tr_max_name: device.netdat.max_tr_size})

    # Update fault level data for substation device (i.e. devices not found in the PowerFactory model
    sub_devices(all_devices, feeder, unknown_sites)

    # package general information
    gen_info = [feeder_name.loc_name, get_grid_data(app)]
    # package detailed fl data
    detailed_fls = [pg_max_all, phase_max_all, pg_min_all, phase_min_all, section_loads]

    return gen_info, all_devices, detailed_fls


def store_switch_state(app, switch_state: dict[object:int], state: bool) -> dict[object:int]:
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
        if obj.HasAttribute('bus1'):
            cubicle = obj.bus1
        elif obj.HasAttribute('bus2'):
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


def get_grid_data(app) -> list[dict[str:float]]:
    """
    PowerFactory model external grid data read to put in a pd.DataFrame
    :param app:
    :return:
    """

    all_grids = app.GetCalcRelevantObjects('*.ElmXnet')
    grids = [grid for grid in all_grids if grid.outserv == 0]

    grid_data = {}
    for grid in grids:
        grid_data['Parameter'] = ['3-P fault level (A):', 'R/X:', 'Z2/Z1:', 'X0/X1:', 'R0/X0:']
        grid_data[f'{grid.loc_name} Maximum'] = [
            round(grid.GetAttribute('ikss'), 3),
            round(grid.GetAttribute('rntxn'), 8),
            round(grid.GetAttribute('z2tz1'), 8),
            round(grid.GetAttribute('x0tx1'), 8),
            round(grid.GetAttribute('r0tx0'), 8)
        ]
        grid_data[f'{grid.loc_name} Minimum'] = [
            round(grid.GetAttribute('ikssmin'), 3),
            round(grid.GetAttribute('rntxnmin'), 8),
            round(grid.GetAttribute('z2tz1min'), 8),
            round(grid.GetAttribute('x0tx1min'), 8),
            round(grid.GetAttribute('r0tx0min'), 8)
        ]
    return grid_data


def site_name_convert(app, site_names: list[str]) -> dict[str:dict[pft.StaCubic: pft.ElmTerm]]:
    """
    Check the site names exist in Powerfactory.
    If it exists, convert the site name to a PowerFactory object by matching it with the equvalent switch/breaker name.
    Convert the switch/breaker to a StaCubic and ElmTerm object.
    :param app:
    :param site_names:
    :return:
    """

    breaker_switches = {switch.loc_name:switch for switch in app.GetCalcRelevantObjects('*.ElmCoup')}
    switches = {switch.loc_name:switch for switch in app.GetCalcRelevantObjects('*.StaSwitch')}
    all_switches = {**breaker_switches, **switches}

    unknown_sites = []
    site_name_map = {}
    for name in site_names:
        flag = False
        for switch in all_switches:
            if name in switch:
                switch_obj = all_switches[switch]
                cubicle, device_term = coup_to_term(switch_obj)
                site_name_map[name] = {cubicle: device_term}
                flag = True
                break
        if not flag:
            unknown_sites.append(name)

    return site_name_map, unknown_sites


def coup_to_term(switch):
    """
    Convert an ElmCoup object to an equivalment ElmTerm object
    """
    if switch.GetClassName() == "ElmCoup":
        if switch.HasAttribute('bus1'):
            cubicle = switch.bus1
            device_term_1 = cubicle.cterm
            if device_term_1.iUsage == 1:
                return cubicle, device_term_1
        if switch.HasAttribute('bus2'):
            cubicle = switch.bus2
            device_term_2 = cubicle.cterm
            return cubicle, device_term_2
    else:
        cubicle = switch.fold_id                # StaSwitch
        device_term = cubicle.cterm
        return cubicle, device_term


def pf_to_obj(site_name_map: dict[str:dict[pft.StaCubic: pft.ElmTerm]], device_term: pft.ElmTerm, all_devices) -> object:
    """ Convert a PowerFactory device object to the relevant script object"""

    for device_str, inner_dict in site_name_map.items():
        inner_values = [dev.loc_name for dev in inner_dict.values()]
        if device_term.loc_name in inner_values:
            for device in all_devices:
                if device.name == device_str:
                    return device
    return None


def get_fdr_name(app, feeder: str) -> pft.ElmFeeder:
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
            break
    if not feeder_name:
        app.PrintPlain(f"Feeder name was not found in PowerFactory")
        app.PrintPlain("Please check the feeder spelling in the input file and try again.")
        sys.exit(0)

    return feeder_name


def get_downstream_objects(app, site_name_map) \
        -> tuple[dict[pft.ElmTerm:pft.ElmTerm], dict[pft.ElmTerm:pft.ElmLod]]:
    """

    :param app:
    :param devices:
    :return:
    """

    all_grids = app.GetCalcRelevantObjects('*.ElmXnet')
    grids = [grid for grid in all_grids if grid.outserv == 0]

    devices_terminals = {}
    devices_loads = {}
    for dictionary in site_name_map.values():
        for key, value in dictionary.items():
            cubicle = key
            termination = value
        devices_terminals[termination] = [termination]
        devices_loads[termination] = []
        # Do a topological search of the device downstream ojects
        down_devices = cubicle.GetAll(1, 0)
        # If the external grid is in the downstream list, you're searching in the wrong direction
        if any(item in grids for item in down_devices):
            ds_objs_list = cubicle.GetAll(0, 0)
        else:
            ds_objs_list = down_devices
        for down_object in ds_objs_list:
            if down_object.GetClassName() == "ElmTerm":
                devices_terminals[termination].append(down_object)
            if down_object.GetClassName() == "ElmLod":
                devices_loads[termination].append(down_object)

    return devices_terminals, devices_loads


def us_ds_device(devices_terminals: dict[pft.ElmTerm:pft.ElmTerm], site_name_map: dict, all_devices: list[object]) \
        -> list[object]:
    """
    Update all devices with the lists of downstream devices and upstreams devices
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
            bu_device = False
            for other_device, other_terms in d_t_dic.items():
                if len(other_terms) == min_val:
                    bu_device = other_device
            dev_obj = pf_to_obj(site_name_map, device, all_devices)
            if bu_device:
                dev_obj_us = pf_to_obj(site_name_map, bu_device, all_devices)
                if bu_device not in dev_obj.netdat.upstream_devices:
                    dev_obj.netdat.upstream_devices.append((pf_to_obj(site_name_map, bu_device, all_devices)))
                if device not in dev_obj_us.netdat.upstream_devices:
                    dev_obj_us.netdat.downstream_devices.append((pf_to_obj(site_name_map, device, all_devices)))

    return all_devices


def get_ds_capacity(devices_loads: dict[pft.ElmTerm:pft.ElmLod]) -> dict[pft.ElmTerm:float]:
    """
    Calculate the capacity of all distribution transformers downstream of each device.
    """

    ds_capacity = {}
    for device, loads in devices_loads.items():
        load_kva = {load: load.Strat for load in loads}
        total_kva = sum(load_kva.values())
        load_amps = round((total_kva * 1000) / (11000 * math.sqrt(3)))
        ds_capacity[device] = load_amps
    return ds_capacity


def get_device_sections(devices_terms: dict[pft.ElmTerm:list[pft.ElmTerm]]) -> dict[pft.ElmTerm:list[pft.ElmTerm]]:
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


def get_section_max_tr(section_loads: dict[pft.ElmTerm:pft.ElmLod]) -> (
        tuple)[dict[str:float], dict[pft.ElmTerm:pft.ElmTerm]]:
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


def terminal_fls(devices_sections: dict[pft.ElmTerm:pft.ElmTerm], bound: str, f_type: str) \
        -> dict[pft.ElmTerm:dict[pft.ElmTerm:float]]:
    """

    """

    if f_type == "Ground":
        # Ground fault (max and min bound)
        attribute = 'm:Ikss:A'
    elif bound == "Min":
        # Phase fault, min bound
        attribute = 'm:Ikss:B'
    else:
        # Phase fault, max bound
        attribute = 'm:Ikss'

    results_all = {}
    for device, terminals in devices_sections.items():
        results_all[device] = {}
        for terminal in terminals:
            if terminal.HasAttribute(attribute):
                results_all[device][terminal] = round(terminal.GetAttribute(attribute), 3) * 1000
            else:
                results_all[device][terminal] = 0

    return results_all


def sect_fl_bound(results_all: dict[pft.ElmTerm:dict[pft.ElmTerm:float]], bound: str) -> dict[pft.ElmTerm:float]:
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


def append_floating_terms(app, results_all: dict[pft.ElmTerm:dict[pft.ElmTerm:float]],
                          floating_terms: dict[pft.ElmTerm:dict[pft.ElmLne:float]], bound: str, f_type: str) \
        -> dict[pft.ElmTerm:dict[pft.ElmTerm:float]]:
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
            analysis.short_circuit(app, bound, f_type, location=line, ppro=ppro)
            line_current = analysis.get_line_current(line)
            results_all[device].update({term: line_current})

    return results_all


def unknown_sites_warning(app, unknown_sites):
    if unknown_sites:
        app.PrintPlain(f'The following sites were not found in PowerFactory: {unknown_sites}')
        app.PrintPlain('These sites are assumed to be substation devices.')
        app.PrintPlain('If this is incorrect, check the site name spelling matches the appropriate switch in '
                       'PowerFactory and run the script again')


def sub_devices(all_devices: list[object], feeder: str, unknown_sites: list[str]):

    def str_to_obj(string, all_devices):
        for device in all_devices:
            if device.name == string:
                return device

    feeder_obj = str_to_obj(feeder, all_devices)

    for site in unknown_sites:
        site_obj = str_to_obj(site, all_devices)
        current_split = site_obj.netdat.i_split

        # Update device transformer data
        site_obj.netdat.tr_max_name = None
        site_obj.netdat.tr_max_pg = None
        site_obj.netdat.tr_max_3p = None
        site_obj.netdat.max_tr_size = None
        site_obj.netdat.max_tr_fuse = None

        # Update device backup data
        site_obj.netdat.upstream_devices = None
        site_obj.netdat.downstream_devices.append(feeder_obj.name)
        feeder_obj.netdat.upstream_devices.append(site_obj.name)

        # Site current seen at 11kV:
        site_max_pg_fl = (feeder_obj.netdat.max_pg_fl + 1) / current_split
        site_max_3p_fl = (feeder_obj.netdat.max_3p_fl + 1) / current_split
        site_min_pg_fl = feeder_obj.netdat.max_pg_fl / current_split
        site_min_2p_fl = feeder_obj.netdat.max_3p_fl / current_split

        # Convert 11kV current to current seen by device:
        site_obj.netdat.max_pg_fl = site_obj.netdat.trnsp_pg_stardelta(site_obj, site_max_pg_fl)
        site_obj.netdat.max_3p_fl = site_obj.netdat.trnsp_3p_stardelta(site_obj, site_max_3p_fl)
        site_obj.netdat.min_pg_fl = site_obj.netdat.trnsp_pg_stardelta(site_obj, site_min_pg_fl)
        site_obj.netdat.min_2p_fl = site_obj.netdat.trnsp_2p_stardelta(site_obj, site_min_2p_fl)
