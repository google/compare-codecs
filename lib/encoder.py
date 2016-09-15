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
"""Encoder and related classes.

This file contains classes that generically define the idea of a codec,
an encoder, an option and so forth.

A codec is a generic mechanism for processing an .yuv file and returning
a score. Given a set of options, a file and a rate, it can produce an encoder.
The codec has a set of options that can have varying values.

An encoder is a codec with a given set of options.

An encoding is an encoder applied to a given filename and target bitrate.

A variant is an encoder with at least one option changed.

Configuration of the module is through the encoder_configuration module.
"""

import encoder_configuration
import glob
import json
import md5
import os
import random
import re
import shutil
import subprocess
import sys


class Error(Exception):
  """Generic errors in all Encoder-related problems."""
  pass


class ParseError(Error):
  """Errors in parsing a configuration string."""
  pass


def Tool(name):
  return os.path.join(encoder_configuration.conf.tooldir(), name)


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
    self.mandatory = False

  def Mandatory(self):
    """Set this parameter as mandatory.

    Intended use is as a trailer on the constructor."""
    self.mandatory = True
    return self

  def CanChange(self):
    return len(self.values) > 1

  def PickAnother(self, not_this):
    """Find a new value for the option, different from not_this.
    not_this doesn't have to be a member of the values list, but can be.
    """
    assert self.CanChange
    rest = list(self.values - set([not_this]))
    return rest[random.randint(0, len(rest) - 1)]

  def LegalValue(self, value):
    return value in self.values

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
    return value in self.values

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

  def LegalValue(self, value):
    # This class does not have an opinion of legal values.
    return True


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

  def LockOption(self, name, value):
    if not name in self.options:
      raise Error('No such option name: %s' % name)
    if not value in self.options[name].values:
      raise Error('No such option value for %s: %s' % (name, value))
    self.options[name].values = frozenset([value])
    self.options[name].Mandatory()

  def Option(self, name):
    return self.options[name]

  def HasOption(self, name):
    return name in self.options

  def AllOptions(self):
    return self.options.values()

  def AllMandatoryOptions(self):
    return [option for option in self.AllOptions() if option.mandatory]

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
    unparsed = string
    matcher = r'\s*%s([^%s ]*)(%s(\S+))?' % (formatter.prefix,
                                             formatter.infix[0:1],
                                             formatter.infix)
    match = re.match(matcher, unparsed)
    while match:
      self._HandleFlag(match)
      unparsed = unparsed[match.end():]
      match = re.match(matcher, unparsed)
    if option_set:
      for option in option_set.options.values():
        if option.mandatory and not option.name in self.values:
          raise ParseError('Mandatory option %s is missing' % option.name)

  def _HandleFlag(self, match):
    if self._HandleNameValueFlag(match):
      return
    if self._HandleChoiceFlag(match):
      return
    # It is not a known name=value or a known flag.
    # Remember it, but don't make it available for manipulation.
    self.other_parts.append(match.group(0).strip())

  def _HandleNameValueFlag(self, match):
    name = match.group(1)
    if match.group(2) and self.option_set.HasOption(name):
      # Known name=value option.
      name = match.group(1)
      value = match.group(3)
      if not self.option_set.options[name].LegalValue(value):
        raise ParseError('Illegal value %s for option %s' % (value, name))
      self.values[name] = value
      return True
    return False

  def _HandleChoiceFlag(self, match):
    option = self.option_set.FindFlagOption(match.group(1))
    if option:
      # Known flag option (no value)
      self.values[option.name] = match.group(1)
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

  def __ne__(self, other):
    return not self.__eq__(other)

  def GetValue(self, name):
    try:
      return self.values[name]
    except KeyError:
      raise Error('No value for option %s' % name)

  def HasValue(self, name):
    return name in self.values

  def _Clone(self):
    """Return a clone of this OptionValueSet.

    Used by internal functions that modify the copy."""
    new_set = OptionValueSet(None, "", self.formatter)
    # Note that setting option_set after creation is needed to bypass
    # the test for "" being a valid configuration.
    new_set.option_set = self.option_set
    new_set.values = self.values.copy()
    new_set.other_parts = self.other_parts
    return new_set

  def ChangeValue(self, name, value):
    """Return an OptionValueSet with the specified parameter changed."""
    if not self.option_set.HasOption(name):
      raise Error('Unknown option name %s' % name)
    new_set = self._Clone()
    new_set.values[name] = value
    return new_set

  def RemoveValue(self, name):
    """Return an OptionValueSet without the specified parameter."""
    if not self.option_set.HasOption(name):
      raise Error('Unknown option name %s' % name)
    if self.option_set.Option(name).mandatory:
      raise Error('Cannot remove option %s' % name)
    new_set = self._Clone()
    del new_set.values[name]
    return new_set

  def RandomlyPatchOption(self, option):
    """ Modify a configuration by changing the value of this option."""
    if self.HasValue(option.name):
      newconfig = self.ChangeValue(
        option.name, option.PickAnother(self.GetValue(option.name)))
    else:
      newconfig = self.ChangeValue(
        option.name, option.PickAnother(''))
    assert self != newconfig
    return newconfig

  def RandomlyPatchConfig(self):
    """ Modify a configuration by changing the value of a random parameter.

    This may change values that are present, or add values for parameters
    that are not present."""
    options = self.option_set.AllChangeableOptions()
    assert len(options) >= 1
    option_to_change = options[random.randint(0, len(options)-1)]
    return self.RandomlyPatchOption(option_to_change)

  def RandomlyRemoveParameter(self):
    """ Return a new OptionValueSet with one less parameter."""
    removable_values = [name for name in self.values.keys()
                        if not self.option_set.Option(name).mandatory]
    if len(removable_values) < 1:
      return None
    option_to_change = random.choice(removable_values)
    return self.RemoveValue(option_to_change)


