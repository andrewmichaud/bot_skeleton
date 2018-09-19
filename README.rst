botskeleton
=============

| |BSD3 License|

| |Build Status|

| |Coverage Status|

| |Issue Count|

.. image:: https://badge.fury.io/py/botskeleton.svg
    :target: https://badge.fury.io/py/botskeleton

.. image:: https://badge.waffle.io/alixnovosi/botskeleton.png?label=ready&title=Ready
    :target: https://waffle.io/alixnovosi/botskeleton
    :alt: 'Stories in Ready'


.. |BSD3 License| image:: http://img.shields.io/badge/license-BSD3-brightgreen.svg
   :target: https://tldrlegal.com/license/bsd-3-clause-license-%28revised%29
.. |Build Status| image:: https://travis-ci.org/alixnovosi/botskeleton.svg?branch=master
   :target: https://travis-ci.org/alixnovosi/botskeleton
.. |Coverage Status| image:: https://coveralls.io/repos/alixnovosi/botskeleton/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/alixnovosi/botskeleton?branch=master
.. |Issue Count| image:: https://codeclimate.com/github/alixnovosi/botskeleton/badges/issue_count.svg
   :target: https://codeclimate.com/github/alixnovosi/botskeleton

=====
short
=====
skeleton for bot children written in Python.

Created by Andrew Michaud ahead of #NaBoMaMo 2017

====
long
====
botskeleton is a framework for content bots,
like `Twitter bots <https://twitter.com/nonogram_bot/status/1042453809945993216>`
and `Mastodon bots <https://botsin.space/@tree_bot>`.

==========
Public API
==========
The public API is contained entirely in botskeleton.py.

===================
:code:`Botskeleton`
===================
The :code:`BotSkeleton` class is the main object for a bot,
holding all the send methods and credentials.
It MUST be constructed with a `secrets_dir`
- this is the directory where it will expect credentials,
and where it will write its history file.
You may also provide a log_filename (default is in the directory of execution,
under "log"),
a bot_name (default is "A bot"),
a history_filename (default is "bot_name-history.json"),
and a delay,
which is the time the bot will sleep after posting.

With a botskeleton,
you can send to the outputs in various ways (outputs described later).
All methods will generate :code:`IterationRecords`,
update the history,
and save the history.

===========
Bot Methods
===========
These are methods intended to be used to send bot methods.

------------------------
:code:`send(self, text)`
------------------------
:code:`send` is a plain text send method.
It will send the text to all configured outputs and save the result.

-------------------------------------------------
:code:`send_with_one_media(self, text, filename)`
-------------------------------------------------
:code:`send_with_one_media` will call each output and have them upload the file
(as dictated by the output),
and send a message with the provided text and that image.

----------------------------------------------------
:code:`send_with_many_media(self, text, *filenames)`
----------------------------------------------------
:code:`send_with_many_media` will call each output and have them upload several files
(as dictated by the output),
and send a message with the provided text and those image.
A current known bug is that the built-in outputs have limits on how many images they can post at once,
but there is no limiting in this method.
If you post more than four images with this method,
you may see strange results in the outputs.

-----------------
:code:`nap(self)`
-----------------
Sleep for the configured amount of seconds.

------------------------------------------
:code:`store_extra_info(self, key, value)`
------------------------------------------
:code:`store_extra_info` will take the provided key and value and store them.
When history is updated,
extra_info is also stored in the history file.
The intended use case is to store something related to each post,
like a random seed used to generate the text,
or some related values that might be nice to see alongside it in the history storage.
Feel free to store whatever you like.

------------------------------------
:code:`store_extra_keys(self, dict)`
------------------------------------
:code:`store_extra_keys` will take an entire dictionary and merge it with the :code:`extra_keys` storage.
As before,
this will be stored in thie history logs.

----------------------------
:code:`update_history(self)`
----------------------------
Save the in-object history to disk,
in the history file.
History is saved as pretty-printed JSON.
This is called automatically by every send method.

--------------------------
:code:`load_history(self)`
--------------------------
Load the history from disk. Done automatically when the :code:`BotSkeleton` object is initialized.

===============
Utility Methods
===============
Some utility methods,
exposed from :code:`drewtilities`

-----------------------------------------
:code:`rate_limited(max_per_hour, *args)`
-----------------------------------------
Annotation to rate-limit a function.
It will sleep such that it is called no more than :code:`max_per_hour` times per hour.

------------------------------------
:code:`set_up_logging(log_filename)`
------------------------------------
Set up a logger with the provided filename.
This is called by the constructor automatically.

