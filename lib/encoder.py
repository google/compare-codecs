"""Encoder and related classes.

This file contains classes that generically define the idea of a codec,
an encoder, an option and so forth.

A codec is a generic mechanism for processing an .yuv file and returning
a score. Given a set of options, a file and a rate, it can produce an encoder.
The codec has a set of options that can have varying values.

An encoder is a codec with a given set of options.

An encoding is an encoder applied to a given filename and target bitrate.

A variant is an encoder with at least one option changed.

This module uses two external variables:

os.getenv(CODEC_WORKDIR) gives the place where data is stored.
os.getenv(CODEC_TOOLPATH) gives the directory of encoder/decoder tools.
"""

import ast
import glob
import md5
import os
import random
import re


class Error(Exception):
  pass

def Tool(name):
  return os.path.join(os.getenv('CODEC_TOOLPATH'), name)


class Option(object):
  """This class represents an option given to an encoder.

  Typically the command line representation is "--name=value".
  This class provides functions to modify an option in a command line string.
  """
  def __init__(self, name, values=[]):
    # The default value is never changed, so it's safe to use [] here.
    # pylint: disable=W0102
    self.name = name
    self.values = frozenset(values)

  def CanChange(self):
    return len(self.values) > 1

  def PickAnother(self, not_this):
    """Find a new value for the option, different from not_this.
    not_this doesn't have to be a member of the values list, but can be.
    """
    assert(self.CanChange)
    rest = list(self.values - set([not_this]))
    return rest[random.randint(0, len(rest) - 1)]

  def OptionString(self, value):
    return '--%s=%s' % (self.name, value)

  def _OptionSearchExpression(self):
    return r'--%s=(\S+)' % self.name

  def FlagIsValidValue(self, flag):
    """ Return true if a flag can represent a value of this option.
    Overridden by ChoiceOption. """
    # pylint: disable=W0613, R0201
    return False

  def Format(self, value, formatter):
    return formatter.Format(self.name, value)


class ChoiceOption(Option):
  """This class represents a set of exclusive options (without values).

  One example is the --good, --best option to vpxenc.
  The "name" of this option is a concatenation of the set of legal values.
  """
  def __init__(self, flags):
    # The name is just for output, it does not affect the behaviour
    # of the program.
    super(ChoiceOption, self).__init__('/'.join(flags), flags)

  def OptionString(self, value):
    return '--%s' % value

  def FlagIsValidValue(self, value):
    return (value in self.values)

  def Format(self, value, formatter):
    return formatter.Format(value, None)


class IntegerOption(Option):
  """This class represents an option with a range of values.
  """
  def __init__(self, name, min_in, max_in):
    """Note that the value of the max parameter is included in the set."""
    super(IntegerOption, self).__init__(
      name, [str(s) for s in xrange(min_in, max_in+1)])
    self.min = min_in
    self.max = max_in


class DummyOption(Option):
  """This class represents an option that cannot be set by
  OptionValueSet.RandomlyChangeConfig, but can be set by
  OptionValueSet.ChangeValue."""

  def __init__(self, name):
    super(DummyOption, self).__init__(name, [])

  def CanChange(self):
    return False


class OptionSet(object):
  """A set of option definitions.
  Together, these constitute all possible variation dimensions for a codec.
  """
  def __init__(self, *args):
    self.options = {}
    for arg in args:
      self.RegisterOption(arg)

  def RegisterOption(self, option):
    self.options[option.name] = option

  def Option(self, name):
    return self.options[name]

  def HasOption(self, name):
    return name in self.options

  def AllOptions(self):
    return self.options.values()

  def AllChangeableOptions(self):
    return [option for option in self.AllOptions() if option.CanChange()]

  def FindFlagOption(self, flag):
    for name in self.options:
      if self.options[name].FlagIsValidValue(flag):
        return self.options[name]
    return None

  def Format(self, name, value, formatter):
    return self.options[name].Format(value, formatter)


class OptionFormatter(object):
  """Formatter for the command line form of an option.

  Intended to be called by the option class in order to format
  in a codec-specific fashion.
  This class is used as a default argument, so needs to be immutable."""

  def __init__(self, prefix='--', infix='='):
    self.prefix = prefix
    self.infix = infix

  def Format(self, name, value):
    if value is None:
      return '%s%s' % (self.prefix, name)
    else:
      return '%s%s%s%s' % (self.prefix, name, self.infix, value)


