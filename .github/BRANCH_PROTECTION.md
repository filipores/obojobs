# Branch Protection Rules

This document describes the recommended branch protection rules for the `main` branch.

## Recommended Settings for `main`

Configure these settings in GitHub: **Settings > Branches > Add branch protection rule**

### Branch name pattern
```
main
```

### Protection Rules

#### Require a pull request before merging
- [x] **Require approvals**: 1
- [x] **Dismiss stale pull request approvals when new commits are pushed**
- [x] **Require review from Code Owners** (if CODEOWNERS file exists)

#### Require status checks to pass before merging
- [x] **Require branches to be up to date before merging**
- Required status checks:
  - `backend-tests`
  - `frontend-tests`
  - `e2e-tests`
  - `Analyze (javascript-typescript)` (CodeQL)
  - `Analyze (python)` (CodeQL)

#### Require conversation resolution before merging
- [x] All PR comments must be resolved

#### Require signed commits
- [ ] Optional (recommended for high-security projects)

#### Require linear history
- [x] Enforces squash or rebase merges (no merge commits)

#### Do not allow bypassing the above settings
- [x] Apply rules to administrators

### Additional Recommendations

#### Lock branch
- [ ] Keep disabled to allow merges

#### Restrict who can push
- [ ] Only if you need specific team restrictions

## Setting Up via GitHub CLI

```bash
# Enable branch protection (requires admin access)
gh api repos/{owner}/{repo}/branches/main/protection \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  -f required_status_checks='{"strict":true,"contexts":["backend-tests","frontend-tests","e2e-tests"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' \
  -f restrictions=null \
  -f required_linear_history=true \
  -f allow_force_pushes=false \
  -f allow_deletions=false
```

## Commit Message Convention

This repository uses [Conventional Commits](https://www.conventionalcommits.org/).

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change that neither fixes nor adds |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `build` | Build system or dependencies |
| `ci` | CI configuration |
| `chore` | Other changes |
| `revert` | Reverts a previous commit |

### Examples
```
feat(auth): add OAuth2 login support
fix(api): handle null response from payment provider
docs: update API documentation for v2 endpoints
chore(deps): update dependencies
```

## Pre-commit Hooks

This repository uses Husky for Git hooks:

- **pre-commit**: Runs lint-staged to lint and format staged files
- **commit-msg**: Validates commit messages against conventional commits

### Setup
```bash
npm install  # Installs dependencies and sets up Husky via prepare script
```

### Bypassing Hooks (Emergency Only)
```bash
git commit --no-verify -m "emergency: fix critical production issue"
```