class Videofile(object):
  def __init__(self, filename):
    """ Parse the file name to find width, height and framerate. """
    self.filename = filename
    match = re.search(r'_(\d+)x(\d+)_(\d+)', filename)
    if match:
      self.width = int(match.group(1))
      self.height = int(match.group(2))
      self.framerate = int(match.group(3))
    else:
      match = re.search(r'_(\d+)_(\d+)_(\d+).yuv$', filename)
      if match:
        self.width = int(match.group(1))
        self.height = int(match.group(2))
        self.framerate = int(match.group(3))
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

  def FrameCount(self):
    framesize = self.width * self.height * 3 / 2
    return os.path.getsize(self.filename) / framesize

  def ClipTime(self):
    return float(self.FrameCount()) / self.framerate


class Codec(object):
  """Abstract class representing a codec.

  Subclasses must define the options and start_encoder variables
  The class also contains a cache of evaluation results, and a score
  function.
  This is used by the functions that return the "best" of something,
  as well as for making evaluations and comparison reports.
  """
  def __init__(self, name, formatter=None):
    self.name = name
    self.option_set = OptionSet()
    self.option_formatter = formatter or OptionFormatter()

  def Option(self, name):
    return self.option_set.Option(name)

  def AllOptions(self):
    return self.option_set.AllOptions()

  def StartEncoder(self, context):
    # pylint: disable=R0201, W0613
    raise Error("The base codec class has no start encoder")

  def Execute(self, parameters, bitrate, videofile, workdir):
    # pylint: disable=W0613, R0201
    raise Error("The base codec class can't execute anything")

  def VerifyEncode(self, parameters, bitrate, videofile, workdir):
    """Returns true if a new encode of the file gives exactly the same file."""
    # pylint: disable=W0613, R0201
    raise Error("The base codec class can't verify anything")

  def EncodeCommandLine(self, parameters, bitrate, videofile, workdir):
    """Returns a command line for encoding. Base codec class has none."""
    # pylint: disable=W0613, R0201
    return '# No command available'

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

  def EncoderVersion(self):
    """Return a string representing the version of the codec.

    For internal functions, return the git hash of the software + a modification
    marker."""
    # pylint: disable=no-self-use
    git_hash = subprocess.check_output(['git', 'log', '--format=%h %ad', '-1'],
                                       shell=False).rstrip()
    returncode = subprocess.call(['git', 'diff-index', '--quiet', 'HEAD'])
    if returncode:
      return 'compare-codecs %s (modified)' % git_hash
    else:
      return 'compare-codecs %s' % git_hash


