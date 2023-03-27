import warnings

# defines conversion factors to meter
_space_convs = {"micron": 1e-6,
                "micrometer": 1e-6,
                "micro": 1e-6,
                "milli": 1e-3,
                "millimeter": 1e-3,
                "nano": 1e-9,
                "nanometer": 1e-9,
                'meter': 1
                }

# defines conversion factors to minutes
_time_convs = {"millisecond": 1e-3 / 60,
               "milliseconds": 1e-3 / 60,
               "microsecond": 1e-6 / 60,
               "microseconds": 1e-6 / 60,
               "second": 1 / 60,
               "s": 1 / 60,
               "seconds": 1 / 60,
               "hours": 60,
               "hour": 60,
               "h": 60,
               "day": 24 * 60,
               "days": 24 * 60,
               "week": 7 * 24 * 60,
               "weeks": 7 * 24 * 60,
               "minutes": 1,
               "min": 1}


def get_dims(pcdict, space_convs=_space_convs):
    """
    Parses PhysiCell data and generates CC3D space dimensions and unit conversions

    This function looks for the value of the maximum and minimum of all coordinates in PhysiCell (
    pcdict['domain']['x_min'], pcdict['domain']['x_max'], etc) and saves them to variables. It also looks for the
    discretization variables from PhysiCell (pcdict['domain']['dx'], etc) and saves them to variables. Using the size of
    the domain and the discretization it defines what will be the number of pixels in CompuCell3D's domain.
    It also looks for the unit used in PhysiCell to determine what will be the pixel/unit factor in CC3D.

    :param pcdict: Dictionary created from parsing PhysiCell XML
    :param space_convs: Dictionary of predefined space units
    :return pcdims, ccdims: Two tuples representing the dimension data from PhysiCell and in CC3D.
          ((xmin, xmax), (ymin, ymax), (zmin, zmax), units), and
          (cc3dx, cc3dy, cc3dz, cc3dspaceunitstr, cc3dds, autoconvert_space)
    """
    xmin = float(pcdict['domain']['x_min']) if "x_min" in pcdict['domain'].keys() else None
    xmax = float(pcdict['domain']['x_max']) if "x_max" in pcdict['domain'].keys() else None

    ymin = float(pcdict['domain']['y_min']) if "y_min" in pcdict['domain'].keys() else None
    ymax = float(pcdict['domain']['y_max']) if "y_max" in pcdict['domain'].keys() else None

    zmin = float(pcdict['domain']['z_min']) if "z_min" in pcdict['domain'].keys() else None
    zmax = float(pcdict['domain']['z_max']) if "z_max" in pcdict['domain'].keys() else None

    units = pcdict['overall']['space_units'] if 'overall' in pcdict.keys() and \
                                                'space_units' in pcdict['overall'].keys() else 'micron'

    autoconvert_space = True
    if units not in space_convs.keys():
        message = f"WARNING: {units} is not part of known space units. Automatic space-unit conversion disabled." \
                  f"Available units for auto-conversion are:\n{space_convs.keys()}"
        warnings.warn(message)
        autoconvert_space = False

    # the dx/dy/dz tags mean that for every voxel there are dx space-units.
    # therefore [dx] = [space-unit/voxel]. Source: John Metzcar

    dx = float(pcdict['domain']['dx']) if "dx" in pcdict['domain'].keys() else 1
    dy = float(pcdict['domain']['dy']) if "dy" in pcdict['domain'].keys() else 1
    dz = float(pcdict['domain']['dz']) if "dz" in pcdict['domain'].keys() else 1

    # print(dx, dy, dz, type(dx), type(dy), type(dz), )
    if not dx == dy == dz:
        message = "WARNING! Physicell's dx/dy/dz are not all the same: " \
                  f"dx={dx}, dy={dy}, dz={dz}\n" \
                  f"Using {max(min(dx, dy, dz), 1)}"
        warnings.warn(message)

    ds = max(min(dx, dy, dz), 1)

    diffx = 1 if xmin is None or xmax is None else round(xmax - xmin)
    diffy = 1 if ymin is None or ymax is None else round(ymax - ymin)
    diffz = 1 if zmin is None or zmax is None else round(ymax - zmin)

    cc3dx = round(diffx / ds)
    cc3dy = round(diffy / ds)
    cc3dz = round(diffz / ds)

    cc3dds = cc3dx / diffx  # pixel/unit

    # [cc3dds] = pixel/unit
    # [cc3dds] * unit = pixel

    cc3dspaceunitstr = f"1 pixel = {cc3dds} {units}"

    pcdims, ccdims = ((xmin, xmax), (ymin, ymax), (zmin, zmax), units), \
                     (cc3dx, cc3dy, cc3dz, cc3dspaceunitstr, cc3dds, autoconvert_space)

    return pcdims, ccdims


