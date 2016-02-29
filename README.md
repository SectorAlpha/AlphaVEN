# AlphaVEN

Alpha Video ENcoder (AlphaVEN) is a freely availble video editing tool used by the team at Sector Alpha

## Features

For now, development is underway for a command line tool, to feature many commonly used video editing methods including
   - appending videos.
   - splitting videos.
   - incorporating fade in and fadeout transitions.

The syntax is to be as concise as possible - the aim is to be easier to use than raw ffmpeg, after all.

## Usage
To run AlphaVEN, execute `python multimake_yt [OPTIONS] /file/`
/file/ is a file containing formatted instructions, like this:
`Example Title 01 - Test
testvid1,no,no,no,no
testvid2,00:00:05,00:00:07,fi,fo
;
Example Title 02 - Trials
testvid2,no,no,no,no
testvid1,no,no,no,no
testvid2,no,00:00:03,no,no
;

#This line should be ignored`

The file is divided into sections by semicolons. Each section specifies a single video to be created. 
The first line of each section is the name of the output file that will be created
The remaining lines specify sections to cut from a series of input videos. These consist of comma-separated lists:
1. The input file name
2. The time to start from in that video (no = start of video)
3. The time to finish at in that video (no = end of video)
4. Whether this segment should fade in (no or fi)
5. Whether this segment should fade out (no or fo)

*OPTIONS:*


## Dependencies
  - FFMPEG https://www.ffmpeg.org/
  - MMCAT

## TODO
Much more work to do on this, but this is a start of sorts:
  - alter the duration of fading in and fading out.
  - incorporate whether a merge should occur or not (maybe you just want to extract lots of videos from a single source video)

~Cosmo
~Dirdle
