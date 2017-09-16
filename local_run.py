'''
Wrapper around the caravan core. 
1. Reads event info from a pickle file, generated by events_receiver.py 
2. Generates a RunInfo a passes it to the caravan_run function 
3. Once the simulation is completed, the report is generated an saved in a folder named after the event hash, 
so it could retrieved by the web interface
5. Report is sent by mail ... work in progress
'''

from __future__ import print_function
import os
import sys
import pickle
import time 
import shutil
from caravan.settings import globalkeys as gk
from caravan.core.runutils import RunInfo
from caravan.core.core import caravan_run
from caravan.settings import globals as glb
from caravan.report import report


progress_check_time_out = 20 # in seconds, set accordingly to the speed of your machine


if len(sys.argv) < 2: 
    print("Expects as argument an info.pickle file, generated by local_run.py")
    sys.exit(1)


# extracting event info from the pickle file passed by local_run.py
event_file = sys.argv[1]
with open(event_file, "rb") as f: 
    event_info = pickle.load(f)


event = {
    gk.LAT: event_info["latitude"],
    gk.LON: event_info["longitude"],
    gk.MAG: event_info["magnitude"],
    gk.DEP: event_info["depth"],
    gk.STR: glb.params[gk.STR]["default"],
    gk.IPE: glb.params[gk.IPE]["default"],
    gk.GMO: False
}


# event for testing the simulation process
#event = {'mag': '6.8', 'ipe': 2, 'dep': '20', 'gm_only': False, 'lon': '74.0', 'str': '90', 'lat': '42.7'}

runinfo = RunInfo(event)
scenario = runinfo.scenario()

dbhash = scenario.dbhash()
print("Running simulation, hash:", dbhash)


# starting the main process 
caravan_run(runinfo)

# displaying, on the console, the same output seen in the web interface, could be useful for debug purposes
for msg in runinfo.msg(): 
    print(" >>", msg)
    # An awful way to check if dealing with an already simulated scenario
    # though it is very unlike to happen as events are real streamed events
    if "skipping simulation" in msg: 
        print("Scenario already simulated, exiting")
        sys.exit(1)


session_id = runinfo.session_id()
print("-> session_id:", session_id)

# waiting for simulation to terminate before generating the report
while True: 
    time.sleep(progress_check_time_out)
        
    progress = runinfo.progress()
    print("-> progress:", round(progress))

    if progress >= 100.0:
        print("done")
        break


print("Generating report") 
report(session_id)



# copying report from /caravan/static/report (default location) to event_folder
event_folder = os.path.dirname(event_file)
shutil.copy(
    "./caravan/static/report/report.pdf", 
    os.path.join(event_folder, "report.pdf") 
)


# creating a (folder) symlink to the event_folder (event_id)
# the symlink is named after the scenario hash, so corresponding report could be retrieved by caravan
event_folder_link = os.path.join(
    os.path.dirname(event_folder), str(dbhash)
)

os.symlink(event_folder, event_folder_link)


# now the report can be sent via mail, still waiting for info on your provider and/or newsletter mechanism ...
event_report = os.path.join(event_folder_link, "report.pdf")


sys.exit(0)
