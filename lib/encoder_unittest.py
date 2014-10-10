#!/usr/bin/python
"""Unit tests for encoder module."""

import test_tools
import re
import unittest

import encoder


class DummyCodec(encoder.Codec):
  def __init__(self):
    super(DummyCodec, self).__init__('dummy', encoder.EncodingMemoryCache(self))
    self.extension = 'fake'
    self.option_set = encoder.OptionSet(
      encoder.Option('score',  ['0', '5', '10']),
    )

  def StartEncoder(self):
    return encoder.Encoder(self, encoder.OptionValueSet(self.option_set,
                                                        "--score=5"))

  def Execute(self, parameters, rate, videofile, workdir):
    # rate is unused. This is known.
    # pylint: disable=W0613
    m = re.search(r'--score=(\d+)', parameters.ToString())
    if m:
      return {'psnr': int(m.group(1)), 'bitrate': 100}
    else:
      return {'psnr': -100, 'bitrate': 100}


class StorageOnlyCodec(object):
  """A codec that is only useful for testing storage."""
  def __init__(self):
    self.name = 'unittest'
    self.cache = None
    self.option_set = encoder.OptionSet()
    self.option_formatter = encoder.OptionFormatter(prefix='--', infix=':')

  def SpeedGroup(self, bitrate):
    # pylint: disable=R0201
    return str(bitrate)

  def ConfigurationFixups(self, parameters):
    # pylint: disable=R0201
    return parameters


class TestConfig(unittest.TestCase):

  def test_ChoiceOption(self):
    option = encoder.ChoiceOption(['foo', 'bar'])
    # Check FlagIsValidValue function.
    self.assertFalse(option.FlagIsValidValue('baz'))
    self.assertTrue(option.FlagIsValidValue('foo'))

  def test_IntegerOption(self):
    option = encoder.IntegerOption('foo', 5, 6)
    self.assertTrue(str(6) in option.values)
    self.assertFalse(str(4) in option.values)


