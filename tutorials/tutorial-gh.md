# gh (GitHub CLI) — quick orientation

> A short orientation to gh as it's used in this project, plus pointers
> to good external tutorials. Read this for the project context; read the
> linked material for depth.

## What gh is

GitHub's official command-line tool. It does on the command line what
you'd otherwise do via the GitHub web UI: create repos, open pull
requests, manage issues, check CI status, etc. It is *not* a replacement
for `git` — `git` manages local commits and branches, `gh` manages the
GitHub-specific layer (PRs, issues, workflow runs).

## Why we use it

Three reasons:

1. **Authentication for `git push`.** On macOS particularly, `gh auth
   setup-git` is the cleanest way to configure git's credentials for
   pushing to GitHub. One-time setup, then `git push` works without
   prompts.
2. **Creating the GitHub repo.** `gh repo create` skips the
   web-UI-then-paste-URL dance.
3. **Issues and PRs from the terminal.** Once labmates start
   contributing, you'll want to triage issues without context-switching.

## One-time setup

```bash
# Install
brew install gh                      # macOS
# (Windows / Linux: see the install link below)

# Authenticate (interactive — browser-based OAuth)
gh auth login

# Configure git to use gh's credentials for HTTPS pushes
gh auth setup-git
```

After this, `git push` to any GitHub repo just works, and you can use
all the `gh` commands.

## Commands you'll use in this project

```bash
# Create a new repo from the current directory
gh repo create REPO_NAME --public --source . --push

# Open the repo's web page in the browser
gh browse

# List open issues
gh issue list

# Create a new issue from the terminal
gh issue create --title "..." --body "..."

# View a specific PR
gh pr view 123
gh pr view 123 --comments    # with all review comments inline

# Create a PR for the current branch
gh pr create --fill   # uses the latest commit message
# or with explicit fields:
gh pr create --title "..." --body "..." --base main

# Check status of CI on the current PR
gh pr checks
```

## A useful daily-driver tip

`gh pr view --web` opens the current branch's PR in the browser — fastest
way to switch from terminal to GitHub UI when you need the visual diff
view or want to leave a review comment.

## External material

For depth:

- **Official quickstart**: https://docs.github.com/en/github-cli/github-cli/quickstart
- **Practical patterns guide (PR workflows, gh api scripting)**:
  https://32blog.com/en/cli/cli-github-cli-gh
- **Codecademy walkthrough**: https://www.codecademy.com/article/github-cli-tutorial
- **Full command reference**: https://cli.github.com/manual/

The quickstart is enough for our project's current needs. The patterns
guide is worth reading once you start doing PR-heavy work.

## What `gh` doesn't replace

`git` itself. `gh` is the GitHub-specific layer; `git` is the version
control system. You still need to know `git add`, `git commit`,
`git push`, `git branch`, etc. They're complementary.

If your terminal git skills are rusty, the Pro Git book is the canonical
reference (https://git-scm.com/book) — chapters 1-3 are the daily-driver
material.
