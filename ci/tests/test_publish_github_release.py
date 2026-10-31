import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from ci.publish_github_release import (
    PublishError, artifact, configuration, main, release_asset_name, release_state,
)


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.env = {
            "CI_DEFAULT_BRANCH": "master",
            "CI_COMMIT_BRANCH": "master",
            "CI_COMMIT_REF_PROTECTED": "true",
            "CI_PIPELINE_SOURCE": "push",
            "GITHUB_RELEASE_REPOSITORY": "example/plugin",
            "GITHUB_RELEASE_TOKEN": "test-token",
            "GITHUB_RELEASE_TAG": "Forge-Release",
            "GITHUB_RELEASE_APPLICATION_ID": "com.example.plugin",
            "GITHUB_RELEASE_ASSET_PREFIX": "EXAMPLE",
            "CI_PROJECT_PATH": "plugins/example",
            "CI_PROJECT_ID": "12",
            "CI_PIPELINE_IID": "34",
            "CI_PIPELINE_ID": "56",
            "CI_PIPELINE_URL": "https://git.example/pipelines/56",
            "CI_COMMIT_SHA": "a" * 40,
        }

    def test_configuration_requires_protected_default_branch_push(self):
        config = configuration(self.env)
        self.assertEqual(config["repository"], "example/plugin")
        for key, value in (
            ("CI_COMMIT_REF_PROTECTED", "false"),
            ("CI_PIPELINE_SOURCE", "merge_request_event"),
            ("CI_COMMIT_BRANCH", "feature"),
        ):
            with self.subTest(key=key):
                invalid = dict(self.env, **{key: value})
                with self.assertRaises(PublishError):
                    configuration(invalid)

    def test_artifact_requires_checksum_and_matching_application(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "app/build/outputs/apk/release"
            output.mkdir(parents=True)
            apk = output / "app-release.apk"
            apk.write_bytes(b"signed apk")
            digest = hashlib.sha256(apk.read_bytes()).hexdigest()
            (output / "verified-apk.sha256").write_text(
                f"{digest}  {apk.relative_to(root).as_posix()}"
            )
            (output / "output-metadata.json").write_text(json.dumps({
                "applicationId": "com.example.plugin",
                "variantName": "release",
                "elements": [{"outputFile": apk.name, "versionName": "1.2.3", "versionCode": 12}],
            }))
            self.assertEqual(
                artifact(root, "com.example.plugin")[1:],
                (digest, "1.2.3", 12),
            )
            with self.assertRaises(PublishError):
                artifact(root, "com.other.plugin")
            (output / "verified-apk.sha256").write_text("wrong")
            with self.assertRaises(PublishError):
                artifact(root, "com.example.plugin")

    def test_release_state_rejects_unowned_or_wrong_tag(self):
        release = {
            "body": '<!-- weartak-plugin-release-v1 {"project_id":"12","pipeline_iid":34} -->',
            "tag_name": "Forge-Release",
            "prerelease": False,
        }
        self.assertEqual(release_state(release, "12", "Forge-Release")["pipeline_iid"], 34)
        with self.assertRaises(PublishError):
            release_state(release, "13", "Forge-Release")
        with self.assertRaises(PublishError):
            release_state(release, "12", "wrong-tag")

    def test_release_asset_names_preserve_plugin_case_and_pipeline(self):
        for name in ("Sextant", "LACE", "TAK-CAD", "goTenna", "MOPP"):
            for version in ("5.8.4", "5.8.4+abcdef12", "5.8.4-p42+abcdef12"):
                with self.subTest(name=name, version=version):
                    self.assertEqual(
                        release_asset_name(name, version, 42),
                        f"WearTAK-Plugin-{name}-5.8.4-p42.apk",
                    )
        self.assertEqual(
            release_asset_name("Template", "0.1.0-app-template", 34),
            "WearTAK-Plugin-Template-0.1.0-app-template-p34.apk",
        )
        with self.assertRaises(PublishError):
            release_asset_name("Sextant", "5.8.4-p41+abcdef12", 42)

    def test_main_publishes_verified_filename_and_retains_existing_assets(self):
        self.run_publication()

    def test_main_reuses_verified_asset_on_retry(self):
        self.run_publication(existing=True)

    def test_main_does_not_publish_release_when_upload_checksum_differs(self):
        self.run_publication(corrupt=True)

    def run_publication(self, *, existing=False, corrupt=False):
        with tempfile.TemporaryDirectory() as temporary:
            apk = Path(temporary) / "app-release.apk"
            contents = b"unchanged signed apk"
            apk.write_bytes(contents)
            digest = hashlib.sha256(contents).hexdigest()
            filename = "WearTAK-Plugin-EXAMPLE-5.8.4-p34.apk"
            old_asset = {"id": 7, "name": "EXAMPLE-5.8.4-p34.apk"}
            new_asset = {
                "id": 8, "name": filename, "label": filename,
                "state": "uploaded", "size": len(contents),
            }
            assets = [old_asset, new_asset] if existing else [old_asset]
            release = {
                "id": 9, "tag_name": self.env["GITHUB_RELEASE_TAG"],
                "draft": False, "prerelease": False,
                "body": '<!-- weartak-plugin-release-v1 '
                        '{"project_id":"12","pipeline_iid":33} -->',
            }
            api = Mock()
            api.assets.side_effect = lambda release_id: list(assets)
            api.download_digest.return_value = (
                len(contents), "0" * 64 if corrupt else digest,
            )

            def request(method, path, data=None, **kwargs):
                if method == "GET" and path == "":
                    return {
                        "full_name": self.env["GITHUB_RELEASE_REPOSITORY"],
                        "archived": False, "disabled": False,
                    }
                if method == "GET" and path.startswith("git/ref/tags/"):
                    return {"ref": f"refs/tags/{self.env['GITHUB_RELEASE_TAG']}"}
                if method == "GET" and path.startswith("releases/"):
                    return dict(release)
                if method == "POST" and path.startswith("releases/9/assets?"):
                    self.assertIn(f"name={filename}", path)
                    self.assertEqual(data, contents)
                    self.assertTrue(kwargs["binary"])
                    assets.append(new_asset)
                    return new_asset
                if method == "PATCH" and path == "releases/9":
                    release.update(data)
                    return dict(release)
                if method == "POST" and path == "dispatches":
                    return None
                self.fail(f"Unexpected API request: {method} {path}")

            api.request.side_effect = request
            with (
                patch.dict("os.environ", self.env, clear=True),
                patch("ci.publish_github_release.artifact", return_value=(
                    apk, digest, "5.8.4-p34+abcdef12", 5840034,
                )),
                patch("ci.publish_github_release.GitHub", return_value=api),
            ):
                self.assertEqual(main(), 1 if corrupt else 0)
            self.assertEqual(apk.read_bytes(), contents)
            self.assertIn(old_asset, assets)
            self.assertEqual(release["tag_name"], self.env["GITHUB_RELEASE_TAG"])
            uploads = [
                call for call in api.request.call_args_list
                if call.args[0] == "POST" and "/assets?" in call.args[1]
            ]
            self.assertEqual(len(uploads), 0 if existing else 1)
            release_updates = [
                call for call in api.request.call_args_list if call.args[0] == "PATCH"
            ]
            self.assertEqual(len(release_updates), 0 if corrupt else 1)
            if not corrupt:
                self.assertIn("**5.8.4-p34+abcdef12**", release["body"])
                self.assertIn("**5840034**", release["body"])
                self.assertIn(digest, release["body"])


if __name__ == "__main__":
    unittest.main()
