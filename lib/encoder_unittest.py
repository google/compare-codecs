#!/usr/bin/python
# Copyright 2014 Google.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for encoder module."""

import os
import re
import shutil
import test_tools
import unittest

import encoder


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
    # rate is unused. This is known.
    # pylint: disable=W0613
    m = re.search(r'--score=(\d+)', parameters.ToString())
    if m:
      return {'psnr': int(m.group(1)), 'bitrate': 100}
    else:
      return {'psnr': -100, 'bitrate': 100}

def Returns1(target_bitrate, result):
  """Score function that returns a constant value."""
  # pylint: disable=W0613
  return 1.0


class StorageOnlyCodec(object):
  """A codec that is only useful for testing storage."""
  def __init__(self):
    self.name = 'unittest'
    self.option_set = encoder.OptionSet()
    self.option_formatter = encoder.OptionFormatter(prefix='--', infix=':')

  def SpeedGroup(self, bitrate):
    # pylint: disable=R0201
    return str(bitrate)

  def ConfigurationFixups(self, parameters):
    # pylint: disable=R0201
    return parameters

class StorageOnlyCodecWithNoBitrate(StorageOnlyCodec):
  def __init__(self):
    super(StorageOnlyCodecWithNoBitrate, self).__init__()
    self.name = 'merged-bitrate'

  def SpeedGroup(self, bitrate):
    # pylint: disable=R0201
    return 'all'


class StorageOnlyContext(object):
  """A context that is only useful for testing storage."""
  def __init__(self):
    self.codec = StorageOnlyCodec()
    self.cache = None


