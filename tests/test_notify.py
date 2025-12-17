import datetime
import importlib.util
import subprocess
from pathlib import Path

from conftest import get_issue
from qubesbuilder.distribution import QubesDistribution
from utils.notify_issues import NotifyIssueCli

PROJECT_PATH = Path(__file__).resolve().parents[1]
DEFAULT_BUILDER_CONF = PROJECT_PATH / "tests/builder.yml"

github_action_spec = importlib.util.spec_from_file_location(
    "github_action", str(PROJECT_PATH / "github-action.py")
)
github_action = importlib.util.module_from_spec(github_action_spec)
github_action_spec.loader.exec_module(github_action)

AutoActionError = github_action.AutoActionError
format_additional_info = github_action.format_additional_info


def test_notify_000_template_build_success_upload(
    token, github_repository, workdir
):
    tmpdir, env = workdir
    build_log = "dummy"
    # We need seconds because we create multiple issues successively.
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d%H%M%s")
    template_name = "fedora-42"
    package_name = f"qubes-template-{template_name}-4.2.0-{timestamp}"
    distribution = "vm-fc42"

    #
    # build
    #

    status = "building"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    issue_title = f"qubes-template-{template_name} 4.2.0-{timestamp} (r4.2)"
    issue_desc = f"""Template {template_name} 4.2.0-{timestamp} for Qubes OS r4.2, see comments below for details and build status.

If you're release manager, you can issue GPG-inline signed command (depending on template):

* `Upload-template r4.2 {template_name} 4.2.0-{timestamp} templates-itl` (available 5 days from now)
* `Upload-template r4.2 {template_name} 4.2.0-{timestamp} templates-community` (available 5 days from now)

Above commands will work only if package in testing repository isn't superseded by newer version.

For more information on how to test this update, please take a look at https://www.qubes-os.org/doc/testing/#updates.
"""

    issue = get_issue(issue_title=issue_title, repository=github_repository)

    # Check if issue has been created
    assert issue is not None

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-{status}"

    # Check description
    assert issue.body == issue_desc

    #
    # built
    #
    status = "built"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    #
    # upload
    #
    upload_repository = "templates-itl-testing"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "upload",
        "r4.2",
        tmpdir,
        package_name,
        distribution,
        "uploaded",
        upload_repository,
        str(tmpdir / "state_file"),
        str(tmpdir / "stable_state_file"),
    ]
    subprocess.run(cmd, check=True, env=env)

    # Refresh issue object
    issue.update()

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-testing"

    # Check that comment exists
    comments = list(issue.get_comments())
    assert len(comments) == 2
    assert (
        comments[0].body
        == f"Template {template_name}-4.2.0-{timestamp} was built ([build log]({build_log}))."
    )
    assert (
        comments[1].body
        == f"Template {template_name}-4.2.0-{timestamp} was uploaded to {upload_repository} repository."
    )


def test_notify_001_template_build_failure(token, github_repository, workdir):
    tmpdir, env = workdir
    build_log = "dummy"
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d%H%M%s")
    template_name = "debian-13"
    package_name = f"qubes-template-{template_name}-4.2.0-{timestamp}"
    distribution = "vm-trixie"

    #
    # build
    #

    status = "building"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    issue_title = f"qubes-template-{template_name} 4.2.0-{timestamp} (r4.2)"
    issue = get_issue(issue_title=issue_title, repository=github_repository)

    #
    # failure
    #

    status = "failed"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    # Refresh issue object
    issue.update()

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-failed"

    # Check that comment exists
    comments = list(issue.get_comments())
    assert len(comments) == 1
    assert (
        comments[0].body
        == f"Template {template_name}-4.2.0-{timestamp} failed to build ([build log]({build_log}))."
    )


