#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Basic tutorial 12: Streaming
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+12%3A+Streaming
"""
import sys
import gi

gi.require_version('GLib', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GLib

# initialize GStreamer
Gst.init(sys.argv[1:])


class CustomData:
    is_live = False
    pipeline = None
    loop = None


def cb_message(bus, msg, data):
    def error():
        err, debug_info = msg.parse_error()
        print("Error: {0}".format(err))
        print("Debug info: {0}".format(debug_info))
        data.pipeline.set_state(Gst.State.READY)
        data.loop.quit()

    def eos():
        data.pipeline.set_state(Gst.State.READY)
        data.loop.quit()

    def buffering():
        percent = 0
        # If the stream is live, we do not care about buffering.
        if (data.is_live):
            return
        percent = msg.parse_buffering()
        sys.stdout.write("\rBuffering ({0}%)".format(percent))
        sys.stdout.flush()
        # Wait until buffering is complete before start/resume playing
        if (percent < 0):
            data.pipeline.set_state(Gst.State.PAUSED)
        else:
            data.pipeline.set_state(Gst.State.PLAYING)

    def clock_lost():
        # Get a new clock
        data.pipeline.set_state(Gst.State.PAUSED)
        data.pipeline.set_state(Gst.State.PLAYING)

    def default():
        pass

    handlers = dict({
        Gst.MessageType.ERROR: error,
        Gst.MessageType.EOS: eos,
        Gst.MessageType.BUFFERING: buffering,
        Gst.MessageType.CLOCK_LOST: clock_lost
    })
    if msg.type in handlers:
        handlers[msg.type]()


data = CustomData()
pipeline = Gst.parse_launch("playbin uri=http://docs.gstreamer.com/media/sintel_trailer-480p.webm")
bus = pipeline.get_bus()

# Start playing
ret = pipeline.set_state(Gst.State.PLAYING)
if (ret == Gst.StateChangeReturn.FAILURE):
    print("Unable to set pipeline to the playing state")
    exit(-1)
elif (ret == Gst.StateChangeReturn.NO_PREROLL):
    data.is_live = True

main_loop = GLib.MainLoop(None)
data.loop = main_loop
data.pipeline = pipeline

bus.add_signal_watch()
bus.connect("message", cb_message, data)
data.loop.run()

pipeline.set_state(Gst.State.PLAYING)