def get_time(pcdict, time_convs=_time_convs):
    """
    Parses PhysiCell data and generates CC3D time dimensions and unit conversions

    This function fetches the maximum time set in PhysiCell (pcdict['overall']['max_time']['#text']) and the time
    discretization (pcdict['overall']['dt_mechanics']['#text']) to set the max time for the CC3D simulation and what is
    MCS/unit factor in CC3D

    :param pcdict: Dictionary created from parsing PhysiCell XML
    :param time_convs: Dictionary of predefined space units
    :return pctime, cctime: Two tuples representing the dimension data from PhysiCell and in CC3D.
        (mt, time_unit, mechdt), and (steps, cc3dtimeunitstr, cc3ddt, autoconvert_time)
    """

    mt = float(pcdict['overall']['max_time']['#text']) if "max_time" in pcdict['overall'].keys() and \
                                                          '#text' in pcdict['overall']['max_time'].keys() else 100000

    mtunit = pcdict['overall']['max_time']['@units'] if "max_time" in pcdict['overall'].keys() and '@units' in \
                                                        pcdict['overall']['max_time'].keys() else None

    time_unit = pcdict['overall']['time_units'] if "time_units" in pcdict['overall'].keys() else None

    if mtunit != time_unit:
        message = f"Warning: Psysicell time units in " \
                  "\n`<overall>\n\t<max_time units=...`\ndiffers from\n" \
                  f"`<time_units>unit</time_units>`.\nUsing: {time_unit}"
        warnings.warn(message)

    autoconvert_time = True
    if time_unit not in time_convs.keys():
        message = f"WARNING: {time_unit} is not part of known time units. Automatic time-unit conversion disabled." \
                  f"Available units for auto-conversion are:\n{time_convs.keys()}"
        warnings.warn(message)
        autoconvert_time = False

    mechdt = float(pcdict['overall']['dt_mechanics']['#text']) if "dt_mechanics" in pcdict['overall'].keys() else None

    steps = round(mt / mechdt)

    cc3ddt = 1 / (mt / steps)  # MCS/unit

    # [cc3ddt] = MCS/unit
    # [cc3ddt] * unit = MCS

    cc3dtimeunitstr = f"1 MCS = {cc3ddt} {time_unit}"

    # timeconvfact = 1/cc3ddt
    pctime, cctime = (mt, time_unit, mechdt), (steps, cc3dtimeunitstr, cc3ddt, autoconvert_time)

    return pctime, cctime


def get_parallel(pcdict):
    return int(pcdict['parallel']['omp_num_threads']) if 'parallel' in pcdict.keys() and \
                                                         'omp_num_threads' in pcdict['parallel'].keys() else 1


def get_boundary_wall(pcdict):
    """
    Looks for the existance of a wall around the PhysiCell simulation and returns a flag saying if it does or not
    :param pcdict: Dictionary created from parsing PhysiCell XML
    :return wall_exists: bool for the existance of the boundary wall
    """
    wall_exists = False
    if "options" in pcdict.keys() and "virtual_wall_at_domain_edge" in pcdict['options'].keys():
        wall = pcdict["options"]["virtual_wall_at_domain_edge"].upper()
        if wall == "TRUE":
            wall_exists = True
            return wall_exists
        else:
            return wall_exists
    else:
        return wall_exists
    return wall_exists


