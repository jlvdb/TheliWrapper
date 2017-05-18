import argparse
from collections import namedtuple


def number_empty(type):
    # test type only if input ist not given as empty string ('') explicitly
    def type_test(value):
        if value != '':
            strtype = "float" if type == float else "int"
            try:
                value = type(value)
            except ValueError:
                raise argparse.ArgumentTypeError(
                    "invalid %s value: '%s'" % (strtype, value))
        return value
    return type_test


Parameter = namedtuple(
    "Parameter",
    ["arg", "name", "group", "type", "choices", "mapping", "default", "help"])

parameter_list = [
    ['scp_match_flipped', 'V_SCAMP_MATCHFLIPPED', "Astrometry (Scamp)",
     bool, None, ("Y", "N"), False,
     ""],
    ['bg_method', 'V_BACK_APPLYMODE', "Backgroud modeling",
     str, ("subtract", "divide", "defringe",
           "devide+defringe"), (0, 1, 2, 3), None,
     ""],
    ['coll_discard_masks', 'V_COLLMASKACTION', "Collapse correction",
     bool, None, (1, 0), True,
     ""],
    ['wt_uniform', 'V_GLOBW_UNIFORMWEIGHT', "Weighting",
     bool, None, ("TRUE", "FALSE"), False,
     ""],
    ['ref_query_radius', 'V_AP_RADIUS', "Astro/Photometry",
     float, None, None, "",
     ""],
    ['grouplen', '', "Sequence splitting",
     int, None, None, "",
     ""]]
parameter_list = [
    Parameter(*parameter_list[i]) for i in range(len(parameter_list))]
parameter_map = {}
for param in parameter_list:
    if not param.arg == '':
        parameter_map[param.arg] = param


parser = argparse.ArgumentParser()

for arg, info in parameter_map.items():
    kwargs = {'help': argparse.SUPPRESS}
    # bool action depends on default value
    if info.type is bool:
        kwargs['action'] = "store_false" if info.default else "store_true"
    else:
        # use special parser that allows empty string in some cases
        if info.type in (int, float) and info.default == '':
            kwargs['type'] = number_empty(info.type)
        else:
            kwargs['type'] = info.type
            # add choices if given
            if info.choices is not None:
                kwargs['choices'] = info.choices
            # set default if given
            if info.default is not None:
                kwargs['default'] = info.default
    parser.add_argument("--" + arg.replace("_", "-"), **kwargs)


def translate_theli_args(parsedargs):
    # apply mapping to convert to correct internal parameter values
    for param in parameter_list:
        name = param[0]
        value = getattr(parsedargs, name)
        # ignore unset arguments
        if value is None:
            continue
        # bool: requires a mapping from bool to the proper type of str
        # can be either Y/N, 1/0 or TRUE/FALSE
        if param.type is bool:
            translated = param.mapping[int(not value)]
            setattr(parsedargs, name, translated)
        # apply mapping, if neccessary
        else:
            if param.mapping is not None:
                if param.choices is None:
                    raise ValueError(
                        "choices cannot be 'None' if mapping is given")
                if len(param.mapping) != len(param.choices):
                    raise IndexError(
                        "choices and mapping lengths do not match")
                idx = param.choices.index(value)
                translated = param.mapping[idx]
                setattr(parsedargs, name, translated)
    # convert parsed arguments to THELI parameter dict
    # take all parameters except those beloging to GUI widgets
    parameter_dict = {}
    all_params = [internal for internal, param in parameter_map.items()
                  if param.name != '']
    for param in parsedargs.__dict__:
        value = getattr(parsedargs, param)
        if param in all_params and value is not None:
            key = parameter_map[param].name.replace("-", "_")
            parameter_dict[key] = value
    return parsedargs, parameter_dict


args = parser.parse_args()
print(args)


args, theli_args = translate_theli_args(args)
print(args)
print(theli_args)
