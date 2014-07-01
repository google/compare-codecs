---
layout: default
title: Contributing
---

Contributing to the Codec Comparision Project
---------------------------------------------

The intent of the project is to let people compare what they think makes sense
to compare.

The requirements for contributions are:

  * You must be willing to sign the [agreement](/agreement/).
  * You must make all your contributions available under the site's
    [license](/license/).


### How to Run a Comparision

The steps for running a comparision yourself are:

  * Clone this site using git, onto a system running Linux. The setup has been
    tested using Ubuntu 12.04; other Linux distributions might work.
    Contributions to make it work on other systems are welcome!

  * Go to the main directory and run the `install_prerequisites.sh` script.
    Run the `FIXME` script to install your test video clips.

  * Source the `init.sh` file. This sets your path and environment variables
    correctly.

  * Select your codecs from the list of codecs
    given by `list_codecs`, and run `compare_codecs --score <codec1> <codec2>`.
    This can take quite a while, and produce quite a bit of output. Run it
    again to view the results in text format.

  * At the end of the run, the name of an HTML file is printed. Open this file
    in the browser of your choice.


### Using Others' Encoding Data

If you wish to download the result of other people's encoding runs, you can
run `FIXME` to download the git repository with test results into your test
results cache. You can run `FIXME` to get a standard set of comparisions
generated; these, together with all the ones you generate, will be listed on
`FIXME`.


### Uploading your encoding results

If you have run encodings that give new numbers, you are encouraged to share
them by uploading them to the git repository for results.

(Instructions follow)

The results will be subject to some vetting to see that they are reasonable,
but mostly, we expect to accept all results. It will be possible to find out
who uploaded a given result, so that if any contributor's data is found to
contain systematic errors, they can be purged from the system.


### Uploading New Settings

Settings are represented as encoders: a codec run with a particular set of
parameters. If you have found a set of paramteters that work well in a use
case, you're encouraged to upload it.

For each codec, there are a set of named encoders: one called "default", a
set called `best-<scenario>`, and any other names that contributors find
useful.

(Instructions go here)


### Uploading a New Codec

A new codec contribution consists of:

  * A name for the new codec

  * A pull and build instruction added to the `install_prerequisites.sh`
    script so that the necessary binaries are available (if needed).

  * A Python module that defines the parameters for the codec, and how the
    codec is going to be executed. Use existing files as guidelines.

The codec source must be available for use under a reasonable license (no
secrets allowed), but does not need to be licenseable under this project's
license; people running the test set are merely using it.


### Uploading a New Test Video

More coming ...