def get_cell_volume(subdict):
    if 'phenotype' in subdict.keys() and 'volume' in subdict['phenotype'].keys() and \
            'total' in subdict['phenotype']['volume'].keys():
        volume = float(subdict['phenotype']['volume']['total']['#text'])
        units = subdict['phenotype']['volume']['total']['@units']
        return volume, units
    return None, None


def get_cell_mechanics(subdict):
    if 'phenotype' in subdict.keys() and 'mechanics' in subdict['phenotype'].keys():
        d = {}
        for key, item in subdict['phenotype']['mechanics'].items():
            if key != "options":
                d[key] = {'units': item['@units'],
                          'value': float(item['#text'])}
    else:
        return None

    return d


def check_below_minimum_volume(volume, minimum=8):
    if volume is None:
        return False, minimum
    return volume < minimum, minimum


_physicell_phenotype_codes = {
    "0": "Ki67 Advanced",
    "1": "Ki67 Basic",
    "2": "Flow Cytometry Basic",
    "5": "Simple Live",
    "6": "Flow Cytometry Advanced",
    "7": "Ki67 Basic",
    "100": "Standard apoptosis model",
    "101": "Standard necrosis model"}


def get_cycle_rate_data(rate_data, volume_datum, using_rates):
    if type(rate_data) != list:

        if using_rates:
            phase_duration = 1 / float(rate_data['#text']) if float(rate_data['#text']) \
                else 9e99
        else:
            phase_duration = float(rate_data['#text']) if float(rate_data['#text']) \
                else 9e99

        fixed_duration = rate_data['@fixed_duration'].upper()
        duration_data = (fixed_duration, phase_duration)
        phase_durations = [duration_data]
        fluid_change_rate = [float(volume_datum['fluid_change_rate']['#text'])]
        cytoplasmic_biomass_change_rate = [float(volume_datum['cytoplasmic_biomass_change_rate']['#text'])]
        nuclear_biomass_change_rate = [float(volume_datum['nuclear_biomass_change_rate']['#text'])]
        calcification_rate = [float(volume_datum['calcification_rate']['#text'])]
        fluid_fraction = [float(volume_datum['fluid_fraction']['#text'])]
        nuclear = [float(volume_datum['nuclear']['#text'])]
        calcified_fraction = [float(volume_datum['calcified_fraction']['#text'])]
        rel_rupture = [None]
        total = [float(volume_datum['total']['#text'])]
    else:

        phase_durations = []
        fluid_change_rate = []
        cytoplasmic_biomass_change_rate = []
        nuclear_biomass_change_rate = []
        calcification_rate = []

        fluid_fraction = []
        nuclear = []
        calcified_fraction = []
        rel_rupture = []
        total = []
        for rate_datum in rate_data:
            fixed_duration = rate_datum['@fixed_duration'].upper()
            if using_rates:
                phase_duration = 1 / float(rate_datum['#text']) if float(rate_datum['#text']) \
                    else 9e99
            else:
                phase_duration = float(rate_datum['#text']) if float(rate_datum['#text']) \
                    else 9e99
            duration_data = (fixed_duration, phase_duration)
            phase_durations.append(duration_data)

            fluid_change_rate.append(float(volume_datum['fluid_change_rate']['#text']))
            cytoplasmic_biomass_change_rate.append(
                float(volume_datum['cytoplasmic_biomass_change_rate']['#text']))
            nuclear_biomass_change_rate.append(float(volume_datum['nuclear_biomass_change_rate']['#text']))
            calcification_rate.append(float(volume_datum['calcification_rate']['#text']))

            fluid_fraction.append(float(volume_datum['fluid_fraction']['#text']))
            nuclear.append(float(volume_datum['nuclear']['#text']))
            calcified_fraction.append(float(volume_datum['calcified_fraction']['#text']))
            rel_rupture.append(None)
            total.append(float(volume_datum['total']['#text']))

    return phase_durations, fluid_change_rate, cytoplasmic_biomass_change_rate, nuclear_biomass_change_rate, \
           calcification_rate, fluid_fraction, nuclear, calcified_fraction, rel_rupture, total


