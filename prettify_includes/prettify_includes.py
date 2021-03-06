#!/usr/bin/python3

import sys
import re
import argparse

class PathComparator:
	def __init__(self,x):
		self.filename = x[-1]
		self.paths = x[:-1]

	def __lt__(self,other):
		if len(self.paths) == 0 and len(other.paths) == 0:
			return self.filename < other.filename

		if len(self.paths) == 0:
			return True

		if len(other.paths) == 0:
			return False

		if self.paths[0] == other.paths[0]:
			return PathComparator(self.paths[1:] + [self.filename]) < PathComparator(other.paths[1:] + [other.filename])

		return self.paths[0] < other.paths[0]

# Helper functions
def remove_duplicates_from_list(mylist,key):
	"""
	Remove duplicate entries (based on the functor "key") from the
	list *IN PLACE*
	"""
	last = mylist[-1]
	for i in range(len(mylist)-2, -1, -1):
		if last == key(mylist[i]):
			del mylist[i]
		else:
			last = key(mylist[i])
	return mylist

# The main function
def modify_file(filename,reserved_prefixes,external_begin,external_end,debug):
	# This one looks strange, but it's easily explained. At some point later in
	# the code, we _only_ add a #include statement if it's not the external
	# begin/end include.
	#
	# However, when we test this, we have the "incoming" path in (prefix,rest)
	# form. The rest begins with '/'. So we transform it to this form.
	external_prefix = external_begin.split('/')[0]
	external_begin_path = "/"+("/".join(external_begin.split('/')[1:]))
	external_end_path = "/"+("/".join(external_end.split('/')[1:]))

	# 1. Read ALL the lines into the lines array
	lines = []
	with open(filename,'r') as f:
		# readlines idiotically leaves in the \n at the end. rstrip removes those
		lines = [l.rstrip() for l in f.readlines()]

	begin_of_includes = None
	end_of_includes = None

	# Helper struct, holds all relevant information about an include line
	class IncludeLine:
		def __init__(
			self,
			path,
			prefix,
			rest):

			self.prefix = prefix
			self.path = path
			self.rest = rest

		def __repr__(
			self):

			return self.path.__repr__()

	# We store the original #include lines to compare it with the modified lines
	# later (and maybe not update the file)
	original_raw_include_lines = []

	# These are the extracted include lines
	include_lines = []

	# Precompile regex (will be faster!)
	compiled_include_regex = re.compile(r'\s*#include\s+<(([^/]+)(/[^>]*)?)>')

	line_counter = 0
	for line in lines:
		include_search_result = compiled_include_regex.search(line)

		# Is it an include line?
		if include_search_result != None:
			# Save the original for later
			original_raw_include_lines.append(
				line)

			# We've found the first #include in the file!
			if begin_of_includes == None:
				begin_of_includes = line_counter
			else:
				# We found the start _and_ the end and then another #include line!
				if end_of_includes != None:
					sys.stderr.write('Error: The file {} has non-continuous includes.\nBegin of includes was line {}, end of includes was line {}.\nLine {}:\n\n{}\n\n...re-enters an include chain. Cannot continue...\n'.format(filename,begin_of_includes,end_of_includes,line_counter,line))
					return False

			prefix = include_search_result.group(2)
			rest = include_search_result.group(3)
			path = include_search_result.group(1)

			# This way we handle the special case where we have no prefix (e.g. <algorithm>).
			if rest == None:
				rest = prefix
				prefix = None

			# Here we "hack" a little and filter the includes. We don't want external_begin/external_end in the list.
			if prefix != external_prefix or (rest != external_begin_path and rest != external_end_path):
				include_lines.append(
					IncludeLine(
						path = path,
						prefix = prefix,
						rest = rest))
		else:
			# A non-#include-line. If we've found the start, then the only allowed
			# lines are blank lines
			if begin_of_includes != None and re.search('^\s*$',line) == None and end_of_includes == None:
				end_of_includes = line_counter

		line_counter += 1

	if debug == True:
		print('Begin of includes: {}, end of includes: {}'.format(begin_of_includes,end_of_includes))

	# There might be files without any <> includes
	if begin_of_includes == None and end_of_includes == None:
		return True

	assert begin_of_includes != None and end_of_includes != None

	groups = {}

	for l in include_lines:
		corrected_prefix = l.prefix if l.prefix != None else ''
		if not corrected_prefix in groups:
			groups[corrected_prefix] = [l]
		else:
			groups[corrected_prefix].append(
				l)

	for name,includes in groups.items():
		includes.sort(
			key = lambda x : PathComparator(x.path.split('/')))

		remove_duplicates_from_list(
			includes,
			lambda x : x.path)

	new_includes = []

	for prefix in reserved_prefixes:
		if prefix not in groups:
			continue
		new_includes += list(
				map(
					lambda x : '#include <{}>'.format(x.path),
					groups[prefix]))

	rest_groups = groups.keys() - set(reserved_prefixes) - {''}

	if len(rest_groups) != 0 or '' in groups:
		new_includes.append('#include <'+external_begin+'>')
		rest_groups = list(rest_groups)
		rest_groups.sort()
		for group in rest_groups:
			new_includes += list(
					map(
						lambda x : '#include <{}>'.format(x.path),
						groups[group]))

		if '' in groups:
			new_includes += list(
					map(
						lambda x : '#include <{}>'.format(x.path),
						groups['']))

		new_includes.append('#include <'+external_end+'>')

	modifications_present = new_includes != original_raw_include_lines
	new_includes.append('\n')
	lines[begin_of_includes:end_of_includes] = new_includes

	if debug == True:
		if modifications_present == False:
			print('No modification to {}'.format(filename))
		else:
			# Remove old includes and add the new ones
			print('Modification needed: ')
			for l in lines:
				sys.stdout.write(
					l+'\n')

	else:
		if modifications_present == True:
			with open(filename,'w') as f:
				f.write(("\n".join(lines))+'\n')

# Begin of program
parser = argparse.ArgumentParser(
	description = 'Clean up blocks of #include statements')

parser.add_argument(
	'--reserved-prefix',
	# This creates a list instead of a single value (e.g. --reserved-prefix a --reserved-prefix b => [a,b]
	action = 'append')

parser.add_argument(
	'--external-begin',
	default = 'fcppt/config/external_begin.hpp')

parser.add_argument(
	'--external-end',
	default = 'fcppt/config/external_end.hpp')

parser.add_argument(
	'--debug',
	action='store_true')

parser.add_argument(
	'files',
	nargs = '+')

parser_result = parser.parse_args(
	args = sys.argv[1:])

reserved_prefixes = parser_result.reserved_prefix if parser_result.reserved_prefix != None else []

erroneous_files = []

for filename in parser_result.files:
	if parser_result.debug == True:
		print('Looking at file {}'.format(filename))

	if modify_file(filename,reserved_prefixes,parser_result.external_begin,parser_result.external_end,parser_result.debug) == False:
		erroneous_files.append(
			filename)

print('The following files encountered errors:')
for f in erroneous_files:
	print(f)
