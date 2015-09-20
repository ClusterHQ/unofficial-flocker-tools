#!/usr/bin/python
"""
optimization tool. see which parts of the install are taking the longest.

1. 'ts' is in moreutils package, install it.
2. trial test_integration.py | ts -s '%.s, ' > ~/log.txt
3. python ts.py ~/log.txt > ~/log.csv
4. open ~/log.csv
"""
import sys
data = [s.split(",  ") for s in open(sys.argv[1]).read().strip().split("\n")]
relative_data = []
last_absolute_time = 0.0
last_job = ""
for absolute_time, job in data:
    absolute_time = float(absolute_time)
    relative_time = absolute_time - last_absolute_time
    relative_data.append((relative_time, job, last_job))
    last_absolute_time = absolute_time
    last_job = job

relative_data.sort()
relative_data.reverse()
for (time, job, previous_job) in relative_data:
    if time > 0.05:
        print "%.2f, %r, %r" % (time, previous_job.replace(',', '\,'), job.replace(',', '\,'))
        """
        print "=== %.2f ===" % (time,)
        print "from:", previous_job
        print "  to:", job
        print
        """