def get_cycle_phenotypes(phenotypes, subdict, ppc):
    if subdict['phenotype']['cycle']['@code'] not in ppc.keys():
        message = f"WARNING: PhysiCell phenotype of code {subdict['phenotype']['cycle']['@code']}\n" \
                  f"not among PhenoCellPy's phenotypes. Falling back on Simple Live phenotype"
        warnings.warn(message)
        phenotypes[ppc["5"]] = None
        return phenotypes
    else:
        code_name = subdict['phenotype']['cycle']['@code']
        phenotype = ppc[code_name]
        if 'phase_transition_rates' in subdict['phenotype']['cycle'].keys():
            using_rates = True
            pheno_data = subdict['phenotype']['cycle']['phase_transition_rates']
        elif 'phase_durations' in subdict['phenotype']['cycle'].keys():
            using_rates = False
            pheno_data = subdict['phenotype']['cycle']['phase_durations']
        else:
            raise ValueError(f"Couldn't find phenotype phase transition data for "
                             f"{subdict['phenotype']['cycle']['name']}.\nIs this PhisiCell model valid?")

        rate_data = pheno_data['rate']
        if 'volume' in subdict['phenotype'].keys():
            volume_datum = subdict['phenotype']['volume']
            phase_durations, fluid_change_rate, cytoplasmic_biomass_change_rate, nuclear_biomass_change_rate, \
            calcification_rate, fluid_fraction, nuclear, calcified_fraction, rel_rupture, total = \
                get_cycle_rate_data(rate_data, volume_datum, using_rates)

            phenotypes[phenotype] = {"rate units": pheno_data['@units'],
                                     "phase durations": phase_durations,
                                     "fluid fraction": fluid_fraction,
                                     "fluid change rate": fluid_change_rate,
                                     "nuclear volume": nuclear,
                                     "cytoplasm biomass change rate": cytoplasmic_biomass_change_rate,
                                     "nuclear biomass change rate": nuclear_biomass_change_rate,
                                     "calcified fraction": calcified_fraction,
                                     "calcification rate": calcification_rate,
                                     "relative rupture volume": rel_rupture,
                                     "total": total}

        else:
            if 'phase_transition_rates' in subdict['phenotype']['cycle'].keys():
                using_rates = True
                pheno_data = subdict['phenotype']['cycle']['phase_transition_rates']
            elif 'phase_durations' in subdict['phenotype']['cycle'].keys():
                using_rates = False
                pheno_data = subdict['phenotype']['cycle']['phase_durations']
            if using_rates:
                phase_duration = 1 / float(rate_data['#text']) if float(rate_data['#text']) \
                    else 9e99
            else:
                phase_duration = float(rate_data['#text']) if float(rate_data['#text']) \
                    else 9e99
            fixed_duration = rate_data['@fixed_duration'].upper()
            duration_data = (fixed_duration, phase_duration)
            phase_durations = [duration_data]
            fluid_change_rate = [None]
            cytoplasmic_biomass_change_rate = [None]
            nuclear_biomass_change_rate = [None]
            calcification_rate = [None]
            fluid_fraction = [None]
            nuclear = [None]
            calcified_fraction = [None]
            phenotypes[phenotype] = {"rate units": pheno_data['@units'],
                                     "phase durations": phase_durations,
                                     "fluid fraction": fluid_fraction,
                                     "fluid change rate": fluid_change_rate,
                                     "nuclear volume": nuclear,
                                     "cytoplasm biomass change rate": cytoplasmic_biomass_change_rate,
                                     "nuclear biomass change rate": nuclear_biomass_change_rate,
                                     "calcified fraction": calcified_fraction,
                                     "calcification rate": calcification_rate,
                                     "relative rupture volume": [None]}
    return phenotypes


