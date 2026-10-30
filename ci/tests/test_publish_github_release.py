import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from ci.publish_github_release import PublishError, artifact, configuration, release_state


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


if __name__ == "__main__":
    unittest.main()
