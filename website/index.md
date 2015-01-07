---
layout: default
title: Your New Jekyll Site
---

Introduction
------------

This site exists to fulfil a frequently heard reqest: To be able to compare
the performance of codecs, consistently, openly, and usefully.


What's Wrong with Measurements?
-------------------------------

Most measurements of codecs occur in some specific context. Very often that
context is set by constraints that appear artificial or unrealistic in the
context where codecs are really used: In the real world - and most especially,
on the Internet, in the delivery of video based services.

This site aims to generate video quality metrics under multiple scenarios, all
of which bear some relation to Real Life. We don't expect to be able to mirror
real life perfectly - that would probably make it impossible to produce
reproducible results, another goal, but we aim to find ways to score the
performance of codecs in such a way that if two codecs differ significantly in
score under a given scenario, the one that scores best is also likely to work
best in practice in real life scenarios that resemble that scenario.


Why Openness?
-------------

This site aims to be open in three very important ways:

  * **Open source.** Scripts, Web pages, video sources, the lot. Anyone should
    be able to, with a few simple commands, build their own copy of the
    website and its backing system, and reproduce our results.

  * **Open contribution.** Anyone who thinks they can make things "a little
    bit better" for a codec in a scenario should be free to make the proposal,
    submit a diff, and have it incorporated in the site. Anyone with a "better
    mousetrap" in the form of a new codec, a new metric or a new scenario
    emulator should similarly be able to contribute their code (provided it's
    freely distributable under the terms we adhere to), and show how their
    codec, metric or scenario performs with all the others.

  * **Open results.** While this is an obvious consequence of being open
    source, it is still an important contrast to other efforts: What we
    measure will be public. There will be no secrets.


Testing a Whole Codec vs. Testing the Encoding in Isolation
-----------------------------------------------------------

Testing codecs has very often been an acrimonious matter, because some parties
wish to test just a specific component of the encoding process, while others
feel that ignoring properties that matter in real life situations is making
comparisons unfair and unreasonable.

One simile (props to `FIXME` from Ericsson for this): "If you want to test the
performance of an engine, you don't want to put it in a car - you isolate it
on a measurement bench to remove the variability from your measurements". True
as far as it goes - but conversely, if you are comparing cars, removing their
engines and testing them in isolation gives no information about their
handling characteristics on the road; for that, brakes, steering and
transmission all matter.

We have chosen to test codecs in, as far as possible, the way they will be
used. This means that we test real implementations, that people use in
production, and test them including all tools that matter, including rate
control, filters, preprocessing, postprocessing and so on - if it improves the
performance, and it's clearly identified (and available in opensource), let it
be used!


Scenarios We Aim to Cover
-------------------------

The scenarios we aim to cover in the initial set are the following:

  * Traditional "Fixed quality, no adaptation". This is not an important
    version in Real Life, but is important because it allows some means of
    comparison with measurements done under this testing methodology at, for
    instance, MPEG.

  * Pre-encoded video targeted at fixed bandwidth delivery. This is a
    scenario where we can take the time we need for encoding, and use tools
    like multi-pass encoding - but the result needs to be measured on the
    experience it achieves if delivered over a fixed bandwidth channel; if
    peaks in bandwidth are big enough to overflow jitter buffers, for
    instance, the codec needs to be penalized.

  * Interactive video, targeted at fixed bandwidth delivery. In this scenario,
    encoding needs to be done one (or a few) frames at a time, with no
    lookahead into future frames (they haven't been produced yet), and no or
    very limited buffering at the receiver side. Codecs that overrun the
    bitrate allocation at any point in time need to be sharply penalized for
    doing so. In this scenario, it's also relevant to look at speed of
    encoding and decoding; encoding that cannot keep up with real time on a
    machine running these tests is unlikely to be very useful in real life if
    one depends on a software codec.

Other scenarios may be added once a consensus emerges on what they should be,
and once the tools are available for measuring the metrics that are important
in those scenarios.


Issues This Site Does Not Cover
-------------------------------

All that this site is concerned with is that it produces reproducible results.
It is absolutely unconcerned with many details that matter for real
deployments, such as commercial licenses, patent restrictions, flexibility of
software, tunability for special scenarios and so on.

These issues can only be evaluated in the context of a specific usage scenario
and business model; it is not possible for a project like this to give useful
guidance in those matters.
