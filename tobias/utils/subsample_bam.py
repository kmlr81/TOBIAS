import os
import sys
import multiprocessing as mp
from datetime import datetime
import subprocess
import argparse

from tobias.utils.utilities import *

#-------------------------------------------------------------------#
def run_commandline(command):

	print("{0} RUNNING: \"{1}\"".format(datetime.now(), command))
	print(command.split())
	p = subprocess.call(command.split())

	return(1)


#-------------------------------------------------------------------#
def add_subsample_arguments(parser):

	parser.formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=40, width=100)
	description = ""
	parser.description = format_help_description("SubsampleBam", description)

	parser._action_groups.pop()	#pop -h

	#Required arguments
	args = parser.add_argument_group('Input arguments')
	args.add_argument('--bam', metavar="", help="Path to .bam-file")
	args.add_argument('--no_rand', metavar="", type=int, help="Number of randomizations (per step)", default=3)
	args.add_argument('--start', metavar="", type=int, help="Start of percent subsample (default: 0)", default=0)
	args.add_argument('--end', metavar="", type=int, help="End of percent subsample (default: 100)", default=100)
	args.add_argument('--step', metavar="", type=int, help="Step between --start and --end (default: 5)", default=5)
	args.add_argument('--cores', metavar="", type=int, help="Cores for multiprocessing (default: 1)", default=1)
	args.add_argument('--outdir', metavar="", help="Output directory (default: current working directory)", default=".")
	args.add_argument('--prefix', metavar="", help="Prefix for output files (default: prefix of .bam)")

	return(parser)

#-------------------------------------------------------------------#
def run_subsampling(args):

	check_required(args, ["bam"])

	args.prefix = os.path.splitext(os.path.basename(args.bam))[0] if args.prefix == None else args.prefix
	args.outdir = os.path.abspath(args.outdir) if args.outdir != None else os.path.abspath(os.getcwd())

	#---------------------------------------------------#
	stime = datetime.now()
	print("-"*70)
	print("------- Started bam subsampling ({0}) -------".format(stime))
	print("-"*70 + "\n")

	#### Getting ready for running 
	cmd_calls = []
	for frac in range(args.start,args.end,args.step):
		for rand in range(1,args.no_rand+1):
			outfile = os.path.join(args.outdir, args.prefix + "_{0}_r{1}.bam".format(frac, rand))
			call = "samtools view -s {0} -bh -o {1} {2}".format((frac)/float(100)+rand, outfile, args.bam)
			cmd_calls.append(call)


	#### Run tasks ###
	all_tasks = len(cmd_calls)
	complete_tasks = 0

	if args.cores > 1:

		prev_complete_tasks = 0

		#Send all jobs to pool
		pool = mp.Pool(processes=args.cores)
		task_list = [pool.apply_async(run_commandline, cmd) for cmd in cmd_calls]
		pool.close()

		#check progress
		while complete_tasks != all_tasks:
			complete_tasks = sum([task.ready() for task in task_list])
			if complete_tasks != prev_complete_tasks:
				print(complete_tasks / float(all_tasks) * 100.0)
				prev_complete_tasks = complete_tasks

		pool.join()

	else:
		for command in cmd_calls:
			res = run_commandline(command)
			complete_tasks += 1
			print(complete_tasks / float(all_tasks) * 100.0)

	print("Completed bam subsampling! Bamfiles are found at:\n{0}".format(args.outdir))


#--------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser = add_subsample_arguments(parser)
	args = parser.parse_args()

	if len(sys.argv[1:]) == 0:
		parser.print_help()
		sys.exit()

	run_subsampling(args)
