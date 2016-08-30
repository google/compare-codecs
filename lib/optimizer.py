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
"""
Optimizer module.

It contains functions that allow to find and score encodings that will
perform highly on the score function.
"""

import encoder
import os
import score_tools

class Optimizer(object):
  """Optimizer class.

  An optimizer object contains:
  - A codec.
  - A video file set, with associated target bitrates.
  - A set of pre-executed encodings (the cache).
  - A score function.
  - A score directory, normally null, which means "take from context".

  One should be able ask an optimizer to find the parameters that give the
  best result on the score function for that codec."""
  def __init__(self, codec, file_set=None,
               cache_class=None, score_function=None,
               scoredir=None):
    # pylint: disable=too-many-arguments
    self.context = encoder.Context(codec,
                                   cache_class or encoder.EncodingDiskCache,
                                   scoredir=scoredir)
    self.file_set = file_set
    self.score_function = score_function or score_tools.ScorePsnrBitrate

  def Score(self, encoding):
    result = encoding.result
    if not result:
      raise encoder.Error('Trying to score an encoding without result')
    score = self.score_function(encoding.bitrate, result)
    # Weakly penalize long command lines.
    score -= len(encoding.encoder.parameters.values) * 0.00001
    return score

  def RebaseEncoding(self, encoding):
    """Take an encoding from another context and rebase it to
    this context, using the same encoder arguments."""
    return encoder.Encoding(self.RebaseEncoder(encoding.encoder),
                            encoding.bitrate, encoding.videofile)

  def RebaseEncoder(self, my_encoder):
    return encoder.Encoder(self.context, my_encoder.parameters)

  def BestEncoding(self, bitrate, videofile):
    encodings = self.AllScoredEncodings(bitrate, videofile)
    if encodings:
      return max(encodings, key=self.Score)
    else:
      return self.context.codec.StartEncoder(self.context).Encoding(bitrate,
                                                                    videofile)

  def AllScoredEncodings(self, bitrate, videofile):
    return self.context.cache.AllScoredEncodings(bitrate, videofile)

  def _WorksBetterOnSomeOtherClip(self, encoding, bitrate, videofile):
    """Find an encoder that works better than this one on some other file.

    This function finds some encoding that works better on another
    videofile than the current encoding, but hasn't been tried on this
    encoding and bitrate."""

    # First, find all encodings with this encoder, and look at their files
    # and bitrates.
    candidates = self.context.cache.AllScoredEncodingsForEncoder(
        encoding.encoder)

    # Then, for each file/bitrate, see if this encoder is the best or not.
    for candidate in candidates:
      if candidate == encoding:
        continue
      best_candidate = self.BestEncoding(bitrate, candidate.videofile)
      if best_candidate != candidate:
        # Construct an encoding based on this encoder, and check if it
        # has been tried. If it hasn't been tried, this is the one to try.
        best_on_this = best_candidate.encoder.Encoding(bitrate, videofile)
        best_on_this.Recover()
        if not best_on_this.Result():
          return best_on_this
    return None

  def _EncodingWithOneLessParameter(self, encoding, bitrate, videofile,
                                    hashnames_to_ignore):
    """Find an untried encoder that has one parameter less than this one."""
    # pylint: disable=R0201
    hashnames_to_ignore = hashnames_to_ignore or set()
    new_encoder = encoding.encoder.RandomlyRemoveParameter()
    if not new_encoder:
      return None
    if new_encoder.Hashname() in hashnames_to_ignore:
      return None
    new_encoding = new_encoder.Encoding(bitrate, videofile)
    new_encoding.Recover()
    return new_encoding

  # pylint: disable=W0613
  def _EncodingGoodOnOtherRate(self, encoding, bitrate, videofile,
                               hashnames_to_ignore):
    """Find an untried encoder that is "best" on some other bitrate."""

    hashnames_to_ignore = hashnames_to_ignore or set()
    if not self.file_set:
      return None
    for other_rate in self.file_set.AllRatesForFile(videofile.filename):
      new_encoder = self.BestEncoding(other_rate, videofile).encoder
      if new_encoder.Hashname() in hashnames_to_ignore:
        continue
      new_encoding = new_encoder.Encoding(bitrate, videofile)
      new_encoding.Recover()
      if not new_encoding.Result():
        return new_encoding
    return None

  def BestUntriedEncoding(self, bitrate, videofile, hashnames_to_ignore=None):
    """Attempts to guess the best untried encoding for this file and rate.

    Arguments:
    - bitrate - target bitrate in kbits/sec.
    - videofile - encoder.Videofile object for the file to be encoded.
    - hashnames_to_ignore - set of hashnames for encoders that should not be
                            returned from this function.
    """
    hashnames_to_ignore = hashnames_to_ignore or set()
    current_best = self.BestEncoding(bitrate, videofile)
    might_work_better = self._WorksBetterOnSomeOtherClip(
        current_best, bitrate, videofile)
    if might_work_better:
      return might_work_better
    might_work_better = self._EncodingGoodOnOtherRate(
        current_best, bitrate, videofile, hashnames_to_ignore)
    if might_work_better:
      return might_work_better
    might_work_better = self._EncodingWithOneLessParameter(
        current_best, bitrate, videofile, hashnames_to_ignore)
    if might_work_better and not might_work_better.Result():
      return might_work_better
    # Randomly vary some parameters and see if things improve.
    # This is the final fallback.
    encodings = current_best.SomeUntriedVariants()
    for encoding in encodings:
      if not encoding.Result():
        return encoding
    return None

  def BestOverallEncoder(self):
    """Returns the configuration that is best over all files.

    This looks only at configurations that have been run for every
    file and rate in the fileset."""
    files_and_rates = self.file_set.AllFilesAndRates()
    all_scored_encodings = self.context.cache.AllScoredEncodings(
        files_and_rates[0][0],
        encoder.Videofile(files_and_rates[0][1]))
    candidate_encoder_ids = set([x.encoder.Hashname()
                                for x in all_scored_encodings])
    candidate_encoders = dict([(x.encoder.Hashname(), x.encoder)
                              for x in all_scored_encodings])
    for rate, filename in files_and_rates[1:]:
      these_encoders = set([x.encoder.Hashname()
                            for x in self.context.cache.AllScoredEncodings(
                              rate, encoder.Videofile(filename))])
      candidate_encoder_ids.intersection_update(these_encoders)
    if len(candidate_encoder_ids) == 0:
      return None
    if len(candidate_encoder_ids) == 1:
      return candidate_encoders[candidate_encoder_ids.pop()]
    best_score = -10000
    best_encoder = None
    for hashname in candidate_encoder_ids:
      this_total = 0
      this_encoder = candidate_encoders[hashname]
      for rate, filename in files_and_rates:
        this_encoding = this_encoder.Encoding(rate, encoder.Videofile(filename))
        this_encoding.Recover()
        this_total += self.Score(this_encoding)
      if this_total > best_score:
        best_score = this_total
        best_encoder = this_encoder
    return best_encoder


class FileAndRateSet(object):
  def __init__(self, verify_files_present=True):
    self.rates_and_files = set()
    self.verify_files_present = verify_files_present
    self.set_is_complete = True

  def AddFilesAndRates(self, filenames, rates, basedir=None):
    for rate in rates:
      for filename in filenames:
        if basedir:
          full_filename = os.path.join(basedir, filename)
        else:
          full_filename = filename
        if self.verify_files_present:
          if not os.path.isfile(full_filename):
            self.set_is_complete = False
            return
        self.rates_and_files.add((rate, full_filename))

  def AllFilesAndRates(self):
    """Returns all rate/file pairs"""
    return list(self.rates_and_files)

  def AllRatesForFile(self, filename_to_find):
    """Returns a list of all rates for a specific filename."""
    rates = set()
    for rate, filename in self.AllFilesAndRates():
      if filename == filename_to_find:
        rates.add(rate)
    return list(rates)

  def AllFileNames(self):
    names = set()
    for _, filename in self.AllFilesAndRates():
      names.add(filename)
    return list(names)