def get_death_phenotypes(phenotypes, subdict, ppc):
    death_models = subdict['phenotype']['death']['model']
    if type(death_models) == list:
        for model in death_models:
            code_name = model['@code']
            if code_name not in ppc.keys():
                message = f"WARNING: PhysiCell phenotype of code {subdict['phenotype']['cycle']['@code']}\n" \
                          f"not among PhenoCellPy's phenotypes. Falling back on Standard apoptosis model phenotype"
                warnings.warn(message)
                phenotypes[ppc["100"]] = None
            else:
                phenotype = ppc[code_name]
                phenotypes[phenotype] = {"rate units": model['death_rate']['@units']}
                phase_durations = model['phase_durations']['duration']
                duration_data = []
                if type(phase_durations) == list:
                    for phasedur in phase_durations:
                        fixed = phasedur['@fixed_duration'].upper()
                        duration = float(phasedur['#text']) if float(phasedur['#text']) else 9e99
                        duration_data.append((fixed, duration))
                else:
                    fixed = phase_durations['@fixed_duration'].upper()
                    duration = float(phase_durations['#text']) if float(phase_durations['#text']) else 9e99
                    duration_data.append((fixed, duration))
                phenotypes[phenotype]["phase durations"] = duration_data

                biomass_chage_rates = model['parameters']
                if code_name == "100":  # apoptosis
                    phenotypes[phenotype]["fluid change rate"] = \
                        [float(biomass_chage_rates['unlysed_fluid_change_rate']['#text'])]
                    phenotypes[phenotype]["cytoplasm biomass change rate"] = \
                        [float(biomass_chage_rates['cytoplasmic_biomass_change_rate']['#text'])]
                    phenotypes[phenotype]["nuclear biomass change rate"] = \
                        [float(biomass_chage_rates['nuclear_biomass_change_rate']['#text'])]
                    phenotypes[phenotype]["calcification rate"] = \
                        [float(biomass_chage_rates['calcification_rate']['#text'])]
                    phenotypes[phenotype]["relative rupture volume"] = [None]
                elif code_name == "101":  # necrosis
                    phenotypes[phenotype]["fluid change rate"] = \
                        [float(biomass_chage_rates['unlysed_fluid_change_rate']['#text']),
                         float(biomass_chage_rates['lysed_fluid_change_rate']['#text'])]
                    phenotypes[phenotype]["cytoplasm biomass change rate"] = \
                        [float(biomass_chage_rates['cytoplasmic_biomass_change_rate']['#text']),
                         float(biomass_chage_rates['cytoplasmic_biomass_change_rate']['#text'])]
                    phenotypes[phenotype]["nuclear biomass change rate"] = \
                        [float(biomass_chage_rates['nuclear_biomass_change_rate']['#text']),
                         float(biomass_chage_rates['nuclear_biomass_change_rate']['#text'])]
                    phenotypes[phenotype]["calcification rate"] = \
                        [float(biomass_chage_rates['calcification_rate']['#text']),
                         float(biomass_chage_rates['calcification_rate']['#text'])]
                    phenotypes[phenotype]["relative rupture volume"] = [None, 2]
    else:
        model = death_models
        code_name = model['@code']
        if code_name not in ppc.keys():
            message = f"WARNING: PhysiCell phenotype of code {subdict['phenotype']['cycle']['@code']}\n" \
                      f"not among PhenoCellPy's phenotypes. Falling back on Standard apoptosis model phenotype"
            warnings.warn(message)
            phenotypes[ppc["100"]] = None
            return phenotypes
        else:
            phenotype = ppc[code_name]
            phenotypes[phenotype] = {"rate units": model['death_rate']['@units']}
            if 'phase_durations' in model.keys():
                phase_durations = model['phase_durations']['duration']
                duration_data = []
                if type(phase_durations) == list:
                    for phasedur in phase_durations:
                        fixed = phasedur['@fixed_duration'].upper()
                        duration = float(phasedur['#text'])
                        duration_data.append((fixed, duration))
                else:
                    fixed = phase_durations['@fixed_duration'].upper()
                    duration = float(phase_durations['#text'])
                    duration_data.append((fixed, duration))
                phenotypes[phenotype]["phase durations"] = duration_data
            else:
                phenotypes[phenotype]["phase durations"] = [(None, None)] * len(phenotypes[phenotype]["rate units"])

            if 'parameters' in model.keys():
                biomass_chage_rates = model['parameters']
                if code_name == "100":  # apoptosis
                    phenotypes[phenotype]["fluid change rate"] = \
                        [float(biomass_chage_rates['unlysed_fluid_change_rate']['#text'])]
                    phenotypes[phenotype]["cytoplasm biomass change rate"] = \
                        [float(biomass_chage_rates['cytoplasmic_biomass_change_rate']['#text'])]
                    phenotypes[phenotype]["nuclear biomass change rate"] = \
                        [float(biomass_chage_rates['nuclear_biomass_change_rate']['#text'])]
                    phenotypes[phenotype]["calcification rate"] = \
                        [float(biomass_chage_rates['calcification_rate']['#text'])]
                    phenotypes[phenotype]["relative rupture volume"] = [None]
                elif code_name == "101":  # necrosis
                    phenotypes[phenotype]["fluid change rate"] = \
                        [float(biomass_chage_rates['unlysed_fluid_change_rate']['#text']),
                         float(biomass_chage_rates['lysed_fluid_change_rate']['#text'])]
                    phenotypes[phenotype]["cytoplasm biomass change rate"] = \
                        [float(biomass_chage_rates['cytoplasmic_biomass_change_rate']['#text']),
                         float(biomass_chage_rates['cytoplasmic_biomass_change_rate']['#text'])]
                    phenotypes[phenotype]["nuclear biomass change rate"] = \
                        [float(biomass_chage_rates['nuclear_biomass_change_rate']['#text']),
                         float(biomass_chage_rates['nuclear_biomass_change_rate']['#text'])]
                    phenotypes[phenotype]["calcification rate"] = \
                        [float(biomass_chage_rates['calcification_rate']['#text']),
                         float(biomass_chage_rates['calcification_rate']['#text'])]
                    phenotypes[phenotype]["relative rupture volume"] = [None, 2]
    return phenotypes