def test_notify_002_template_build_success_upload_failure(
    token, github_repository, workdir
):
    tmpdir, env = workdir
    build_log = "dummy"
    # We need seconds because we create multiple issues successively.
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d%H%M%s")
    template_name = "whonix-gateway-17"
    package_name = f"qubes-template-{template_name}-4.2.0-{timestamp}"
    distribution = "vm-bookworm"

    #
    # build
    #

    status = "building"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    issue_title = f"qubes-template-{template_name} 4.2.0-{timestamp} (r4.2)"
    issue_desc = f"""Template {template_name} 4.2.0-{timestamp} for Qubes OS r4.2, see comments below for details and build status.

If you're release manager, you can issue GPG-inline signed command (depending on template):

* `Upload-template r4.2 {template_name} 4.2.0-{timestamp} templates-itl` (available 5 days from now)
* `Upload-template r4.2 {template_name} 4.2.0-{timestamp} templates-community` (available 5 days from now)

Above commands will work only if package in testing repository isn't superseded by newer version.

For more information on how to test this update, please take a look at https://www.qubes-os.org/doc/testing/#updates.
"""

    issue = get_issue(issue_title=issue_title, repository=github_repository)

    # Check if issue has been created
    assert issue is not None

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-{status}"

    # Check description
    assert issue.body == issue_desc

    #
    # built
    #
    status = "built"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    #
    # upload testing
    #
    upload_repository = "templates-community-testing"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "upload",
        "r4.2",
        tmpdir,
        package_name,
        distribution,
        "uploaded",
        upload_repository,
        str(tmpdir / "state_file"),
        str(tmpdir / "stable_state_file"),
    ]
    subprocess.run(cmd, check=True, env=env)

    #
    # upload stable
    #
    upload_repository = "templates-community"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "upload",
        "r4.2",
        tmpdir,
        package_name,
        distribution,
        "failed",
        upload_repository,
        str(tmpdir / "state_file"),
        str(tmpdir / "stable_state_file"),
    ]
    subprocess.run(cmd, check=True, env=env)

    # Refresh issue object
    issue.update()

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-testing"

    # Check that comment exists
    comments = list(issue.get_comments())
    assert len(comments) == 3
    assert (
        comments[0].body
        == f"Template {template_name}-4.2.0-{timestamp} was built ([build log]({build_log}))."
    )
    assert (
        comments[1].body
        == f"Template {template_name}-4.2.0-{timestamp} was uploaded to {upload_repository}-testing repository."
    )
    assert (
        comments[2].body
        == f"Template {template_name}-4.2.0-{timestamp} failed to upload to {upload_repository} repository ([build log](dummy))."
    )


def test_notify_020_iso_build_success_upload(token, github_repository, workdir):
    tmpdir, env = workdir
    build_log = "dummy"
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d%H%M%s")
    distribution = "host-fc42"
    package_name = f"iso-{distribution}-4.2.{timestamp}"

    #
    # build
    #

    status = "building"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    issue_title = f"iso 4.2.{timestamp} (r4.2)"
    issue_desc = f"""ISO 4.2.{timestamp} for Qubes OS r4.2, see comments below for details and build status.

For more information on how to test this update, please take a look at https://www.qubes-os.org/doc/testing/#updates.
"""

    issue = get_issue(issue_title=issue_title, repository=github_repository)

    # Check if issue has been created
    assert issue is not None

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-{status}"

    # Check description
    assert issue.body == issue_desc

    #
    # built
    #

    status = "built"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    #
    # upload
    #
    upload_repository = "iso-testing"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "upload",
        "r4.2",
        tmpdir,
        package_name,
        distribution,
        "uploaded",
        upload_repository,
        str(tmpdir / "state_file"),
        str(tmpdir / "stable_state_file"),
    ]
    subprocess.run(cmd, check=True, env=env)

    # Refresh issue object
    issue.update()

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-testing"

    # Check that comment exists
    comments = list(issue.get_comments())
    assert len(comments) == 2
    assert (
        comments[0].body
        == f"ISO for r4.2 was built ([build log]({build_log}))."
    )
    assert (
        comments[1].body == f"ISO for r4.2 was uploaded to testing repository."
    )


def test_notify_021_iso_build_failure(token, github_repository, workdir):
    tmpdir, env = workdir
    build_log = "dummy"
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d%H%M%s")
    distribution = "host-fc42"
    package_name = f"iso-{distribution}-4.2.{timestamp}"

    #
    # build
    #

    status = "building"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    issue_title = f"iso 4.2.{timestamp} (r4.2)"
    issue = get_issue(issue_title=issue_title, repository=github_repository)

    #
    # failure
    #

    status = "failed"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    # Refresh issue object
    issue.update()

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-failed"

    # Check that comment exists
    comments = list(issue.get_comments())
    assert len(comments) == 1
    assert (
        comments[0].body
        == f"ISO for r4.2 failed to build ([build log](dummy))."
    )


