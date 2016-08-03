import os
import argparse as ap
import maker
import warnings
import datetime as dt
import subprocess as sp

#Consts
FADEIN_STRINGS = ["in", "In", "fadein", "Fadein", "fi"]
FADEOUT_STRINGS = ["out", "Out", "fadeout", "Fadeout", "fo"]

class Ven():
    
    def __init__(self):
        """Create new AlphaVEN instance."""
        #lol pro init we've got here :^)
        pass

    def parseInputFile(self):
        """Read the input file into relevant pieces.
        
        The input file will be separated into paragraphs.
        The first paragraph may be a settings block.
        Otherwise, each paragraph describes the creation of
        a single output video.
        """
        with open(self.args.file) as inputfile:
            data = inputfile.read()
            self.paralist = data.split("\n\n")
            self.getSettings()
        pass
    
    def getSettings(self):
        """Get settings from the input."""
        
        #First check that there are settings.
        if self.args.settings:
            self.hassettings = True
        elif self.args.nosettings:
            self.hassettings = False
        else:
            self.hassettings = isSettingsParagraph(self.paralist[0])
        
        if not (self.args.settings or isSettingsParagraph(self.paralist[0])):
            #The map is just a function that returns its input
            #This is so things that call map(video) can use it
            #even if there's nothing to map.
            self.map = lambda x: x
            
        else:
            # If there are settings, read them
            rawsettings = self.paralist[0]
            self.paralist = self.paralist[1:]
            
            for line in rawsettings.split('\n'):
                if line[:4] == "map:":
                    self.createMap(line[4:])
                    self.map = lambda x: self.mapdict[x]
                elif line[:4] == "set:":
                    #Various settings can be made by this line
                    #Ideally, the Maker's init should take care of them
                    #by treating them as kwargs
                    #So we'll store them as a dict, and blat them in
                    self.createGeneralSettings(line[4:])
            
    def createMap(self, line):
        """Create a map that converts video names to paths."""
        self.mapdict = {}
        for part in line.split(','):
            a = part.split('=')
            self.mapdict[a[0]] = a[1]
        pass        
        
    def createGeneralSettings(self, line):
        """Create a dictionary of the settings all videos will share."""
        self.gensetdict = {}
        for part in line.split(','):
            a = part.split('=')
            self.gensetdict[a[0]] = a[1]
    
#     def bundleLines(self):
#         """Break up the lines in each paragraph into usable bundles."""
#         self.bundledparalist = []
#         for para in self.paralist:
#             if self.args.verbose:
#                 print('\n' + "Dividing paragraph: \n" + para.split('\n')[0])
#             #Extract the inputs and transitions
#             lines = para.split('\n')[1:]
#             
#             #paramaker = maker.Maker(title=paratitle, **self.gensetdict)
#             det = self.determineLineTypes(lines)
#             bundledlines = self.collateLines(lines, det)
#             self.bundledparalist.append(bundledlines)
#         pass
#Was used for testing part of createMakers
              
    def createMakers(self):
        """Create a Maker for each of the outputs."""
        self.makers = []
        for para in self.paralist:
            #Extract the inputs and transitions
            paratitle = para.split('\n')[0]
            lines = para.split('\n')[1:]
            
            paramaker = maker.Maker(title=paratitle, **self.gensetdict)
            det = self.determineLineTypes(lines)
            bundledlines = self.collateLines(lines, det)
            # k tracks which video segment to add transitions to
            k = 0
            for b in bundledlines:
                vidname = b.videoline.split(',')[0]
                paramaker.addVideo(vidname, self.map(vidname))
                #Start by decomposing a bundle into a precise sequence of videos and transitions
                timepairs = self.processSegmentation(b.videoline)                
                if len(timepairs) == 1:
                    #A single video segment, using all available transitions itself
                    #First, add the segmentation to the maker (kth segment)
                    s, e = timepairs[0]
                    segdict = {}
                    if s != "s":
                        segdict["start"] = s
                    if e != "e":
                        segdict["end"] = e                     
                    
                    #Second, add the transitions
                    transdict = {}
                    for t in b.translines:
                        trans = readTransLine(t)
                        transdict[trans[0]] = trans[1]
                    
                    paramaker.addVideoSegment(vidname, **segdict)
                    paramaker.addTransition(k, **transdict)                    
                    k += 1                    
                else:
                    #Multiple video segments in this bundle.
                    #Transitions apply only to the first and/or last segment(s)
                    
                    #Need to add each video segment, and add a transition iff appropriate
                    tlist = [readTransLine(t) for t in b.translines]
                    tmax = len(tlist)
                    smax = len(timepairs)
                    l = 0
                    for s,e in timepairs:
                        segdict = {}
                        transdict = {}
                        
                        if s != "s":
                            segdict["start"] = s
                        if e != "e":
                            segdict["end"] = e 
                                                
                        if tmax == 1:
                            #There is one transition to assign
                            transition = tlist[0]
                            if (l == 0 and transition[0] == "fadein") \
                            or (l == smax - 1 and transition[0] == "fadeout"):
                                #Assign the transition
                                transdict[transition[0]] = transition[1]
                                                        
                        elif tmax == 2:
                            #Two transitions to assign
                            if l == 0:
                                transdict[tlist[0][0]] = tlist[0][1]
                            if l == smax - 1:
                                transdict[tlist[1][0]] = tlist[1][1]
                        
                        else:
                            #No transitions: segments only.
                            pass
                        
                        l += 1
                                
                        paramaker.addVideoSegment(vidname, **segdict)
                        paramaker.addTransition(k, **transdict)  
                        
                        k += 1                       
                        
            self.makers.append(paramaker)
            
    def determineLineTypes(self, lines):
        """Determine whether lines are videos or transitions."""
        tracker = []
        for l in lines:
            p1 = l.split(',')[0]            
            #If this succeeds, the map has a path for p1
            #or no map was given, and p1 could be anything
            #If it fails, a map must exist but p1 isn't in it.
            #If so, p1 could be a path itself, or a non-video line.
            try:
                path1 = self.map(p1)                                
            except KeyError:
                path1 = p1
                #If '.': either a path or a fractional fade time
                #If it's a fractional fade time, it has to say "fade" somewhere
                if '.' in path1 and not "fade" in path1:
                    warnings.warn("Path not in map", UserWarning)               
            finally:
                if '.' in path1 and not "fade" in path1:
                    tracker.append(True)
                else:
                    tracker.append(False)
    
        return tracker
    
    def collateLines(self, lines, deter):
        """Group together lines into one bundle for each video."""
        bundles = []
        i = j = 0
        L = len(lines)
        going = True
        while going:
            #Read off each line up to and including the first video
            if deter[i]:
                #If a video, read each line from the last find to this
                bunch = lines[j:i+1]
                if i < L - 1 and lines[i+1].split(' ')[0] in FADEOUT_STRINGS:
                    #Check if the next line should be included
                    bunch.append(lines[i+1])
                    if i == L - 2:
                        #If we're using the next line as well, end early
                        going = False
                    i += 1
                if self.args.verbose:
                    print("Bundling lines: {0} of types: {1}".format(bunch, deter[j:i+1]))
                bundles.append(LineBundle(bunch, deter[j:i+1]))
                j = i + 1 
            i += 1
            #If we're at the end of the list, stop running               
            if i == L:
                going = False
        return bundles
            
    def processSegmentation(self, s):
        """Convert string video segments to format for Maker."""
        #s is a string like "vidname, -t1, t2-t3, t4-"
        #Open dashes indicate "from the start" or "to the end"
        #The required format is "vidname", [(dt, dt), (dt, dt),...]
        #or use 's', 'e' for start/end points.
        times = []
        spl = s.split(',')
        if len(spl) == 1:
            times.append(("s","e"))
        else:
            segnames = [x.strip() for x in spl][1:]
    
            for segn in segnames:
                start,end = segn.split('-')
                t1 = processTimeString(start, "s")
                t2 = processTimeString(end, "e")
                times.append((t1,t2))
        return times

    
