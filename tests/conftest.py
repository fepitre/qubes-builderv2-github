import os
import random
import shutil
import string
import subprocess
from pathlib import Path

import pytest
from github import Github

PROJECT_PATH = Path(__file__).resolve().parents[1]
DEFAULT_BUILDER_CONF = PROJECT_PATH / "tests/builder.yml"


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for _ in range(length))
    return result_str


@pytest.fixture(scope="session")
def token():
    github_api_key = os.environ.get("GITHUB_API_KEY")
    if not github_api_key:
        raise ValueError("Cannot find GITHUB_API_TOKEN.")
    return github_api_key


@pytest.fixture(scope="session")
def github_repository(token):
    g = Github(token)
    user = g.get_user()
    if user.login != "fepitre2-bot":
        raise ValueError(f"Unexpected user '{user}'.")
    repo_name = f"tests-{get_random_string(16)}"
    repo = user.create_repo(repo_name)
    yield repo
    repo.delete()


@pytest.fixture(scope="session")
def workdir(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("github-")

    # Better copy testing keyring into a separate directory to prevent locks inside
    # local sources (when executed locally).
    gnupghome = f"{tmpdir}/.gnupg"
    shutil.copytree(PROJECT_PATH / "tests/gnupg", gnupghome)
    os.chmod(gnupghome, 0o700)

    # Copy builder.yml
    shutil.copy2(DEFAULT_BUILDER_CONF, tmpdir)

    with open(f"{tmpdir}/builder.yml", "a") as f:
        f.write(
            f"""
artifacts-dir: {tmpdir}/artifacts

repository-upload-remote-host:
  rpm: {tmpdir}/repo/rpm/r4.2
  deb: {tmpdir}/repo/deb/r4.2
  iso: {tmpdir}/repo/iso/r4.2

executor:
  type: qubes
  options:
    dispvm: "qubes-builder-dvm"
"""
        )

    # Clone qubes-builderv2
    subprocess.run(
        [
            "git",
            "-C",
            str(tmpdir),
            "clone",
            "-b",
            "main",
            "--recurse-submodules",
            "https://github.com/QubesOS/qubes-builderv2",
        ]
    )

    shutil.copytree(PROJECT_PATH, tmpdir / "qubes-builder-github")

    env = os.environ.copy()
    # Enforce keyring location
    env["GNUPGHOME"] = tmpdir / ".gnupg"
    # We prevent rpm to find ~/.rpmmacros and put logs into workdir
    env["HOME"] = tmpdir
    # Set PYTHONPATH with cloned qubes-builderv2
    env[
        "PYTHONPATH"
    ] = f"{tmpdir / 'qubes-builderv2'!s}:{os.environ.get('PYTHONPATH','')}"

    yield tmpdir, env
    # shutil.rmtree(tmpdir)
