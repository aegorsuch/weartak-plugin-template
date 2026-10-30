const test = require('node:test');
const assert = require('node:assert/strict');
const { createReleaseTestIssue } = require('./create_release_test_issue.cjs');

function fixture({ existing = false } = {}) {
  const calls = [];
  const release = {
    draft: false,
    prerelease: false,
    name: 'TAK.gov Forge CI/CD Pipeline Release (1.2.3-p34)',
    html_url: 'https://github.com/example/plugin/releases/tag/Forge-Release',
  };
  const github = {
    rest: {
      repos: {
        getRelease: async () => ({ data: release }),
      },
      issues: {
        listForRepo: async () => ({
          data: existing
            ? [{ number: 9, body: '<!-- weartak-release-test:56 -->' }]
            : [],
        }),
        create: async (input) => {
          calls.push(input);
          return { data: { number: 10, body: input.body } };
        },
      },
    },
  };
  const context = {
    repo: { owner: 'example', repo: 'plugin' },
    payload: { client_payload: { pipeline_id: '56', release_id: 7 } },
  };
  const core = { info() {} };
  return { calls, github, context, core };
}

test('creates an assigned checklist issue for a published release', async () => {
  const testFixture = fixture();
  const issue = await createReleaseTestIssue({
    ...testFixture,
    tester: 'release-tester',
  });
  assert.equal(issue.number, 10);
  assert.equal(testFixture.calls[0].assignees[0], 'release-tester');
  assert.match(testFixture.calls[0].body, /https:\/\/github\.com\/example\/plugin\/releases/);
});

test('does not duplicate an existing pipeline issue', async () => {
  const testFixture = fixture({ existing: true });
  const issue = await createReleaseTestIssue({
    ...testFixture,
    tester: 'release-tester',
  });
  assert.equal(issue.number, 9);
  assert.equal(testFixture.calls.length, 0);
});

test('manual dispatch looks up configured fixed tag', async () => {
  const testFixture = fixture();
  testFixture.context.payload = {};
  testFixture.github.rest.repos.getReleaseByTag = async ({ tag }) => {
    assert.equal(tag, 'Forge-Release');
    return {
      data: {
        draft: false,
        prerelease: false,
        id: 7,
        name: 'TAK.gov Forge CI/CD Pipeline Release (1.2.3-p34)',
        html_url: 'https://github.com/example/plugin/releases/tag/Forge-Release',
      },
    };
  };
  await createReleaseTestIssue({
    ...testFixture,
    tester: 'release-tester',
    releaseTag: 'Forge-Release',
  });
  assert.equal(testFixture.calls.length, 1);
});
