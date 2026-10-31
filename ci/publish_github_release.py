"""Publish one verified default-branch APK to a configured GitHub rolling release."""

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


MARKER = "weartak-plugin-release-v1"
DISPATCH_EVENT = "weartak-plugin-release-published"
OUTPUT = Path("app/build/outputs/apk/release")


class PublishError(Exception):
    pass


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != "https":
            raise PublishError("Refusing non-HTTPS asset redirect.")
        redirect = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirect is not None:
            redirect.remove_header("Authorization")
        return redirect


class GitHub:
    def __init__(self, token, repository):
        self.token = token
        self.repository = repository
        self.opener = urllib.request.build_opener(SafeRedirect())

    def request(self, method, path, data=None, *, binary=False, missing_ok=False):
        host = "https://uploads.github.com" if binary else "https://api.github.com"
        url = f"{host}/repos/{self.repository}" + (f"/{path}" if path else "")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "WearTAK-Forge-release",
        }
        if data is not None and not binary:
            headers["Content-Type"] = "application/json"
            data = json.dumps(data).encode()
        elif binary:
            headers["Content-Type"] = "application/vnd.android.package-archive"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=120) as response:
                content = response.read()
                return json.loads(content) if content else None
        except urllib.error.HTTPError as error:
            if error.code == 404 and missing_ok:
                return None
            raise PublishError(
                f"GitHub {method} {path.split('?')[0]} returned HTTP {error.code}. "
                "Check protected GITHUB_RELEASE_TOKEN permissions and repository setup."
            ) from None
        except urllib.error.URLError:
            raise PublishError(
                "Cannot reach GitHub API. Check runner DNS, HTTPS egress, TLS trust, "
                "and GitHub availability."
            ) from None

    def download_digest(self, asset_id):
        request = urllib.request.Request(
            f"https://api.github.com/repos/{self.repository}/releases/assets/{asset_id}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/octet-stream",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "WearTAK-Forge-release",
            },
        )
        try:
            with self.opener.open(request, timeout=120) as response:
                digest = hashlib.sha256()
                size = 0
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    digest.update(chunk)
                return size, digest.hexdigest()
        except urllib.error.HTTPError as error:
            raise PublishError(f"Asset verification download failed: HTTP {error.code}.") from None
        except urllib.error.URLError:
            raise PublishError("Cannot download uploaded APK for verification.") from None

    def assets(self, release_id):
        items = []
        page = 1
        while True:
            batch = self.request(
                "GET", f"releases/{release_id}/assets?per_page=100&page={page}"
            )
            items.extend(batch)
            if len(batch) < 100:
                return items
            page += 1


def configuration(env):
    if not env.get("CI_DEFAULT_BRANCH") or env.get("CI_COMMIT_BRANCH") != env.get("CI_DEFAULT_BRANCH"):
        raise PublishError("Publishing requires a push to the GitLab default branch.")
    if env.get("CI_COMMIT_REF_PROTECTED") != "true" or env.get("CI_PIPELINE_SOURCE") != "push":
        raise PublishError("Publishing requires a protected default-branch push pipeline.")
    required = (
        "GITHUB_RELEASE_REPOSITORY",
        "GITHUB_RELEASE_TOKEN",
        "GITHUB_RELEASE_TAG",
        "GITHUB_RELEASE_APPLICATION_ID",
        "GITHUB_RELEASE_ASSET_PREFIX",
        "CI_PROJECT_PATH",
        "CI_PROJECT_ID",
        "CI_PIPELINE_IID",
        "CI_PIPELINE_ID",
        "CI_PIPELINE_URL",
        "CI_COMMIT_SHA",
    )
    for name in required:
        if not env.get(name):
            raise PublishError(f"Missing required CI variable {name}.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", env["GITHUB_RELEASE_REPOSITORY"]):
        raise PublishError("Invalid GITHUB_RELEASE_REPOSITORY.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", env["GITHUB_RELEASE_TAG"]):
        raise PublishError("Invalid GITHUB_RELEASE_TAG.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", env["GITHUB_RELEASE_APPLICATION_ID"]):
        raise PublishError("Invalid GITHUB_RELEASE_APPLICATION_ID.")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", env["GITHUB_RELEASE_ASSET_PREFIX"]):
        raise PublishError("Invalid GITHUB_RELEASE_ASSET_PREFIX.")
    for name in ("CI_PROJECT_ID", "CI_PIPELINE_IID", "CI_PIPELINE_ID"):
        if not re.fullmatch(r"[1-9][0-9]*", env[name]):
            raise PublishError(f"Invalid {name}.")
    if not re.fullmatch(r"[0-9a-f]{40,64}", env["CI_COMMIT_SHA"]):
        raise PublishError("Invalid CI_COMMIT_SHA.")
    pipeline_url = urllib.parse.urlsplit(env["CI_PIPELINE_URL"])
    if pipeline_url.scheme != "https" or not pipeline_url.netloc:
        raise PublishError("CI_PIPELINE_URL must be an HTTPS URL.")
    return {
        "repository": env["GITHUB_RELEASE_REPOSITORY"],
        "token": env["GITHUB_RELEASE_TOKEN"],
        "tag": env["GITHUB_RELEASE_TAG"],
        "application_id": env["GITHUB_RELEASE_APPLICATION_ID"],
        "asset_prefix": env["GITHUB_RELEASE_ASSET_PREFIX"],
        "project_path": env["CI_PROJECT_PATH"],
        "project_id": env["CI_PROJECT_ID"],
        "pipeline_iid": int(env["CI_PIPELINE_IID"]),
        "pipeline_id": env["CI_PIPELINE_ID"],
        "pipeline_url": env["CI_PIPELINE_URL"],
        "source_sha": env["CI_COMMIT_SHA"],
    }


