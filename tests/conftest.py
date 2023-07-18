import os
import random
import shutil
import string
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from github import Github

PROJECT_PATH = Path(__file__).resolve().parents[1]
DEFAULT_BUILDER_CONF = PROJECT_PATH / "tests/builder.yml"


# qubesbuilder/config
def deep_merge(a: dict, b: dict, allow_append: bool = False) -> dict:
    result = deepcopy(a)
    for b_key, b_value in b.items():
        a_value = result.get(b_key, None)
        if isinstance(a_value, dict) and isinstance(b_value, dict):
            result[b_key] = deep_merge(a_value, b_value, allow_append)
        else:
            if allow_append and isinstance(result.get(b_key, None), list):
                result[b_key] += deepcopy(b_value)
            else:
                result[b_key] = deepcopy(b_value)
    return result


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for _ in range(length))
    return result_str


@pytest.fixture(scope="session")
def token():
    github_api_key = os.environ.get("GITHUB_API_KEY")
    if not github_api_key:
        raise ValueError("Cannot find GITHUB_API_KEY.")
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
    dispvm: "builder-dvm"
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

    if env.get("CACHE_DIR", None):
        shutil.copytree(env["CACHE_DIR"], tmpdir / "artifacts/cache")
    else:
        subprocess.run(
            [
                "./qb",
                "--builder-conf",
                tmpdir / "builder.yml",
                "package",
                "init-cache",
            ],
            cwd=tmpdir / "qubes-builderv2",
        )

    yield tmpdir, env
    # shutil.rmtree(tmpdir)


def set_conf_options(builder_conf, options):
    with open(builder_conf, "r") as f:
        conf = yaml.safe_load(f.read())
    conf = deep_merge(conf, options)
    with open(builder_conf, "w") as f:
        f.write(yaml.dump(conf))


def set_dry_run(builder_conf):
    set_conf_options(builder_conf, {"github": {"dry-run": True}})


def get_issue(issue_title, repository):
    issue = None
    for i in repository.get_issues():
        if i.title == issue_title:
            issue = i
            break
    return issue
