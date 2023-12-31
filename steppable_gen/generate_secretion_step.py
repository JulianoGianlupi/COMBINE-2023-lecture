try:
    from .gen_functions import generate_steppable, steppable_imports, generate_cell_type_loop
except:
    from gen_functions import generate_steppable, steppable_imports, generate_cell_type_loop  # why are python imports
    # like this? 1st option does not work when running this file by itself. Second doesn't work when importing the
    # file.............................................................................................................

import warnings


# general idea: define secretor objects in start as self variables. Use those in the step function
# in cell loops. Could I list all secretors and loop them? probably


def get_field_names(sec_dict):
    fields = []
    for ctype, subdict in sec_dict.items():
        for field_name in subdict.keys():
            if field_name not in fields:
                fields.append(field_name)
    return fields


def make_secretors(field_names):
    sec_dict = "\t\tself.secretors = {"
    for name in field_names:
        sec_dict += f"'{name}': self.get_field_secretor('{name}'),"
    sec_dict = sec_dict[:-1]
    sec_dict += "}\n"
    return sec_dict


def make_secretion_uptake_loop(ctype, comment):
    # secretion in physicell is
    # secretion rate * (target amount - amount at cell) + net secretion
    # looking at units that is correct:
    # < secretion_rate units = "1/min" > 0 < / secretion_rate >
    # < secretion_target units = "substrate density" > 1 < / secretion_target >
    # < uptake_rate units = "1/min" > 0 < / uptake_rate >
    # < net_export_rate units = "total substrate/min" > 0 < / net_export_rate >
    loop = generate_cell_type_loop(ctype, 3)
    check_field = "\t\t\t\tif field_name in cell.dict.keys():\n\t\t\t\t\tdata=cell.dict[field_name]\n"
    seen = "\t\t\t\t\tseen = secretor.amountSeenByCell(cell)\n"
    secrete_rate = "\t\t\t\t\tnet_secretion = max(0, data['secretion_rate_MCS'] * (data['secretion_target'] - seen)) + data['net_export_MCS']\n"
    where_secrete = "\t\t\t\t\t# In PhysiCell cells are point-like, in CC3D they have an arbitrary shape. With this " \
                    "\n\t\t\t\t\t# CC3D allows several different secretion locations: over the whole cell (what the " \
                    "translator uses),\n\t\t\t\t\t# just inside the cell surface, just outside the surface, " \
                    "at the surface. You should explore the options\n"
    secrete = "\t\t\t\t\tif net_secretion:\n\t\t\t\t\t\tsecretor.secreteInsideCell(cell, net_secretion)\n"

    uptake = "\t\t\t\t\tif data['uptake_rate']:\n\t\t\t\t\t\t" \
             "secretor.uptakeInsideCell(cell, 1e10, data['uptake_rate'])\n"
    return loop + check_field + seen + comment + secrete_rate + where_secrete + secrete + uptake


def make_secretion_uptake_loops(cell_types, sec_dict):
    secretor_loop = "\t\tfor field_name, secretor in self.secretors.items():\n"

    loops = ""
    for ctype in cell_types:
        if ctype in sec_dict.keys():

            comment = sec_dict[ctype][list(sec_dict[ctype].keys())[0]]['secretion_comment'] + '\n'
            loops += make_secretion_uptake_loop(ctype, comment)
    return secretor_loop + loops


def generate_secretion_uptake_step(cell_types, sec_dict, secretion_dt=None, first=False):
    if not sec_dict:
        message = "WARNING: no secretion data found\n"
        warnings.warn(message)
        return ''

    if secretion_dt is None:
        secretion_dt = 1

    already_imports = not first

    field_names = get_field_names(sec_dict)

    secretors = make_secretors(field_names)

    loops = make_secretion_uptake_loops(cell_types, sec_dict)

    sec_step = generate_steppable("SecretionUptake", secretion_dt, False, already_imports=already_imports,
                                  additional_start=secretors, additional_step=loops)

    return sec_step


