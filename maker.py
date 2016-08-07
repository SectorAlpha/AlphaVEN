import os
import subprocess as sp
import datetime as dt
import warnings

#TODO major changes
#-Logging
#-Finish changing to better structure

DEFAULTOUTPUT = "output"
#Consider changing to a Dimension object?
DEFAULTRES = "800x600"
DEFAULTFADETIME = 1
DEFAULTFORMAT = ".mp4"

#The command to find the length of a video (in hh:mm:ss.ms format)
DURATIONFIND = ["ffprobe", "-v", "error", "-select_streams", "v:0", \
              "-show_entries", "stream=duration", "-sexagesimal", "-of", \
              "default=noprint_wrappers=1:nokey=1"]

class Maker:
    """Class to contain information about creation of video.
    
    By creating a Maker with appropriate parameters, the properties of a
    desired output video can be fully defined in advance of forming
    ffmpeg commands to construct it.
    """    
    
    def __init__(self, **kwargs):
        """Create a new Maker."""
        
        self.title = kwargs["title"] if "title" in kwargs else DEFAULTOUTPUT
        self.fadetime = kwargs["fadetime"] if "fadetime" in kwargs else DEFAULTFADETIME
        self.format = kwargs["format"] if "format" in kwargs else DEFAULTFORMAT      
        #Not yet implemented functionally speaking:
        self.resolution = kwargs["res"] if "res" in kwargs else DEFAULTRES
        
        self.viddict = {}
        self.seglist = []
        self.filtergraph = []
        self.command = ["ffmpeg"]
        self.labgen = labelGenerator()
        pass
            
    def __repr__(self):
        """String representation of the Maker."""
        #TODO non-terrible version of this...
        s = "Maker of " + self.title 
        s += "\nTotal segments = " + str(len(self.seglist))
        return s
    
    def addVideo(self, name, path):
        """Add a video object to the maker, using name to refer to path"""
        if name in self.viddict:
            if not os.path.join(path) == self.viddict[name].path:
                #If the video name is taken for another video, error
                raise ValueError("Video short name conflict.")
            else:
                #If the video exists already, just do nothing
                #Maybe raise a warning?
                pass
        else:
            vid = Video(self, name)
            vid.path = os.path.join(path)
            vid.measureVideoLength()
            self.viddict[name] = vid
            pass
    
    def addVideoSegment(self, vidname, **kws):
        """Add a new video segment to this maker.
        
        Keywords:
        start: time in video to start segment
        end: time in video to end segment
        path: path to video file as list (used if this Maker does not 
            already have this video available).
        """
        l = next(self.labgen)
        lab = LinkLabel(l,l)
        if vidname in self.viddict:           
            vid = self.viddict[vidname]            
        else:
            vid = Video(self, vidname)
            if "path" in kws:
                vid.path = os.path.join(kws["path"])            
            vid.measureVideoLength()
            self.viddict[vidname] = vid
        self.seglist.append(VideoSegment(vid, lab, **kws))  
        
    def addTransition(self, n, **kws):
        """Add transitions to the nth video segment.
        
        Keywords:
        fadein: time to spend fading in, or None.
        fadeout: time to spend fading out, or None.
        To use the default fadetime, use fadein/out=''"""
        seg = self.seglist[n]
        seg.transition = Transition(seg, **kws)
        pass

    def addInputsCommand(self):
        """Adds the inputs to the command."""
        for seg in self.seglist:
            self.command.extend(seg.getInputCommand())
        pass
    
    def addFilterCommand(self):
        """Add the filtergraph to the command."""
        self.command.append("-filter_complex")
        self.command.append(','.join(self.filtergraph))
        pass
    
    def addOutputCommand(self):
        """Add the output video path to the command."""
        #This should really be a path, not a title
        self.command.append(self.title + self.format)
        pass
        
    def addTransitionFilter(self):
        """Add the transitions between segments to the filtergraph."""
        for seg in self.seglist:
            self.filtergraph.extend(seg.transition.getFilterComponents())
    
    def addConcatFilter(self):
        """Create a command to concatenate the video segments."""
        
        concatstring = ""
        for seg in self.seglist:
            label = seg.linklabel
            concatstring += (label.vlabel + label.alabel)
        concatstring += "concat=n={0}:v=1:a=1".format(len(self.seglist))
        self.filtergraph.append(concatstring)
        pass
    
