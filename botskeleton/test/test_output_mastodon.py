import os
from shutil import copyfile
from typing import Any, Generator

import pytest

import botskeleton

HERE = os.path.abspath(os.path.dirname(__file__))

def test_mastodon_activates_correctly(testdir: str, credentials: str) -> None:
    bs = botskeleton.BotSkeleton(secrets_dir=testdir)

    assert(bs.outputs["mastodon"]["active"])

def test_mastodon_activates_with_instance_id_correctly(testdir: str, credentials: str) -> None:
    # no instance set
    bs = botskeleton.BotSkeleton(secrets_dir=testdir)

    assert(bs.outputs["mastodon"]["active"])
    mastodon_obj: Any = bs.outputs["mastodon"]["obj"]
    assert(mastodon_obj.instance_base_url == "https://mastodon.social")

    TESTSTR = "https://butts.butts"
    TESTFILE = os.path.join(credentials, "INSTANCE_BASE_URL")
    with open(TESTFILE, "w") as f:
        f.write(TESTSTR)

    bs = botskeleton.BotSkeleton(secrets_dir=testdir)

    assert(bs.outputs["mastodon"]["active"])
    mastodon_obj = bs.outputs["mastodon"]["obj"]
    assert(mastodon_obj.instance_base_url == TESTSTR)

    os.remove(TESTFILE)


@pytest.fixture(scope="function")
def credentials(testdir: str) -> Generator[str, str, None]:
    credentials_mastodon = os.path.join(testdir, "credentials_mastodon")
    os.mkdir(credentials_mastodon)

    files = ["ACCESS_TOKEN"]
    for file in files:
        open(os.path.join(credentials_mastodon, file), "a").close()

    yield credentials_mastodon

    for file in files:
        os.remove(os.path.join(credentials_mastodon, file))

    os.rmdir(credentials_mastodon)

@pytest.fixture(scope="function")
def testdir() -> Generator[str, str, None]:
    directory = os.path.join(HERE, "testing_playground")
    os.mkdir(directory)

    yield directory

    os.rmdir(directory)
