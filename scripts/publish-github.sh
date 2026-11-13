#!/usr/bin/env bash
# First publication only. No remote mutation occurs without --publish.
# Author: AI 酋长 Andy | WeChat: AIPMAndy
set -euo pipefail
IFS=$'\n\t'

OWNER='AIPMAndy'
REPOSITORY='chinese-international-student-career-guide'
TARGET="${OWNER}/${REPOSITORY}"
TAG='v1.0.0'
REMOTE='github'
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
MODE="${1:---help}"

usage() {
  cat <<'HELP'
Usage: bash scripts/publish-github.sh --check | --publish | --help

--check    Validate this project, clean main, release files, AIPMAndy login,
           and an explicit HTTP 404 for the exact destination. Read-only.
--publish  Perform the same checks, create the exact public repository,
           add a dedicated github remote, then atomically push main and v1.0.0.
--help     Show this help; no login, network, git changes, or publication.

This is a first-publication script. It stops if the target repository or the
local github remote already exists. It never changes origin, force-pushes,
deletes repositories, logs in, switches accounts, or creates a GitHub Release.
HELP
}

fail() { printf 'Stopped: %s\n' "$*" >&2; exit 1; }

if [[ "$#" -gt 1 ]]; then usage >&2; exit 2; fi
case "$MODE" in
  --help|-h) usage; exit 0 ;;
  --check|--publish) ;;
  *) usage >&2; exit 2 ;;
esac

for required_command in git gh python3 awk mktemp; do
  command -v "$required_command" >/dev/null 2>&1 || fail "Missing command: $required_command"
done
cd -- "$PROJECT_ROOT"

[[ "$(basename -- "$PROJECT_ROOT")" == "$REPOSITORY" ]] || fail 'The project folder name does not match the intended new repository.'
git_root="$(git rev-parse --show-toplevel 2>/dev/null)" || fail 'Initialize and commit this new project first; this script does not initialize Git.'
git_root="$(cd -- "$git_root" && pwd -P)"
[[ "$git_root" == "$PROJECT_ROOT" ]] || fail 'The Git root must be exactly this new project directory.'
[[ "$(git symbolic-ref --quiet --short HEAD)" == 'main' ]] || fail 'The current branch must be main.'
head_commit="$(git rev-parse --verify HEAD)" || fail 'A local commit is required.'
[[ -z "$(git status --porcelain --untracked-files=normal)" ]] || fail 'Review and commit all project changes first; the worktree must be clean.'
[[ -z "$(git remote | awk '$0 == "github" { print }')" ]] || fail 'A github remote already exists. First-publication automation will not reuse or overwrite it.'

python3 - <<'PY'
from pathlib import Path
import json, sys, zipfile

root = Path.cwd()
required = [
    'README.md', 'LICENSE', 'CONTENT_LICENSE.md', 'CONTRIBUTING.md',
    'content/core/00-start.md', 'content/core/15-coverage-gaps.md',
    'data/template-schema.json', 'scripts/build_site.py', 'dist/index.html',
    'templates/career-workbook.xlsx',
    'downloads/chinese-international-student-career-guide.pdf',
    'downloads/editable-templates.zip', 'downloads/source-code.zip',
]
missing = [p for p in required if not (root / p).is_file() or (root / p).stat().st_size == 0]
if missing:
    sys.exit('Missing or empty publication files: ' + ', '.join(missing))
if '# 中国留学生求职全局保姆级攻略' not in (root / 'README.md').read_text('utf-8'):
    sys.exit('README project identity does not match.')
if not (root / 'downloads/chinese-international-student-career-guide.pdf').read_bytes().startswith(b'%PDF-'):
    sys.exit('The PDF file does not have a PDF header.')
for name in ['templates/career-workbook.xlsx', 'downloads/editable-templates.zip', 'downloads/source-code.zip']:
    with zipfile.ZipFile(root / name) as archive:
        if archive.testzip() is not None:
            sys.exit('Archive integrity check failed: ' + name)
for name in ['website/static-validation.json', 'website/coverage-validation.json']:
    record = json.loads((root / name).read_text('utf-8'))
    if record.get('errors'):
        sys.exit('Resolve validation errors before publishing: ' + name)
print('Local project identity, publication files, and archive checks passed.')
PY

for tracked_file in README.md LICENSE CONTENT_LICENSE.md scripts/build_site.py templates/career-workbook.xlsx dist/index.html; do
  git ls-files --error-unmatch -- "$tracked_file" >/dev/null 2>&1 || fail "Required public file is not tracked: $tracked_file"
done

if git show-ref --verify --quiet "refs/tags/$TAG"; then
  [[ "$(git rev-parse "${TAG}^{commit}")" == "$head_commit" ]] || fail "Local $TAG points to a different commit. This script will not move it."
