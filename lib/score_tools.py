#!/usr/bin/python
#
# Tools for evaluating metrics.
#

def PickScorer(name):
  # For now, just return KeyError if the scorer doesn't exist.
  scorer_map = {
    'psnr': ScorePsnrBitrate,
    'rt': ScoreCpuPsnr,
  }

  return scorer_map[name]

def ScorePsnrBitrate(target_bitrate, result):
  """Returns the score of a particular encoding result.

  Arguments:
  - target_bitrate: Desired bitrate in kilobits per second
  - result: a dictionary containing the analysis of the encoding.

  In this particular score function, the PSNR and the achieved bitrate
  of the encoding are of interest.
  """
  if not result:
    return None
  score = result['psnr']
  # We penalize bitrates that exceed the target bitrate.
  if result['bitrate'] > int(target_bitrate):
    score -= (result['bitrate'] - int(target_bitrate)) * 0.1
  return score

def ScoreCpuPsnr(target_bitrate, result):
  """Returns the score relevant to interactive usage.

  The constraints are:
  - Stay within the requested bitrate
  - Encode time needs to stay below clip length
  - Decode time needs to stay below clip length
  Otherwise, PSNR rules."""
  score = result['psnr']
  # We penalize bitrates that exceed the target bitrate.
  if result['bitrate'] > int(target_bitrate):
    score -= (result['bitrate'] - int(target_bitrate)) * 0.1
  # We penalize CPU usage that exceeds clip time.
  used_time = result['encode_cputime']
  available_time = result['cliptime']
  
  if used_time > available_time:
    badness = (used_time - available_time) / available_time
    score -= badness * 100
  return score

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
