"""Tests for base botskeleton."""
import os
from shutil import copyfile
from typing import Generator

import pytest

import botskeleton

HERE = os.path.abspath(os.path.dirname(__file__))
JSON = os.path.join(HERE, "json")


def test_no_secrets_dir_fails() -> None:
    try:
        bs = botskeleton.BotSkeleton()
        pytest.fail("Should throw exception for no secrets dir.")
    except botskeleton.BotSkeletonException as e:
        pass


# need to test individual outputs in output_X tests, because they might need files present.
def test_outputs_start_inactive(testdir: str) -> None:
    bs = botskeleton.BotSkeleton(secrets_dir=testdir)

    # it would be funny to make this a mapped lambda
    for _, output in bs.outputs.items():
        assert not output["active"]


def test_load_null_history(testdir: str) -> None:
    name = "foobot"
    bs = botskeleton.BotSkeleton(bot_name=name, secrets_dir=testdir)

    assert bs.history == []

    open(bs.history_filename, "w").close()
    bs.load_history()
    assert bs.history == []

    os.remove(bs.history_filename)
    os.remove(f"{bs.history_filename}.bak")


def test_load_existing_modern_history(testdir: str, testhist: str) -> None:
    bs = botskeleton.BotSkeleton(secrets_dir=testdir, history_filename=testhist)
    bs.load_history()

    assert bs.history != []
    assert len(bs.history) == 2


def test_convert_legacy_history(testdir: str, legacyhist: str, hoistedhist: str) -> None:
    bs = botskeleton.BotSkeleton(secrets_dir=testdir, history_filename=legacyhist)
    bs.load_history()

    assert bs.history != []

    # compare against testdir - they should be the same in structure if not content.
    mbs = botskeleton.BotSkeleton(secrets_dir=testdir, history_filename=hoistedhist)
    mbs.load_history()

    assert len(bs.history) == len(mbs.history)
    for i, elem in enumerate(bs.history):
        melem = mbs.history[i]
        for key, item in elem.__dict__.items():
            print(f"item: {str(item)}\nitem {str(melem.__dict__[key])}")
            assert str(item) == str(melem.__dict__[key])


# regression test for the history corruption snafu.
def test_repair_corrupted_history(testdir: str, corruptedhist: str, repairedcorruptedhist: str
                                  ) -> None:
    bs = botskeleton.BotSkeleton(secrets_dir=testdir, history_filename=corruptedhist)
    bs.load_history()

    assert bs.history != []

    # compare against repairedhist. they should be identical.
    mbs = botskeleton.BotSkeleton(secrets_dir=testdir, history_filename=repairedcorruptedhist)
    mbs.load_history()

    assert mbs.history != []

    assert len(bs.history) == len(mbs.history)
    for i, elem in enumerate(bs.history):
        melem = mbs.history[i]
        for key, item in elem.__dict__.items():
            print(f"item: {str(item)}\nitem {str(melem.__dict__[key])}")
            assert str(item) == str(melem.__dict__[key])


def test_idempotency(testdir: str, testhist: str) -> None:
    bs = botskeleton.BotSkeleton(secrets_dir=testdir, history_filename=testhist)
    bs.load_history()
    bs.update_history()

    identical = True
    hist_source = os.path.join(JSON, "test_entries.json")
    with open(testhist, "r") as f1, open(hist_source, "r") as f2:
        for line1, line2 in zip(f1, f2):
            if line1 != line2:
                print(f"{line1}\n{line2}")
                identical = False
                break

    if not identical:
        pytest.fail("Test history changed when it shouldn't have been.")


# @pytest.fixture(scope="function")
# def mastodon_creds(testdir: str) -> str:
#     directory = os.path.join(testdir, "credentials_mastodon")
#     os.mkdir(directory)
#     yield directory
#     os.rmdir(directory)


@pytest.fixture(scope="function")
def testhist(testdir: str) -> Generator[str, str, None]:
    hist_source = os.path.join(JSON, "test_entries.json")
    hist_file = os.path.join(testdir, "test.json")
    copyfile(hist_source, hist_file)
    yield hist_file
    os.remove(hist_file)


@pytest.fixture(scope="function")
def legacyhist(testdir: str) -> Generator[str, str, None]:
    hist_source = os.path.join(JSON, "legacy_entries.json")
    hist_file = os.path.join(testdir, "legacy.json")
    copyfile(hist_source, hist_file)
    yield hist_file
    os.remove(hist_file)


@pytest.fixture(scope="function")
def hoistedhist(testdir: str) -> Generator[str, str, None]:
    hist_source = os.path.join(JSON, "legacy_hoisted_entries.json")
    hist_file = os.path.join(testdir, "hoisted.json")
    copyfile(hist_source, hist_file)
    yield hist_file
    os.remove(hist_file)


@pytest.fixture(scope="function")
def corruptedhist(testdir: str) -> Generator[str, str, None]:
    hist_source = os.path.join(JSON, "corrupted_entries.json")
    hist_file = os.path.join(testdir, "corrupted.json")
    copyfile(hist_source, hist_file)
    yield hist_file
    os.remove(hist_file)


@pytest.fixture(scope="function")
def repairedcorruptedhist(testdir: str) -> Generator[str, str, None]:
    hist_source = os.path.join(JSON, "repaired_corrupted_entries.json")
    hist_file = os.path.join(testdir, "repaired.json")
    copyfile(hist_source, hist_file)
    yield hist_file
    os.remove(hist_file)


@pytest.fixture(scope="module")
def testdir() -> Generator[str, str, None]:
    directory = os.path.join(HERE, "testing_playground")
    os.mkdir(directory)
    yield directory
    os.rmdir(directory)