def artifact(root, application_id):
    directory = root / OUTPUT
    apks = list(directory.glob("*.apk"))
    if len(apks) != 1 or apks[0].is_symlink() or not apks[0].is_file():
        raise PublishError("Expected exactly one verified release APK.")
    apk = apks[0]
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    checksum = (directory / "verified-apk.sha256").read_text().strip()
    if checksum != f"{digest}  {apk.relative_to(root).as_posix()}":
        raise PublishError("APK does not match signature-verification checksum.")
    metadata = json.loads((directory / "output-metadata.json").read_text())
    elements = metadata.get("elements", [])
    if (
        metadata.get("applicationId") != application_id
        or metadata.get("variantName") != "release"
        or len(elements) != 1
        or elements[0].get("outputFile") != apk.name
    ):
        raise PublishError("Gradle metadata does not match the configured release APK.")
    version = elements[0].get("versionName")
    code = elements[0].get("versionCode")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9A-Za-z.+_-]+", version):
        raise PublishError("Invalid APK versionName.")
    if type(code) is not int or code <= 0:
        raise PublishError("Invalid APK versionCode.")
    return apk, digest, version, code


def release_state(release, project_id, tag):
    matches = re.findall(rf"<!-- {MARKER} (.*?) -->", release.get("body") or "")
    if len(matches) != 1:
        raise PublishError("Rolling release is not automation-owned; refusing to modify it.")
    try:
        state = json.loads(matches[0])
    except json.JSONDecodeError:
        raise PublishError("Rolling release provenance is invalid.") from None
    if (
        not isinstance(state, dict)
        or state.get("project_id") != project_id
        or not isinstance(state.get("pipeline_iid"), int)
        or state["pipeline_iid"] <= 0
        or release.get("tag_name") != tag
        or release.get("prerelease")
    ):
        raise PublishError("Rolling release provenance is invalid; refusing to modify it.")
    return state


def release_asset_name(asset_prefix, version, pipeline_iid):
    filename_version = version.split("+", 1)[0]
    pipeline_version = re.fullmatch(r"(.+)-p([1-9][0-9]*)", filename_version)
    if pipeline_version:
        if int(pipeline_version[2]) != pipeline_iid:
            raise PublishError("APK version pipeline does not match the publishing pipeline.")
        filename_version = pipeline_version[1]
    return f"WearTAK-Plugin-{asset_prefix}-{filename_version}-p{pipeline_iid}.apk"