else
  git var GIT_COMMITTER_IDENT >/dev/null || fail 'Set a local Git identity before creating an annotated tag.'
fi

# CLI credentials are inspected in place. No auth login/switch/setup-git or
# persistent credential configuration is performed by this script.
export GH_HOST='github.com'
export GH_PROMPT_DISABLED='1'
gh auth status --hostname github.com || fail 'GitHub CLI is not authenticated for github.com.'
login="$(gh api --hostname github.com user --jq '.login')" || fail 'Could not verify the active account.'
[[ "$login" == "$OWNER" ]] || fail "Authenticated account is not $OWNER. No account switching was attempted."

check_dir="$(mktemp -d)"
trap 'rm -rf -- "$check_dir"' EXIT
if gh api --hostname github.com --method GET --include "repos/$TARGET" >"$check_dir/response" 2>"$check_dir/error"; then
  fail "The exact target $TARGET already exists. This script will not publish to an existing repository."
fi
http_status="$(awk '/^HTTP\// { code=$2 } END { print code }' "$check_dir/response")"
[[ "$http_status" == '404' ]] || fail "Repository absence was not confirmed by HTTP 404 (observed: ${http_status:-no HTTP status}). Network, auth, and API errors are not treated as absence."

printf 'Verified account: %s\nVerified absent target: %s\nCommit: %s\n' "$login" "$TARGET" "$head_commit"
if [[ "$MODE" == '--check' ]]; then
  printf 'Read-only preflight complete. No local refs, remotes, or remote data changed.\n'
  exit 0
fi

# Only the explicit --publish path reaches remote creation. If the repository
# appears between the check and create, gh fails and this script stops.
gh repo create "$TARGET" --public \
  --description '中国留学生跨地区求职路线、官方条件核验、招聘窗口、完整中文攻略与可编辑模板'
created_identity="$(gh api --hostname github.com "repos/$TARGET" --jq '[.full_name, (.private | tostring)] | join("|")')"
[[ "$created_identity" == "${TARGET}|false" ]] || fail 'Created repository identity or visibility could not be verified. No push performed.'

# origin can remain assigned to Sites. Only this new local github remote is added.
git remote add "$REMOTE" "https://github.com/${TARGET}.git"
if ! git show-ref --verify --quiet "refs/tags/$TAG"; then
  git tag -a "$TAG" "$head_commit" -m 'v1.0.0: 中国留学生求职全局保姆级攻略'
fi
[[ "$(git rev-parse refs/heads/main)" == "$head_commit" ]] || fail 'Local main changed during publication. Inspect the new repository before continuing.'
[[ "$(git rev-parse "${TAG}^{commit}")" == "$head_commit" ]] || fail 'The tag changed during publication.'
[[ "$(git remote get-url --all "$REMOTE")" == "https://github.com/${TARGET}.git" ]] || fail 'Unexpected fetch URL or URL rewrite on the dedicated github remote.'
[[ "$(git remote get-url --push --all "$REMOTE")" == "https://github.com/${TARGET}.git" ]] || fail 'Unexpected push URL or URL rewrite on the dedicated github remote.'

# The helper is set for this one Git command; global config is unchanged.
# Atomic push publishes both refs together. No --force, mirror, or deletion.
git -c credential.helper= \
  -c 'credential.https://github.com.helper=!gh auth git-credential' \
  push --atomic "$REMOTE" \
  "${head_commit}:refs/heads/main" \
  "refs/tags/${TAG}:refs/tags/${TAG}"

remote_commit="$(gh api --hostname github.com "repos/$TARGET/git/ref/heads/main" --jq '.object.sha')"
[[ "$remote_commit" == "$head_commit" ]] || fail 'Remote main does not match the checked local commit. Inspect the new repository before continuing.'
remote_tag_commit="$(git -c credential.helper= -c 'credential.https://github.com.helper=!gh auth git-credential' \
  ls-remote "$REMOTE" "refs/tags/$TAG" "refs/tags/${TAG}^{}" \
  | awk -v tagref="refs/tags/$TAG" '$2 == tagref { direct=$1 } $2 == tagref "^{}" { peeled=$1 } END { print peeled ? peeled : direct }')"
[[ "$remote_tag_commit" == "$head_commit" ]] || fail 'The remote version tag does not resolve to the checked commit.'
default_branch="$(gh api --hostname github.com "repos/$TARGET" --jq '.default_branch')"
if [[ "$default_branch" != 'main' ]]; then
  gh repo edit "$TARGET" --default-branch main
fi
published_url="$(gh api --hostname github.com "repos/$TARGET" --jq '.html_url')"
printf 'Published main and %s to %s\n' "$TAG" "$published_url"
printf 'Next: inspect the public files, then create release assets and enable Pages only if desired.\n'
