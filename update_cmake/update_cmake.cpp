#include <fcppt/config/external_begin.hpp>
#include <boost/filesystem/convenience.hpp>
#include <boost/filesystem/operations.hpp>
#include <boost/filesystem/path.hpp>
#include <boost/regex.hpp>
#include <algorithm>
#include <exception>
#include <fstream>
#include <iostream>
#include <ostream>
#include <string>
#include <vector>
#include <cstdlib>
#include <fcppt/config/external_end.hpp>

namespace
{

typedef std::vector<
	std::string
> file_vector;

template<
	typename Iterator
>
void
add_files(
	Iterator _iterator,
	boost::regex const &_regex,
	file_vector &_files
)
{
	for(
		;
		_iterator != Iterator();
		++_iterator
	)
	{
		if(
			!boost::filesystem::is_regular_file(
				*_iterator
			)
		)
			continue;

		if(
			!boost::regex_match(
				_iterator->path().filename().string(),
				_regex
			)
		)
			continue;

		_files.push_back(
			_iterator->path().generic_string()
		);
	}
}

}

int
main(
	int argc,
	char **argv
)
try
{
	if(
		argc <= 3
	)
	{
		std::cerr
			<< "Usage: "
			<< argv[0]
			<< " <CMakeFile> <VAR_NAME> <path1> [path2] ...\n"
			<< "In front of every path the additional options -r, -n and -e are accepted.\n"
			<< "-r will search recursively, while -n will not.\n"
			<< "-e will change the regex the filenames have to match.\n"
			<< "The default is -r -e \".*\\..pp\"\n";

		return EXIT_FAILURE;
	}

	std::string const cmake_file(
		argv[1]
	);

	std::ifstream ifs(
		cmake_file.c_str()
	);

	if(
		!ifs.is_open()
	)
	{
		std::cerr
			<< cmake_file
			<< " does not exist.\n";

		return EXIT_FAILURE;
	}

	std::string const out_file(
		cmake_file
		+ ".new"
	);

	std::ofstream ofs(
		out_file.c_str(),
		std::ios_base::binary
	);

	if(
		!ofs.is_open()
	)
	{
		std::cerr
			<< "Cannot open "
			<< out_file
			<< '\n';

		return EXIT_FAILURE;
	}

	file_vector files;

	std::string mode(
		"r"
	);

	boost::regex fileregex(
		".*\\..pp"
	);

	for(
		int arg = 3;
		arg < argc;
		++arg
	)
	{
		std::string const arg_string(
			argv[arg]
		);

		if(
			!arg_string.empty()
			&&
			arg_string[0] == '-'
		)
		{
			if(
				arg_string.size() < 2
			)
			{
				std::cerr
					<< "- must be followed by an option\n";

				return EXIT_FAILURE;
			}

			if(
				arg_string[1]
				== 'n'
				||
				arg_string[1]
				== 'r'
			)
				mode =
					arg_string.substr(
						1u
					);
			else if(
				arg_string[1]
				== 'e'
			)
			{
				++arg;

				if(
					arg == argc
				)
				{
					std::cerr
						<< "-e must be followed by a regex!\n";

					return EXIT_FAILURE;
				}

				fileregex =
					argv[arg];
			}

			continue;
		}

		if(
			mode == "r"
		)
			::add_files(
				boost::filesystem::recursive_directory_iterator(
					arg_string
				),
				fileregex,
				files
			);
		else if(
			mode == "n"
		)
			::add_files(
				boost::filesystem::directory_iterator(
					arg_string
				),
				fileregex,
				files
			);
		else
		{
			std::cerr
				<< "Invalid mode "
				<< mode
				<< '\n';

			return EXIT_FAILURE;
		}
	}

	std::sort(
		files.begin(),
		files.end()
	);

	std::string const search_line(
		std::string(
			"\t"
		)
		+ argv[2]
	);

	std::string line;

	while(
		std::getline(
			ifs,
			line
		)
		&&
		line
		!= search_line
	)
		ofs
			<< line
			<< '\n';

	if(
		line != search_line
	)
	{
		std::cerr
			<< search_line
			<< " not found!\n";

		return EXIT_FAILURE;
	}

	ofs
		<< line
		<< '\n';

	for(
		file_vector::const_iterator it(
			files.begin()
		);
		it != files.end();
		++it
	)
		ofs
			<< '\t'
			<< *it
			<< '\n';

	std::string const search_end(
		")"
	);

	while(
		std::getline(
			ifs,
			line
		)
		&&
		line
		!= search_end
	) ;

	if(
		line != search_end
	)
	{
		std::cerr
			<< search_end
			<< " not found!\n";

		return EXIT_FAILURE;
	}

	ofs
		<< line
		<< '\n';

	while(
		std::getline(
			ifs,
			line
		)
	)
		ofs
			<< line
			<< '\n';

	return EXIT_SUCCESS;
}
catch(
	std::exception const &_error
)
{
	std::cerr
		<< _error.what()
		<< '\n';

	return EXIT_FAILURE;
}
