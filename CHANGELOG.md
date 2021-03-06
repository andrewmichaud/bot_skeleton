### 3.3.6 (2019-07-02):
#### phony version due to pypi fatfinger

### 3.3.5 (2019-07-02):
#### even less verbosity
* BUGFIX
    * make logs even less verbose by not logging tweet/toot output.

### 3.3.4 (2019-07-02):
#### verbosity
* BUGFIX
    * make logs somewhat less verbose by not logging full history on load/save.

### 3.3.3 (2019-05-30):
#### nope
* BUGFIX
    * drewtilities was splitting logs on second instead of day.

### 3.3.2 (2019-05-30):
#### dependency repin
hopefully last update today

### 3.3.1 (2019-05-30):
#### typing fix
* BUGFIX
    * fix typing of one method.

### 3.3.0 (2019-05-30):
#### better log handling
* FEATURE
    * use botskeleton's new date rotated logs.
    * pass arguments from re-exposed drewtilities log helper correctly.

### 3.2.6 (2019-03-20):
#### correct argument handling
* BUGFIX
    * my recent attempts to allow keyword AND positional arguments in botskeleton while leaning
    towards the keyword arguments was flawed.
    you couldn't call the methods at all without positional arguments.
    this fixes that,
    handling arguments correctly.
    there's even a nice-ish error message.
    * birdsite needs a non-empty caption if you're doing captions at all.
    I've resolved this by putting in a sensible default,
    to be used if no caption is provided when uploading an image/images.

### 3.2.5 (2019-03-11):
#### html unescaping
* BUGFIX
    * both birdsite and mastodon batch reply would give HTML-encoded strings to the caller.
    this runs html.unescape on the strings to turn things like &gt; back into >.

### 3.2.4 (2019-03-08):
#### dm manual fix
* BUGFIX
    * birdsite dm was entirely broken without me noticing,
    because birdsite changed the API and tweepy hasn't yet adapted.
    fixed with a manual block similar to how caption upload is done.
    * add another check when procesing error to record,
    in case error can't be json dumped.

* DEV
    * make _handle_caption_upload and _upload_caption "private" with the leading underscore.
    * force keyword-only args in handle_error.
    * have batch_reply handle target handle either with or without a leading "@".

### 3.2.3 (2019-03-08):
#### more error handling
* BUGFIX
    * batch reply won't crash on a duplicate message on the birdsite output.

### 3.2.2 (2019-03-08):
#### correct batch reply
* BUGFIX
    * Batch reply for both birdsite and mastodon was broken.
    * Fix birdsite reply to get the full message text correctly.
    * Fix mastodon reply to get the correct target account or fail out.

### 3.2.1 (2019-03-07):
#### small fix
* BUGFIX
    * botskeleton send passed the wrong argument in,
    causing all calls to fail if only position argument text was provided.

### 3.2.0 (2019-03-07):
#### batch reply functionality
* FEATURES
    * Can now reply in batch to a target user with perform_batch_reply().
    * You need to supply a callback,
    and a target per service,
    and optionally some other fields,
    and the callback will be used to reply to a number of their recent tweets (number configurable)

* BUGFIXES
    * Permit writing lists as JSON from IterationRecord,
    needed to support lists of OutputRecord.
    * Make _repair a little more robust,
    and have it assume less.
    * Don't try to _repair legacy tweet records,
    this is the wrong behavior and I'm not sure what would happen.

* DEV
    * Make all API methods prefer keyword arguments,
    though positional arguments will still be allowed.
    * All internal methods now use only keyword arguments (or at least most do).
    * Use verbose docstrings that can be formatted as documentation,
    and eventually I'll do that.
    * Expect python3.7 support and update travisCI config appropriately.

### 3.1.3 (2019-03-06):
#### bugfix
* BUGFIX
    * _repair method would not handle extra keys correctly and would fail out.

### 3.1.2 (2019-03-05):
#### Dependency Updates
* DEV
    * Pin new dependencies.

### 3.1.1 (2019-03-05):
#### Dependency Updates
* DEV
    * Pin new dependencies.
    * Get fix from drewtilities.

### 3.1.0 (2018-09-23):
#### Various
* FEATURES
    * Can now upload captions when sending media posts.
    * Provide list of captions alongside files in API calls.
      If there are less captions than files, empty ("") captions will be filled in.

* BUGFIXES
    * Fix history corruption bug that led to nested "output_records".
    * Fix trying inactive outputs on media calls.

* DEV
    * Unit testing/CI set up. Basic unit tests for built-in outputs and history handling.
    * Test added for the fixed history bug.
    * Test added for legacy history conversion, which was kind of just implemented in the previous
      version, without testing.

### 3.0.2 (2018-08-30):
#### Multi-output bugfixes
* BREAKING CHANGES
    * upload_media had to go to make multi-output work in a reasonable way. I did this without
      thinking, which is why 2.2.0 wasn't marked as breaking. I realized I didn't have an easy way
      to restore it, so I'm just admitting this is breaking now.  Replace calls to upload_media
      followed by send_with_many_media just with send_with_many_media - it will do the upload_media
      appropriate for the given service.

