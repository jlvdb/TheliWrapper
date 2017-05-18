"""
This is a command line interface to the wrapper for the THELI GUI
scripts, based on the THELI package for astronomical image reduction.
"""

import os
import sys
import argparse
import shutil
import textwrap
from copy import copy
from system.base import ascii_styled, DIRS
from .commandlist import *


class ActionJobCheck(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super(ActionJobCheck, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        joblist = [values[i:i + 2] for i in range(0, len(values), 2)]
        for job in joblist:
            if job not in parse_actions:
                raise parser.error(
                    "invalid job descriptor '%s' in '%s'" % (job, values))
        joblist = [parse_actions[job] for job in joblist]
        setattr(namespace, self.dest, joblist)


class ActionParseFile(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super(ActionParseFile, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values == "**this_is_a_mock**":  # don't run again if mock
            return
        # if file does not exist, look into presets folder
        if not os.path.exists(values):
            base_folder = os.path.dirname(os.path.realpath(__file__))
            preset_file = os.path.join(base_folder, "presets", values)
        else:
            preset_file = values
        # load file and strip lines
        try:
            with open(preset_file) as conf:
                content = conf.readlines()
        except FileNotFoundError:
            raise parser.error("found no parameter file: %s" % values)
        except IOError:
            raise parser.error(
                "could not read from parameter file: %s" % values)
        # workaround: need to give mock positionals to accomplish parsing
        arguments = ["Fs", "**this_is_a_mock**"]
        for line in content:
            line = line.strip()
            if line.startswith("#") or line == "":
                continue
            if not line.startswith("--"):
                line = "--" + line
            line = line.split()
            arguments.extend(line)
        # parse arguments from file
        new_args = parser.parse_args(arguments)
        for arg in vars(new_args):
            # make sure that mocks will not end up in our arguments
            if arg not in ("jobs", "inst", "main", "bias", "dark", "flat",
                           "flatoff", "science", "sky", "standard"):
                setattr(namespace, arg, getattr(new_args, arg))


class ActionHelpJob(argparse.Action):
    def __init__(self, option_strings, dest, nargs='?', **kwargs):
        super(ActionHelpJob, self).__init__(
            option_strings, dest, nargs, **kwargs)
        self.width = min(120, shutil.get_terminal_size((60, 24))[0])

    def __call__(self, parser, namespace, values, option_string=None):
        print(Parser.format_usage())
        # generate help entries
        help_pad = 8
        if values is None:
            infostr = ("List of job abbreviations. Assemble those you need in "
                       "THIS order to create the JOBLIST:")
            print(textwrap.fill(infostr, width=self.width) + "\n")
            print("job abbreviations:")
            for arg in parse_actions_ordered:
                action = parse_actions[arg]
                helpstr = ("\n" + help_pad * " ").join(
                    textwrap.wrap(
                        action["help"], width=(self.width - help_pad)))
                print("{:{pad}}{:}".format(
                    "  %s  " % arg, helpstr, pad=help_pad))
            print()
        else:
            infostr = "THELI parameters that influence the " + \
                "job %s:" % ascii_styled(values, "br-")
            print(textwrap.fill(infostr, width=self.width) + "\n")
            thelihelp = ActionHelpTheli(option_string, "dummy_dest")
            thelihelp.print_help(values, match_jobs_only=True)
        print(Parser.epilog)
        sys.exit(0)


class ActionHelpTheli(argparse.Action):
    """Behaves like the argparse help formatter, but has some extras:
    it supports pattern search to shrink down the long parameter listing"""

    def __init__(self, option_strings, dest, nargs='?', **kwargs):
        super(ActionHelpTheli, self).__init__(
            option_strings, dest, nargs, **kwargs)
        # alignment
        self.width = min(120, shutil.get_terminal_size((60, 24))[0])
        self.help_pad = min(36, int(self.width * 0.4))

    def highlight_pattern(self, string, pattern, h_all=False):
        """highlightes first occurence of the search pattern in the string"""
        stylestr = "br-"
        if pattern is None:
            return string
        try:
            idx = string.lower().index(pattern.lower())
            if h_all:
                return ascii_styled(string, stylestr)
            else:
                head = string[:idx]
                midd = string[idx:idx + len(pattern)]
                tail = string[idx + len(pattern):]
                return head + ascii_styled(midd, stylestr) + tail
        except ValueError:
            return string

    def format_argument(self, arg, param):
        # format the argument and choices
        if "choi" in param:
            string = "  %s " % arg
            # replace white spaces with rarely used character "´"
            choicestr = " ".join([c.replace(" ", "´") for c in param["choi"]])
            choicestr = "{%s}" % choicestr
            # use textwrap which splits at white spaces
            # run with respect to indented first line
            lines = textwrap.wrap(
                choicestr, width=(self.width - len(string) - 1))
            # all but first line: merge and resplit them on terminal width
            rest = textwrap.wrap(
                " ".join(lines[1:]), width=(self.width - 1))
            # construct final string with new line separation
            choicestr = lines[0]
            if len(rest) > 0:
                choicestr += "\n" + "\n".join(rest)
            # make list comma separated and revert original white spaces
            choicestr = choicestr.replace(" ", ",").replace("´", " ")
            string += choicestr.replace("\n", ",\n") + "  "
        else:
            if "meta" in param:
                metavar = " " + param["meta"]
            elif param["type"] == str:
                metavar = " STR"
            elif param["type"] == int:
                metavar = " INT"
            elif param["type"] == float:
                metavar = " FLOAT"
            string = "  %s%s  " % (arg, metavar)
        string = "{:{pad}}".format(string, pad=self.help_pad)
        # format help message
        if len(string) > self.help_pad:
            string += "\n" + " " * self.help_pad
        # wrap long lines and keep alignment at 'help_pad'
        helpstr = ("\n" + self.help_pad * " ").join(
            textwrap.wrap(param["help"], width=(self.width - self.help_pad)))
        return string + helpstr

    def print_help(self, pattern, match_jobs_only=False):
        # apply search pattern to help
        helpdict = copy(parse_parameters)
        if pattern is not None:
            for group in parse_parameters:
                if pattern.lower() in group.lower() and not match_jobs_only:
                    continue
                filtered_args = {}
                if match_jobs_only:
                    for arg, param in parse_parameters[group].items():
                        if "task" not in param:
                            continue
                        if any(pattern.lower() in t.lower()
                               for t in param["task"]):
                            filtered_args[arg] = param
                else:
                    for arg, param in parse_parameters[group].items():
                        if pattern.lower() in arg.lower() or \
                                pattern.lower() in param["help"].lower():
                            filtered_args[arg] = param
                if len(filtered_args) == 0:
                    helpdict.pop(group)
                else:
                    helpdict[group] = filtered_args
        # generate sorted and formatted help
        for group in sorted(helpdict.keys()):
            print(self.highlight_pattern(group + ":", pattern, h_all=True))
            # sort the dictionary by the 'sort' keywords
            sorting = [(val["sort"], arg)
                       for arg, val in helpdict[group].items()]
            for pos, arg in sorted(sorting, key=lambda x: x[0]):
                helpstr = self.format_argument(arg, helpdict[group][arg])
                helpstr = self.highlight_pattern(helpstr, pattern)
                print(helpstr)
            print()

    def __call__(self, parser, namespace, values, option_string=None):
        print(Parser.format_usage())
        infostr = "Grouped list of additional THELI parameters"
        if values is not None:
            infostr += " (containing '%s')" % ascii_styled(values, "br-")
        print(textwrap.fill(infostr, width=self.width) + ":\n")
        # generate help entries
        self.print_help(values)
        print(Parser.epilog)
        sys.exit(0)


class ActionVersion(argparse.Action):
    """prints versions of the THELI installation, the GUI scripts and this
    command line wrapper"""

    def __init__(self, option_strings, dest, nargs=0, **kwargs):
        super(ActionVersion, self).__init__(
            option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        pad = 15
        versionstr = "{:{pad}}{:}\n".format(
            "THELI:", __version_theli__, pad=pad)
        versionstr += "{:{pad}}{:}\n".format(
            "GUI scripts:", __version_gui__, pad=pad)
        versionstr += "-" * 25 + "\n"
        versionstr += "{:{pad}}{:}".format(
            os.path.basename(__file__), __version__, pad=pad)
        print(versionstr)
        sys.exit()


def TypeNumberEmpty(type):
    """Type test for int and float in Parser. Accepts an empty string to unset
    parameters (corresponding to emtpy GUI line edits)"""
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


class TheliParser(argparse.ArgumentParser):

    def parse_theli_args(self):
        """convert command line arguments into the THELI parameter file formats
        and group them in dictionary which can be parsed to Parameters.set(),
        extract the main folder"""
        # invoke argument parser
        parsedargs = self.parse_args()
        # apply mapping to convert to correct internal parameter values
        for group, content in parse_parameters.items():
            for argstr, param in content.items():
                arg = argstr[2:].replace("-", "_")
                value = getattr(parsedargs, arg)
                # ignore unset arguments
                if value is None:
                    continue
                # bool -> str: mapping from Y/N to the proper type of str,
                #              can be either Y/N, 1/0 or TRUE/FALSE
                if "maps" in param:
                    if "choi" not in param:
                        raise ValueError(
                            "mapping has to be given together with choices")
                    if len(param["maps"]) != len(param["choi"]):
                        raise IndexError(
                            "choices and mapping lengths do not match")
                    idx = param["choi"].index(value)
                    translated = param["maps"][idx]
                    setattr(parsedargs, arg, translated)
        # convert parsed arguments to THELI parameter dict
        # take all parameters except those beloging to GUI widgets
        parameter_dict = {}
        for group, content in parse_parameters.items():
            all_params = [argstr[2:].replace("-", "_")
                          for argstr, param in content.items()
                          if "name" in param]
            for param in parsedargs.__dict__:
                value = getattr(parsedargs, param)
                if param in all_params and value is not None:
                    argstr = "--" + param.replace("_", "-")
                    try:
                        key = content[argstr]["name"]
                        parameter_dict[key] = value
                    except KeyError:
                        pass  # in different group
        return parsedargs, parameter_dict
        # USE os.getcwd() as maindir now
        # get a root folder from any of the data folders
        # folderargs = (
        #     "science", "bias", "dark", "flat", "flatoff", "sky", "standard")
        # maindir = None
        # for folder in folderargs:
        #     value = getattr(parsedargs, folder)
        #     if value is not None:
        #         main, base = os.path.split(os.path.normpath(value))
        #         if main != "":
        #             maindir = main
        #             break
        # if maindir is None:
        #     raise Parser.error(
        #         "could not determine root folder from any "
        #         "of the data folders")
        # return parsedargs, parameter_dict, main


Parser = TheliParser(
    add_help=False,
    description="This is a command line wrapper for the THELI GUI scripts, "
                "based on the  THELI package for astronomical image "
                "reduction.",
    epilog="The manual for the original THELI GUI is available online at:\n"
           "https://www.astro.uni-bonn.de/theli/gui/",
    formatter_class=lambda prog: argparse.HelpFormatter(
        prog, max_help_position=28))

Parser.add_argument(
    'jobs', metavar='JOBLIST', action=ActionJobCheck,
    help="listing of job descriptors (see --help-jobs)")
Parser.add_argument(
    'inst', metavar="INST",
    help="THELI instrument identification string")

presetgroup = Parser.add_argument_group(title="configuration file")
presetgroup.add_argument(
    "--config", "-c", metavar="FILE", action=ActionParseFile,
    help="configuration file containing THELI parameters, either file path "
         "or name of a file in the 'presets' folder")

foldergroup = Parser.add_argument_group(
    title="data folders",
    description="data folders, must be all subfolders of the root/main-folder")
# USE os.getcwd() as maindir now
foldergroup.add_argument(
    '--main', '-m', metavar='ROOTFOLDER', default=os.getcwd(),
    help="root/main folder containing all data, defaults to current working "
         "directory")
foldergroup.add_argument(
    '--bias', '-b', metavar="DIR",
    help="bias frames")
foldergroup.add_argument(
    '--dark', '-d', metavar="DIR",
    help="dark frames")
foldergroup.add_argument(
    '--flat', '-f', metavar="DIR",
    help="flat fields")
foldergroup.add_argument(
    '--flatoff', '-fo', metavar="DIR",
    help="flat-off fields (NIR)")
foldergroup.add_argument(
    '--science', '-s', metavar="DIR",
    help="target observations")
foldergroup.add_argument(
    '--sky', '-sky', metavar="DIR",
    help="blank sky observations")
foldergroup.add_argument(
    '--standard', '-std', metavar="DIR",
    help="standard field observations")

optargs = Parser.add_argument_group(title="optional arguments")
optargs.add_argument(
    "--title", "-t", default="auto",
    help="manual title of the current project")
optargs.add_argument(
    "--reduce-sky", action="store_true",
    help="fully reduce sky observation")
optargs.add_argument(
    "--redo", action="store_true",
    help="redo the task, if possible")
optargs.add_argument(
    "--ignore-scamp-segfault", action="store_true",
    help="ignore segmentation faults of scamp")
optargs.add_argument(
    "--threads", metavar="N", type=int, default=9999,
    help="use at most N threads (default: all)")
optargs.add_argument(
    "--verbosity", "-v", type=str, default="normal",
    choices=("quiet", "normal", "full"))

theli_group = Parser.add_argument_group(
    title="THELI parameters",
    description="parameters to control THELI routines (see --help-theli)")
for group, content in parse_parameters.items():
    for arg, param in content.items():
        kwargs = {'help': argparse.SUPPRESS}
        # use special parser that allows empty string in some cases
        if param["type"] in (int, float) and "defa" in param:
            if param["defa"] == '':
                kwargs['type'] = TypeNumberEmpty(param["type"])
            # set default if given
            else:
                kwargs['default'] = param["defa"]
        else:
            kwargs['type'] = param["type"]
            # add choices if given
            if "choi" in param:
                kwargs['choices'] = param["choi"]
            # set default if given
            if "defa" in param:
                kwargs['default'] = param["defa"]
        theli_group.add_argument(arg, **kwargs)

helpgroup = Parser.add_argument_group(title="help")
helpgroup.add_argument(
    "--help", action="help",
    help="show this help message and exit")
helpgroup.add_argument(
    "--help-jobs", metavar='jobkey', action=ActionHelpJob,
    help="list of possible parameters for JOBLIST, "
         "list THELI parameters belonging to a job with [jobkey]")
helpgroup.add_argument(
    "--help-parameters", metavar='pattern', action=ActionHelpTheli,
    help="list of THELI reduction parameters in groups, "
         "can be filtered with optional [pattern]")
helpgroup.add_argument(
    '--version', action=ActionVersion,
    help="show program and software version numbers and exit")
