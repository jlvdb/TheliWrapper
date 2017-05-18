# load the THELI base reduction class
from theli_base import (__version__, __version_theli__, __version_gui__,
                        ascii_styled,
                        Reduction)
from theli_argparser import Parser

# args, theli_args, maindir = Parser.parse_theli_args()
# USE os.getcwd() as maindir now
args, theli_args = Parser.parse_theli_args()

project = Reduction(
    args.inst, args.main, title=args.title,
    biasdir=args.bias, darkdir=args.dark, flatdir=args.flat,
    flatoffdir=args.flatoff, sciencedir=args.science, skydir=args.sky,
    stddir=args.standard, reduce_skydir=args.reduce_sky,
    ncpus=args.threads, verbosity=args.verbosity, parseparams=theli_args)
for job in args.jobs:
    # read parameters for Reduction - classmethods
    jobargs = [getattr(args, param) for param in job["para"]]
    # execute job
    getattr(project, job["func"])(*jobargs)
