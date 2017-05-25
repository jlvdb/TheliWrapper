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

from system.version import __version_theli__, __version_gui__, __version__
from .commandlist import *  # command line parameter data base


# This is supposed to test if the terminal supports ANSI escape sequences.
# If not define fall back function
try:
    # this might not cover all cases
    assert((sys.platform != 'Pocket PC' and
           (sys.platform != 'win32' or 'ANSICON' in os.environ)) or
           not hasattr(sys.stdout, 'isatty') and sys.stdout.isatty())

    def highlight_text(string):
        """Format the input 'string' using ANSI-escape sequences bold red"""
        return "\033[1;31;0m" + string + "\033[0;0;0m"

except AssertionError:
    def highlight_text(string):
        """Return input string if ANSI escape sequences are not supported"""
        return string


class ActionParseFile(argparse.Action):
    """Read a parameter file with optinal arguments and parse it to the
    parameter name space. If the file (-path) does not exist, look into the
    ../preset folder

    Arguments:
        arguments are parsed by argparse
    """

    def __init__(self, option_strings, dest, **kwargs):
        super(ActionParseFile, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, configfile, option_string=None):
        # if configfile does not exist, look into presets folder
        if not os.path.exists(configfile):
            base_folder = os.path.split(
                os.path.dirname(os.path.realpath(__file__)))[0]
            configfile = os.path.join(base_folder, "presets", configfile)
        try:
            with open(configfile) as conf:
                content = conf.readlines()
        except FileNotFoundError:
            raise parser.error("parameter file not found: %s" % configfile)
        except IOError:
            raise parser.error(
                "cannot read from parameter file: %s" % configfile)
        # copy the values positional command line parameters
        arguments = [namespace.jobs, namespace.inst]
        # convert file content to command line arguments and parse them
        for line in content:
            line = line.strip()
            # allow comment lines and prepend "--" to lines
            if line.startswith("#") or line == "":
                continue
            if not line.startswith("--"):
                line = "--" + line
            line = line.split()
            arguments.extend(line)
        new_args = parser.parse_args(arguments)
        # write the new arguments to the parameter name space
        for arg in vars(new_args):
            # make sure that folders are not parsed in configureation file
            if arg not in ("main", "bias", "dark", "flat", "flatoff",
                           "science", "sky", "standard"):
                setattr(namespace, arg, getattr(new_args, arg))
            elif arg is None:
                parser.error(
                    "parsing data folders in configuration file is not " +
                    "allowed")


class ActionHelpJob(argparse.Action):
    """Print job help on screen, if --help-jobs is used and exit. Displays the
    job abbreviations for use with JOBLIST, short description and help text.
    If a job abbriviation is given as optional parameter, list the THELI
    parameters that influence this job.

    Arguments:
        arguments are parsed by argparse
    """

    def __init__(self, option_strings, dest, nargs='?', **kwargs):
        super(ActionHelpJob, self).__init__(
            option_strings, dest, nargs, **kwargs)
        # determine maximum possible text display width, limit it to 120
        self.width = min(120, shutil.get_terminal_size((60, 24))[0])

    def __call__(self, parser, namespace, jobabbr, option_string=None):
        # generate help text
        print(Parser.format_usage())
        help_pad = 8  # indent of the help text
        if jobabbr is None:
            infostr = ("List of job abbreviations. Assemble those you need in "
                       "THIS order to create the JOBLIST:")
            print(textwrap.fill(infostr, width=self.width) + "\n")
            print("job abbreviations:")
            # list the jobs in the correct order with their help texts
            for arg in parse_actions_ordered:
                action = parse_actions[arg]
                # use wordwrap to format text and join lines with indentation
                helpstr = [action["name"] + ":"]
                helpstr.extend(textwrap.wrap(
                    action["help"], width=(self.width - help_pad)))
                helpstr = ("\n" + help_pad * " ").join(helpstr)
                # print abbreviation, short description, help text (new line)
                print("{:{pad}}{:}".format(
                    "  %s  " % arg, helpstr, pad=help_pad))
            print()
        else:  # display THELI parameters that act on the job 'jobabbr'
            infostr = "THELI parameters that influence the " + \
                "job %s:" % highlight_text(jobabbr)
            print(textwrap.fill(infostr, width=self.width) + "\n")
            # find all THELI parameters belonging to job
            thelihelp = ActionHelpTheli(option_string, "dummy_dest")
            thelihelp.print_help(jobabbr, match_jobs_only=True)
        print(Parser.epilog)
        sys.exit(0)


