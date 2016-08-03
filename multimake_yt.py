# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 22:33:25 2016

@author: Oscar
"""

from __future__ import print_function

import make_youtube_video as mkyt
import argparse
import subprocess as sub
import os

def readinstr(filename):
    '''Reads a file to create a series of instructions. '''
    if VERBOSE:
        print("Reading instructions from ", filename)
    with open(filename) as f:
        content = f.read()
        instblks = content.split(';')
        instgrps = []
        for block in instblks:
            inst = processinstruction(block)
            if inst:
                instgrps.append(inst)
    
    if VERBOSE:
        print('\n', "Read the following instructions:")
        for i in instgrps:
            print(i)
    return instgrps

def processinstruction(textblock):
    '''Processes a single block of instructions, i.e. an entire input file
    for make_youtube_video, and returns the relevant details. 
    Returns None if the block is empty of instructions.'''
    lines = textblock.strip().split('\n')
    if VERBOSE:
        print('\n' + "Processing instructions: ")
        for l in lines:
            print(l)
    # The first line is the title (output name) and shouldn't be processed
    title = lines[0].rstrip()
    lines = lines[1:]
    instructions = []
    for l in lines:
        # Skip blank lines
        if l != '' and l[0] != '#':
            comms = l.rstrip().split(',')
            # For some reason, there's (sometimes) a space at the start of
            # vidname which messes things up
            #TODO find out where that's coming from instead of just stripping
            vidname = comms[0].strip()
            
            if VERBOSE:
                print("Getting duration for ", vidname)
            videolen = mkyt.get_video_duration(vidname)
            if comms[1] == "no":
                starttime = 0
            else:
                starttime = mkyt.convert_to_seconds(comms[1])
                
            if comms[2] == "no":
                endtime  = videolen
            else:
                endtime = mkyt.convert_to_seconds(comms[2])
            
            fadein = not (comms[3] == "no")
            if fadein and starttime >= FADETIME:
                starttime = starttime - FADETIME
                
            fadeout = not (comms[4] == "no")
            if fadeout and (endtime <= videolen - FADETIME):
                endtime = endtime + FADETIME
                
            c = (title, vidname, starttime, endtime, fadein, fadeout)
            if VERBOSE:
                print("Information obtained: ", c)
            instructions.append(c)
    if instructions:
        return instructions
    else:
        pass
   
def makevideo(inst):
    '''Creates a single video based on a set of instructions.'''
    # Step 1: process the inputs using mkyt
    title = inst[0][0]
    outputnamer = mkyt.tempfoldernamegen(title + FORMAT)
    for i in inst:
        if VERBOSE:
            print("Executing run_ffmpeg for ", i)
        mkyt.run_ffmpeg(*(i[1:]), outnamegen = outputnamer)#, \
        #dimensions = DIMENS, aspectr = ASPECTR)
    # We now have a series of videos in /temp/ called 1-$title, 2-$title
    # And potentially a number of useless duplicates in /fadetemp/?
    # Never figured out whether they were different or not...
    
    # Step 2: combine the video segments using mmcat
    mmcatalyse(title, TEMPDIR, len(inst), FORMAT)
    pass

def mmcatalyse(title, temp, segments, form):
    '''Calls mmcat to concatenate the videos created previously. Why yes, this
    adds ANOTHER rendering operation...
    title:      output video title
    temp:       temp directory storing files. Use empty string if same dir.
    segments:   number of video segments'''
    #TODO set things up to use a single ffmpeg command for everything
    #it can't be that hard right :^)
    # Also, find a way to input the shell instead of hardcoding bash, 
    # might be handy one day
    cattsk = ["bash", "mmcat"]
    renaming = ' ' in title
    if renaming:
        spacelesstitle = temp + "".join(title.split()) + form   
    # Append each input name to the command string
    for x in range(0, segments):
        titlepath = temp + str(x) + '-' + title + form
        # Move the file to a spaceless name if required
        if renaming:
            spacelesstitlepath = "".join(titlepath.split())
            if VERBOSE:
                print("Moving file from", titlepath, "to", spacelesstitlepath)
            os.rename(titlepath, spacelesstitlepath)        
            cattsk.append(spacelesstitlepath)
        else:
            cattsk.append(titlepath)
    if renaming:        
        cattsk.append(spacelesstitle)
    else:
        cattsk.append(title + form)
        
    if VERBOSE:
        print("Calling", " ".join(cattsk))
    sub.check_call(cattsk, shell=False)
    
    if renaming:        
        os.rename(spacelesstitle, title + form)
    pass

def execute(filename):
    insts = readinstr(filename)
    # insts is a list of lists of tuples of arguments for mkyt.run_ffmpeg()
    # Each sub-list represents a single output video
    # each sub-sub-list (tuple) represents the usage of a single input video
    for i in insts:
        makevideo(i)
    pass

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    
    #Positional argument, requires this
    parser.add_argument("file",help="The file that defines which videos to \
create. For formatting, please see AlphaVEN README.")    
    parser.add_argument("-v","--verbose",help="Display extra information",\
    action="store_true")
    parser.add_argument("-t","--fadetime",help="Length of fades in seconds. \
Default is 1 second.")
    parser.add_argument("-e","--tempdir",help="Temporary directory to store \
files in during program operation.")
    parser.add_argument("-o","--format",help="Format of output file to write")
    parser.add_argument("-d","--dimens",help="Dimensions of video, \
default is 848x480")
    parser.add_argument("-a","--aspect",help="Aspect ratio of video, \
default is 16:9")    

    args = parser.parse_args()    
    
    VERBOSE     = args.verbose    
    FADETIME    = args.fadetime if args.fadetime    else mkyt.fadetime
    TEMPDIR     = args.tempdir  if args.tempdir     else mkyt.tempdir
    DIMENS      = args.dimens   if args.dimens      else "848x480"
    ASPECTR     = args.aspect   if args.aspect      else "16:9"
    # taking the defaults from mkyt like this is definitely unwise
    #TODO need a MUCH better way to organise defaults
    # maybe they should be read from the file?
    
    # Generously allow some leeway in inputting video format
    if args.format:
        if args.format[0] == '.':
            FORMAT = args.format
        else: 
            FORMAT = '.' + args.format
    else:
        FORMAT = ".mkv"

    #Seriously, fix this global variable tarball before it gets any worse
    mkyt.dimensions = DIMENS
    mkyt.aspectr = ASPECTR
    mkyt.VERBOSE = VERBOSE
    
    execute(args.file)
    pass
