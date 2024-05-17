import study_templates


def short_circuit(app, location: object, ppro: int, Format: str, Type: str) -> object:
    """
    Set the Short-circuit command module and perform a short-circuit calculation
    :param app: PowerFactory Application
    :param location: element location of fault. None if All Busbars
    :param ppro: fault distance from terminal
    :param Format: 'Max', 'Min'
    :param Type: 'Phase', 'Ground'
    :return: Short-Circuit Command
    """

    ComShc = app.GetFromStudyCase("Short_Circuit.ComShc")
    study_templates.apply_sc(ComShc, Format, Type)
    if location:
        ComShc.SetAttribute("e:iopt_allbus", 0)
        ComShc.SetAttribute("e:shcobj", location)
        ComShc.SetAttribute("e:iopt_dfr", 0)
        ComShc.SetAttribute("e:ppro", ppro)
    else:
        ComShc.SetAttribute("e:iopt_allbus", 1)

    return ComShc.Execute()
