# AlphaVEN

Alpha Video ENcoder (AlphaVEN) is a freely availble video editing tool used by the team at Sector Alpha

## Features

For now, development is underway for a command line tool, to feature many commonly used video editing methods including
   - appending videos.
   - splitting videos.
   - incorporating fade in and fadeout transitions.

The syntax is to be as concise as possible - the aim is to be easier to use than raw ffmpeg, after all.

## Usage
To run AlphaVEN, run `python alphaven [OPTIONS] [file] `

*file* is a file containing formatted instructions. For an example, see exampleinput.ven.

The file is divided into sections by double line breaks. Each section except the optional first section specifies a single video to be created. 
The first line of each section is the name of the output file that will be created
The remaining lines specify sections to cut from a series of input videos. These consist of comma-separated lists containing the input file name and a series of timestamps indicating which portions of the input file to include, and indicators to use fade-ins or fade-outs between those lines.
  
The first section may be used to define options. Starting a line with "map:" lets you assign paths to short names for convenience. Starting a line with "set:" lets you set certain universal settings. 

**OPTIONS:**
-h, --help: 	Prints help
-v, --verbose: 	Prints additional information during execution
-s, --settings: tell alphaVEN to treat the first paragraph as settings

## Dependencies
  - FFMPEG https://www.ffmpeg.org/

## TODO
Much more work to do on this, but this is a start of sorts:
  - add ability to confidently combine file formats and differing resolutions
  - write more comprehensive README and instructions
## Dependencies
  - FFMPEG https://www.ffmpeg.org/

## TODO
Much more work to do on this, but this is a start of sorts:
  - ensure proper results for videos of differing formats and resolutions

~Cosmo
~Dirdle