class Context(object):
  """Context for an Encoder object.

  This class encapsulates the "workdir" and the "storage" concepts.
  This base implementation defaults to a memory cache.
  Since a storage module needs the context to create itself, the class
  object of the storage module class, not a storage module object,
  is passed to the context constructor.
  """

  def __init__(self, codec, cache_class=None, scoredir=None):
    self.codec = codec
    if cache_class:
      self.cache = cache_class(self, scoredir)
    else:
      self.cache = EncodingMemoryCache(self, scoredir)


class Encoder(object):
  """This class represents a codec with a specific set of parameters.
  It makes sense to talk about "this encoder produces quality X".
  """
  def __init__(self, context, parameters=None, filename=None):
    """Parameters:
    context - a Context object, used for accessing codec, cache and workdir.
    parameters - an OptionValueSet object.
    filename - a string, passed to the cache for fetching the parameters.
    It makes sense to give either the parameters or the filename.
    """
    self.context = context
    self.stored = False
    if parameters is None:
      if filename is None:
        raise Error("Encoder with neither parameters nor filename")
      else:
        self.parameters = self.context.cache.ReadEncoderParameters(filename)
        if self.Hashname() != os.path.basename(filename):
          raise Error("Filename %s for codec %s contains wrong arguments"
                      % (filename, context.codec.name))
    else:
      self.parameters = context.codec.ConfigurationFixups(parameters)

  def Encoding(self, bitrate, videofile):
    return Encoding(self, bitrate, videofile)

  def HasSameParameters(self, other_encoder):
    return self.parameters == other_encoder.parameters

  def Execute(self, bitrate, videofile, workdir):
    return self.context.codec.Execute(
      self.parameters, bitrate, videofile, workdir)

  def EncodeCommandLine(self, bitrate, videofile, workdir):
    return self.context.codec.EncodeCommandLine(
        self.parameters, bitrate, videofile, workdir)

  def VerifyEncode(self, bitrate, videofile, workdir):
    """Returns true if a new encode of the file gives exactly the same file."""
    return self.context.codec.VerifyEncode(
      self.parameters, bitrate, videofile, workdir)

  def ParametersCanChange(self):
    return len(self.parameters.option_set.AllChangeableOptions()) >= 1

  def Store(self):
    self.context.cache.StoreEncoder(self)

  def Hashname(self):
    parameter_hash = md5.new()
    parameter_hash.update(self.parameters.ToString())
    hashname = parameter_hash.hexdigest()[:12]
    return hashname

  def OptionValues(self):
    """Returns a dictionary of all current option values."""
    values = {}
    for option in self.context.codec.AllOptions():
      values[option.name] = self.parameters.GetValue(option.name)
    return values

  def DisplayValues(self):
    """Returns the values of the tweakable parameters.

    This is intended to be displayed in a column under codec.DisplayHeading,
    so it is important that sequence here is the same as for DisplayHeading.
    """
    return ' '.join([self.parameters.GetValue(option.name)
                     for option in self.context.codec.AllOptions()])

  def AllScoredRates(self, videofile):
    return self.context.cache.AllScoredRates(self, videofile)

  def AllScoredVariants(self, videofile, vary):
    option = self.context.codec.Option(vary)
    encodings = []
    for value in option.values:
      variant_encoder = Encoder(self.context,
                                option.SetValue(self.parameters, value))
      encodings.extend(self.context.cache.AllScoredRates(variant_encoder,
                                                         videofile).encodings)
    return encodings

  def ChangeValue(self, name, new_value):
    """Return a new encoder with a changed value for this parameter."""
    return Encoder(self.context, self.parameters.ChangeValue(name, new_value))

  def RandomlyRemoveParameter(self):
    parameters = self.parameters.RandomlyRemoveParameter()
    if parameters:
      return Encoder(self.context, parameters)
    else:
      return None


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
    self.context = encoder.context
    assert type(bitrate) == type(0)
    self.bitrate = bitrate
    self.videofile = videofile
    self.result = None

  def Result(self):
    return self.result

  def ResultWithoutFrameData(self):
    return {i: self.result[i] for i in self.result if i != 'frame'}

  def SomeUntriedVariants(self):
    """Returns some variant encodings that have not been tried.

    If no such variant can be found, returns an empty sequence.
    """
    result = []
    # Some codecs can't vary anything. If so, return the empty set.
    if not self.encoder.ParametersCanChange():
      return []
    # Check for suggested variants.
    suggested_tweak = self.context.codec.SuggestTweak(self)
    if suggested_tweak:
      suggested_tweak.Recover()
      if not suggested_tweak.Result():
        result.append(suggested_tweak)
    # Generate up to 10 single-hop variants.
    # Just using a variable as a counter doesn't satisfy pylint.
    # pylint: disable=W0612
    seen = set()
    for i in range(10):
      variant_encoder = Encoder(
        self.context,
        self.context.codec.RandomlyChangeConfig(self.encoder.parameters))
      params_as_string = variant_encoder.parameters.ToString()
      if not params_as_string in seen:
        variant_encoding = Encoding(variant_encoder, self.bitrate,
                                    self.videofile)
        variant_encoding.Recover()
        if not variant_encoding.Result():
          result.append(variant_encoding)
          seen.add(params_as_string)

    # If none resulted, make 10 attempts to find an untried candidate
    # by making 2 random changes to the configuration.
    if not result:
      for i in range(10):
        variant_encoder = Encoder(
          self.context,
          self.context.codec.RandomlyChangeConfig(
            self.context.codec.RandomlyChangeConfig(self.encoder.parameters)))
        params_as_string = variant_encoder.parameters.ToString()
        if not params_as_string in seen:
          variant_encoding = Encoding(variant_encoder,
                                      self.bitrate,
                                      self.videofile)
          variant_encoding.Recover()
          if not variant_encoding.Result():
            result.append(variant_encoding)
            seen.add(params_as_string)

    return result

  def Workdir(self):
    workdir = os.path.join(self.context.cache.WorkDir(),
                           self.encoder.Hashname(),
                           self.context.codec.SpeedGroup(self.bitrate))
    if (os.path.isdir(self.context.cache.WorkDir())
        and not os.path.isdir(workdir)):
      # The existence of the cache's WorkDir is something the cache needs to
      # worry about. This function only makes dirs inside the cache.
      os.makedirs(workdir)
    return workdir

  def Execute(self):
    self.result = self.encoder.Execute(self.bitrate, self.videofile,
                                       self.Workdir())
    return self

  def VerifyEncode(self):
    """Returns true if a new encode of the file gives exactly the same file."""
    return self.encoder.VerifyEncode(self.bitrate, self.videofile,
                                     self.Workdir())

  def EncodeCommandLine(self):
    """Returns a command line suitable for display, not execution."""
    return self.encoder.EncodeCommandLine(self.bitrate, self.videofile, '$')

  def Store(self):
    self.encoder.Store()
    self.context.cache.StoreEncoding(self)

  def Recover(self):
    self.result = self.context.cache.ReadEncodingResult(self)

  def ChangeValue(self, name, value):
    new_encoder = self.encoder.ChangeValue(name, value)
    new_encoding = new_encoder.Encoding(self.bitrate, self.videofile)
    return new_encoding