def get_cell_phenotypes(subdict, ppc=_physicell_phenotype_codes):
    phenotypes = {}
    if 'phenotype' not in subdict.keys():
        return None, None
    if 'cycle' in subdict['phenotype'].keys():
        phenotypes = get_cycle_phenotypes(phenotypes, subdict, ppc)
    if 'death' in subdict['phenotype'].keys():
        phenotypes = get_death_phenotypes(phenotypes, subdict, ppc)
    pheno_names = list(phenotypes.keys())
    return phenotypes, pheno_names


def get_custom_data(subdict):
    if "custom_data" in subdict.keys():
        return subdict["custom_data"]

    return None


def get_cell_constraints(pcdict, space_unit, minimum_volume=8):
    constraints = {}
    any_below = False
    volumes = []
    for child in pcdict['cell_definitions']['cell_definition']:
        ctype = child['@name'].replace(" ", "_")
        constraints[ctype] = {}
        volume, unit = get_cell_volume(child)
        if volume is None or unit is None:
            message = f"WARNING: cell volume for cell type {ctype} either doesn't have a unit \n(unit found: {unit}) " \
                      f"or" \
                      f" doesn't have a value (value found: {volume}). \nSetting the volume to be the minimum volume, " \
                      f"{minimum_volume}"
            warnings.warn(message)
            volume = None
            unit = "not specified"
            dim = 3
        else:
            dim = int(unit.split("^")[-1])
        if volume is None:
            volumepx = None
        else:
            volumepx = volume * (space_unit ** dim)
        below, minimum_volume = check_below_minimum_volume(volumepx, minimum=minimum_volume)
        constraints[ctype]["volume"] = {f"volume ({unit})": volume,
                                        "volume (pixels)": volumepx}
        volumes.append(volumepx)
        if below:
            any_below = True
            message = f"WARNING: converted cell volume for cell type {ctype} is below {minimum_volume}. Converted volume " \
                      f"{volumepx}. \nIf cells are too small in CC3D they do not behave in a biological manner and may " \
                      f"disapear. \nThis program will enforce that: 1) the volume proportions stay as before; 2) the " \
                      f"lowest cell volume is {minimum_volume}"
            warnings.warn(message)
        constraints[ctype]["mechanics"] = get_cell_mechanics(child)
        constraints[ctype]["custom_data"] = get_custom_data(child)
        constraints[ctype]["phenotypes"], constraints[ctype]["phenotypes_names"] = get_cell_phenotypes(child)

    return constraints, any_below, volumes, minimum_volume


