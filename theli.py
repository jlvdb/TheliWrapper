#!/usr/bin/env python3
from system.reduction import Reduction
from commandline.parser import Parser, read_theli_parameter_file


def main():
    args, joblist, theli_args = Parser.parse_theli_args()

    # create a file with current parameters
    if args.config_save is not None:
        read_theli_parameter_file(args)
    # run the reduction pipeline
    else:
        project = Reduction(
            args.inst, args.main, title=args.title,
            biasdir=args.bias, darkdir=args.dark, flatdir=args.flat,
            flatoffdir=args.flatoff, sciencedir=args.science, skydir=args.sky,
            stddir=args.standard, reduce_skydir=args.reduce_sky,
            ncpus=args.threads, verbosity=args.verbosity,
            parseparams=theli_args, logdisplay=args.log_display,
            check_filters=args.disable_filter_check,
            ignore_weight_timestamp=args.ignore_weight_timestamp)
        for job in joblist:
            # read parameters for Reduction - classmethods
            jobargs = [getattr(args, param) for param in job["para"]]
            # execute job
            getattr(project, job["func"])(*jobargs)


if __name__ == '__main__':
    main()