# Utility functions for EncodingDiskCache.
def _FileNameToBitrate(full_filename):
  filename = os.path.dirname(full_filename)
  target_bitrate = os.path.basename(filename)
  try:
    return int(target_bitrate)
  except ValueError:
    # The bitrate is not encoded in the filename.
    # Let it remain zero, we don't know what the target rate is.
    return 0

def _FileNameToVideofile(full_filename):
  # Construct a pseudo videofile from the filename.
  filename = os.path.basename(full_filename)
  filename = re.sub(r'\.result', '.yuv', filename)
  return Videofile(filename)


class EncodingDiskCache(object):
  """Encoder and encoding information, saved to disk."""
  def __init__(self, context, scoredir=None):
    self.context = context
    self.bad_encodings = {}
    if scoredir:
      self.workdir = os.path.join(encoder_configuration.conf.sysdir(),
                                  scoredir, context.codec.name)
    else:
      # Default work directory.
      self.workdir = os.path.join(encoder_configuration.conf.workdir(),
                                  context.codec.name)
    if not os.path.isdir(self.workdir):
      os.mkdir(self.workdir)

  def WorkDir(self):
    return self.workdir

  def SearchPathForScores(self):
    """Returns the list of paths that will be searched for scores.

    This consists of the current working directory (always first)
    and what's configured as the "scorepath", both with the codec
    name appended."""
    path = [self.workdir]
    path.extend([os.path.join(this_path, self.context.codec.name)
                 for this_path in encoder_configuration.conf.scorepath()])
    return path

  def _FileNameToEncoder(self, full_filename):
    filename = os.path.dirname(full_filename)  # Cut off resultfile
    filename = os.path.dirname(filename)  # Cut off bitrate dir
    return Encoder(self.context, filename=filename)

  def _FilesToEncodings(self, files, videofile, bitrate=None,
                        encoder=None):
    candidates = []
    for full_filename in files:
      try:
        candidate = Encoding(
          encoder or self._FileNameToEncoder(full_filename),
          bitrate or _FileNameToBitrate(full_filename),
          videofile or _FileNameToVideofile(full_filename))
      except ParseError as err:
        self.bad_encodings[full_filename] = err
        continue
      try:
        candidate.Recover()
        candidates.append(candidate)
      except Error as err:
        # TODO(hta): Change this to a more specific catch once available.
        self.bad_encodings[full_filename] = err
        continue
    return candidates

  def _QueryScoredEncodings(self, encoder=None, bitrate=None, videofile=None):
    if encoder:
      encoder_part = encoder.Hashname()
    else:
      encoder_part = '*'
    if bitrate:
      bitrate_part = self.context.codec.SpeedGroup(bitrate)
    else:
      bitrate_part = '*'
    if videofile:
      videofile_part = os.path.splitext(
          os.path.basename(videofile.filename))[0] + '.result'
    else:
      videofile_part = '*' + '.result'
    files = []
    for path in self.SearchPathForScores():
      pattern = os.path.join(path, encoder_part,
                             bitrate_part, videofile_part)
      files.extend(glob.glob(pattern))
    return self._FilesToEncodings(files, videofile, bitrate)

  def AllScoredEncodings(self, bitrate, videofile):
    return self._QueryScoredEncodings(bitrate=bitrate, videofile=videofile)

  def AllScoredRates(self, encoder, videofile):
    return self._QueryScoredEncodings(encoder=encoder, videofile=videofile)

  def AllScoredEncodingsForEncoder(self, encoder):
    return self._QueryScoredEncodings(encoder=encoder)

  def StoreEncoder(self, encoder, workdir=None):
    """Stores an encoder object on disk.

    An encoder object consists of a parameter set.
    Its name is the first 12 bytes of the SHA-1 of its string
    representation."""
    if encoder.stored:
      return
    if workdir:
      dirname = os.path.join(workdir, self.context.codec.name,
                             encoder.Hashname())
    else:
      dirname = os.path.join(self.workdir, encoder.Hashname())
    if not os.path.isdir(dirname):
      os.makedirs(dirname)
    with open(os.path.join(dirname, 'parameters'), 'w') as parameterfile:
      parameterfile.write(encoder.parameters.ToString())
    encoder.stored = True

  def ReadEncoderParameters(self, dirname):
    if os.path.isabs(dirname):
      with open(os.path.join(dirname, 'parameters'), 'r') as parameterfile:
        return OptionValueSet(self.context.codec.option_set,
                              parameterfile.read(),
                              formatter=self.context.codec.option_formatter)
    else:
      for repository in self.SearchPathForScores():
        filename = os.path.join(repository, dirname, 'parameters')
        if os.path.isfile(filename):
          with open(filename, 'r') as parameterfile:
            return OptionValueSet(self.context.codec.option_set,
                                  parameterfile.read(),
                                  formatter=self.context.codec.option_formatter)

  def AllEncoderFilenames(self, only_workdir=False):
    filenames = []
    if only_workdir:
      path_list = [self.WorkDir()]
    else:
      path_list = self.SearchPathForScores()
    for path in path_list:
      pattern = os.path.join(path, '*')
      filenames.extend([this_file for this_file in glob.glob(pattern)])
    return filenames

  def RemoveEncoder(self, hashname):
    shutil.rmtree(os.path.join(self.workdir, hashname))

  def StoreEncoding(self, encoding):
    """Stores an encoding object on disk.

    An encoding object consists of its result (if executed).
    The bitrate is encoded as a directory, the videofilename
    is encoded as part of the output filename.
    """
    dirname = os.path.join(self.workdir,
                           encoding.encoder.Hashname(),
                           self.context.codec.SpeedGroup(encoding.bitrate))
    if not os.path.isdir(dirname):
      os.mkdir(dirname)
    if not encoding.result:
      return
    videoname = encoding.videofile.basename
    with open('%s/%s.result' % (dirname, videoname), 'w') as resultfile:
      json.dump(encoding.result, resultfile, indent=2)

  def ReadEncodingResult(self, encoding):
    """Reads an encoding result back from storage, if present.

    None is returned if file does not exist.
    If scoredir is given, only that directory is searched.
    If it is not given, all directories in the search path are searched."""

    searchpath = self.SearchPathForScores()

    for workdir in searchpath:
      dirname = os.path.join(workdir, encoding.encoder.Hashname(),
                             self.context.codec.SpeedGroup(encoding.bitrate))
      filename = os.path.join(dirname,
                              '%s.result' % encoding.videofile.basename)
      if not os.path.isfile(filename):
        continue
      with open(filename, 'r') as resultfile:
        stringbuffer = resultfile.read()
        try:
          return json.loads(stringbuffer)
        except:
          raise Error('Unexpected JSON error: %s, filename was %s' %
                      (sys.exc_info()[0], filename))
    return None