def get_space_time_from_diffusion(unit):
    parts = unit.split("/")
    timeunit = parts[-1]
    spaceunit = parts[0].split("^")[0]
    return spaceunit, timeunit


def get_secretion(pcdict):
    # will have to be done in python
    sec_data = {}
    for child in pcdict['cell_definitions']['cell_definition']:
        if 'secretion' not in child['phenotype'].keys():
            break
        ctype = child['@name'].replace(" ", "_")
        sec_data[ctype] = {}
        sec_list = child['phenotype']['secretion']['substrate']
        if type(sec_list) == list:
            for sec in sec_list:
                substrate = sec["@name"].replace(" ", "_")
                sec_data[ctype][substrate] = {}
                sec_data[ctype][substrate]['secretion_rate'] = float(
                    sec['secretion_rate']['#text']) if 'secretion_rate' in sec.keys() else 0
                sec_data[ctype][substrate]['secretion_unit'] = sec['secretion_rate'][
                    '@units'] if 'secretion_rate' in sec.keys() else "None"
                sec_data[ctype][substrate]['secretion_target'] = float(
                    sec['secretion_target']['#text']) if 'secretion_target' in sec.keys() else 0
                sec_data[ctype][substrate]['uptake_rate'] = float(
                    sec['uptake_rate']['#text']) if 'uptake_rate' in sec.keys() else 0
                sec_data[ctype][substrate]['uptake_unit'] = sec['uptake_rate'][
                    '@units'] if 'uptake_rate' in sec.keys() else "None"
                sec_data[ctype][substrate]['net_export'] = float(
                    sec['net_export_rate']['#text']) if 'net_export_rate' in sec.keys() else 0
                sec_data[ctype][substrate]['net_export_unit'] = sec['net_export_rate'][
                    '@units'] if 'net_export_rate' in sec.keys() else "None"
        else:
            sec = sec_list
            substrate = sec["@name"].replace(" ", "_")
            sec_data[ctype][substrate] = {}
            sec_data[ctype][substrate]['secretion_rate'] = float(
                sec['secretion_rate']['#text']) if 'secretion_rate' in sec.keys() else 0
            sec_data[ctype][substrate]['secretion_unit'] = sec['secretion_rate'][
                '@units'] if 'secretion_rate' in sec.keys() else "None"
            sec_data[ctype][substrate]['secretion_target'] = float(
                sec['secretion_target']['#text']) if 'secretion_target' in sec.keys() else 0
            sec_data[ctype][substrate]['uptake_rate'] = float(
                sec['uptake_rate']['#text']) if 'uptake_rate' in sec.keys() else 0
            sec_data[ctype][substrate]['uptake_unit'] = sec['uptake_rate'][
                '@units'] if 'uptake_rate' in sec.keys() else "None"
            sec_data[ctype][substrate]['net_export'] = float(
                sec['net_export_rate']['#text']) if 'net_export_rate' in sec.keys() else 0
            sec_data[ctype][substrate]['net_export_unit'] = sec['net_export_rate'][
                '@units'] if 'net_export_rate' in sec.keys() else "None"
    return sec_data


