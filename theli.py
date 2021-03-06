#!/usr/bin/env python3
from system.base import ascii_styled
from system.reduction import Reduction
from commandline.parser import Parser, read_theli_parameter_file


def main():
    args, joblist, theli_args = Parser.parse_theli_args()
    have_no_data_folders = all(
        f is None for f in (
            args.bias, args.dark, args.flat, args.flatoff,
            args.science, args.sky, args.standard))
    # create a file with current parameters
    if args.config_save is not None:
        read_theli_parameter_file(args)
    elif args.jobs == "":
        print(
            ascii_styled("\nERROR: ", "br-") +
            "No jobs specified, there is nothing to do.")
        print("       Use --help or --help-jobs for more information\n")
    elif have_no_data_folders:
        print(
            ascii_styled("\nERROR: ", "br-") +
            "No data folders specified, there is nothing to do.")
        print("       Use --help for more information\n")
    # run the reduction pipeline
    else:
        project = Reduction(
            args.inst, args.main, title=args.title,
            biasdir=args.bias, darkdir=args.dark, flatdir=args.flat,
            flatoffdir=args.flatoff, sciencedir=args.science, skydir=args.sky,
            stddir=args.standard, reduce_skydir=args.reduce_sky,
            ncpus=args.threads, verbosity=args.verbosity,
            parseparams=theli_args, logdisplay=args.log_display,
            check_filters=args.disable_filter_check, redo=args.redo)
        for job in joblist:
            # read parameters for Reduction - classmethods
            jobargs = [getattr(args, param) for param in job["para"]]
            # execute job
            getattr(project, job["func"])(*jobargs)


if __name__ == '__main__':
    main()