class ActionHelpTheli(argparse.Action):
    """Print job help on screen, if --help-parameters is used. Displays the
    available THELI parameters, the parameter type and choices and help text.
    If a search string is given, list the parameters that contain this string
    either in the name or in the help text.

    Arguments:
        arguments are parsed by argparse
    """

    def __init__(self, option_strings, dest, nargs='?', **kwargs):
        super(ActionHelpTheli, self).__init__(
            option_strings, dest, nargs, **kwargs)
        # determine maximum possible text display width, limit it to 120
        self.width = min(120, shutil.get_terminal_size((60, 24))[0])
        # scaling padding/indent of the help text, limited to 36
        self.help_pad = min(36, int(self.width * 0.4))

    def highlight_pattern(self, string, pattern, h_all=False):
        """Highlightes first occurence of the search pattern in string or full
        string. Reterns input string if pattern is None or not in string.

        Arguments:
            string [string]:
                string in which the first occurence of 'pattern' is highlighted
            pattern [string]:
                pattern to search in 'string'
            h_all [bool]:
                weather the whole string is highlighted or just the pattern
        Returns:
            string [string]:
                'string' with 'pattern' highlighted with ANSI-escape sequences
        """
        if pattern is None:
            return string
        try:
            # convert string and pattern to lower case to be case insensitive
            idx = string.lower().index(pattern.lower())
            # exits here, if pattern not in string
            if h_all:  # colorize full string
                return highlight_text(string)
            else:  # colorize pattern only
                head = string[:idx]
                midd = string[idx:idx + len(pattern)]
                tail = string[idx + len(pattern):]
                return head + highlight_text(midd) + tail
        except ValueError:
            return string

    def format_argument(self, arg, param):
        """Formats the help text for a THELI argument (arg) from an entry in
        parse_parameters (param). Line breaks and indentation are formatted
        according to terminal size.

        Arguments:
            arg [string]:
                THELI command line argument (e.g. "--ref-cat")
            param [dict]:
                specifies the properties of command line argument 'arg' like
                choices, default, meta variable or help text
        Returns:
            help [string]:
                formatted help text
        """
        # indent argument by 2
        string = "  %s " % arg
        # if argument has choices
        if "choi" in param:
            # Use textwrap to fit choices to window, goal: comma separated list
            # of choices, wrapped in {}, note: textwrap wraps on white spaces.
            # replace white spaces in choices by "´"
            choicestr = " ".join([c.replace(" ", "´") for c in param["choi"]])
            choicestr = "{%s}" % choicestr
            # use textwrap to fit first line (length reduced by arg. string)
            # wrap remaining lines on full terminal width
            lines = textwrap.wrap(
                choicestr, width=(self.width - len(string) - 1))
            rest = textwrap.wrap(
                " ".join(lines[1:]), width=(self.width - 1))
            # construct final string with new line separation
            choicestr = lines[0]
            if len(rest) > 0:
                choicestr += ",\n" + ",\n".join(rest)
            # replace white spaces back to commas, restore white spaces
            choicestr = choicestr.replace(" ", ",").replace("´", " ")
            string += choicestr + "  "
        # if argument does not have choices add information about argument type
        else:
            if "meta" in param:  # meta argument type, if type is str
                string += param["meta"] + "  "
            elif param["type"] == str:
                string += "STR  "
            elif param["type"] == int:
                string += "INT  "
            elif param["type"] == float:
                string += "FLOAT  "
        # add trailing white spaces to pad the help string, begin in new line
        # if string is too wider than indentation
        string = "{:{pad}}".format(string, pad=self.help_pad)
        if len(string) > self.help_pad:
            string += "\n" + " " * self.help_pad
        # wrap long lines and keep indentation
        helpstr = ("\n" + self.help_pad * " ").join(
            textwrap.wrap(param["help"], width=(self.width - self.help_pad)))
        return string + helpstr

    def print_help(self, pattern, match_jobs_only=False):
        """Generates the help text and prints it to stdout. Filter the results,
        if --help-parameters is given with a filter pattern.

        Arguments:
            pattern [string]:
                optional pattern to filter the displayed entries of the help
                (default: None)
            match_jobs_only [bool]:
                applies search pattern to job abbreviation instead of argument
                name and help text
        Returns:
            None
        """
        helpdict = copy(parse_parameters)
        # remove entries from helpdict, which do not contain the pattern either
        # argument name or help text
        # if the group name itself matches, keep the whole group
        # if match_jobs_only is True, filter on job abbreviations instead
        # perform case insensitive matching by converting to lower case
        lpattern = pattern.lower()
        if pattern is not None:
            for group in parse_parameters:
                # keep whole group, if it machtes the pattern
                if lpattern in group.lower() and not match_jobs_only:
                    continue
                # collect arguments that match pattern
                filtered_args = {}
                if match_jobs_only:
                    for arg, param in parse_parameters[group].items():
                        if "task" not in param:
                            continue
                        # if any task matches, keep argument
                        if any(lpattern in task.lower()
                               for task in param["task"]):
                            filtered_args[arg] = param
                else:
                    for arg, param in parse_parameters[group].items():
                        # if argument name or help text match, keep argument
                        if lpattern in arg.lower() or \
                                lpattern in param["help"].lower():
                            filtered_args[arg] = param
                # if group contains no matching entry, remove it completely,
                # otherwise keep only selection
                if len(filtered_args) == 0:
                    helpdict.pop(group)
                else:
                    helpdict[group] = filtered_args
        # print helpdict sorted alphabetically by group name
        for group in sorted(helpdict.keys()):
            print(self.highlight_pattern(group + ":", pattern, h_all=True))
            # sort arguments by 'sort' keyword
            sorting = [(val["sort"], arg)
                       for arg, val in helpdict[group].items()]
            for pos, arg in sorted(sorting, key=lambda x: x[0]):
                helpstr = self.format_argument(arg, helpdict[group][arg])
                helpstr = self.highlight_pattern(helpstr, pattern)
                print(helpstr)
            print()

    def __call__(self, parser, namespace, pattern, option_string=None):
        """Print the THELI parameter help and exit.
        """
        print(Parser.format_usage())
        infostr = "Grouped list of additional THELI parameters"
        if pattern is not None:
            infostr += " (containing '%s')" % highlight_text(pattern)
        print(textwrap.fill(infostr, width=self.width) + ":\n")
        # generate help entries
        self.print_help(pattern)
        print(Parser.epilog)
        sys.exit(0)


