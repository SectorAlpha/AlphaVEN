#!/bin/python
#
# Merges a series of videos together. defining a start and end time.. with fade in and out
#
#   $ bash split_video_for_youtube.sh video.avi
#   video.part1.mkv
#   video.part2.mkv
#
#   $ youtube-upload [OPTIONS] video.part*.mkv
#

# imports
from time import sleep
import os
import subprocess
import re
import glob

######## settings #################
renderer="ffmpeg"

# fade in/out time in seconds
fadetime=1

#output format
out_extension="mkv"

#instruction file
filename="instructions.csv"

#video size
dimensions="848x480"

#aspect ratio
aspectr="16:9"

# output name
outname = "output.mkv"

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

def convert_to_seconds(string):
	# takes an input like this 00:00:15
	array = string.split(":")
	total_seconds = (int(array[0]) * 3600) + (int(array[1])) * 60 + int(array[2])
	return total_seconds

def generate_fade_string(temp_name_1, fadein, fadeout):

	# get new video len
	new_vid_len = get_video_duration(temp_name_1)
	new_vid_len = new_vid_len - fadetime

        fade_string = ""
	if fadein == True and fadeout == True:
		fade_string = "-vf \"fade=t=in:st=0:d=%s,fade=t=out:st=%s:d=%s\" -af \"afade=t=in:st=0:d=%s,afade=t=out:st=%s:d=%s\"" % (fadetime, new_vid_len, fadetime, fadetime, new_vid_len, fadetime)

	if fadein == True and fadeout == False:
		fade_string = "-vf \"fade=t=in:st=0:d=%s\" -af \"afade=t=in:st=0:d=%s\"" % (fadetime, fadetime)

	if fadein == False and fadeout == True:
		fade_string = "-vf \"fade=t=out:st=%s:d=%s\" -af \"afade=t=out:st=%s:d=%s\"" % (new_vid_len, fadetime, new_vid_len, fadetime)

	return fade_string


def run_ffmpeg(video, i, basename, startseconds, endseconds, fadein, fadeout):
	# infile, vcodec, size, aspect ratio, audio codec, start time, end time, fps, fps, output file
	if fadein == False and fadeout == False:
		temp_name_1 = tempdir + "%s-%s.%s" % (i, basename, out_extension)
	else:
		temp_name_1 = fadetempdir + "%s-%s.%s" % (i, basename, out_extension)
	render_string = "ffmpeg -i \"%s\" -qscale 0 -q:a 0 -q:v 0 -vcodec %s -s %s -aspect %s -acodec %s -ss %s -to %s -map 0 -async %s -r %s -y \"%s\" </dev/null" % (video, vcodec, dimensions, aspectr, acodec, startseconds, endseconds, fps, fps, temp_name_1)
	print render_string
	ffmpeg_call(render_string)
	sleep(2)

	if fadein == True or fadeout == True:
		# now we just need to add the fade in and fade out
		startseconds = 0
		endseconds = new_vid_len = get_video_duration(temp_name_1)
		temp_name_2 = tempdir + "%s-%s.%s" % (i, basename, out_extension)
		fade_string = generate_fade_string(temp_name_1, fadein, fadeout)

		render_string = "ffmpeg -i \"%s\" -qscale 0 -q:a 0 -q:v 0 -vcodec %s -acodec %s %s -ss %s -to %s -map 0 -async %s -r %s -y \"%s\" </dev/null" % (temp_name_1, vcodec, acodec, fade_string, startseconds, endseconds, fps, fps, temp_name_2)
		print fade_string
		print render_string
		ffmpeg_call(render_string)
		sleep(2)
	return


def ffmpeg_call(string):
	duration, err = subprocess.Popen(string, stdout=subprocess.PIPE, shell=True).communicate()
	return

def get_video_duration(filething):
	print filething, "video duration"
	proc, err = subprocess.Popen("ffmpeg -i %s -vframes 1 -f rawvideo -y /dev/null 2>&1" % filething, stdout=subprocess.PIPE, shell=True).communicate()
	print proc
	duration, err = subprocess.Popen("echo \"%s\" | grep -m1 \"^[[:space:]]*Duration:\" | cut -d\":\" -f2- | cut -d\",\" -f1 | sed \"s/[:\.]/ /g\"" % proc, stdout=subprocess.PIPE, shell=True).communicate() 
	dur_array = duration.split(" ")
	total_time = (int(dur_array[1]) * 3600) + (int(dur_array[2])) * 60 + int(dur_array[3])
	return total_time

if __name__ == "__main__":
	# open the file
	f = open(filename,'r')
	filelen = file_len(filename)
	if justmerge == False:
		for i in range(0,filelen):
			line = f.readline()
   	    	 # removes the "\n"
			line = re.sub("[\n\r]+", "",line)
			data = line.split(",")
			print data
			video = data[0]
			basename = video.split(".")[0]
			videolen = get_video_duration(video)

			if data[1] == "no":
				startseconds = 0
			else:
				startseconds = convert_to_seconds(data[1])
			

			if data[2] == "no":
				endseconds  = videolen
			else:
				endseconds = convert_to_seconds(data[2])

			# are we fading in
			if data[3] == "no":
				fadein = False
			else:
				fadein = True
				# do we need to modify the time slightly	
				if startseconds >= fadetime:
					startseconds = startseconds - fadetime

			# are we fading out        
			if data[4] == "no":
				fadeout = False
			else:
				fadeout = True
				# do we need to modify the time sllightly
				if endseconds <= videolen - fadetime:
					endseconds = endseconds + fadetime			


			# apply the rendering

			run_ffmpeg(video, i, basename, startseconds, endseconds, fadein, fadeout)

	if merge == True:
		temp_files = glob.glob(tempdir + "*")
		temp_files.sort(key=os.path.getmtime)
		mmcat_string = " ".join(temp_files)
		mmcat_string = mmcat_string + " " + outname
        
#		command_string = "bash mmcat %s </dev/null" % mmcat_string
		command_string = "bash mmcat %s" % mmcat_string
		print command_string
		# finally merge everything together
		duration, err = subprocess.Popen(command_string, stdout=subprocess.PIPE, shell=True).communicate()


#	video_filenames_string="ls -dt -1 $PWD/temp/*.*"
#	video_filenames, err = subprocess.Popen(video_filenames_string, stdout=subprocess.PIPE, shell=True).communicate()
#	print video_filenames


		



