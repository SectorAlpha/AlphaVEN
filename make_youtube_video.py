#!/bin/python
#
# Merges a series of videos together. 
# defining a start and end time.. with fade in and out

# Usage:
# 

#   $ bash split_video_for_youtube.sh video.avi
#   video.part1.mkv
#   video.part2.mkv
#
#   $ youtube-upload [OPTIONS] video.part*.mkv
#

# imports
from __future__ import print_function

from time import sleep
import os
import subprocess
import glob
import argparse


######## settings #################
renderer="ffmpeg"

# fade in/out time in seconds
fadetime=1

# fade directory
fadetempdir = "fadetemp/"

# temp directory
tempdir = "temp/"

vcodec = "libx264"

#acodec = "libfdk_aac"
acodec = "libvorbis"

fps = "29"

merge = False

justmerge = False

VERBOSE = False

######## end ###########

# just a note

# video file, start time, end time, fade in, fade out

####################

# function to calculate file length

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    f.close()
    return i + 1

def convert_to_seconds(string, sep = ':'):
    array = string.split(sep)
    total_seconds = \
 (int(array[0]) * 3600) + (int(array[1])) * 60 + int(array[2])
    return total_seconds

def generate_fade_string(temp_name_1, fadein, fadeout):

    # get new video len
    new_vid_len = get_video_duration(temp_name_1)
    new_vid_len = new_vid_len - fadetime

    fade_string = ""
    if fadein and fadeout:
        fade_string = \
  "-vf \"fade=t=in:st=0:d=%s,fade=t=out:st=%s:d=%s\" \
  -af \"afade=t=in:st=0:d=%s,afade=t=out:st=%s:d=%s\"" \
  % (fadetime, new_vid_len, fadetime, fadetime, new_vid_len, fadetime)

    if fadein and (not fadeout):
        fade_string = "-vf \"fade=t=in:st=0:d=%s\" \
  -af \"afade=t=in:st=0:d=%s\"" % (fadetime, fadetime)

    if (not fadein) and fadeout:
        fade_string = "-vf \"fade=t=out:st=%s:d=%s\" \
  -af \"afade=t=out:st=%s:d=%s\"" \
  % (new_vid_len, fadetime, new_vid_len, fadetime)

    return fade_string


def run_ffmpeg(video, startseconds, endseconds, fadein, fadeout, outnamegen):
    # infile, vcodec, size, aspect ratio, audio codec, start time, 
    #end time, fps, fps, output file

    tempnameroot = outnamegen.next()
    
    if VERBOSE:
        print("Input file %s \nStart point %s \nEnd point %s \nFades: "
         %(video, startseconds, endseconds) + fadein*"in" + fadeout*"out")
    
    if not (fadein or fadeout):
        temp_name_1 = tempdir + tempnameroot
    else:
        temp_name_1 = fadetempdir + tempnameroot
        
    render_string = "ffmpeg -i \"%s\" -qscale 0 -q:a 0 -q:v 0 -vcodec %s \
-s %s -aspect %s -acodec %s -ss %s -to %s -map 0 -async %s -r %s -y \"%s\" \
</dev/null" \
% (video, vcodec, dimensions, aspectr, acodec, startseconds, endseconds, \
fps, fps, temp_name_1)      
         #TODO feed all these as arguments instead of mixing args and 
         #global variables
         #Preferably some kind of kwargs setup?

    if VERBOSE:    
        print('Sending "', render_string, '" to ffmpeg.')
    ffmpeg_call(render_string)
    sleep(2)

    if fadein or fadeout:
        # now we just need to add the fade in and fade out
        startseconds = 0
        endseconds = get_video_duration(temp_name_1)
        
        temp_name_2 = tempdir + tempnameroot
        
        fade_string = generate_fade_string(temp_name_1, fadein, fadeout)

        render_string = "ffmpeg -i \"%s\" -qscale 0 -q:a 0 -q:v 0 -vcodec %s \
-acodec %s %s -ss %s -to %s -map 0 -async %s -r %s -y \"%s\" </dev/null" \
% (temp_name_1, vcodec, acodec, fade_string, startseconds, endseconds, fps, \
fps, temp_name_2)
        if VERBOSE:
            print('Sending "', render_string, '" to ffmpeg.')
            
        ffmpeg_call(render_string)
        sleep(2)
    return