class ActionVersion(argparse.Action):
    """Print version of the THELI installation, the GUI scripts and the
    command line wrapper and exit.

    Arguments:
        arguments are parsed by argparse
    """

    def __init__(self, option_strings, dest, nargs=0, **kwargs):
        super(ActionVersion, self).__init__(
            option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        pad = 17
        versionstr = "{:{pad}}{:}\n".format(
            "THELI:", __version_theli__, pad=pad)
        versionstr += "{:{pad}}{:}\n".format(
            "GUI scripts:", __version_gui__, pad=pad)
        versionstr += "-" * 25 + "\n"
        versionstr += "{:{pad}}{:}".format(
            os.path.basename(__file__), __version__, pad=pad)
        print(versionstr)
        sys.exit(0)


def TypeNumberEmpty(type):
    """Test input value for being 'type', but also accept an empty string to
    represent unset parameters (corresponding to emtpy GUI line edits).

    Arguments:
        type [type]:
            specifies the type (int, float, ...) the input argument has to obey
    Returns:
        type_text [function]:
            function that takes 'value' as argument and tests, if it is either
            an empty string or of type 'type'
    """
    def type_test(value):
        if value == '':
            return value
        else:
            strtype = "float" if type == float else "int"
            try:
                value = type(value)
            except ValueError:
                raise argparse.ArgumentTypeError(
                    "invalid %s value: '%s'" % (strtype, value))
    return type_test  # closure being of fixed type


class TheliParser(argparse.ArgumentParser):
    """Argument parser with custom parsing method that handles the argument
    conversion. Maps choices to internal values, creates the list of jobs to
    execute and a valid THELI parameter dictionary.
    """

    def parse_theli_args(self):
        """Extension of the default argparse.ArgumentParser.parse_args()
        """
        # invoke default argument parser
        parsedargs = self.parse_args()
        # convert choices to internal parameter values
        for group, content in parse_parameters.items():
            for argstr, param in content.items():
                # convert to name in argparser namespace
                arg = argstr[2:].replace("-", "_")
                value = getattr(parsedargs, arg)  # read value
                # ignore unset arguments
                if value is None:
                    continue
                # apply mapping, assume that "choices" exist and the arrays
                # have equal shape
                if "maps" in param:
                    idx = param["choi"].index(value)
                    translated = param["maps"][idx]
                    setattr(parsedargs, arg, translated)
        # split the joblist string into a list and collect the job list data
        jobstring = parsedargs.jobs
        joblist = [jobstring[i:i + 2] for i in range(0, len(jobstring), 2)]
        for i, job in enumerate(joblist):
            # check if they are valid
            if job not in parse_actions:
                raise parser.error(
                    "invalid job descriptor '%s', " % job +
                    "for help use --help-jobs")
            # replace the job key with the attributes from parse_actions
            joblist[i] = parse_actions[job]
        # convert arguments to THELI parameter dict (see Parameters class)
        parameter_dict = {}
        for group, content in parse_parameters.items():
            # take all parameters except those belonging to GUI widgets
            all_params = [argstr[2:].replace("-", "_")
                          for argstr, param in content.items()
                          if "name" in param]
            for param in parsedargs.__dict__:
                value = getattr(parsedargs, param)
                if param in all_params and value is not None:
                    # convert to command line string
                    argstr = "--" + param.replace("_", "-")
                    # if parameter is in current group add it to parameter_dict
                    # this is not very efficient but works
                    try:
                        key = content[argstr]["name"]
                        parameter_dict[key] = value
                    except KeyError:
                        pass  # in different group
        return parsedargs, joblist, parameter_dict


# Actual parser, arguments are grouped, THELI parameter help is supressed

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
    'jobs', metavar='JOBLIST',
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
foldergroup.add_argument(
    '--main', '-m', metavar='ROOTDIR', default=os.getcwd(),
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

# add the THELI parameters
theli_group = Parser.add_argument_group(
    title="THELI parameters",
    description="parameters to control THELI routines (see --help-theli)")
for group, content in parse_parameters.items():
    for arg, param in content.items():
        # determine arguments for .add_argument based on parse_parameters data
        kwargs = {'help': argparse.SUPPRESS}
        # use special type test that allows empty string if default is ''
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
