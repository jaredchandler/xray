# xray

xray: a tool to help you reason about unix/linux file permissions.

This is alpha software produced in a research setting. 
This was mainly intended as a proof of concept and has been debugged to about that level.
Many of the edges on this code are rough. I hope you will find this useful.

If you have questions, please contact me at jared.chandler@tufts.edu. I will do my best to help you out.

## Manifest

	xray.py :		The main program
	xray_cmd_parser.py :	Parses commands for the REPL
	settings.py :		Shares command line arguments between modules
	Agents.py :		Implements agent classes
	DirTree.py :		Converts input text format into data structure and performs symbolic execution

--------------------------------

## Requirements

	Python 2.7 

	*   It may run on python 3.4  
	**  It doesn't run under python 3.7 yet
	*** I've run this with pypy for when I needed better performance. Refactoring is for the next version

--------------------------------

## Invoke 

	python2.7 xray.py --file demo/demo.txt --groups demo/dmpcgroups.txt

	The file argument is an ascii file containing information from your filesystem.
	It can be created by running the command 'find /dirname -ls' where the directory name is something directly off the file system root and piping the output into an ascii file. 

	The groups argument is a listing of user names and groups they belong to, one username per line in the format:
	username : group1 group2 group3


--------------------------------

Welcome Banner


	===================================================================
	 __   _______       __     __
	 \ \ / /  __ \     /\ \   / /   File Permission Query Environment 
	  \ V /| |__) |   /  \ \_/ /   
	   > < |  _  /   / /\ \   /     File:   demo/demo.txt
	  / . \| | \ \  / ____ \| |     Groups: demo/dmpcgroups.txt
	 /_/ \_\_|  \_\/_/    \_\_|     Root:   /dmpc 

	===================================================================

	Root is the top level directory from which permissions are inherited.

--------------------------------

## The Prompt DEPTH

	4 > 

	The number displayed is the aggregation depth for results from a query.
	4 means that anything deeper than 4 directories from the root directory will
	be summarized. 

	Depth can be set using the depth command:

	4 > depth 5
	Depth is 5
	5 > depth 6
	Depth is 6

--------------------------------

## The Promp XRAY MODE

	4 >>> 

	When you see >>> that indicates that xray mode is on. 
	When xray mode is on, the calculated contstraint information will be displayed 
	under each location returned by the query.

	xray mode can be set using the xray on | off command

	4 > xray on
	XRAY is ON
	4 >>> xray off
	XRAY is OFF
	4 > 


--------------------------------

## More Help

	type 'help' to see a list of commands
	type 'help cmdname' to get more information about each command


--------------------------------

## Example Commands

	# What can everyone find? ( Shows both true and false )
	
	everyone can discover in /dmpc/.*	

	# What can everyone find? (Shows only the true cases)

	example everyone can discover in /dmpc/.*

	# Can use regex in path to limit to only PDFS

	everyone can discover in .*pdf

	# Can use group membership by 'users in groupname' form

	users in hr can edit in /dmpc/hr/.*

	# Can use explicitly named users

	michael can edit in /dmpc/.*

	# Can use counterexample to limit it query to only condition violations

	counterexample michael can discover in /dmpc/.*

	# Dual of the previous query

	example michael cannot discover in /dmpc/.*


--------------------------------

## Semantic Permissions Supported
	
	# Can you find a location by enumerating the files in each parent directory

	discover

	# Can you get to a location if you already know the exact path

	traverse

	# Can you edit at a location if you already know the exact path

	edit

	# Can you execute at a location if you already know the exact path

	execute