def test_notify_040_component_build_success_upload(
    token, github_repository, workdir
):
    tmpdir, env = workdir
    build_log = "dummy"
    distribution = "vm-fc42"
    package_name = "core-admin-linux"
    version = "4.2.6"

    subprocess.run(
        [
            "git",
            "-C",
            str(tmpdir),
            "clone",
            "-b",
            f"v{version}",
            f"https://github.com/QubesOS/qubes-{package_name}",
            package_name,
        ],
        check=True,
    )

    #
    # build
    #

    status = "building"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir / package_name),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    # FIXME: improve generation of expected desc?
    issue_desc = f"""Update of {package_name} to v4.2.6 for Qubes OS r4.2, see comments below for details and build status.

From commit: https://github.com/QubesOS/qubes-{package_name}/commit/a6ff3071aa650f6ae9639c07e133eb27cffd91df

[Changes since previous version](https://github.com/QubesOS/qubes-{package_name}/compare/v4.2.5...v4.2.6):
QubesOS/qubes-{package_name}@a6ff307 version 4.2.6
QubesOS/qubes-{package_name}@3ddb7e5 Merge remote-tracking branch 'origin/pr/118'
QubesOS/qubes-{package_name}@690f1a7 qubes-vm-update: summary in the end of output
QubesOS/qubes-{package_name}@d362831 Move the zvol ignore rules much earlier in the udev chain of events.
QubesOS/qubes-{package_name}@241a5f7 Handle every other error condition explicitly and add -e.
QubesOS/qubes-{package_name}@dd6d3ee Fix prefix.
QubesOS/qubes-{package_name}@7ca327a Fix build.
QubesOS/qubes-{package_name}@65a1c29 This variable does not point to the right place in 64 bit systems.
QubesOS/qubes-{package_name}@26ca480 Add missing files.
QubesOS/qubes-{package_name}@2da3cf1 Tab instead of space.
QubesOS/qubes-{package_name}@9984d65 Ignore all ZFS volumes that are part of a Qubes storage pool.

Referenced issues:


If you're release manager, you can issue GPG-inline signed command:

* `Upload-component r4.2 {package_name} a6ff3071aa650f6ae9639c07e133eb27cffd91df current all` (available 5 days from now)
* `Upload-component r4.2 {package_name} a6ff3071aa650f6ae9639c07e133eb27cffd91df security-testing all`

You can choose subset of distributions like:
* `Upload-component r4.2 {package_name} a6ff3071aa650f6ae9639c07e133eb27cffd91df current vm-bookworm,vm-fc37` (available 5 days from now)

Above commands will work only if packages in current-testing repository were built from given commit (i.e. no new version superseded it).

For more information on how to test this update, please take a look at https://www.qubes-os.org/doc/testing/#updates.
"""
    issue_title = f"{package_name} v{version} (r4.2)"
    issue = get_issue(issue_title=issue_title, repository=github_repository)

    # Check if issue has been created
    assert issue is not None

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-{distribution}-{status}"

    # Check description
    assert issue.body == issue_desc

    # with open(tmpdir / "state_file", "w") as fd:
    #     fd.write("1178add9fcb18e865b0fc3408cfbd2baa1391024")

    with open(tmpdir / "stable_state_file", "w") as fd:
        fd.write("1178add9fcb18e865b0fc3408cfbd2baa1391024")

    #
    # built
    #
    status = "built"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "build",
        "r4.2",
        str(tmpdir / package_name),
        package_name,
        distribution,
        status,
    ]
    subprocess.run(cmd, check=True, env=env)

    # Refresh issue object
    issue.update()

    #
    # upload
    #
    upload_repository = "current-testing"
    cmd = [
        str(PROJECT_PATH / "utils/notify_issues.py"),
        f"--build-log={build_log}",
        f"--message-templates-dir={PROJECT_PATH}/templates",
        f"--github-report-repo-name={github_repository.full_name}",
        "upload",
        "r4.2",
        str(tmpdir / package_name),
        package_name,
        distribution,
        "uploaded",
        upload_repository,
        str(tmpdir / "state_file"),
        str(tmpdir / "stable_state_file"),
    ]
    subprocess.run(cmd, check=True, env=env)

    # Refresh issue object
    issue.update()

    # Only one status tag
    assert len(issue.labels) == 1
    assert issue.labels[0].name == f"r4.2-{distribution}-cur-test"

    # Check that comment exists
    comments = list(issue.get_comments())
    assert len(comments) == 2
    assert (
        comments[0].body
        == f"Package for vm-fc42 was built ([build log]({build_log}))."
    )
    assert (
        comments[1].body
        == f"Package for vm-fc42 was uploaded to current-testing repository."
    )


def test_notify_100_includes_tail(token, github_repository, workdir):
    tmpdir, env = workdir

    distribution = QubesDistribution("host-fc41")
    build_log = "dummy"
    package_name = "core-admin-linux"
    version = "4.2.6"

    subprocess.run(
        [
            "git",
            "-C",
            str(tmpdir),
            "clone",
            "-b",
            f"v{version}",
            f"https://github.com/QubesOS/qubes-{package_name}",
            package_name,
        ],
        check=True,
    )

    exc = ValueError("Invalid something or broken stuff")
    tail = "\ntraceback: boom\n           bim bada boum"
    additional_info = format_additional_info(base=exc.args, tail=tail)

    cli = NotifyIssueCli(
        token=token,
        release_name="r4.3",
        source_dir=Path(tmpdir) / package_name,
        github_report_repo_name=github_repository.full_name,
        message_templates_dir=PROJECT_PATH / "templates",
        min_age_days=0,
    )

    cli.run(
        command="build",
        dist=distribution,
        package_name=package_name,
        repository_type="current-testing",
        build_status="building",
    )

    cli.run(
        command="build",
        dist=distribution,
        package_name=package_name,
        repository_type="current-testing",
        build_status="failed",
        build_log=build_log,
        additional_info=additional_info,
    )

    issue_title = f"{package_name} v{version} (r4.3)"
    issue = get_issue(issue_title=issue_title, repository=github_repository)

    comments = list(issue.get_comments())
    assert len(comments) == 1

    body = comments[0].body
    assert "Log tail (last ~30 lines)" in body
    assert "traceback: boom" in body
    assert "bim bada boum" in body