* BUGFIXES
    * send_with_many_media in outputs has unnecessary (and broken?) use of splat operator
    * mastodon actually extremely misused splats
    * didn't pass up extra keys while adapting old birdsite records to new multirecords
    * mastodon output didn't pass media ids when sending correctly, meaning images never made it to
      toots

### 2.2.0 (2018-08-17):
#### Multi-output
* FEATURES
    * Support more than one site!!!
    * Rework output from skeleton so it doesn't assume only one site output.
    * Move birdsite to a new output separate from the main one.
    * Add support for Mastodon.
    * Change record formatting to multi-output site, convert old records in-place.

###### NOTE:
Entries beyond this point are backfilled.
They should be relatively accurate, but won't be exact.

### 2.1.0 (not actually tagged)
#### Error handling
* DEV/BUGFIXES
    * add framework for handling errors
    * call error handler for errors
    * will call out to dm_sos if it can't handle the error
    * add default handler for birdsite's duplicate tweet error, which bots hit a lot

### 2.0.5 (also 2.0.3-2.0.4) (2018-05-22):
#### Bugfixes
* DEV/BUGFIXES
    * pass over errors a few more times to make them store correctly and not crash the program
    * JSON-dump their dict when creating the TweetRecord
    * also do some type-checking when trying to assume things about error structure

### 2.0.2 (2018-04-18):
#### DREWTILITIES
* DEV/BUGFIX
    * we expect errors to be objects, so just pass the whole object in TweetRecords

### 2.0.1 (2018-01-02):
#### DREWTILITIES
* DEV/BUGFIX
    * errors can't be indexed, just stringify them when storing in TweetRecords

### 2.0.0 (2017-12-14):
#### DREWTILITIES
* DEV
    * use drewtilities package (same author) for random_line, log setup, rate limiting
    * remove those methods from this package
    * store log object on botskeleton object
    * store error records when errors happen
    * upload_media should also store history items
    * TweepErrors are a supertype of tweepy.RateLimitError, so we don't have to catch both
    * remove some unused variables
    * try to save whole error in TweetRecord

### 1.2.2 (2017-11-16):
#### README change
* DEV/BUGFIX
    * Also forgot that the call is math.ceil, not math.ceiling.

### 1.2.1 (2017-11-16):
#### README change
* DEV/BUGFIX
    * Forgot to import math in last commit, which is needed.

### 1.2.0 (2017-11-09):
#### README change
* FEATURE
    * Show clint progress bars on sleeps.
    * Show progress on imported rate_limited calls.

* DEV
    * Make README an RST file, which PyPI likes more, and GitHub is fine with.

### 1.1.0 (2017-11-03):
#### Bugfixes
* FEATURE
    * Add a history feature. TweetRecord objects store tweet id, tweet text, filename, and some
      extra keys (if the caller has them).
    * History updated on every send-type call, and saved/loaded from disk.
    * send_with_media will save media_ids as well.
    * History items will generate and store timestamps.
    * Also add a nap function to sleep for some time. Based on delay passed into constructor.
    * Caller can call to sleep between send calls.

* DEV
    * Just import path from os so we don't have to do os.path one million times.

### 1.0.5 (2017-10-26):
#### Bugfixes
* BUGFIXES
    * Didn't pass owner_handle to send_direct_message correctly, so that didn't work. Fix that.
    * Fix a typo'd call to send_dm_sos.
    * Fix some missing spaces in send_dm_sos calls.
    * Actual API send_direct_message needs user/text params - call that correctly.

### 1.0.4 (2017-10-26):
#### random_line, some 3.6 passes
* FEATURES
    * Add random_line function, and expose that.
    * Add send_with_one_media to send text and one image.
    * Expose set_up_logging to callers.

* DEV
    * Use python3.6 format strings, everywhere.

### 1.0.3 (2017-10-24):
#### catch rate limit errors
* BUGFIXES:
    * Tweepy throws RateLimitErrors separate from TweepErrors. Catch both separately in API calls.

### 1.0.2 (2017-10-24):
#### secrets_dir bugfixes
* BUGFIXES:
    * SECRETS_DIR was not specified correctly - it ended up wherever the library was on disk.
      Update so it must be provided to the skeleton. This allows caller to put it wherever they
      want, useful for when you're using bots in production.

### 1.0.1 (2017-10-24):
#### initial bugfixes
* BUGFIXES:
    * Added \_\_init\_\_.py in botskeleton so bots can import it correctly.
    * Fixed class name for proper new-style class.
    * Fixed name in setup.py and specified python_requires correctly.

### 1.0.0 (2017-10-24):
#### Initial release
* Features
    * Basic bot library ripped from shared code from #NaBoMaMo 2016 bots.
    * basic repo stuff like LICENSE, setup.py
