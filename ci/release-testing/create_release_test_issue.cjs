const { readFileSync } = require('node:fs');
const { join } = require('node:path');

const MARKER_PREFIX = 'weartak-release-test';

async function createReleaseTestIssue({ github, context, core, tester, releaseTag }) {
  const { owner, repo } = context.repo;
  if (!tester || !/^[A-Za-z0-9-]+$/.test(tester)) {
    throw new Error('Set repository variable RELEASE_TESTER to a GitHub username.');
  }

  const payload = context.payload.client_payload || {};
  let release;
  let pipelineId = payload.pipeline_id;
  if (payload.release_id !== undefined) {
    if (!/^[1-9][0-9]*$/.test(String(pipelineId || '')) || !Number.isInteger(payload.release_id)) {
      throw new Error('Release dispatch must include valid pipeline_id and release_id.');
    }
    ({ data: release } = await github.rest.repos.getRelease({
      owner,
      repo,
      release_id: payload.release_id,
    }));
  } else {
    if (!releaseTag) {
      throw new Error('Set repository variable GITHUB_RELEASE_TAG for manual verification.');
    }
    ({ data: release } = await github.rest.repos.getReleaseByTag({
      owner,
      repo,
      tag: releaseTag,
    }));
    pipelineId = `manual-${release.id}`;
  }
  if (release.draft || release.prerelease || !release.html_url) {
    throw new Error('Release must be published before creating tester issue.');
  }
  const marker = `<!-- ${MARKER_PREFIX}:${pipelineId} -->`;
  const title = `Release testing: ${release.name}`;
  let page = 1;
  while (true) {
    const { data: issues } = await github.rest.issues.listForRepo({
      owner,
      repo,
      state: 'all',
      per_page: 100,
      page,
    });
    const existing = issues.find((issue) => !issue.pull_request && issue.body?.includes(marker));
    if (existing) {
      core.info(`Release testing issue already exists: #${existing.number}`);
      return existing;
    }
    if (issues.length < 100) {
      break;
    }
    page += 1;
  }

  const checklist = readFileSync(join(__dirname, 'checklist.md'), 'utf8');
  const body = [
    `Release: ${release.html_url}`,
    '',
    `GitLab pipeline: ${pipelineId}`,
    '',
    checklist.trim(),
    '',
    marker,
  ].join('\n');
  const { data: issue } = await github.rest.issues.create({
    owner,
    repo,
    title,
    body,
    assignees: [tester],
  });
  core.info(`Created release testing issue #${issue.number}`);
  return issue;
}

module.exports = { createReleaseTestIssue };