class Video:
    """Class to contain information about a single video."""

    def __init__(self, maker, name = "DEFAULT"):
        self.maker = maker
        self.name = name
        self.path = self.name + self.maker.format
        #This could be improved to proper pathbuilding?

    def measureVideoLength(self):
        """Use ffprobe to determine the length of a video."""
        
        findcmd = DURATIONFIND + [self.path]
        try:
            durastr = sp.check_output(findcmd).decode().strip()
        except sp.CalledProcessError:
            print("Failed to measure length of video:", self.path)
            #TODO better handling?
            exit()
        self.duration = dt.datetime.strptime(durastr, "%H:%M:%S.%f").time()
 
class Transition:
    """Class representing transitions to/from a video segment."""
    
    def __init__(self, videosegment, **kws):
        """Create a new Transition object.
        
        Keywords:
        fadein: duration of fade-in in seconds, or None
        fadeout: duration of fade-out in seconds, or None
        """
        #The segment is the video segment bracketed by this 
        #transition's fades.
        self.videosegment = videosegment
        
        if "fadein" in kws:
            if kws["fadein"]:
                self.fadein = kws["fadein"]
            elif not (kws["fadein"] == None or kws["fadein"] == 0):
                #If the fade time isn't explicitly 0
                self.fadein = self.videosegment.parentvideo.maker.fadetime
            else:
                self.fadein = None
        else:
            self.fadein = False
            
        if "fadeout" in kws:
            if kws["fadeout"]:
                self.fadeout = kws["fadeout"]
                self.starttime = (self.videosegment.getDuration() \
                - dt.timedelta(seconds=int(self.fadeout))).total_seconds()
            elif not (kws["fadeout"] == None or kws["fadeout"] == 0):
                self.fadeout = self.videosegment.parentvideo.maker.fadetime
                self.starttime = (self.videosegment.getDuration() \
                - dt.timedelta(seconds=int(self.fadeout))).total_seconds()
            else:
                self.fadeout = None
        else:
            self.fadeout = False
    
    def __repr__(self):
        """Create a printable representation of this transition."""
        s = str(self.videosegment) + ": "
        if self.fadein:
            s += "fade-in: {0} ".format(self.fadein)
        if self.fadeout:
            s += "fade-out: {0} ".format(self.fadeout)
        if not (self.fadein or self.fadeout):
            s += "no fades"
        return s
    
    def getFilterComponents(self):
        """Create the filtergraph strings for this transition."""
        
        filtercomps = []
        
        if self.fadein:
            filtercomps.append("{0}fade=in:d={1}".\
                            format(self.videosegment.linklabel.vlabel,\
                                   self.fadein))
            if self.fadeout:
                #If both kinds of fade are required
                filtercomps[0] += ", fade=out:d={0}:start_time={1}".\
                            format(self.fadeout,\
                                   self.starttime)
        elif self.fadeout:
            filtercomps.append("{0}fade=out:d={1}:start_time={2}".\
                            format(self.videosegment.linklabel.vlabel,\
                                   self.fadeout,\
                                   self.starttime))
        if self.fadein or self.fadeout:
            #If there's a fade filter, give it an output label
            self.videosegment.linklabel.\
                updateLabel(video=next(self.videosegment.\
                                       parentvideo.maker.labgen))
            filtercomps[-1] += self.videosegment.linklabel.vlabel
        return filtercomps
    