def publish(api, state, apk, digest, version, code, *, asset_prefix):
    asset_name = release_asset_name(asset_prefix, version, state["pipeline_iid"])
    repository = api.request("GET", "")
    if (
        repository.get("full_name") != state["repository"]
        or repository.get("archived") is not False
        or repository.get("disabled") is not False
    ):
        raise PublishError("Destination must be the configured active GitHub repository.")
    tag_ref = urllib.parse.quote(state["tag"], safe="")
    if not api.request("GET", f"git/ref/tags/{tag_ref}", missing_ok=True):
        raise PublishError(
            f"Pre-create fixed release tag {state['tag']} on the GitHub destination. "
            "Publisher never creates or moves tags."
        )
    release = api.request(
        "GET", f"releases/tags/{tag_ref}", missing_ok=True
    )
    if release:
        previous = release_state(release, state["project_id"], state["tag"])
        if previous["pipeline_iid"] > state["pipeline_iid"]:
            print("Skipping older pipeline; newer pipeline already owns the rolling release.")
            return
        if previous["pipeline_iid"] == state["pipeline_iid"] and (
            previous.get("source_sha") != state["source_sha"]
            or previous.get("sha256") != digest
        ):
            raise PublishError("Same pipeline has different source/artifact; refusing replacement.")

    state = dict(state, sha256=digest)
    title = f"TAK.gov Forge CI/CD Pipeline Release ({version}-p{state['pipeline_iid']})"
    body = (
        "Automatically published stable WearTAK plugin build.\n\n"
        f"- APK version: **{version}** (versionCode **{code}**)\n"
        f"- GitLab project: **{state['project_path']}**\n"
        f"- Pipeline: **{state['pipeline_id']}** ({state['pipeline_url']})\n"
        f"- Source commit: `{state['source_sha']}`\n"
        f"- SHA256: `{digest}`\n\n"
        f"<!-- {MARKER} {json.dumps(state, sort_keys=True)} -->"
    )
    if not release:
        release = api.request(
            "POST",
            "releases",
            {
                "tag_name": state["tag"],
                "name": title,
                "body": body,
                "draft": True,
                "prerelease": False,
                "make_latest": "false",
            },
        )
    release_id = release["id"]
    assets = api.assets(release_id)
    matches = [item for item in assets if item.get("name") == asset_name]
    if len(matches) > 1:
        raise PublishError("Duplicate publisher asset names; refusing to modify release.")
    if matches:
        uploaded = matches[0]
        if (
            uploaded.get("label") != asset_name
            or api.download_digest(uploaded["id"]) != (apk.stat().st_size, digest)
        ):
            raise PublishError("Existing asset differs from verified APK; refusing replacement.")
    else:
        query = urllib.parse.urlencode({"name": asset_name, "label": asset_name})
        uploaded = api.request(
            "POST",
            f"releases/{release_id}/assets?{query}",
            apk.read_bytes(),
            binary=True,
        )
    size = apk.stat().st_size
    if (
        uploaded.get("state") != "uploaded"
        or uploaded.get("size") != size
        or api.download_digest(uploaded["id"]) != (size, digest)
    ):
        raise PublishError("Uploaded APK failed size/SHA256 verification.")
    api.request(
        "PATCH",
        f"releases/{release_id}",
        {
            "name": title,
            "body": body,
            "draft": False,
            "prerelease": False,
            "make_latest": "false",
        },
    )
    confirmed = api.request("GET", f"releases/{release_id}")
    confirmed_state = release_state(confirmed, state["project_id"], state["tag"])
    if (
        confirmed.get("draft")
        or confirmed.get("name") != title
        or confirmed_state != state
        or not any(
            item.get("id") == uploaded.get("id")
            and item.get("state") == "uploaded"
            and item.get("size") == size
            for item in api.assets(release_id)
        )
    ):
        raise PublishError("Published release could not be verified.")
    try:
        api.request(
            "POST",
            "dispatches",
            {
                "event_type": DISPATCH_EVENT,
                "client_payload": {
                    "pipeline_id": state["pipeline_id"],
                    "release_id": release_id,
                },
            },
        )
    except PublishError:
        raise PublishError(
            "Release is published, but tester notification failed; retry this job."
        ) from None
    print(f"Published {title}: version {version} ({code}), SHA256 {digest}")


def main():
    try:
        config = configuration(os.environ)
        state = {key: value for key, value in config.items() if key not in {
            "token", "tag", "application_id", "asset_prefix", "repository"
        }}
        state["tag"] = config["tag"]
        state["repository"] = config["repository"]
        apk, digest, version, code = artifact(Path.cwd(), config["application_id"])
        publish(
            GitHub(config["token"], config["repository"]),
            state,
            apk,
            digest,
            version,
            code,
            asset_prefix=config["asset_prefix"],
        )
    except (PublishError, OSError, ValueError, KeyError, TypeError) as error:
        message = str(error) if isinstance(error, PublishError) else type(error).__name__
        print(f"ERROR: {message} Publication incomplete; existing assets are retained.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