class EncodingMemoryCache(object):
  """Encoder and encoding information, in-memory only. For testing."""
  def __init__(self, context, scoredir=None):
    if scoredir:
      raise Error('Cannot have scoredir on a memory cache')
    self.context = context
    self.encoders = {}
    self.encodings = []
    self.workdir = '/not-valid-file/' + self.context.codec.name

  def WorkDir(self):
    return self.workdir

  def AllScoredEncodings(self, bitrate, videofile):
    result = []
    for encoding in self.encodings:
      if (bitrate == encoding.bitrate and
          videofile.filename == encoding.videofile.filename and
          encoding.Result()):
        result.append(encoding)
    return result

  def AllScoredRates(self, encoder, videofile):
    result = []
    for encoding in self.encodings:
      if (videofile == encoding.videofile and
          encoder.parameters.ToString() ==
              encoding.encoder.parameters.ToString() and
          encoding.Result()):
        result.append(encoding)
    return result

  def AllScoredEncodingsForEncoder(self, encoder):
    return [encoding for encoding in self.encodings
            if (encoder.HasSameParameters(encoding.encoder) and
                encoding.Result())]

  def StoreEncoder(self, encoder):
    self.encoders[encoder.Hashname()] = encoder

  def ReadEncoderParameters(self, filename):
    if filename in self.encoders:
      return self.encoders[filename].parameters
    return None

  def StoreEncoding(self, encoding):
    self.encodings.append(encoding)

  def ReadEncodingResult(self, encoding_in, scoredir=None):
    # pylint: disable=W0613
    # Since the memory cache stores the results as a list of encodings,
    # we must find an encoding with the same properties as the one we're
    # reading parameters for, and return the result from that.
    for encoding in self.encodings:
      if (encoding_in.videofile.filename == encoding.videofile.filename and
          encoding_in.encoder.parameters.ToString() ==
              encoding.encoder.parameters.ToString() and
          encoding_in.bitrate == encoding.bitrate and
          encoding.Result()):
        return encoding.Result()
    return None