class OptionValueSet(object):
  """Values for a set of options.

  The values are immutable.
  This class knows how to parse the set from a string (via an injected
  formatter module + an OptionSet for the names), and how to generate
  a string from the set of values.
  """
  def __init__(self, option_set, string, formatter=OptionFormatter()):
    """Initialization.
    Arguments:
    option_set - OptionSet, the set of parseable names and flags
    string - all the values, in "--name=value --flag" format
    formatter - OptionFormatter that gives the prefix and infix separators
    """

    self.option_set = option_set
    self.formatter = formatter
    self.values = {}
    self.other_parts = []
    for flag in string.split():
      m = re.match(r'%s([^%s]*)(%s)?' % (formatter.prefix, formatter.infix[0:1],
                                         formatter.infix),
                   flag)
      if m:
        if self._HandleNameValueFlag(m):
          continue
        if self._HandleChoiceFlag(m):
          continue
      # It is not a known name=value or a known flag.
      # Remember it, but don't make it available for manipulation.
      self.other_parts.append(flag)

  def _HandleNameValueFlag(self, m):
    name = m.group(1)
    if m.group(2) and self.option_set.HasOption(name):
      # Known name=value option.
      name = m.group(1)
      value = m.string[m.end():]
      self.values[name] = value
      return True
    return False

  def _HandleChoiceFlag(self, m):
    option = self.option_set.FindFlagOption(m.group(1))
    if option:
      # Known flag option (no value)
      self.values[option.name] = m.group(1)
      return True
    return False

  def ToString(self):
    # ToString returns parts in sorted order, for consistency.
    parts = [self.option_set.Format(name, value, self.formatter)
                       for name, value in self.values.iteritems()]
    return ' '.join(sorted(parts + self.other_parts))

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.ToString() == other.ToString()
    else:
      # If the other is something that can be used to construct an OVS,
      # accept it. (This may reorder options.)
      return self == OptionValueSet(self.option_set, other)

  def GetValue(self, name):
    try:
      return self.values[name]
    except KeyError:
      raise Error('No value for option %s' % name)

  def ChangeValue(self, name, value):
    """Return an OptionValueSet with the specified parameter changed."""
    if not self.option_set.HasOption(name):
      raise Error('Unknown option name %s' % name)
    new_set = OptionValueSet(self.option_set, "", self.formatter)
    new_set.values = self.values
    new_set.values[name] = value
    new_set.other_parts = self.other_parts
    return new_set

  def RandomlyPatchOption(self, option):
    """ Modify a configuration by changing the value of this option."""
    newconfig = self.ChangeValue(option.name,
                                 option.PickAnother(self.GetValue(option.name)))
    assert(self != newconfig)
    return newconfig

  def RandomlyPatchConfig(self):
    """ Modify a configuration by changing the value of a random parameter."""
    options = self.option_set.AllChangeableOptions()
    assert(len(options) >= 1)
    option_to_change = options[random.randint(0, len(options)-1)]
    return self.RandomlyPatchOption(option_to_change)


class Videofile(object):
  def __init__(self, filename):
    """ Parse the file name to find width, height and framerate. """
    self.filename = filename
    m = re.search(r'_(\d+)x(\d+)_(\d+)', filename)
    if m:
      self.width = int(m.group(1))
      self.height = int(m.group(2))
      self.framerate = int(m.group(3))
    else:
      m = re.search(r'_(\d+)_(\d+)_(\d+).yuv$', filename)
      if m:
        self.width = int(m.group(1))
        self.height = int(m.group(2))
        self.framerate = int(m.group(3))
      else:
        raise Error("Unable to parse filename " + filename)
    self.basename = os.path.splitext(os.path.basename(filename))[0]

  def MeasuredBitrate(self, encodedsize):
    """Returns bitrate of an encoded file in kilobits per second.

    Argument: Encoded file size in bytes.
    """
    # YUV is 8 bits per pixel for Y, 1/4 that for each of U and V.
    framesize = self.width * self.height * 3 / 2
    framecount = os.path.getsize(self.filename) / framesize
    encodedframesize = encodedsize / framecount
    return encodedframesize * self.framerate * 8 / 1000