def get_microenvironment(pcdict, space_factor, space_unit, time_factor, time_unit, autoconvert_time=True,
                         autoconvert_space=True, space_convs=_space_convs, time_convs=_time_convs,
                         steady_state_threshold=1000):
    diffusing_elements = {}
    fields = pcdict['microenvironment_setup']['variable']
    for subel in fields:

        auto_s_this = autoconvert_space
        auto_t_this = autoconvert_time

        diffusing_elements[subel['@name']] = {}
        diffusing_elements[subel['@name']]["use_steady_state"] = False
        diffusing_elements[subel['@name']]["concentration_units"] = subel["@units"]
        diffusing_elements[subel['@name']]["D_w_units"] = \
            float(subel['physical_parameter_set']['diffusion_coefficient']['#text'])

        this_space, this_time = get_space_time_from_diffusion(subel['physical_parameter_set']['diffusion_coefficient']
                                                              ['@units'])

        if this_space != space_unit:
            message = f"WARNING: space unit found in diffusion coefficient of {subel['@name']} does not match" \
                      f"space unit found while converting <overall>:\n\t<overall>:{space_unit};\n\t{subel['@name']}:" \
                      f"{this_space}" \
                      f"\nautomatic space-unit conversion for {subel['@name']} disabled"
            warnings.warn(message)
            auto_s_this = False
            # space_conv_factor = 1
        if this_time != time_unit:
            message = f"WARNING: time unit found in diffusion coefficient of {subel['@name']} does not match" \
                      f"space unit found while converting <overall>:\n\t<overall>:{time_unit};" \
                      f"\n\t{subel['@name']}:{this_time}" \
                      f"\nautomatic time-unit conversion for {subel['@name']} disabled"
            warnings.warn(message)
            auto_t_this = False
            # time_conv_factor = 1

        diffusing_elements[subel['@name']]["auto"] = (auto_s_this, auto_t_this)

        if auto_s_this:
            space_conv_factor = space_factor
        else:
            space_conv_factor = 1

        if auto_t_this:
            time_conv_factor = time_factor
        else:
            time_conv_factor = 1

        D = diffusing_elements[subel['@name']]["D_w_units"] * space_conv_factor * space_conv_factor / time_conv_factor
        diffusing_elements[subel['@name']]["D"] = D
        if D > steady_state_threshold:
            diffusing_elements[subel['@name']]["use_steady_state"] = True

        # [cc3dds] = pixel/unit
        # [cc3dds] * unit = pixel -> pixel^2 = ([cc3dds] * unit)^2
        # [cc3ddt] = MCS/unit
        # [cc3ddt] * unit = MCS -> 1/MCS = 1/([cc3ddt] * unit)

        if auto_s_this and auto_t_this:
            diffusing_elements[subel['@name']]["D_conv_factor_text"] = f"1 pixel^2/MCS" \
                                                                       f" = {space_conv_factor * space_conv_factor / time_conv_factor}" \
                                                                       f" {space_unit}^2/{time_unit}"
            diffusing_elements[subel['@name']]["D_conv_factor"] = space_conv_factor * space_conv_factor / \
                                                                  time_conv_factor
            diffusing_elements[subel['@name']]["D_og_unit"] = f"{space_unit}^2/{time_unit}"
        else:
            diffusing_elements[subel['@name']]["D_conv_factor_text"] = "disabled autoconversion"
            diffusing_elements[subel['@name']]["D_conv_factor"] = 1
            diffusing_elements[subel['@name']]["D_og_unit"] = "disabled autoconversion, not known"
        diffusing_elements[subel['@name']]["gamma_w_units"] = float(subel['physical_parameter_set']['decay_rate']
                                                                    ['#text'])
        gamma = diffusing_elements[subel['@name']]["gamma_w_units"] / time_conv_factor
        diffusing_elements[subel['@name']]["gamma"] = gamma
        if auto_t_this:
            diffusing_elements[subel['@name']][
                "gamma_conv_factor_text"] = f"1/MCS = {1 / time_conv_factor} 1/{time_unit}"
            diffusing_elements[subel['@name']]["gamma_conv_factor"] = 1 / time_conv_factor
            diffusing_elements[subel['@name']]["gamma_og_unit"] = f" 1/{time_unit}"
        else:
            diffusing_elements[subel['@name']]["gamma_conv_factor_text"] = "disabled autoconversion"
            diffusing_elements[subel['@name']]["gamma_conv_factor"] = 1
            diffusing_elements[subel['@name']]["gamma_og_unit"] = "disabled autoconversion, not known"

        diffusing_elements[subel['@name']]["initial_condition"] = subel['initial_condition']['#text']

        diffusing_elements[subel['@name']]["dirichlet"] = subel['Dirichlet_boundary_condition']['@enabled']
        diffusing_elements[subel['@name']]["dirichlet_value"] = float(subel['Dirichlet_boundary_condition']['#text'])

    return diffusing_elements
