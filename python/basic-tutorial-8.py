#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Basic tutorial 8: Short-cutting the pipeline
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+8%3A+Short-cutting+the+pipeline
"""
import sys
from array import array
import gi

gi.require_version('GLib', '2.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstAudio', '1.0')

from gi.repository import GLib, GstAudio
from gi.repository import Gst

Gst.init(sys.argv)

# GC object already tracked
# http://stackoverflow.com/questions/7496629/gstreamer-appsrc-causes-random-crashes
# gobject.threads_init()

CHUNK_SIZE = 1024  # Amount of bytes we are sending in each buffer
SAMPLE_RATE = 44100  # Samples per second we are sending


# Structure to contain all our information, so we can pass it to callbacks
class CustomData:
    pipeline = None
    app_source = None
    tee = None
    audio_queue = None
    audio_convert1 = None
    audio_resample = None
    audio_sink = None
    video_queue = None
    audio_convert2 = None
    visual = None
    video_convert = None
    video_sink = None
    app_queue = None
    app_sink = None
    num_samples = 0
    a = 0.0
    b = 0.0
    c = 0.0
    d = 0.0
    sourceid = 0
    main_loop = None


# This method is called by the idle GSource in the mainloop,
# to feed CHUNK_SIZE bytes into appsrc.
# The idle handler is added to the mainloop
# when appsrc requests us to start sending data (need-data signal)
# and is removed when appsrc has enough data (enough-data signal)
def push_data(data):
    num_samples = CHUNK_SIZE // 2  # Because each sample is 16 bits

    # Generate some psychodelic waveforms
    data.c += data.d
    data.d -= data.c / 1000.0
    freq = 1100.0 + 1000.0*data.d

    # version 2, using array
    raw = array('H')
    for i in range(num_samples):
        data.a += data.b
        data.b -= data.a / freq
        a5 = (int(500 * data.a)) % 65535
        raw.append(a5)
    b_data = raw.tostring()

    data.num_samples += num_samples
    buffer = Gst.Buffer.new_wrapped(b_data)

    # Set its timestamp and duration
    buffer.timestamp = Gst.util_uint64_scale(
        data.num_samples, Gst.SECOND, SAMPLE_RATE)
    buffer.duration = Gst.util_uint64_scale(
        CHUNK_SIZE, Gst.SECOND, SAMPLE_RATE)

    # Push the buffer into the appsrc
    ret = data.app_source.emit("push-buffer", buffer)
    if (ret != Gst.FlowReturn.OK):
        return False
    return True


# This signal callback triggers when appsrc needs data.
# Here, we add an idle handler
# to the mainloop to start pushing data into the appsrc
def start_feed(source, size, data):
    if (data.sourceid == 0):
        print("Start feeding")
        data.sourceid = GLib.idle_add(push_data, data)


# This callback triggers when appsrc has enough data and we can stop sending.
# We remove the idle handler from the mainloop
def stop_feed(source, data):
    if (data.sourceid != 0):
        print("Stop feeding")
        GLib.source_remove(data.sourceid)
        data.sourceid = 0


# The appsink has received a buffer
def new_buffer(sink, data):
    # Retrieve the buffer
    buffer = sink.emit("pull-sample")
    if (buffer):
        # The only thing we do in this example is
        # print a * to indicate a received buffer
        print("*", end=" ")
    return False


# This function is called when an error message is posted on the bus
def error_cb(bus, msg, data):
    err, debug_info = msg.parse_error()
    print("Error received from element {}: {}".format(msg.src.get_name(), err))
    print("Debugging information: {}".format(debug_info))
    data.pipeline.set_state(Gst.State.READY)
    data.main_loop.quit()


data = CustomData()
# Initialize custom data structure
data.a = 0.0
data.b = 1.0
data.c = 0.0
data.d = 1.0

# Create the elements
data.app_source = Gst.ElementFactory.make("appsrc", "app_source")
data.tee = Gst.ElementFactory.make("tee", "tee")
data.audio_queue = Gst.ElementFactory.make("queue", "audio_queue")
data.audio_convert1 = Gst.ElementFactory.make("audioconvert", "audio_convert1")
data.audio_resample = Gst.ElementFactory.make("audioresample", "audio_resample")
data.audio_sink = Gst.ElementFactory.make("autoaudiosink", "audio_sink")
data.video_queue = Gst.ElementFactory.make("queue", "video_queue")
data.audio_convert2 = Gst.ElementFactory.make("audioconvert", "audio_convert2")
data.visual = Gst.ElementFactory.make("wavescope", "visual")
data.video_convert = Gst.ElementFactory.make("videoconvert", "csp")
data.video_sink = Gst.ElementFactory.make("autovideosink", "video_sink")
data.app_queue = Gst.ElementFactory.make("queue", "app_queue")
data.app_sink = Gst.ElementFactory.make("appsink", "app_sink")

# Create empty pipeline
data.pipeline = Gst.Pipeline.new("test-pipeline")

if (not data.app_source or not data.tee or not data.audio_queue
        or not data.audio_convert1 or not data.audio_resample
        or not data.audio_sink or not data.video_queue
        or not data.audio_convert2 or not data.visual
        or not data.video_convert or not data.video_sink
        or not data.app_queue or not data.app_sink
        or not data.pipeline):
    print("Not all elements could be created.")
    exit(-1)

# exit()
# Configure wavescope
data.visual.set_property("shader", 0)
data.visual.set_property("style", 1)

# Configure appsrc
info = GstAudio.AudioInfo()
info.set_format(
    format=GstAudio.AudioFormat.S16,
    rate=SAMPLE_RATE,
    channels=1,
    position=None
)
data.app_source.set_property("caps", info.to_caps())
data.app_source.connect("need-data", start_feed, data)
data.app_source.connect("enough-data", stop_feed, data)

# Configure appsink
data.app_sink.set_property("emit-signals", True)
data.app_sink.set_property("caps", info.to_caps())
data.app_sink.connect("new-sample", new_buffer, data)

# Link all elements that can be
# automatically linked because they have "Always" pads
data.pipeline.add(data.app_source)
data.pipeline.add(data.tee)
data.pipeline.add(data.audio_queue)
data.pipeline.add(data.audio_convert1)
data.pipeline.add(data.audio_resample)
data.pipeline.add(data.audio_sink)
data.pipeline.add(data.video_queue)
data.pipeline.add(data.audio_convert2)
data.pipeline.add(data.visual)
data.pipeline.add(data.video_convert)
data.pipeline.add(data.video_sink)
data.pipeline.add(data.app_queue)
data.pipeline.add(data.app_sink)

ret = data.app_source.link(data.tee)
# Pipeline 1:
ret = ret and data.tee.link(data.audio_queue)
ret = ret and data.audio_queue.link(data.audio_convert1)
ret = ret and data.audio_convert1.link(data.audio_resample)
ret = ret and data.audio_resample.link(data.audio_sink)

# Pipeline 2:
ret = ret and data.tee.link(data.video_queue)
ret = ret and data.video_queue.link(data.audio_convert2)
ret = ret and data.audio_convert2.link(data.visual)
ret = ret and data.visual.link(data.video_convert)
ret = ret and data.video_convert.link(data.video_sink)

# Pipeline 3:
ret = ret and data.tee.link(data.app_queue)
ret = ret and data.app_queue.link(data.app_sink)

if not ret:
    print("Elements could not be linked.")
    exit(-1)

# Start playing the pipeline
data.pipeline.set_state(Gst.State.PLAYING)

# Instruct the bus to emit signals for each received
# message, and connect to the interesting signals
bus = data.pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message::error", error_cb, data)

# Create a GLib Mainloop and set it to run
data.main_loop = GLib.MainLoop()
data.main_loop.run()

# Free resources
data.pipeline.set_state(Gst.State.NULL)
exit()