class Codec(object):
  """Abstract class representing a codec.

  Subclasses must define the options and start_encoder variables
  """
  def __init__(self, name, cache=None):
    self.name = name
    self.option_set = OptionSet()
    if cache:
      self.cache = cache
    else:
      self.cache = EncodingDiskCache(self)

  def Option(self, name):
    return self.option_set.Option(name)

  def AllOptions(self):
    return self.option_set.AllOptions()

  def StartEncoder(self):
    # pylint: disable=R0201
    raise Error("The base codec class has no start encoder")

  def AllScoredEncodings(self, bitrate, videofile):
    return self.cache.AllScoredEncodings(bitrate, videofile)

  def BestEncoding(self, bitrate, videofile):
    encodings = self.AllScoredEncodings(bitrate, videofile)
    if not encodings.Empty():
      return encodings.BestEncoding()
    else:
      return self.StartEncoder().Encoding(bitrate, videofile)

  def Execute(self, parameters, bitrate, videofile, workdir):
    # pylint: disable=W0613, R0201
    raise Error("The base codec class can't execute anything")

  def ConfigurationFixups(self, config):
    """Hook for applying inter-parameter tweaks."""
    # pylint: disable=R0201
    return config

  def RandomlyChangeConfig(self, parameters):
    return self.ConfigurationFixups(parameters.RandomlyPatchConfig())

  def SpeedGroup(self, bitrate):
    """Return the speed group of a bitrate.
    Intended for making subdirectories to search in when finding
    reasonable encoders to try.
    The default is to have one directory per target bitrate, since
    encodings with different target bitrates will be different."""
    # pylint: disable=R0201
    return str(bitrate)

  def SuggestTweak(self, encoding):
    """Suggest a tweaked encoder based on an encoding result."""
    # pylint: disable=W0613, R0201
    return None

  def DisplayHeading(self):
    """A short string suitable for displaying on top of a column
    showing parameter values for a given encoder."""
    return ' '.join([option.name for option in self.AllOptions()])


class Encoder(object):
  """This class represents a codec with a specific set of parameters.
  It makes sense to talk about "this encoder produces quality X".
  """
  def __init__(self, codec, parameters=None, filename=None):
    """Parameters:
    codec - a Codec object
    parameters - an OptionValueSet object
    filename - a string, passed to the cache for fetching the parameters
    It makes sense to give either the parameters or the filename.
    """
    self.codec = codec
    self.stored = False
    if parameters is None:
      if filename is None:
        raise Error("Encoder with neither parameters nor filename")
      else:
        self.parameters = self.codec.cache.ReadEncoderParameters(filename)
        if self.Hashname() != filename:
          raise Error("Filename %s contains wrong arguments" % filename)
    else:
      self.parameters = codec.ConfigurationFixups(parameters)

  def Encoding(self, bitrate, videofile):
    return Encoding(self, bitrate, videofile)

  def Execute(self, bitrate, videofile, workdir):
    return self.codec.Execute(self.parameters, bitrate, videofile, workdir)

  def Store(self):
    self.codec.cache.StoreEncoder(self)

  def Hashname(self):
    m = md5.new()
    m.update(self.parameters.ToString())
    hashname = m.hexdigest()[:12]
    return hashname

  def OptionValue(self, option_name):
    """Returns the value of an option, or '?' if option has no value."""
    try:
      return Option(option_name).GetValue(self.parameters)
    except Error:
      return '?'

  def ChoiceValue(self, option_name_list):
    """Returns the value of an option, or '?' if option has no value."""
    try:
      return ChoiceOption(option_name_list).GetValue(self.parameters)
    except Error:
      return '?'

  def OptionValues(self):
    """Returns a dictionary of all current option values."""
    values = {}
    for option in self.codec.AllOptions():
      values[option.name] = self.parameters.GetValue(option.name)
    return values

  def DisplayValues(self):
    """Returns the values of the tweakable parameters.

    This is intended to be displayed in a column under codec.DisplayHeading,
    so it is important that sequence here is the same as for DisplayHeading.
    """
    return ' '.join([self.parameters.GetValue(option.name)
                     for option in self.codec.AllOptions()])

  def AllScoredRates(self, videofile):
    return self.codec.cache.AllScoredRates(self, videofile)

  def AllScoredVariants(self, videofile, vary):
    option = self.codec.Option(vary)
    encodings = []
    for value in option.values:
      variant_encoder = Encoder(self.codec,
                                option.SetValue(self.parameters, value))
      encodings.extend(self.codec.cache.AllScoredRates(variant_encoder,
                                                       videofile).encodings)
    return EncodingSet(encodings)


