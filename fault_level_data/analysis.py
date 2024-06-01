import study_templates


def short_circuit(app, location: object, ppro: int, bound: str, f_type: str) -> object:
    """
    Set the Short-circuit command module and perform a short-circuit calculation
    :param app: PowerFactory Application
    :param location: element location of fault. None if All Busbars
    :param ppro: fault distance from terminal
    :param bound: 'Max', 'Min'
    :param f_type: 'Phase', 'Ground'
    :return: Short-Circuit Command
    """

    ComShc = app.GetFromStudyCase("Short_Circuit.ComShc")
    study_templates.apply_sc(ComShc, bound, f_type)
    if location:
        ComShc.SetAttribute("e:iopt_allbus", 0)
        ComShc.SetAttribute("e:shcobj", location)
        ComShc.SetAttribute("e:iopt_dfr", 0)
        ComShc.SetAttribute("e:ppro", ppro)
    else:
        ComShc.SetAttribute("e:iopt_allbus", 1)

    return ComShc.Execute()


def get_line_current(elmlne: object) -> float:
    if elmlne.bus1:
        Ia1 = elmlne.GetAttribute('m:Ikss:bus1:A')
        Ib1 = elmlne.GetAttribute('m:Ikss:bus1:B')
        Ic1 = elmlne.GetAttribute('m:Ikss:bus1:C')

    if elmlne.bus2:
        Ia2 = elmlne.GetAttribute('m:Ikss:bus2:A')
        Ib2 = elmlne.GetAttribute('m:Ikss:bus2:B')
        Ic2 = elmlne.GetAttribute('m:Ikss:bus2:C')

    if elmlne.bus1 and elmlne.bus2:
        return round(max(Ia1, Ib1, Ic1, Ia2, Ib2, Ic2), 3)
    elif elmlne.bus1:
        return round(max(Ia1, Ib1, Ic1), 3)
    elif elmlne.bus2:
        return round(max(Ia2, Ib2, Ic2), 3)
    else:
        return None