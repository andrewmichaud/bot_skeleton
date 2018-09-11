"""Tests for base botskeleton."""
import os
from shutil import copyfile

import pytest

import botskeleton

HERE = os.path.abspath(os.path.dirname(__file__))

def test_no_secrets_dir_fails() -> None:
    try:
        bs = botskeleton.BotSkeleton()
        pytest.fail("Should throw exception for no secrets dir.")
    except botskeleton.BotSkeletonException as e:
        pass

# need to test individual outputs in output_X tests, because they might need files present.
def test_outputs_start_inactive(testdir) -> None:
    bs = botskeleton.BotSkeleton(secrets_dir=testdir)

    # it would be funny to make this a mapped lambda
    for _, output in bs.outputs.items():
        assert not output["active"]

def test_load_null_history(testdir) -> None:
    name = "foobot"
    bs = botskeleton.BotSkeleton(bot_name=name, secrets_dir=testdir)

    assert bs.history == []

    open(bs.history_filename, "w").close()
    bs.load_history()
    assert bs.history == []

    os.remove(bs.history_filename)
    os.remove(f"{bs.history_filename}.bak")

def test_load_existing_modern_history(testdir, testhist) -> None:
    bs = botskeleton.BotSkeleton(secrets_dir=testdir, history_filename=testhist)
    bs.load_history()

    assert bs.history != []
    assert len(bs.history) == 2

def test_convert_legacy_history(testdir, legacyhist, hoistedhist) -> None:
    bs = botskeleton.BotSkeleton(secrets_dir=testdir, history_filename=legacyhist)
    bs.load_history()

    assert bs.history != []
    assert len(bs.history) == 2

    # compare against testdir - they should be the same in structure if not content.
    mbs = botskeleton.BotSkeleton(secrets_dir=testdir, history_filename=hoistedhist)
    mbs.load_history()

    assert len(bs.history) == len(mbs.history)
    for i, elem in enumerate(bs.history):
        melem = mbs.history[i]
        for key, item in elem.__dict__.items():
            print(f"item: {str(item)}\nitem {str(melem.__dict__[key])}")
            assert str(item) == str(melem.__dict__[key])





@pytest.fixture(scope="function")
def birdsite_creds(testdir: str) -> str:
    directory = os.path.join(testdir, "credentials_birdsite")
    os.mkdir(directory)
    yield directory
    os.rmdir(directory)

@pytest.fixture(scope="function")
def mastodon_creds(testdir: str) -> str:
    directory = os.path.join(testdir, "credentials_mastodon")
    os.mkdir(directory)
    yield directory
    os.rmdir(directory)

@pytest.fixture(scope="function")
def testhist(testdir: str) -> str:
    hist_source = os.path.join(HERE, "test_entries.json")
    hist_file = os.path.join(testdir, "test.json")
    copyfile(hist_source, hist_file)
    yield hist_file
    os.remove(hist_file)

@pytest.fixture(scope="function")
def legacyhist(testdir: str) -> str:
    hist_source = os.path.join(HERE, "legacy_entries.json")
    hist_file = os.path.join(testdir, "legacy.json")
    copyfile(hist_source, hist_file)
    yield hist_file
    os.remove(hist_file)

@pytest.fixture(scope="function")
def hoistedhist(testdir: str) -> str:
    hist_source = os.path.join(HERE, "legacy_hoisted_entries.json")
    hist_file = os.path.join(testdir, "hoisted.json")
    copyfile(hist_source, hist_file)
    yield hist_file
    os.remove(hist_file)

@pytest.fixture(scope="module")
def testdir() -> str:
    directory = os.path.join(HERE, "testing_playground")
    os.mkdir(directory)
    yield directory
    os.rmdir(directory)
