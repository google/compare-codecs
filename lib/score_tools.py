#!/usr/bin/python
#
# Tools for evaluating metrics.
#

def DelayCalculation(frame_info_list, framerate, bitrate, buffer_size,
                     print_trace=False):
  """Calculate the total delay in frame delivery for these frames.
  Arguments:
  - frame_info_list: a list of frame information records.
      Each frame information record has the size in bits in the "size" field
  - framerate: frames per second
  - bitrate: integer, bits per second
  - buffer_size: Initial buffer size, in seconds
  Returns:
  Delay as a proportion of total clip time - that is, if the clip is 10s
  long, and the function returns 0.2, the clip will take 12 seconds to play.
  """
  for frame in frame_info_list:
    frame['transmit_time'] = float(frame['size']) / bitrate
  playback_clock = buffer_size
  buffer_clock = 0
  delay = 0
  frame_count = 0
  for frame in frame_info_list:
    buffer_clock += frame['transmit_time'] # time this frame arrives
    playback_clock += 1.0/framerate # time this frame should be played back
    if buffer_clock > playback_clock:
      delay += (buffer_clock - playback_clock)
      if print_trace:
        print 'Frame %d %f behind' % (frame_count,
                                      buffer_clock - playback_clock)
      # In this model, we assume that playback pauses until frame is available.
      # No further delay penalty is imposed on the next frame.
      playback_clock = buffer_clock
    frame_count += 1
  return delay / (float(frame_count) / framerate)