class Encoding(object):
  """The encoding represents the result of applying a specific encoder
  to a specific videofile with a specific target bitrate.
  """
  def __init__(self, encoder, bitrate, videofile):
    """Arguments:
    encoder - an Encoder
    bitrate - a number
    videofile - a Videofile
    """
    self.encoder = encoder
    assert(type(bitrate) == type(0))
    self.bitrate = bitrate
    self.videofile = videofile
    self.result = None

  def SomeUntriedVariants(self):
    """Returns some variant encodings that have not been tried.

    If no such variant can be found, returns an empty EncodingSet.
    """
    result = []
    # Check for suggested variants.
    suggested_tweak = self.encoder.codec.SuggestTweak(self)
    if suggested_tweak:
      suggested_tweak.Recover()
      if not suggested_tweak.Score():
        result.append(suggested_tweak)
    # Generate up to 10 single-hop variants.
    # Just using a variable as a counter doesn't satisfy pylint.
    # pylint: disable=W0612
    for i in range(10):
      variant_encoder = Encoder(
        self.encoder.codec,
        self.encoder.codec.RandomlyChangeConfig(self.encoder.parameters))
      variant_encoding = Encoding(variant_encoder, self.bitrate, self.videofile)
      variant_encoding.Recover()
      if not variant_encoding.Score():
        result.append(variant_encoding)
    # If none resulted, try to make 2 changes.
    if not result:
      for i in range(10):
        variant_encoder = Encoder(
          self.encoder.codec,
          self.encoder.codec.RandomlyChangeConfig(
            self.encoder.codec.RandomlyChangeConfig(self.encoder.parameters)))
        variant_encoding = Encoding(variant_encoder,
                                    self.bitrate,
                                    self.videofile)
        variant_encoding.Recover()
        if not variant_encoding.Score():
          result.append(variant_encoding)

    return EncodingSet(result)

  def Workdir(self):
    workdir = os.path.join(self.encoder.codec.cache.WorkDir(),
                           self.encoder.Hashname(),
                           self.encoder.codec.SpeedGroup(self.bitrate))
    if not os.path.isdir(workdir):
      os.makedirs(workdir)
    return workdir

  def Execute(self):
    self.result = self.encoder.Execute(self.bitrate, self.videofile,
                                       self.Workdir())
    return self

  def Score(self):
    return ScoreResult(self.bitrate, self.result)

  def Store(self):
    self.encoder.Store()
    self.encoder.codec.cache.StoreEncoding(self)

  def Recover(self):
    self.encoder.codec.cache.ReadEncodingResult(self)


class EncodingSet(object):
  def __init__(self, encodings):
    self.encodings = encodings

  def Empty(self):
    return len(self.encodings) == 0

  def BestEncoding(self):
    if self.encodings:
      return max(self.encodings, key=lambda e: e.Score())
    return None

  def BestGuess(self):
    for encoding in self.encodings:
      if not encoding.Score():
        return encoding

def ScoreResult(target_bitrate, result):
  """Returns the score of a particular encoding result.

  The score is a number that can be positive or negative, but it MUST NOT
  be zero, because the Score() is also used as a boolean to check if the
  result is present or not."""
  if not result:
    return None
  score = result['psnr']
  # We penalize bitrates that exceed the target bitrate.
  if result['bitrate'] > int(target_bitrate):
    score -= (result['bitrate'] - int(target_bitrate)) * 0.1
    if abs(score) < 0.01:
      score = 0.01
  return score


