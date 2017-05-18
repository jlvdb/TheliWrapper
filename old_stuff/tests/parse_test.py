#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.split(os.path.dirname(os.path.realpath(__file__)))[0])
import theli


parser = theli.Parser
args = parser.parse_args()


project = theli.Reduction(
    args.inst, args.main, args.science,
    biasdir=args.bias, darkdir=args.dark, flatdir=args.flat,
    flatoffdir=args.flatoff, skydir=args.sky, stddir=args.standard,
    title=args.title, ncpus=args.threads, reduce_skydir=args.reduce_sky,
    verbosity=args.verbosity)
project.params.set(theli.translate_theli_args(args))
