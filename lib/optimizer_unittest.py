#!/usr/bin/python
#
# Unit tests for the optimizer.
#
import re
import unittest

import encoder
import optimizer

class DummyCodec(encoder.Codec):
  def __init__(self):
    super(DummyCodec, self).__init__('dummy')
    self.extension = 'fake'
    self.option_set = encoder.OptionSet(
      encoder.Option('score',  ['0', '5', '10']),
    )

  def StartEncoder(self, context):
    return encoder.Encoder(context,
                           encoder.OptionValueSet(self.option_set,
                                                  "--score=5"))

  def Execute(self, parameters, rate, videofile, workdir):
    # pylint: disable=W0613
    m = re.search(r'--score=(\d+)', parameters.ToString())
    if m:
      return {'psnr': int(m.group(1)), 'bitrate': 100}
    else:
      return {'psnr': -100, 'bitrate': 100}


class DummyVideofile(encoder.Videofile):
  def __init__(self, filename, clip_time):
    super(DummyVideofile, self).__init__(filename)
    self.clip_time = clip_time

  def ClipTime(self):
    return self.clip_time


def Returns1(target_bitrate, result):
  """Score function that returns a constant value."""
  # pylint: disable=W0613
  return 1.0

def ReturnsClipTime(target_bitrate, result):
  # pylint: disable=W0613
  return float(result['cliptime'])


class TestOptimizer(unittest.TestCase):
  def setUp(self):
    self.codec = DummyCodec()
    self.file_set = None
    self.cache_class = encoder.EncodingMemoryCache
    self.score_function = None
    self.videofile = DummyVideofile('foofile_640_480_30.yuv', clip_time=1)

  def StdOptimizer(self):
    return optimizer.Optimizer(self.codec, self.file_set,
                               cache_class=self.cache_class)

  def testInit(self):
    optimizer.Optimizer(self.codec, self.file_set,
                        cache_class=self.cache_class)

  def test_AlternateScorer(self):
    my_optimizer = optimizer.Optimizer(self.codec, self.file_set,
                                       cache_class=self.cache_class,
                                       score_function=Returns1)
    my_optimizer.BestEncoding(100, self.videofile).Execute().Store()
    self.assertEqual(1,
        my_optimizer.Score(my_optimizer.BestEncoding(100, self.videofile)))

  def test_FirstBestEncodingNoScore(self):
    my_optimizer = self.StdOptimizer()
    encoding = my_optimizer.BestEncoding(100, self.videofile)
    self.assertIsNone(encoding.Result())

  def test_BestEncodingOneAlternative(self):
    my_optimizer = self.StdOptimizer()
    my_optimizer.BestEncoding(100, self.videofile).Store()
    encoding = my_optimizer.BestEncoding(100, self.videofile)
    self.assertEqual(encoding.videofile, self.videofile)

  def test_BestEncodingExecuteGivesScore(self):
    my_optimizer = self.StdOptimizer()
    my_optimizer.BestEncoding(100, self.videofile).Execute().Store()
    self.assertEqual(5, my_optimizer.Score(
        my_optimizer.BestEncoding(100, self.videofile)))

  def test_BestEncodingOtherSpeedNoScore(self):
    my_optimizer = self.StdOptimizer()
    my_optimizer.BestEncoding(100, self.videofile).Execute().Store()
    self.assertIsNone(my_optimizer.BestEncoding(200, self.videofile).Result())

  def test_AutoGenerateClipTime(self):
    context = optimizer.Optimizer(self.codec, self.file_set,
                                  cache_class=self.cache_class,
                                  score_function=ReturnsClipTime)
    my_encoder = encoder.Encoder(context,
        encoder.OptionValueSet(encoder.OptionSet(), ''))
    # Must use a tricked-out videofile to avoid disk access.
    videofile = DummyVideofile('test_640x480_20.yuv', clip_time=1)
    my_encoding = encoder.Encoding(my_encoder, 123, videofile)
    my_encoding.result = {'psnr':42, 'bitrate':123}
    # If cliptime is not present, this will raise an exception.
    context.Score(my_encoding)


if __name__ == '__main__':
  unittest.main()