class EncodingDiskCache(object):
  """Encoder and encoding information, saved to disk."""
  def __init__(self, codec):
    self.codec = codec
    # Default work directory is current directory.
    self.workdir = '%s/%s' % (os.getenv('CODEC_WORKDIR'),
                              codec.name)
    if not os.path.isdir(self.workdir):
      os.mkdir(self.workdir)

  def WorkDir(self):
    return self.workdir

  def _FilesToEncodings(self, files, videofile, bitrate=0, encoder_in=None):
    candidates = []
    for full_filename in files:
      encoder = encoder_in
      if encoder is None:
        filename = os.path.dirname(full_filename)  # Cut off resultfile
        filename = os.path.dirname(filename)  # Cut off bitrate dir
        filename = os.path.basename(filename)  # Cut off leading codec name
        encoder = Encoder(self.codec, filename=filename)
      if bitrate == 0:
        filename = os.path.dirname(full_filename)
        target_bitrate = os.path.basename(filename)
        try:
          this_bitrate = int(target_bitrate)
        except ValueError:
          # The bitrate is not encoded in the filename.
          # Let it remain zero, we don't know what the target rate is.
          this_bitrate = 0
      else:
        this_bitrate = bitrate
      candidate = Encoding(encoder, this_bitrate, videofile)
      candidate.Recover()
      candidates.append(candidate)
    return EncodingSet(candidates)


  def AllScoredEncodings(self, bitrate, videofile):
    videofilename = videofile.filename
    basename = os.path.splitext(os.path.basename(videofilename))[0]
    pattern = os.path.join(self.workdir, '*', self.codec.SpeedGroup(bitrate),
                           basename + '.result')
    files = glob.glob(pattern)
    return self._FilesToEncodings(files, videofile, bitrate=bitrate)

  def AllScoredRates(self, encoder, videofile):
    videofilename = videofile.filename
    basename = os.path.splitext(os.path.basename(videofilename))[0]
    pattern = os.path.join(self.workdir, encoder.Hashname(),
                           '*', basename + '.result')
    files = glob.glob(pattern)
    return self._FilesToEncodings(files, videofile, encoder_in=encoder)

  def StoreEncoder(self, encoder):
    """Stores an encoder object on disk.

    An encoder object consists of a parameter set.
    Its name is the first 12 bytes of the SHA-1 of its string
    representation."""
    if encoder.stored:
      return
    dirname = os.path.join(self.workdir, encoder.Hashname())
    if not os.path.isdir(dirname):
      os.mkdir(dirname)
    with open(os.path.join(dirname, 'parameters'), 'w') as parameterfile:
      parameterfile.write(encoder.parameters.ToString())
    encoder.stored = True

  def ReadEncoderParameters(self, hashname):
    dirname = os.path.join(self.workdir, hashname)
    with open(os.path.join(dirname, 'parameters'), 'r') as parameterfile:
      return OptionValueSet(self.codec.option_set, parameterfile.read())

  def StoreEncoding(self, encoding):
    """Stores an encoding object on disk.

    An encoding object consists of its result (if executed).
    The bitrate is encoded as a directory, the videofilename
    is encoded as part of the output filename.
    """
    dirname = '%s/%s/%s' % (self.workdir, encoding.encoder.Hashname(),
                            self.codec.SpeedGroup(encoding.bitrate))
    if not os.path.isdir(dirname):
      os.mkdir(dirname)
    if not encoding.result:
      return
    videoname = encoding.videofile.basename
    with open('%s/%s.result' % (dirname, videoname), 'w') as resultfile:
      resultfile.write(str(encoding.result))

  def ReadEncodingResult(self, encoding):
    """Reads an encoding result back from storage, if present.

    Encoder is unchanged if file does not exist."""
    dirname = ('%s/%s/%s' % (self.workdir, encoding.encoder.Hashname(),
                             self.codec.SpeedGroup(encoding.bitrate)))
    filename = '%s/%s.result' % (dirname, encoding.videofile.basename)
    if os.path.isfile(filename):
      with open(filename, 'r') as resultfile:
        stringbuffer = resultfile.read()
        encoding.result = ast.literal_eval(stringbuffer)


class EncodingMemoryCache(object):
  """Encoder and encoding information, in-memory only. For testing."""
  def __init__(self, codec):
    self.codec = codec
    self.encoders = {}
    self.encodings = []

  def WorkDir(self):
    # pylint: disable=R0201
    return '/tmp'

  def AllScoredEncodings(self, bitrate, videofile):
    result = []
    for encoding in self.encodings:
      if (bitrate == encoding.bitrate and
          videofile == encoding.videofile and
          encoding.Score()):
        result.append(encoding)
    return EncodingSet(result)

  def AllScoredRates(self, encoder, videofile):
    result = []
    for encoding in self.encodings:
      if (videofile == encoding.videofile and
          encoder == encoding.encoder and
          encoding.Score()):
        result.append(encoding)
    return EncodingSet(result)

  def StoreEncoder(self, encoder):
    self.encoders[encoder.Hashname()] = encoder

  def ReadEncoderParameters(self, filename):
    if filename in self.encoders:
      return self.encoders[filename].parameters
    return None

  def StoreEncoding(self, encoding):
    self.encodings.append(encoding)


