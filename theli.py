#!/usr/bin/env python3
from system.reduction import Reduction
from commandline.parser import Parser


args, joblist, theli_args = Parser.parse_theli_args()

project = Reduction(
    args.inst, args.main, title=args.title,
    biasdir=args.bias, darkdir=args.dark, flatdir=args.flat,
    flatoffdir=args.flatoff, sciencedir=args.science, skydir=args.sky,
    stddir=args.standard, reduce_skydir=args.reduce_sky,
    ncpus=args.threads, verbosity=args.verbosity, parseparams=theli_args)

for job in joblist:
    # read parameters for Reduction - classmethods
    jobargs = [getattr(args, param) for param in job["para"]]
    # execute job
    getattr(project, job["func"])(*jobargs)
