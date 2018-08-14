# @Author: Anton Bracke <anton>
# @Date:   2018-08-03T19:00:46+02:00
# @Email:  anton@ju60.de
# @Last modified by:   anton
# @Last modified time: 2018-08-05T00:48:21+02:00

import cwiid
import time
import socket
import signal
import sys
import json
from thread import start_new_thread

TCP_IP = '127.0.0.1'
TCP_PORT = 5005

s = None
looping = True

def connect_wiimote(mac):
    wm = None
    print 'Press 1+2 on your Wiimote (' + mac + ') now ...'
    print 'Connecting to Wiimote (' + mac + ') ...'
    while not wm:
        try:
            wm = cwiid.Wiimote(mac)
        except RuntimeError:
            print "Error opening wiimote connection"
    print 'Wiimote (' + mac + ') connected.'
    wm.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_ACC | cwiid.RPT_IR
    # wm.rpt_mode = cwiid.RPT_BTN
    wm.rumble = True
    time.sleep(.5)
    wm.rumble = False
    return wm

def read_line(client):
    buffer = ''
    while True:
        tmp = client.recv(1)
        if not tmp:
            return tmp
        buffer += tmp
        if '\n' in buffer:
            break
    return buffer.rstrip()

def handle_input(client, wms):
    while True:
        try:
            line = read_line(client)
        except:
            continue
        if not line:
            break
        if line == 'quit':
            client.close()
            break
        args = line.split('$')
        if len(args) == 3:
            if args[1] == 'rumble':
                wms[int(args[0])].rumble = (args[2] == 'true')
            if args[1] == 'led':
                wms[int(args[0])].led = int(args[2])

def socket_loop(wms):
    states_battery = [None] * len(wms)
    states_error = [None] * len(wms)
    states_buttons = [None] * len(wms)
    states_acc = [None] * len(wms)
    states_ir = [None] * len(wms)

    client, addr = s.accept()
    print 'new client connected'
    start_new_thread(handle_input, (client, wms,))

    try:
        while True:
            for id in range(len(wms)):
                tmp = wms[id].state
                if (tmp['battery'] != states_battery[id]):
                    client.send(json.dumps({'id': id, 'key': 'battery', 'value': tmp['battery']}) + "\n")
                    states_battery[id] = tmp['battery']
                if (tmp['error'] != states_error[id]):
                    client.send(json.dumps({'id': id, 'key': 'error', 'value': tmp['error']}) + "\n")
                    states_error[id] = tmp['error']
                if (tmp['buttons'] != states_buttons[id]):
                    client.send(json.dumps({'id': id, 'key': 'buttons', 'value': tmp['buttons']}) + "\n")
                    states_buttons[id] = tmp['buttons']
                if (tmp['acc'] != states_acc[id]):
                    client.send(json.dumps({'id': id, 'key': 'acc', 'value': tmp['acc']}) + "\n")
                    states_acc[id] = tmp['acc']
                if (tmp['ir_src'] != states_ir[id]):
                    client.send(json.dumps({'id': id, 'key': 'ir', 'value': tmp['ir_src']}) + "\n")
                    states_ir[id] = tmp['ir_src']
            time.sleep(0.05)
    except BaseException as e:
        print 'error: ' + str(e)

    client.close()
    print 'client disconnected'

def open_socket():
    s = None
    while not s:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((TCP_IP, TCP_PORT))
            s.listen(1)
        except socket.error as exc:
            print 'Port already in use'
    print 'Socket opened: ' + TCP_IP + ':' + str(TCP_PORT)
    return s

def main():
    global s, looping
    wms = []

    s = open_socket()

    for i in range(1, len(sys.argv)):
        wms.append(connect_wiimote(sys.argv[i]))

    while looping:
        socket_loop(wms)

try:
    main()
except KeyboardInterrupt:
    print("interrupt received, stopping...")
finally:
    # clean up
    looping = False
    if s:
        s.close()