class DummyVideofile(encoder.Videofile):
  def __init__(self, filename, clip_time):
    super(DummyVideofile, self).__init__(filename)
    self.clip_time = clip_time

  def ClipTime(self):
    return self.clip_time


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

  def test_LockOption(self):
    opts = encoder.OptionSet(encoder.Option('foo', ['value1', 'value2']))
    self.assertEqual(2, len(opts.Option('foo').values))
    self.assertTrue(opts.Option('foo').CanChange())
    opts.LockOption('foo', 'value1')
    self.assertTrue(opts.Option('foo').mandatory)
    self.assertEqual(1, len(opts.Option('foo').values))
    self.assertFalse(opts.Option('foo').CanChange())

  def test_FindFlagOption(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo', 'bar']))
    self.assertIsNone(opts.FindFlagOption('baz'))
    self.assertEquals('foo/bar', opts.FindFlagOption('foo').name)

  def test_Format(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo', 'bar']))
    self.assertEquals('--foo', opts.Format('foo/bar', 'foo',
                                           encoder.OptionFormatter()))

  def test_Mandatory(self):
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo', 'bar']))
    self.assertFalse(opts.AllMandatoryOptions())
    opts = encoder.OptionSet(encoder.ChoiceOption(['foo', 'bar']).Mandatory())
    self.assertEquals(set([opt.name for opt in opts.AllMandatoryOptions()]),
                      set(['foo/bar']))


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
    # Check that old set is not modified.
    self.assertEqual('--foo', valueset.ToString())

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

  def test_RandomlyRemoveParameterSuccessfully(self):
    config = encoder.OptionValueSet(
        encoder.OptionSet(encoder.Option('foo', ['foo', 'bar'])),
        '--foo=foo')
    newconfig = config.RandomlyRemoveParameter()
    self.assertEqual('', newconfig.ToString())

  def test_RandomlyRemoveParameterWithOnlyMandatory(self):
    config = encoder.OptionValueSet(
        encoder.OptionSet(encoder.Option('foo', ['foo', 'bar']).Mandatory()),
        '--foo=foo')
    newconfig = config.RandomlyRemoveParameter()
    self.assertFalse(newconfig)


class TestCodec(unittest.TestCase):
  def setUp(self):
    self.videofile = DummyVideofile('foofile_640_480_30.yuv', clip_time=1)

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
  def test_OptionValues(self):
    codec = DummyCodec()
    my_encoder = encoder.Encoder(encoder.Context(codec),
      encoder.OptionValueSet(encoder.OptionSet(
            encoder.IntegerOption('score', 0, 100)), '--score=77'))
    self.assertEqual(repr(my_encoder.OptionValues()), "{'score': '77'}")
    self.assertEqual(my_encoder.DisplayValues(), '77')

  def test_ParametersCanBeStoredAndRetrieved(self):
    context = encoder.Context(DummyCodec())
    my_encoder = encoder.Encoder(context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    my_encoder.Store()
    filename = my_encoder.Hashname()
    next_encoder = encoder.Encoder(context, filename=filename)
    self.assertEqual(my_encoder.parameters, next_encoder.parameters)

  def test_ParametersCanChangeMayReturnTrue(self):
    context = encoder.Context(DummyCodec())
    my_encoder = encoder.Encoder(context,
        encoder.OptionValueSet(encoder.OptionSet(
            encoder.Option('key', ['value1', 'value2'])),
                               '--parameters'))
    self.assertTrue(my_encoder.ParametersCanChange())

  def test_ParametersCanChangeMayReturnFalse(self):
    context = encoder.Context(DummyCodec())
    my_encoder = encoder.Encoder(context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    self.assertFalse(my_encoder.ParametersCanChange())

  def testInitFromFile(self):
    context = encoder.Context(DummyCodec())
    my_encoder = encoder.Encoder(
        context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    my_encoder.Store()
    new_encoder = encoder.Encoder(context, filename=my_encoder.Hashname())
    self.assertEquals(new_encoder.parameters, my_encoder.parameters)

  def testInitFromBrokenFile(self):
    context = encoder.Context(DummyCodec())
    my_encoder = encoder.Encoder(
        context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    my_encoder.Store()
    # Break stored object. Note: This uses knowledge of the memory cache.
    old_filename = my_encoder.Hashname()
    parameters = context.cache.encoders[old_filename].parameters
    parameters.other_parts.append('--extra-stuff')
    # Now Hashname() should return a different value.
    with self.assertRaisesRegexp(encoder.Error, 'contains wrong arguments'):
      # pylint: disable=W0612
      new_encoder = encoder.Encoder(context, filename=old_filename)

class TestEncoding(unittest.TestCase):

  def testGenerateSomeUntriedVariants(self):
    context = encoder.Context(DummyCodec())
    my_encoder = context.codec.StartEncoder(context)
    videofile = DummyVideofile('foofile_640_480_30.yuv', clip_time=1)
    encoding = my_encoder.Encoding(1000, videofile)
    # The dummy codec has a parameter with multiple possible values,
    # so at least some variants should be returned.
    variants = encoding.SomeUntriedVariants()
    self.assertTrue(variants)

  def testGenerateUntriedVariantsUntilNoneFound(self):
    context = encoder.Context(DummyCodec())
    my_encoder = context.codec.StartEncoder(context)
    videofile = DummyVideofile('foofile_640_480_30.yuv', clip_time=1)
    encoding = my_encoder.Encoding(1000, videofile)
    variants = encoding.SomeUntriedVariants()
    # Keep generating variants until we run out. This should happen
    # after 3 variants for the Dummy codec.
    variant_count = 0
    while variants:
      for variant in variants:
        variant.Execute().Store()
        variant_count += 1
      variants = encoding.SomeUntriedVariants()
    # We cannot guarantee that all 3 are found, since the process
    # is random, but no more than 3 should be found.
    self.assertGreaterEqual(3, variant_count)

  def testReadResultWithoutFrameData(self):
    context = encoder.Context(DummyCodec())
    my_encoder = context.codec.StartEncoder(context)
    videofile = DummyVideofile('foofile_640_480_30.yuv', clip_time=1)
    encoding = my_encoder.Encoding(1000, videofile)
    encoding.result = {'foo': 5, 'frame': ['first', 'second']}
    self.assertEqual({'foo': 5}, encoding.ResultWithoutFrameData())


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
    cache = encoder.EncodingDiskCache(StorageOnlyContext())
    self.assertTrue(cache)

  def testStoreFetchEncoder(self):
    context = StorageOnlyContext()
    cache = encoder.EncodingDiskCache(context)
    my_encoder = encoder.Encoder(
        context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    cache.StoreEncoder(my_encoder)
    new_encoder_data = cache.ReadEncoderParameters(my_encoder.Hashname())
    self.assertEquals(new_encoder_data, my_encoder.parameters)

  def testStoreFetchEncoding(self):
    context = StorageOnlyContext()
    cache = encoder.EncodingDiskCache(context)
    my_encoder = encoder.Encoder(
        context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    cache.StoreEncoder(my_encoder)
    my_encoding = encoder.Encoding(my_encoder, 123,
                                   encoder.Videofile('x/foo_640_480_20.yuv'))
    testresult = {'foo': 'bar'}
    my_encoding.result = testresult
    cache.StoreEncoding(my_encoding)
    my_encoding.result = None
    result = cache.ReadEncodingResult(my_encoding)
    self.assertEquals(result, testresult)

  def testStoreMultipleEncodings(self):
    context = StorageOnlyContext()
    cache = encoder.EncodingDiskCache(context)
    # This particular test needs the context to know about the cache.
    context.cache = cache
    my_encoder = encoder.Encoder(
        context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
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
    self.assertEquals(2, len(result))
    result = cache.AllScoredEncodings(123, videofile)
    self.assertEquals(1, len(result))

  def testAllEncoderFilenames(self):
    context = StorageOnlyContext()
    cache = encoder.EncodingDiskCache(context)
    files = cache.AllEncoderFilenames()
    self.assertEquals(0, len(files))
    my_encoder = encoder.Encoder(
      context,
      encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    cache.StoreEncoder(my_encoder)
    files = cache.AllEncoderFilenames()
    self.assertEquals(1, len(files))
    self.assertEquals(my_encoder.Hashname(), files[0])

  def testRemoveEncoder(self):
    context = StorageOnlyContext()
    cache = encoder.EncodingDiskCache(context)
    my_encoder = encoder.Encoder(
      context,
      encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    cache.StoreEncoder(my_encoder)
    files = cache.AllEncoderFilenames()
    self.assertEquals(1, len(files))
    self.assertEquals(my_encoder.Hashname(), files[0])
    cache.RemoveEncoder(my_encoder.Hashname())
    files = cache.AllEncoderFilenames()
    self.assertEquals(0, len(files))

  def testReadResultFromAlternateDir(self):
    context = StorageOnlyContext()
    otherdir = os.path.join(os.environ['CODEC_WORKDIR'], 'otherdir')
    cache = encoder.EncodingDiskCache(context)
    my_encoder = encoder.Encoder(
        context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    cache.StoreEncoder(my_encoder)
    videofile = encoder.Videofile('x/foo_640_480_20.yuv')
    my_encoding = encoder.Encoding(my_encoder, 123, videofile)

    testresult = {'foo': 'bar'}
    my_encoding.result = testresult
    cache.StoreEncoding(my_encoding)
    my_encoding.result = None
    result = cache.ReadEncodingResult(my_encoding, scoredir=otherdir)
    self.assertIsNone(result)
    shutil.copytree(os.environ['CODEC_WORKDIR'], otherdir)
    result = cache.ReadEncodingResult(my_encoding, scoredir=otherdir)
    self.assertEquals(result, testresult)

  def testAllScoredEncodingsForEncoder(self):
    context = StorageOnlyContext()
    cache = encoder.EncodingDiskCache(context)
    # This particular test needs the context to know about the cache.
    context.cache = cache
    my_encoder = encoder.Encoder(
        context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
    cache.StoreEncoder(my_encoder)
    # Cache should start off empty.
    self.assertFalse(cache.AllScoredEncodingsForEncoder(my_encoder))
    videofile = encoder.Videofile('x/foo_640_480_20.yuv')
    my_encoding = encoder.Encoding(my_encoder, 123, videofile)
    testresult = {'foo': 'bar'}
    my_encoding.result = testresult
    cache.StoreEncoding(my_encoding)
    result = cache.AllScoredEncodingsForEncoder(my_encoder)
    self.assertTrue(result)
    self.assertEquals(1, len(result))
    # The resulting videofile should have a basename = filename,
    # because synthesizing filenames from result files loses directory
    # information.
    self.assertEquals('foo_640_480_20.yuv', result[0].videofile.filename)

  def testStorageWithMergedBitrates(self):
    context = StorageOnlyContext()
    context.codec = StorageOnlyCodecWithNoBitrate()
    cache = encoder.EncodingDiskCache(context)
    # This particular test needs the context to know about the cache.
    context.cache = cache
    my_encoder = encoder.Encoder(
        context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
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
    self.assertEquals(1, len(result))
    result = cache.AllScoredEncodings(123, videofile)
    self.assertEquals(1, len(result))



class TestEncodingMemoryCache(unittest.TestCase):
  def testStoreMultipleEncodings(self):
    context = StorageOnlyContext()
    cache = encoder.EncodingMemoryCache(context)
    # This particular test needs the context to know about the cache.
    context.cache = cache
    my_encoder = encoder.Encoder(
        context,
        encoder.OptionValueSet(encoder.OptionSet(), '--parameters'))
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
    self.assertEquals(2, len(result))
    result = cache.AllScoredEncodings(123, videofile)
    self.assertEquals(1, len(result))


if __name__ == '__main__':
  unittest.main()
