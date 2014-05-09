Coding info for the Compare Codecs project
==========================================
Before running scripts, source the "init.sh" file. It will set
the correct environment variables, including adding "bin" to your
PATH, and pointing the codec work directory to the rigth place.

The Python library used is in the "lib" directory.

The "bin" directory contains useful executables and scripts.
It should be part of your PATH.

The "video" directory contains source videos in YUV format. These are
fetched using the <insert name> script - each group of source videos
lives in one subdirectory.

The encoder working directory, which also contains single encode
results, is in "workdir". Tabulated results live in "results".
