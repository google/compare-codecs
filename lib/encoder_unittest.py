#!/usr/bin/python
"""Unit tests for encoder module."""

import unittest
import re

import encoder

class DummyCodec(encoder.Codec):
  def __init__(self):
    super(DummyCodec, self).__init__('dummy', encoder.EncodingMemoryCache(self))
    self.extension = 'fake'
    self.options = [
      encoder.Option('score',  ['0', '5', '10']),
      ]
    self.start_encoder = encoder.Encoder(self, "echo --score=5")

  def Execute(self, parameters, rate, videofile, workdir):
    m = re.search(r'--score=(\d+)', parameters)
    if m:
      return int(m.group(1))
    else:
      return -100

  def ScoreResult(self, target_bitrate, result):
    return result

class StorageOnlyCodec(object):
  """A codec that is only useful for testing storage."""
  def __init__(self):
    self.name = 'unittest'

  def SpeedGroup(self, bitrate):
    return str(bitrate)


class TestConfig(unittest.TestCase):
  def test_GetValue(self):
    config = '--foo=zoo'
    option = encoder.Option('foo', ['zoo', 'bar'])
    self.assertEqual(option.GetValue(config), 'zoo')

  def test_GetValueNotPresent(self):
    config = '--notfoo=foo'
    option = encoder.Option('foo', ['foo', 'bar'])
    with self.assertRaises(encoder.Error):
      option.GetValue(config)

  def test_SetValue(self):
    config = '--foo=foo'
    option = encoder.Option('foo', ['foo', 'bar'])
    self.assertEqual(option.SetValue(config, 'bar'), '--foo=bar')

  def test_PatchConfig(self):
    config = '--foo=foo'
    option = encoder.Option('foo', ['foo', 'bar'])
    newconfig = option.RandomlyPatchConfig(config)
    # There is only one possible change. It should be chosen.
    self.assertEqual(newconfig, '--foo=bar')

  def test_ChoiceOption(self):
    option = encoder.ChoiceOption(['foo', 'bar'])
    # Option occurs in the middle of the config.
    config = '--foo '
    newconfig = option.RandomlyPatchConfig(config)
    self.assertEqual(newconfig, '--bar ')
    # Option occurs at the end of the config.
    config = '--foo'
    newconfig = option.RandomlyPatchConfig(config)
    self.assertEqual(newconfig, '--bar')
    # Verify that prefixes are not matched.
    config = '--foobar --foo'
    newconfig = option.RandomlyPatchConfig(config)
    self.assertEqual(newconfig, '--foobar --bar')

  def test_IntegerOption(self):
    option = encoder.IntegerOption('foo', 5, 6)
    config = '--foo=5'
    self.assertEqual(option.RandomlyPatchConfig(config), '--foo=6')

  def test_ChoiceOption(self):
    config = '--foo'
    option = encoder.ChoiceOption(['foo', 'bar'])
    newconfig = option.RandomlyPatchConfig(config)
    self.assertEqual(newconfig, '--bar')


class TestCodec(unittest.TestCase):
  def setUp(self):
    self.videofile = encoder.Videofile('foofile_640_480_30.yuv')

  def test_FirstBestEncodingNoScore(self):
    codec = DummyCodec()
    encoding = codec.BestEncoding(100, self.videofile)
    self.assertIsNone(encoding.Score())

  def test_BestEncodingOneAlternative(self):
    codec = DummyCodec()
    codec.BestEncoding(100, self.videofile).Store()
    encoding = codec.BestEncoding(100, self.videofile)
    self.assertEqual(encoding.videofile, self.videofile)
  def test_BestEncodingExecuteGivesScore(self):
    codec = DummyCodec()
    codec.BestEncoding(100, self.videofile).Execute().Store()
    self.assertEqual(5, codec.BestEncoding(100, self.videofile).Score())

  def test_BestEncodingOtherSpeedNoScore(self):
    codec = DummyCodec()
    codec.BestEncoding(100, self.videofile).Execute().Store()
    self.assertIsNone(codec.BestEncoding(200, self.videofile).Score())

  def test_DisplayHeading(self):
    codec = DummyCodec()
    self.assertEqual('score', codec.DisplayHeading())

class TestEncoder(unittest.TestCase):
  def test_CreateStoreFetch(self):
    codec = DummyCodec()
    my_encoder = encoder.Encoder(codec, "parameters")
    my_encoder.Store()
    filename = my_encoder.Hashname()
    next_encoder = encoder.Encoder(codec, filename=filename)
    self.assertEqual(my_encoder.parameters, next_encoder.parameters)

  def test_OptionValues(self):
    codec = DummyCodec()
    my_encoder = encoder.Encoder(codec, '--score=77')
    self.assertEqual(repr(my_encoder.OptionValues()), "{'score': '77'}")
    self.assertEqual(my_encoder.DisplayValues(), '77')


class TestEncoding(unittest.TestCase):
  pass

class TestEncodingSet(unittest.TestCase):
  pass

class TestVideofile(unittest.TestCase):
  def testMpegFormatName(self):
    videofile = encoder.Videofile('test_640x480_20.yuv')
    self.assertEqual(640, videofile.width)
    self.assertEqual(480, videofile.height)
    self.assertEqual(20, videofile.framerate)

  def testMpegFormatWithTrailer(self):
    videofile = encoder.Videofile('test_640x480_20_part.yuv')
    self.assertEqual(640, videofile.width)
    self.assertEqual(480, videofile.height)
    self.assertEqual(20, videofile.framerate)

  def testGoogleFormatName(self):
    videofile = encoder.Videofile('test_640_480_20.yuv')
    self.assertEqual(640, videofile.width)
    self.assertEqual(480, videofile.height)
    self.assertEqual(20, videofile.framerate)

  def testBrokenName(self):
    with self.assertRaises(Exception):
      encoder.Videofile('no_numbers_here.yuv')


class TestEncodingDiskCache(unittest.TestCase):
  def testInit(self):
    cache = encoder.EncodingDiskCache(StorageOnlyCodec())

  def testStoreFetchEncoder(self):
    codec = StorageOnlyCodec()
    cache = encoder.EncodingDiskCache(codec)
    my_encoder = encoder.Encoder(codec, "parameters")
    cache.StoreEncoder(my_encoder)
    new_encoder_data = cache.ReadEncoderParameters(my_encoder.Hashname())
    self.assertEquals(new_encoder_data, my_encoder.parameters)

  def testStoreFetchEncoding(self):
    codec = StorageOnlyCodec()
    cache = encoder.EncodingDiskCache(codec)
    my_encoder = encoder.Encoder(codec, "parameters")
    cache.StoreEncoder(my_encoder)
    my_encoding = encoder.Encoding(my_encoder, 123,
                                   encoder.Videofile('x/foo_640_480_20.yuv'))
    testresult = {'foo': 'bar'}
    my_encoding.result = testresult
    cache.StoreEncoding(my_encoding)
    my_encoding.result = None
    cache.ReadEncodingResult(my_encoding)
    self.assertEquals(my_encoding.result, testresult)

if __name__ == '__main__':
    unittest.main()