if __name__ == "__main__":
    sdict = {'cancer_cell': {
        'oxygen': {'secretion_rate': 0.0, 'secretion_unit': '1/min', 'secretion_target': 38.0, 'uptake_rate': 10.0,
                   'uptake_unit': '1/min', 'net_export': 0.0, 'net_export_unit': 'total substrate/min',
                   'secretion_rate_MCS': 0.0,
                   'secretion_comment': '#WARNING: PhysiCell has a concept of "target secretion" that CompuCell3D does not. \n#The translating program attempts to implement it, but it may not be a 1 to 1 conversion.',
                   'net_export_MCS': 0.0, 'net_secretion_comment': '', 'uptake_rate_MCS': 1.0,
                   'uptake_comment': '#WARNING: To avoid negative concentrations, in CompuCell3D uptake is "bounded." \n# If the amount that would be uptaken is larger than the value at that pixel,\n# the uptake will be a set ratio of the amount available.\n# The conversion program uses 1 as the ratio,\n# you may want to revisit this.'},
        'immunostimulatory_factor': {'secretion_rate': 0.0, 'secretion_unit': '1/min', 'secretion_target': 1.0,
                                     'uptake_rate': 0.0, 'uptake_unit': '1/min', 'net_export': 0.0,
                                     'net_export_unit': 'total substrate/min', 'secretion_rate_MCS': 0.0,
                                     'secretion_comment': '#WARNING: PhysiCell has a concept of "target secretion" that CompuCell3D does not. \n#The translating program attempts to implement it, but it may not be a 1 to 1 conversion.',
                                     'net_export_MCS': 0.0, 'net_secretion_comment': '', 'uptake_rate_MCS': 0.0,
                                     'uptake_comment': '#WARNING: To avoid negative concentrations, in CompuCell3D uptake is "bounded." \n# If the amount that would be uptaken is larger than the value at that pixel,\n# the uptake will be a set ratio of the amount available.\n# The conversion program uses 1 as the ratio,\n# you may want to revisit this.'}},
        'immune_cell': {
            'oxygen': {'secretion_rate': 0.0, 'secretion_unit': '1/min', 'secretion_target': 38.0,
                       'uptake_rate': 10.0, 'uptake_unit': '1/min', 'net_export': 0.0,
                       'net_export_unit': 'total substrate/min', 'secretion_rate_MCS': 0.0,
                       'secretion_comment': '#WARNING: PhysiCell has a concept of "target secretion" that CompuCell3D does not. \n#The translating program attempts to implement it, but it may not be a 1 to 1 conversion.',
                       'net_export_MCS': 0.0, 'net_secretion_comment': '', 'uptake_rate_MCS': 1.0,
                       'uptake_comment': '#WARNING: To avoid negative concentrations, in CompuCell3D uptake is "bounded." \n# If the amount that would be uptaken is larger than the value at that pixel,\n# the uptake will be a set ratio of the amount available.\n# The conversion program uses 1 as the ratio,\n# you may want to revisit this.'},
            'immunostimulatory_factor': {'secretion_rate': 0.0, 'secretion_unit': '1/min',
                                         'secretion_target': 1.0, 'uptake_rate': 0.0,
                                         'uptake_unit': '1/min', 'net_export': 0.0,
                                         'net_export_unit': 'total substrate/min',
                                         'secretion_rate_MCS': 0.0,
                                         'secretion_comment': '#WARNING: PhysiCell has a concept of "target secretion" that CompuCell3D does not. \n#The translating program attempts to implement it, but it may not be a 1 to 1 conversion.',
                                         'net_export_MCS': 0.0, 'net_secretion_comment': '',
                                         'uptake_rate_MCS': 0.0,
                                         'uptake_comment': '#WARNING: To avoid negative concentrations, in CompuCell3D uptake is "bounded." \n# If the amount that would be uptaken is larger than the value at that pixel,\n# the uptake will be a set ratio of the amount available.\n# The conversion program uses 1 as the ratio,\n# you may want to revisit this.'}}}

    sec_step = generate_secretion_uptake_step(['cancer_cell', 'immune_cell'], sdict, first=True)

    # fields = get_field_names(sdict)
    # secretors = make_secretors(fields)
    #
    # loops = make_secretion_loops(['cancer_cell', 'immune_cell'], sdict, secretors, fields)
    pass