class VideoSegment:
    """Class representing a single segment of a video.
    
    Note: Can be the entire video.
    """
    
    def __init__(self, video, linklabel, **kws):
        """Create a new VideoSegment object.
        
        Keywords:
        start: datetime time giving time in video at which to start.
        end: datetime time giving time in video at which to end.
        """
        
        self.parentvideo = video
        self.linklabel = linklabel
        
        if "start" in kws:
            st = kws["start"]
            if st < self.parentvideo.duration:
                self.starttime = st
            else:
                #This is an error; there's no obvious way to proceed
                raise ValueError("Start of video segment later than video length.")
        else:
            self.starttime = dt.time(0)
            
        if "end" in kws:
            et = kws["end"]
            if et < self.parentvideo.duration:
                self.endtime = et
            else:
                #This could happen if e.g. rounding errors make et larger than
                #the video length when they're supposed to be equal.
                #A warning is raised and the segment goes to the end of the video.
                warnings.warn("End of video segment after end of video, entire remainder will be used.")
                self.endtime = self.parentvideo.duration
        else:
            self.endtime = self.parentvideo.duration
            
        if self.endtime < self.starttime:
            raise ValueError("Start of video segment after end.")
        #An empty transition
        self.transition = Transition(self)
    
    def __repr__(self):
        """Create a printable representation of this segment."""
        return self.parentvideo.maker.title + "segment: " \
                + str(self.parentvideo.maker.seglist.index(self))
    
    def getDuration(self):
        """Get the duration of this video segment."""
        return timediff(self.endtime, self.starttime)
    
    def getInputCommand(self):
        """Get the command portion for adding this video segment as an input."""
        commandsection = []
        if self.starttime > dt.time(0):
            commandsection.extend(["-ss", str(self.starttime)])
        if self.endtime < self.parentvideo.duration:
            commandsection.extend(["-t", str(self.getDuration())])
        commandsection.extend(["-i", self.parentvideo.path])
        return commandsection
    
    def setTransition(self, transition):
        """Set the transitions in and out of this video segment."""
        #Create a transition referring to this segment
        #transition should be given as a dictionary of arguments to the
        #Transition constructor.
        self.transition = Transition(self, **transition)

class LinkLabel:
    """Class to represent link labels. Has an Audio and Video label."""
    
    def __init__(self, vlab, alab):
        """Create a new LinkLabel object."""
        self.vlabel = "[{0}:v]".format(vlab)
        self.alabel = "[{0}:a]".format(alab)
        
    def updateLabel(self, **kws):
        """Update one of the labels to a new value."""
        if "video" in kws.keys():
            self.vlabel = "[{0}:v]".format(kws["video"])
        if "audio" in kws.keys():
            self.alabel = "[{0}:a]".format(kws["audio"])

def labelGenerator():
    """Generates unique short names for link labels."""
    i = 0
    while True:
        yield str(i)
        i += 1
    return

def timediff(t1, t2):
    """Find the absolute difference between two datetime Times.
    
    Returns a timedelta object.
    """
    
    delta1 = dt.timedelta(hours=t1.hour, \
                          minutes=t1.minute, \
                          seconds=t1.second, \
                          microseconds=t1.microsecond)
    delta2 = dt.timedelta(hours=t2.hour, \
                          minutes=t2.minute, \
                          seconds=t2.second, \
                          microseconds=t2.microsecond)
    return abs(delta2 - delta1)

if __name__ == "__main__":
    print("Running tests...")
    vidpath1 = os.path.join("..", "res", "testvid1.mp4")
    vidpath2 = os.path.join("..", "res", "testvid2.mp4")
    testmaker = Maker(title="testoutput",format=".mp4")
    testmaker.addVideo("vid1", vidpath1)
    testmaker.addVideo("vid2", vidpath2)
    testmaker.addVideoSegment("vid1", start=dt.time(0,0,3), end=dt.time(0,0,5))
    testmaker.addVideoSegment("vid2", start=dt.time(0,0,4), end=dt.time(0,0,7))
    testmaker.addTransition(0,fadein='')
    testmaker.addTransition(1,fadein=None,fadeout=2)
    testmaker.addInputsCommand()
    testmaker.addTransitionFilter()
    testmaker.addConcatFilter()
    testmaker.addFilterCommand()
    testmaker.addOutputCommand()
    print(testmaker.command)
    print("Tests complete.")
            