class TestOptionSet(unittest.TestCase):
  def test_InitNoArgs(self):
    opts = encoder.OptionSet()
    self.assertFalse(opts.HasOption('foo'))

  def test_InitSingle(self):
    opts = encoder.OptionSet(encoder.Option('foo', ['foo', 'bar']))
    self.assertTrue(opts.Option('foo'))
    self.assertFalse(opts.HasOption('bar'))

  def test_InitMany(self):
    opts = encoder.OptionSet(encoder.Option('foo', ['foo', 'bar']),
                             encoder.Option('bar', ['bar', 'baz']))
    self.assertTrue(opts.Option('foo'))
    self.assertTrue(opts.Option('bar'))
    self.assertFalse(opts.HasOption('baz'))

  def test_RegisterOption(self):
    opts = encoder.OptionSet()
    self.assertFalse(opts.HasOption('foo'))
    opts.RegisterOption(encoder.Option('foo', ['foo', 'bar']))
    self.assertTrue(opts.HasOption('foo'))
    self.assertTrue(opts.Option('foo'))

  def test_FindFlagOption(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo', 'bar']))
    self.assertIsNone(opts.FindFlagOption('baz'))
    self.assertEquals('foo/bar', opts.FindFlagOption('foo').name)

  def test_Format(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo', 'bar']))
    self.assertEquals('--foo', opts.Format('foo/bar', 'foo',
                                           encoder.OptionFormatter()))


class TestOptionValueSet(unittest.TestCase):
  def test_ReproduceOneArg(self):
    valueset = encoder.OptionValueSet(encoder.OptionSet(), '--foo=bar')
    self.assertEqual('--foo=bar', valueset.ToString())

  def test_GetValue(self):
    valueset = encoder.OptionValueSet(
      encoder.OptionSet(encoder.Option('foo', ['baz', 'bar'])), '--foo=bar')
    self.assertEqual('bar', valueset.GetValue('foo'))

  def test_GetValueNotPresent(self):
    option = encoder.Option('foo', ['foo', 'bar'])
    config = encoder.OptionValueSet(encoder.OptionSet(option), '--notfoo=foo')
    with self.assertRaises(encoder.Error):
      config.GetValue('foo')

  def test_ReproduceFlag(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo']))
    valueset = encoder.OptionValueSet(opts, '--foo')
    self.assertEqual('--foo', valueset.ToString())

  def test_UnknownFlagPreserved(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo']))
    valueset = encoder.OptionValueSet(opts, '--bar')
    self.assertEqual('--bar', valueset.ToString())

  def test_FlagsSorted(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo']))
    valueset = encoder.OptionValueSet(opts, '--foo --bar')
    self.assertEqual('--bar --foo', valueset.ToString())

  def test_ChangeValue(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo', 'bar']))
    valueset = encoder.OptionValueSet(opts, '--foo')
    newset = valueset.ChangeValue('foo/bar', 'bar')
    self.assertEqual('--bar', newset.ToString())

  def test_ChangeValueOfUnknownOption(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo', 'bar']))
    valueset = encoder.OptionValueSet(opts, '--foo')
    with self.assertRaises(encoder.Error):
      # pylint: disable=W0612
      newset = valueset.ChangeValue('nosuchname', 'bar')

  def test_RandomlyPatchConfig(self):
    config = encoder.OptionValueSet(
      encoder.OptionSet(encoder.Option('foo', ['foo', 'bar'])),
      '--foo=foo')
    newconfig = config.RandomlyPatchConfig()
    # There is only one possible change. It should be chosen.
    self.assertEqual(newconfig.ToString(), '--foo=bar')
    # Test case where original set did not have value.
    config = encoder.OptionValueSet(
      encoder.OptionSet(encoder.Option('foo', ['foo', 'bar'])),
      '')
    newconfig = config.RandomlyPatchConfig()
    self.assertIn(newconfig.ToString(), ['--foo=foo', '--foo=bar'])

  def test_OtherFormatter(self):
    valueset = encoder.OptionValueSet(
      encoder.OptionSet(encoder.Option('foo', ['foo', 'bar'])),
      '-foo foo',
      formatter=encoder.OptionFormatter(prefix='-', infix=' '))
    self.assertEqual('-foo foo', valueset.ToString())
    valueset = encoder.OptionValueSet(
      encoder.OptionSet(encoder.Option('foo', ['foo', 'bar']),
                        encoder.Option('xyz', ['abc', 'def'])),
      '-foo foo -xyz abc',
      formatter=encoder.OptionFormatter(prefix='-', infix=' '))
    self.assertEqual('-foo foo -xyz abc', valueset.ToString())


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

  def test_RandomlyChangeConfig(self):
    codec = DummyCodec()
    otherconfig = codec.RandomlyChangeConfig(
      encoder.OptionValueSet(codec.option_set, '--score=5'))
    self.assertNotEqual(otherconfig, '--score=5')
    self.assertIn(otherconfig, ['--score=0', '--score=10'])

  def test_FormatterExists(self):
    codec = DummyCodec()
    self.assertTrue(codec.option_formatter)


class TestEncoder(unittest.TestCase):
  def test_CreateStoreFetch(self):
    codec = DummyCodec()
    my_encoder = encoder.Encoder(
        codec, encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    my_encoder.Store()
    filename = my_encoder.Hashname()
    next_encoder = encoder.Encoder(codec, filename=filename)
    self.assertEqual(my_encoder.parameters, next_encoder.parameters)

  def test_OptionValues(self):
    codec = DummyCodec()
    my_encoder = encoder.Encoder(
        codec, encoder.OptionValueSet(encoder.OptionSet(
            encoder.IntegerOption('score', 0, 100)), '--score=77'))
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


class TestEncodingDiskCache(test_tools.FileUsingCodecTest):
  def testInit(self):
    cache = encoder.EncodingDiskCache(StorageOnlyCodec())
    self.assertTrue(cache)

  def testStoreFetchEncoder(self):
    codec = StorageOnlyCodec()
    cache = encoder.EncodingDiskCache(codec)
    my_encoder = encoder.Encoder(
        codec, encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    cache.StoreEncoder(my_encoder)
    new_encoder_data = cache.ReadEncoderParameters(my_encoder.Hashname())
    self.assertEquals(new_encoder_data, my_encoder.parameters)

  def testStoreFetchEncoding(self):
    codec = StorageOnlyCodec()
    cache = encoder.EncodingDiskCache(codec)
    my_encoder = encoder.Encoder(
        codec, encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    cache.StoreEncoder(my_encoder)
    my_encoding = encoder.Encoding(my_encoder, 123,
                                   encoder.Videofile('x/foo_640_480_20.yuv'))
    testresult = {'foo': 'bar'}
    my_encoding.result = testresult
    cache.StoreEncoding(my_encoding)
    my_encoding.result = None
    cache.ReadEncodingResult(my_encoding)
    self.assertEquals(my_encoding.result, testresult)

  def testStoreMultipleEncodings(self):
    # TODO: Clear disk cache before test.
    # This test is sensitive to old data left around.
    codec = StorageOnlyCodec()
    cache = encoder.EncodingDiskCache(codec)
    codec.cache = cache  # This particular test needs the link.
    my_encoder = encoder.Encoder(
        codec, encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    cache.StoreEncoder(my_encoder)
    videofile = encoder.Videofile('x/foo_640_480_20.yuv')
    my_encoding = encoder.Encoding(my_encoder, 123, videofile)

    testresult = {'foo': 'bar'}
    my_encoding.result = testresult
    cache.StoreEncoding(my_encoding)
    my_encoding = encoder.Encoding(my_encoder, 246, videofile)
    my_encoding.result = testresult
    cache.StoreEncoding(my_encoding)
    result = cache.AllScoredRates(my_encoder, videofile)
    self.assertEquals(2, len(result.encodings))
    result = cache.AllScoredEncodings(123, videofile)
    self.assertEquals(1, len(result.encodings))


class TestEncodingFunctions(unittest.TestCase):

  def test_ScoreResult(self):
    result = {'bitrate': 100, 'psnr': 10.0}
    self.assertEqual(10.0, encoder.ScoreResult(100, result))
    self.assertEqual(10.0, encoder.ScoreResult(1000, result))
    # Score is reduced by 0.1 per kbps overrun.
    self.assertAlmostEqual(10.0 - 0.1, encoder.ScoreResult(99, result))
    # Score floors at 0.1 for very large overruns.
    self.assertAlmostEqual(0.1, encoder.ScoreResult(1, result))
    self.assertFalse(encoder.ScoreResult(100, None))


if __name__ == '__main__':
  unittest.main()