------------------------------
:code:`random_line(file_path)`
------------------------------
Return a random line from the provided file.
Useful for bots.

----------------------
:code:`repair(record)`
----------------------
NOT INTENDED FOR MANUAL USE.
This is a method to repair a particular form of history corruption.
Automatically called by :code:`load_history`.

=======================
:code:`IterationRecord`
=======================
Record of one iteration -
one generation of text and a send to all outputs.
Stores extra keys,
a timestamp,
and records for all outputs (see output section).

=================
Other Information
=================

=======
Outputs
=======
:code:`botskeleton` is designed to output to an arbitrary number of outputs.
Outputs need to be in the :code:`outputs` property in :code:`BotSkeleton`.
They need to have an "active" key,
used to decide whether to output,
and an "obj" key that should be a call to the constructor of the object.
:code:`output/output_utils.py` defines the :code:`OutputSkeleton` new outputs must subclass,
and some useful utilities for new outputs.

NOTE Outputs are not considered part of the public API.
:code:`output/output_utils.py` may change without warning,
as may the 

----------
Activation
----------
Outputs are activated if there is a credential directory available for them.
The credential directory is expected to be under "secret_dir",
and to have a name of the form :code:`credentials_{output_name}`.

-------
Methods
-------
These mirror the methods in :code:`botskeleton.py`,
but aren't guaranteed to be identical,
and,
again,
may change without warning.
Outputs must implement these themselves.

---------------------------
:code:`send(self, message)`
---------------------------
Send message with text.

----------------------------------------------------
:code:`send_with_one_media(self, message, filename)`
----------------------------------------------------
Send message with text and filename.
Output will process file as necessary.

-------------------------------------------------------
:code:`send_with_many_media(self, message, *filenames)`
-------------------------------------------------------
Send message with text and filenames.
Output will process files as necessary.

------------------------------------------
:code:`linfo/ldebug/lerror(self, message)`
------------------------------------------
Log with bot name and message at the given level.

------------------------------------------------------
:code:`set_duplicate_handler(self, duplicate_handler)`
------------------------------------------------------
Set duplicate handler.
This is based off of birdsite's error code and likely will be removed,
in favor of just having it in the birdsite output.
Error handlers are stored in :code:`self.handled_errors`,
a dictionary.

---------------------------
:code:`OutputRecord` object
---------------------------
Outputs maintain an :code:`OutputRecord` object,
representing a single send to the output.
They maintain at least a :code:`_type` and timestamp.
Individual outputs can add whatever else they like.
Methods are provided here to convert to a pretty string,
and to convert back from a dictionary to an object.

---------------------------------------
:code:`default_duplicate_handler(self)`
---------------------------------------
Default duplicate error handler.
Does nothing.

================
Built-in Outputs
================
There are two built-in outputs:
birdsite (twitter.com)
mastodon (mastodon.social)

These are subject to change as necessary by the underlying API wrappers they use.
Some notes:

----------------------------------
:code:`outputs/output_birdsite.py`
----------------------------------
Credentials directory is  :code:`SECRETS_DIR/output_birdsite`.
This output expects the following files to be present,
with proper contents.
Creating birdsite accounts and getting keys is beyond the scope of this document.
:code:`CONSUMER_KEY`
:code:`CONSUMER_SECRET`
:code:`ACCESS_TOKEN`
:code:`ACCESS_SECRET`

Optionally,
this file can be provided.
This is used to send DMs when errors are encountered.
:code:`OWNER_HANDLE`

----------------------------------
:code:`outputs/output_mastodon.py`
----------------------------------
Credentials directory is  :code:`SECRETS_DIR/output_mastodon`.
This output expects the following files to be present,
with proper contents.
Creating mastodon bot accounts and getting keys is beyond the scope of this document.
:code:`ACCESS_TOKEN`

Optionally,
this file can be provided.
By default,
the output will try to send to https://mastodon.social.
It is recommended to change this,
perhaps to https://botsin.space,
and make sure you make an account there.
:code:`INSTANCE_BASE_URL`

========
Examples
========
I operate several bots using this API,
and can attest to its general stability.

* https://github.com/alixnovosi/dirtyunix_bot
* https://github.com/alixnovosi/weatherbotskeleton
* https://github.com/alixnovosi/isthisska_bot
* https://github.com/alixnovosi/goties_bot
* https://github.com/alixnovosi/nonogram_bot
* https://github.com/alixnovosi/tree_bot
* https://github.com/alixnovosi/knowsska_bot