class LineBundle():
    """A set of lines for a single input video and its transitions."""
    
    def __init__(self, linegroup, kinds):
        """Create a LineBundle object from lines and their classification."""
        self.length = len(linegroup)
        #Extract the video line, leaving the rest (transitions) behind
        self.videoline = linegroup.pop(kinds.index(True))
        self.translines = linegroup
        
    def __repr__(self):
        """String representation of a linebundle."""
        s = str(len(self.translines))
        return "{0} with {1} transitions".format(self.videoline, s)


def readTransLine(line):
    """Read information from a line defining a transition."""
    comps = line.split(' ' )
    opt = ['','']
    if len(comps) > 1:
        opt[1] = int(comps[1])
    if comps[0] in FADEIN_STRINGS:
        opt[0] = "fadein"  
    if comps[0] in FADEOUT_STRINGS:
        opt[0] = "fadeout"
    return opt       

    
def isSettingsParagraph(p):
    """Attempt to check if a paragraph contains settings.
    
    This feature is not certain to give the correct result
    in all cases. It may be avoided using the --settings or
    --no-settings flag when running AlphaVEN.
    """
    #This feature a useless. USELESS.
    
    for l in p.split('\n'):
        s = l[:4]
        if s == "map:" or s == "set:":
            return True
    return False

def processTimeString(s, default):
    """Process a time string to a dt object or abbreviated string."""
    if s:
        if '.' in s:
            return dt.datetime.strptime(s, "%H:%M:%S.%f").time()
        else:
            return dt.datetime.strptime(s, "%H:%M:%S").time()
            #Could extend this by adding more permitted formats
    else:
        return default
    
def createParser():
    """Create the argument parser."""
    
    parser = ap.ArgumentParser()
    #Required arguments
    parser.add_argument("file", help="The file that defines the \
videos to create")
    #Options
    parser.add_argument("-v", "--verbose", help="Display additional \
information during operation.", action="store_true")
    parser.add_argument("-s", "--settings", help="Treat the first \
paragraph in the input as settings. If this is not used, AlphaVEN \
attempts to automatically detect whether the first paragraph \
contains settings.", action="store_true")
    parser.add_argument("-ns", "--no-settings", help="Do not treat \
the first paragraph in the input as settings. If this is not \
used, AlphaVEN attempts to automatically detect whether the first \
paragraph contains settings.", action="store_true", dest="nosettings")    
    return parser

if __name__ == "__main__":
    ven = Ven()
    parser = createParser()
    ven.args = parser.parse_args()
    ven.parseInputFile()
    ven.createMakers()
    for m in ven.makers:
        m.addInputsCommand()
        m.addTransitionFilter()
        m.addConcatFilter()
        m.addFilterCommand()
        m.addOutputCommand()
        if ven.args.verbose:
            print("Sending {}".format(' '.join(m.command)))
        sp.check_call(m.command)
        print('\n')