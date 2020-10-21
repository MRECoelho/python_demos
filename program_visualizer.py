import time
import pprint
import win32gui
import win32process
import psutil
import pymongo as pm
from shapely.geometry import box
import ctypes
from collections import OrderedDict
import numpy as np
from numpy import ma
import matplotlib.pyplot as plt

# use the following commands if the terminal shows faulty typesetting
# chcp 65001
# set PYTHONIOENCODING=utf-8

if __name__ == "__main__":
    """
    This program is designed to log and visualize the opened programs by the user as part of 
    a program to analyze computer usage and attention span of seniors.
    Program functions purely as a proof of concept.
    """
    def windowEnumerationHandler(hwnd, top_windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title != '':
                pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                prog = psutil.Process(pid).name()
                coords = win32gui.GetWindowRect(hwnd)
                foreground =  1 if hwnd == win32gui.GetForegroundWindow() else 0
                top_windows.append((pid, prog, hwnd, title, coords, foreground))

    def get_all_windows():
        top_windows = []
        win32gui.EnumWindows(windowEnumerationHandler, top_windows)
        for i in top_windows:
            yield i

    def create_snapshot(i):
        # identification per window
        # pid = process id
        # prog = program name
        # hwnd = handle, for future expension of app
        # title = title of the window
        # coords = coordinates of window, for future implementations
        # foreground = boolean, true if window is the top most window
        keys = ["pid", "prog", "hwnd", "title", "coords", "foreground"]
        data = {"iter":i, "time":time.time(), "data":{str(kk):{k:v for k, v in zip(keys, vv)} for kk,vv in enumerate(get_all_windows())}}
        return data

    def log(max_iterations, delay=1):
        # time between snapshots is expressed as delay
        # through emperic research the max_iterations
        # and standard delay will be finetuned to
        # appropriate standards
        snapshot = dict()
        for i in range(max_iterations):
            if len(snapshot) == 0:
                # very first snapshot
                snapshot = create_snapshot(i)
            else:
                prev_hwnd = snapshot['data']['0']['hwnd']   
                prev_window_title = snapshot['data']['0']['title']
                new_snapshot = create_snapshot(i)
                new_hwnd = new_snapshot['data']['0']['hwnd']
                new_window_title = new_snapshot['data']['0']['title']
                if prev_hwnd == new_hwnd and prev_window_title == new_window_title:
                    # same window and same title, thus no snapshot needed according to specs
                    time.sleep(delay)
                    continue
                else:
                    # create a new snapshot
                    snapshot = new_snapshot
            db.snapshot.insert_one(snapshot)
            time.sleep(delay)

    def get_lifetimes():
        # to visualize the lifetime of the opened programs
        # all data needs to be retrieved from the database
        open_list = set()
        current_open_list = set()
        procs=  dict()
        cursor = db.snapshot.find()
        time = 0
        top_window = dict()
        for document in cursor:
            # post process the data 
            # for each document of the database
            i = document['iter']
            time = document['time']
            data = dict()
            for k,v in document['data'].items():
                # store raw data in a hash table for further processing
                # using the iteration number as key
                data[int(k)] = v
            for k,v in sorted(data.items()):
                pid = v['pid']
                prog = v['prog']
                title = v['title']
                hwnd = v['hwnd']
                if k == 0:
                    # top most window is always k == 0
                    top_window[time] = {'hwnd': hwnd, 'prog' : prog, 'title':title}
                if hwnd not in procs:
                    # during log a new hwnd appeared and needs to be added to the list of programs
                    procs[hwnd] = dict()
                    procs[hwnd]['pid'] = pid
                    procs[hwnd]['prog'] = prog
                    procs[hwnd]['session'] = dict()
                    procs[hwnd]['session'][0] = dict()
                    procs[hwnd]['session'][0]['title'] = title
                    procs[hwnd]['session'][0]['usetime']= [[time]]
                elif hwnd in procs:
                    # user switched to a already opened program
                    session = max(procs[hwnd]['session'])
                    if title != procs[hwnd]['session'][session]['title']:
                    # window got new title, e.g. new page loaded in browser
                        procs[hwnd]['session'][session]['usetime'][-1].append(time)
                        session+=1
                        procs[hwnd]['session'][session] = dict()
                        procs[hwnd]['session'][session]['title'] = title
                        procs[hwnd]['session'][session]['usetime']= [[time]]
                open_list |= {hwnd}
            closed_procs = current_open_list.difference(open_list)
            for i in closed_procs:
                session = max(procs[i]['session'])
                procs[i]['session'][session]['usetime'][-1].append(time)
            current_open_list = open_list.copy()
            open_list.clear()
        for v in procs.values():
            session = max(v['session'])
            if len(v['session'][session]['usetime'][-1])==1:
                v['session'][session]['usetime'][-1].append(time)
        foreground_procs=[top_window]
        return (procs,foreground_procs)

    def visualize_lifetimes(procs, program_lifetimes):
        plt.style.use('ggplot')
        fgp = []
        t = []
        # since procs is a dict and for the visualization we need the container
        # to be in the order of the keys
        renumber = {k:v for v,k in enumerate(sorted(procs.keys()))}
        for k,v in sorted( program_lifetimes[0].items() ):
            fgp.append(renumber[v['hwnd']])
            t.append(k)
        x = np.array(t)
        yp = np.array(fgp)
        plt.step(x, yp, where = 'mid', label = 'pre (foreground)', color = 'red')
        y_ticks = [v for k,v in sorted(renumber.items())]
        y_values = [procs[k]['prog'] for k,v in sorted(renumber.items())]
        plt.yticks(y_ticks, y_values)
        plt.show()

    connection=pm.MongoClient('localhost')
    db = connection.snapshot
    db.snapshot.drop() # clear old database
    log(10) # for testing just do 10 iterations with 1 second between them
    visualize_lifetimes(*get_lifetimes())