def ffmpeg_call(string):
    #TODO catch ffmpeg errors and terminate python execution!
    #IMPORTANT!
    duration, err = subprocess.Popen(\
        string, stdout=subprocess.PIPE, shell=True).communicate()
    return

def get_video_duration(filething):
    #TODO update to use ffprobe instead of this complex mess
    procstr="ffmpeg -i \"%s\" -vframes 1 -f rawvideo -y /dev/null 2>&1" \
    % filething
    if VERBOSE:
        print("Sending", procstr,"to ffmpeg")
        
    
    proc, err = subprocess.Popen(procstr, stdout=subprocess.PIPE, \
 shell=True).communicate()

#    if VERBOSE:
#        print(proc)
 
    duration, err = subprocess.Popen(\
 "echo \"%s\" | grep -m1 \"^[[:space:]]*Duration:\" | cut -d\":\" -f2- \
 | cut -d\",\" -f1 | sed \"s/[:\.]/ /g\"" % proc, \
 stdout=subprocess.PIPE, shell=True).communicate() 
    if VERBOSE:
        print("Duration of video determined to be: ", duration)
    dur_array = duration.split(" ")
 
    total_time = \
 (int(dur_array[1]) * 3600) + (int(dur_array[2])) * 60 + int(dur_array[3])
    return total_time

def tempfoldernamegen(basename):
    i = 0
    while True:
        yield str(i) + '-' + basename 
        i += 1

if __name__ == "__main__":
    # Parse the arguments to determine how to run the code
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-f", "--file",help="A file listing videos to create. \
For the format of this file, please see AlphaVEN README. \
Default file name is instructions.csv")
    
    parser.add_argument("-v", "--verbose",help="Output additional information"\
    , action="store_true")
    parser.add_argument("-o","--output",help="Name of output file, \
default is output.mkv")
    parser.add_argument("-d","--dimens",help="Dimensions of video, \
default is 848x480")
    parser.add_argument("-a","--aspect",help="Aspect ratio of video, \
default is 16:9")    
    
    args = parser.parse_args()
    
    VERBOSE = bool(args.verbose)
    
    # Set variables to defaults if not given as arguments
    # Defaults are the same as before
    # Probably this SHOULD be done by defaults in the arguments of  
    # primary_execute, but ehhh
    filename    = args.file     if args.file    else "instructions.csv"
    outname     = args.output   if args.output  else "output.mkv"
    dimensions  = args.dimens   if args.dimens  else "848x480"
    aspectr     = args.aspect   if args.aspect  else "16:9"
    #TODO remaining arguments...
    
    namegen = tempfoldernamegen(outname)
    # open the file safely
    with open(filename,'r') as f:
        #filelen = file_len(filename)   #?
        if not justmerge:               #?
            for line in f:
                # removes all trailing whitespace and breaks apart
                line = line.rstrip()
                data = line.split(",")
                if VERBOSE:
                    print("Getting information for... ", '\n', data, '\n')
                    
                video = data[0]
                videolen = get_video_duration(video)
    
                if data[1] == "no":
                    startseconds = 0
                else:
                    startseconds = convert_to_seconds(data[1])
                    
                if data[2] == "no":
                    endseconds  = videolen
                else:
                    endseconds = convert_to_seconds(data[2])
        
                #Fading in and out (may) require adjusting times
                fadein = not (data[3] == "no")
                if fadein and startseconds >= fadetime:
                    startseconds = startseconds - fadetime
                    
                fadeout = not (data[4] == "no")
                if fadeout and (endseconds <= videolen - fadetime):
                    endseconds = endseconds + fadetime     
                
                run_ffmpeg(\
                    video,\
                    startseconds, \
                    endseconds, \
                    fadein, \
                    fadeout, \
                    namegen)

    if merge:
        temp_files = glob.glob(tempdir + "*")
        temp_files.sort(key=os.path.getmtime)
        mmcat_string = " ".join(temp_files)
        mmcat_string = mmcat_string + " " + outname
        
#        command_string = "bash mmcat %s </dev/null" % mmcat_string
        command_string = "bash mmcat %s" % mmcat_string
        if VERBOSE:
            print(command_string)
        # finally merge everything together
        duration, err = subprocess.Popen\
  (command_string, stdout=subprocess.PIPE, shell=True).communicate()


#    video_filenames_string="ls -dt -1 $PWD/temp/*.*"
#    video_filenames, err = subprocess.Popen(\
#video_filenames_string, stdout=subprocess.PIPE, shell=True).communicate()
#    print video_filenames
