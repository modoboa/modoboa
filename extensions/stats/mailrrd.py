#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Interface with rrdtool to generate appropriate postfix graph statistics
sent, recv, bounced, rejected messages are tracked.
"""
import sys, os, rrdtool, re, time
import pdb
from optparse import OptionParser
try:
    import django.conf
except:
    print "[rrd] Warning no Django conf found"
rrdstep           = 60
xpoints           = 540
points_per_sample = 3
rrd_inited        = False
this_minute       = 0

rrd_file = "postfix.rrd"
png_file = "postfix.png"
log_file = "/var/log/maillog"
tmp_path     = "static/tmp/" 

months_map = {
    'Jan' : 0, 'Feb' : 1, 'Mar' : 2,
    'Apr' : 3, 'May' : 4, 'Jun' : 5,
    'Jul' : 6, 'Aug' : 7, 'Sep' : 8,
    'Oct' : 9, 'Nov' :10, 'Dec' :11,
    'jan' : 0, 'feb' : 1, 'mar' : 2,
    'apr' : 3, 'may' : 4, 'jun' : 5,
    'jul' : 6, 'aug' : 7, 'sep' : 8,
    'oct' : 9, 'nov' :10, 'dec' :11,
}

def str2Time(y,M,d,h,m,s):
    """str2Time

    return epoch time from Year Month Day Hour:Minute:Second time format
    """
    try:
        local = time.strptime("%s %s %s %s:%s:%s" %(y,M,d,h,m,s), \
                          "%Y %b %d %H:%M:%S")
    except:
        print "[rrd] ERROR unrecognized %s time format" %(y,M,d,h,m,s)
        exit(0)
    return int(time.mktime(local))


class parser():
    """parser

    Parse a mail log in syslog format:
    Month day HH:MM:SS host prog[pid]: log message...

    For each epoch record the parser stores number of
    'sent', 'received', 'bounced','rejected' messages over
    a rrdstep period of time.

    parameters : logfile, and starting year
    
    """
    def __init__(self,domain,logfile=log_file,rrdfile=rrd_file,imgFile=png_file,
                 create=False,year=None,debug=False,verbose=False,graph=None):
        """constructor
        """
        self.logfile = logfile
        try:
            self.f = open(logfile)
        except IOError as (errno, strerror):
            print "[rrd] I/O error({0}): {1} ".format(errno, strerror)+logfile
            return None
        self.domain = str(domain) #.replace(".","_")
        self.enable_year_decrement = None
        self.rrdfile = tmp_path + self.domain+"_"+rrdfile
        self.create = create
        self.year = year
        self.debug = debug
        self.verbose = verbose
        self.graph = graph
        self.imgFile = self.domain+"_"+imgFile
        self.types = ['AVERAGE','MAX']
        self.natures = ['sent_recv','boun_reje']
        self.legend = {'sent_recv' : ['sent messages','received messages'],
                       'boun_reje' : ['bounced messages','rejected messages']}

        self.data = {}
        self.last_month = None
        if not self.year:
            self.year = time.localtime().tm_year
        self.first_minute = 0
        self.last_minute  = 0

        if self.create and os.path.exists(logfile):
            print "[rrd] force new RRD"
            os.system("rm -f %s" %rrdfile)

        elif os.path.exists(self.rrdfile):
            self.last_minute = rrdtool.last(self.rrdfile)
            self.first_minute = rrdtool.first(self.rrdfile)
            if self.debug:
                print "[rrd] DEBUG updating rrd from %s"\
                      %time.asctime(time.localtime(self.last_minute))


        self.process_log()

    def year_increment(self,month):
        """year_increment
        """
        if month == 0:
            if self.last_month and self.last_month == 1:
                self.year += 1
                self.enable_year_decrement = True
        elif month == 11:
            if self.enable_year_decrement \
               and self.last_month and self.last_month != 1:
                self.year -= 1
        else:
            self.enable_year_decrement = False

        self.last_month = month

    def process_line(self,text):
        """process_line

        Parse a log line and look for
        'sent','received','bounced',rejected' messages event

        Return True if data are up-to-date
        else False
        """
        # get date
        ret = False

        m = re.match("(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\s+(\w+)\s+(\w+)/?\w*[[](\d+)[]]:\s+(.*)",text)
        if not m : return ret

        mo = m.group(1)
        da = m.group(2)
        ho = m.group(3)
        mi = m.group(4)
        se = m.group(5)
        host = m.group(6)
        prog = m.group(7)
        pid  = m.group(8)
        log  = m.group(9)

        sent = 0
        recv = 0
        boun  = 0
        reje  = 0

        self.year_increment(months_map[mo])
        se = int(int(se)/rrdstep)            # rrd step is one-minute => se = 0
        cur_t = str2Time(self.year,mo,da,ho,mi,se)

        if not self.data.has_key(cur_t):
            self.data[cur_t] = {'sent':0,'recv':0, 'boun':0,'reje':0}

        # watch events
        if re.match(".*\s+status=sent\s+.*",text):
            sent = 1

        elif re.match(".*\s+status=bounced\s+.*",text):
            boun = 1

        elif re.match(".*[0-9A-Z]+: client=(\S+).*",text):
            recv = 1

        elif re.match(".*(?:[0-9A-Z]+: |NOQUEUE: )?reject: .*",text):
            reje = 1

        elif re.match(".*(?:[0-9A-Z]+: |NOQUEUE: )?milter-reject: .*",text):
            if not re.match(".*Blocked by SpamAssassin.*",text):
                reje = 1
            #else regiter spam

        # register events
        if sent or recv or boun or reje:
            self.data[cur_t]['sent'] = self.data[cur_t]['sent'] + sent
            self.data[cur_t]['recv'] = self.data[cur_t]['recv'] + recv
            self.data[cur_t]['boun'] = self.data[cur_t]['boun'] + boun
            self.data[cur_t]['reje'] = self.data[cur_t]['reje'] + reje
            return True

        return False

    def init_rrd(self,m):
        """init_rrd

        Set-up Data Sources (DS)
        Set-up Round Robin Archives (RRA):
        - day,week,month and year archives
        - 2 types : AVERAGE and MAX

        parameter : start time
        return    : last epoch recorded
        """
        ds_type = 'ABSOLUTE'
        rows = xpoints / points_per_sample

        realrows = int(rows * 1.1)    # ensure that the full range is covered
        day_steps = int(3600*24/(rrdstep * rows))
        week_steps = day_steps * 7
        month_steps = week_steps * 5
        year_steps = month_steps * 12

        # Set up data sources for our RRD
        ds1 = 'DS:sent:%s:%s:0:U' %(ds_type,rrdstep*2)
        ds2 = 'DS:recv:%s:%s:0:U' %(ds_type,rrdstep*2)
        ds3 = 'DS:boun:%s:%s:0:U' %(ds_type,rrdstep*2)
        ds4 = 'DS:reje:%s:%s:0:U' %(ds_type,rrdstep*2)

        # Set up RRD to archive data
        rra1 = 'RRA:%s:0.5:%s:%s' %('AVERAGE',day_steps,realrows)   # day
        rra2 = 'RRA:%s:0.5:%s:%s' %('AVERAGE',week_steps,realrows)  # week
        rra3 = 'RRA:%s:0.5:%s:%s' %('AVERAGE',month_steps,realrows) # month
        rra4 = 'RRA:%s:0.5:%s:%s' %('AVERAGE',year_steps,realrows)  # year
        rra5 = 'RRA:%s:0.5:%s:%s' %('MAX',day_steps,realrows)
        rra6 = 'RRA:%s:0.5:%s:%s' %('MAX',week_steps,realrows)
        rra7 = 'RRA:%s:0.5:%s:%s' %('MAX',month_steps,realrows)
        rra8 = 'RRA:%s:0.5:%s:%s' %('MAX',year_steps,realrows)

        # With those setup, we can now created the RRD
        if not os.path.exists(self.rrdfile):
            rrdtool.create(self.rrdfile,
                           '--start',str(m),
                           '--step',str(rrdstep),
                           ds1,ds2,ds3,ds4,
                           rra1,rra2,rra3,rra4,
                           rra5,rra6,rra7,rra8)
            this_minute = m
        else:
            this_minute = rrdtool.last(self.rrdfile) + rrdstep

        return this_minute


    def update_rrd(self,t):
        """update_rrd

        Update RRD with records at t time.

        True  : if data are up-to-date for current minute
        False : syslog may have probably been already recorded
        or something wrong
        """
        m = t - (t % rrdstep)

        if not self.last_minute :
            self.last_minute = self.init_rrd(m)
            print "[rrd] create new RRD file"

        if m < self.last_minute :
            if self.verbose:
                print "[rrd] VERBOSE events at %s already recorded in RRD" %m
            return False
        elif m == self.last_minute :
            return True

        # Missing some RRD steps
        if m > self.last_minute + rrdstep:
            for p in range(self.last_minute+rrdstep,m,rrdstep):
                if self.verbose:
                    print "[rrd] VERBOSE update %s:%s:%s:%s:%s (SKIP)" \
                          %(p,'0','0','0','0')
                rrdtool.update(self.rrdfile,"%s:%s:%s:%s:%s" \
                               %(p,'0','0','0','0'))

        if self.verbose:
            print "[rrd] VERBOSE update %s:%s:%s:%s:%s" \
                  %(m,self.data[m]['sent'], self.data[m]['recv'],\
                    self.data[m]['boun'], self.data[m]['reje'])

        rrdtool.update(self.rrdfile,"%s:%s:%s:%s:%s" \
                       %(m,self.data[m]['sent'], self.data[m]['recv'],\
                         self.data[m]['boun'], self.data[m]['reje']))

        self.last_minute = m
        return True


    def process_log(self):
        """process_log

        Go through entire log file
        """
        for line in self.f.readlines():
            evt = self.process_line(line)

        # Sort everything by time
        sortedData = {}
        sortedData = [ (i,self.data[i]) for i in sorted(self.data.keys()) ]

        for t, dict in sortedData:
            if self.update_rrd(t):
                if not self.first_minute:
                    self.first_minute = t
                self.last_minute = t


    def plot_rrd(self,f=None,color1 = "#990033", color2 = "#330099",
                 year = None, start = None, end = None, t =None, n = None):
        """plot_rrd

        Graph rrd from start to end epoch
        """
        if f:
            self.imgFile = f
        start = str(self.first_minute)
        end   = str(self.last_minute)
        if t:
            self.types = t
        if n:
            self.natures = n

        if self.graph:
            try:
                start = int(time.mktime(time.strptime(self.graph[0], \
                                                      "%Y %b %d %H:%M:%S")))
                end = int(time.mktime(time.strptime(self.graph[1], \
                                                      "%Y %b %d %H:%M:%S")))
            except:
                print "[rrd] ERROR bad time format for option --graph"


        print "[rrd] plot rrd graph from %s to %s" \
              %(time.asctime(time.localtime(float(start))),\
                time.asctime(time.localtime(float(end))))
        if not year: year = time.localtime().tm_year
        self.imgFile
        if not os.path.exists(tmp_path):
            os.mkdir(tmp_path)
        for n in self.natures:
            for t in self.types:
                path = '%s%s_%s_%s'%(tmp_path,n,t,os.path.basename(self.imgFile))
                ds1 = n.split('_')[0]
                ds2 = n.split('_')[1]

                rrdtool.graph(
                    path,
                    '--imgformat','PNG',
                    '--width','540',
                    '--height','100',
                    '--start', str(start),
                    '--end', str(end),
                    '--vertical-label', '%s message' %t.lower(),
                    '--title', '%s message flow per minute' %t.lower(),
                    '--lower-limit', '0',
                    'DEF:%s=%s:%s:%s:' %(ds1,self.rrdfile,ds1,t),
                    'DEF:%s=%s:%s:%s:' %(ds2,self.rrdfile,ds2,t),
                    'LINE:%s%s:%s' %(ds1,color1,self.legend[n][0]),
                    'LINE:%s%s:%s' %(ds2,color2,self.legend[n][1])
                    )

if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("-f","--file",dest="filename",default=rrdfile,
                      help="write rrd data base to FILE",metavar="FILE")
    parser.add_option("-i","--imgFile",default=png_file,
                      help="graph rrd stats to FILE",metavar="FILE")
    parser.add_option("-c","--create",default=False,action="store_true",dest="create",
                      help="force creation of new RRD")
    parser.add_option("-g","--graph",nargs=2,dest="graph",
                      help="generate graph in between time period (y M d YY:MM:SS)", metavar="START STOP")
    parser.parse_args(['--graph', 'start', 'stop'])
    parser.add_option("-l","--logFile",default="maillog",
                      help="postfix log in syslog format",metavar="FILE")
    parser.add_option("-v","--verbose",default=False,action="store_true",dest="verbose",
                      help="set verbose mode")
    parser.add_option("-d","--debug",default=False,action="store_true",dest="debug",
                      help="set debug mode")

    (options,args) = parseOption()
    P = parser(logfile=options.logFile,rrdfile=options.file,
               debug=options.debug,verbose=options.verbose,
               create=options.create,graph=options.graph,imgFile=options.imgFile)
    P.plot_rrd()
