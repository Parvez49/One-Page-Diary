# Git — Working Knowledge

> Interview Q&A lives in **[git_interview.md](git_interview.md)**. This file is the *doing* half:
> the model, the daily commands, and the operations that get you out of trouble.

---

## 1. The mental model (everything follows from this)

Git is a **content-addressable filesystem** with a VCS bolted on top. Four object types,
all stored in `.git/objects`, all named by the SHA-1/SHA-256 of their content:

| Object | Holds | Key property |
|---|---|---|
| **blob** | file *contents* (no name, no path) | identical files anywhere = **one** blob |
| **tree** | a directory listing → blobs + subtrees, with names & modes | this is where filenames live |
| **commit** | one tree + parent(s) + author + message | immutable; the **DAG node** |
| **tag** | a pointer to an object + message | annotated tags only |

```
commit e4f2c1  ──parent──▶ commit 9a3d80 ──parent──▶ commit 1b7e45
   │                          │                         │
   └─tree──▶ root tree        └─tree──▶ root tree       └─tree
             ├── blob  README            ├── blob README
             └── tree  src/              └── tree src/
                       └── blob app.py             └── blob app.py   ← same SHA, shared
```

**Consequences worth stating out loud in an interview:**
- Commits are **snapshots, not diffs**. Diffs are computed on demand between two trees.
- A commit's SHA covers its parent, so **changing history changes every descendant SHA**.
  That is *why* rebasing a shared branch is destructive.
- **Branches are 41-byte files**, not copies. `cat .git/refs/heads/main` → one SHA.
  Branching is O(1) — this is the whole reason Git won.
- Nothing is truly deleted until **`git gc`** prunes unreachable objects (see reflog, §8).

### The three (four) areas

```
  working tree  ──git add──▶  index/stage  ──git commit──▶  local repo  ──git push──▶  remote
       ▲                          │                             │                        │
       └──── git restore ─────────┘                             │                        │
       └──── git restore --source=HEAD --staged --worktree ─────┘                        │
                                          git fetch ◀───────────────────────────────────-┘
```

The **index** is a real file (`.git/index`) — a staged snapshot, not a diff list. That's why
`git add` on a file you then edit again stages the *old* version.

---

## 2. Setup

```bash
git init                                # creates .git/
git init --bare                         # server-side repo: no working tree

git config --global user.name  "Parvez Hossen"
git config --global user.email "you@mail.com"
git config --global --list              # verify identity
git config --list --show-origin         # ⭐ which file set which value
```

**Config precedence** (later wins): `/etc/gitconfig` (system) → `~/.gitconfig` (global) →
`.git/config` (local) → command-line `-c`.

Settings that pay for themselves:

```bash
git config --global init.defaultBranch main
git config --global pull.rebase true          # no accidental merge bubbles on pull
git config --global rebase.autosquash true    # honour fixup! commits
git config --global rerere.enabled true       # ⭐ remember conflict resolutions (§7)
git config --global fetch.prune true          # drop remote refs deleted upstream
git config --global diff.colorMoved zebra     # moved code ≠ changed code
git config --global merge.conflictstyle zdiff3  # shows the ORIGINAL in conflicts
```

**Per-directory identity** — work vs personal on one machine:

```bash
# ~/.gitconfig
[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-work
```

---

## 3. Daily loop

```bash
git status -sb                  # short + branch line; the one to actually use
git add file.py                 # stage a file
git add .                       # stage everything under cwd
git add -p                      # ⭐ stage hunk-by-hunk — split a messy change into clean commits
git commit -m "fix: null guard on user lookup"
git commit --amend --no-edit    # fold staged changes into the last commit
```

⚠️ **`--amend` rewrites the commit** (new SHA). Safe before push, needs
`git push --force-with-lease` after.

### Inspecting

```bash
git log --oneline --graph --decorate --all     # ⭐ the topology view
git log -p file.py                             # history *with* diffs
git log -S "process_payment" --oneline         # ⭐ pickaxe: commits that added/removed the string
git log -L 40,60:app.py                        # evolution of specific LINES
git log --author="parvez" --since="2 weeks"
git show <sha>                                 # one commit in full
git show <sha>:path/to/file.py                 # a file AS IT WAS at that commit
git blame -L 20,40 -w -C app.py                # -w ignore whitespace, -C follow moved code
```

### Diffing — the part people get wrong

| Command | Compares |
|---|---|
| `git diff` | working tree ↔ **index** (unstaged changes) |
| `git diff --staged` | index ↔ **HEAD** (what you're about to commit) |
| `git diff HEAD` | working tree ↔ HEAD (everything uncommitted) |
| `git diff A B` | two commits |
| `git diff A...B` | B vs their **merge base** — "what the PR actually adds" |

---

## 4. Undoing — pick by *where the change lives*

```bash
# Working tree, not staged →
git restore file.py                 # discard edits  ⚠️ unrecoverable, no reflog
git restore .

# Staged, want to unstage (keep edits) →
git restore --staged file.py        # modern
git reset HEAD file.py              # older equivalent

# Last commit, want it undone →
git reset --soft  HEAD~1            # uncommit, keep changes STAGED
git reset --mixed HEAD~1            # uncommit, keep changes in working tree (default)
git reset --hard  HEAD~1            # ⚠️ uncommit and DESTROY changes

# Already pushed / shared →
git revert <sha>                    # ✅ new commit that inverts it. History intact.
git revert -m 1 <merge-sha>         # revert a MERGE: -m 1 = keep first parent (main)
```

**The rule:** `reset` for private history, `revert` for public history.

**Removing files:**

```bash
git rm file.py                # delete from disk AND index
git rm --cached secrets.env   # ⭐ untrack but KEEP on disk — the .gitignore-after-the-fact fix
git clean -nd                 # dry-run: what untracked files would be removed
git clean -fd                 # actually remove untracked files + dirs
```

⚠️ `git clean` is *not* the same as the note-common claim about ignored files —
it removes **untracked** files; add `-x` to also remove **ignored** ones.

---

## 5. Branching

```bash
git switch -c feature/auth           # ⭐ modern: create + switch (checkout is overloaded)
git switch main
git switch -                         # back to previous branch

git branch -vv                       # local branches + upstream + ahead/behind
git branch -m new-name               # rename current
git branch -d old                    # safe delete (refuses if unmerged)
git branch -D old                    # force delete
git push origin --delete old         # delete remote branch
git push -u origin feature/auth      # push + set upstream tracking

git switch --orphan clean-start      # branch with NO history (docs/gh-pages)
```

### Merge vs rebase

```
      A---B---C  main
           \
            D---E---F  feature
```

```bash
git merge feature          # merge commit M — preserves true history, non-destructive
      A---B---C-------M  main
           \         /
            D---E---F

git rebase main            # replays D,E,F as NEW commits on C — linear, but new SHAs
      A---B---C---D'---E'---F'  main
```

- `git merge --no-ff` — always make a merge commit, so the feature branch stays visible.
- `git merge --squash feature` — one commit, no merge record. Common team default.
- **Golden rule:** never rebase a branch others have pulled. See `git_interview.md §5`.

```bash
git rebase -i HEAD~4        # ⭐ squash/reword/drop/reorder before opening a PR
git rebase --onto main old-base feature   # transplant a branch off the wrong parent
git rebase --continue | --skip | --abort
```

### Cherry-pick

```
A---B---C---D  main            git checkout main
     \                          git cherry-pick F
      E---F---G  feature
                               A---B---C---D---F'  main   (F' is a NEW commit, new SHA)
```

```bash
git cherry-pick <sha>          # one commit onto current branch
git cherry-pick A..B           # a range (A exclusive)
git cherry-pick -x <sha>       # ⭐ records "cherry picked from ..." — do this for hotfix backports
```

---

## 6. Remotes

```bash
git remote -v
git remote add origin git@github.com:user/repo.git
git remote set-url origin git@github.com:user/repo.git

git fetch origin              # download refs; changes NOTHING in your working tree
git pull                      # = fetch + merge
git pull --rebase             # = fetch + rebase → linear, no merge bubble
git push
git push --force-with-lease   # ⭐ ALWAYS this, never --force (see below)
```

⚠️ **`--force` vs `--force-with-lease`**
`--force` overwrites the remote unconditionally — if a teammate pushed in between, their
commits are gone. `--force-with-lease` refuses unless the remote is where you last saw it.
There is no reason to type `--force`.

**Publishing a new repo:**

```bash
git init && git add . && git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:user/repo.git
git push -u origin main
```

---

## 7. Stash, worktree, and conflicts

### Stash

```bash
git stash push -m "wip: refactor"   # ⭐ named; bare `git stash` gives useless messages
git stash -u                        # include untracked files
git stash list
git stash show -p stash@{1}         # preview before applying
git stash pop                       # apply + delete
git stash apply stash@{1}           # apply, keep in list
git stash drop stash@{1}
git stash branch fix-x stash@{0}    # ⭐ pop onto a fresh branch (when the base moved on)
```

Stashes are **commits** on a hidden ref — `git fsck` can recover a dropped one.

### Worktree ⭐ (the underused one)

Review a PR without stashing your half-finished work:

```bash
git worktree add ../repo-hotfix hotfix/urgent   # second checkout, SAME .git
git worktree list
git worktree remove ../repo-hotfix
```

### Conflicts

```bash
git status                      # "both modified" = the conflict list
git diff --name-only --diff-filter=U
# edit, then:
git add file.py
git rebase --continue           # or: git merge --continue

git checkout --ours file.py     # during MERGE: ours = current branch
git checkout --theirs file.py   # during REBASE these are SWAPPED ⚠️
git merge --abort               # bail out entirely
```

⚠️ **In a rebase, "ours" is the branch being rebased *onto*** (upstream), and "theirs" is your
commits — the opposite of intuition, because rebase replays your work onto their base.

**`rerere`** (reuse recorded resolution) — with `rerere.enabled=true`, Git remembers how you
resolved a conflict and replays it automatically on the next rebase. Essential for long-lived
branches.

---

## 8. Recovery — reflog is the safety net

**`git reflog` records every move of HEAD**, including commits that are no longer reachable
from any branch. Reset too hard? Deleted a branch? It's still there.

```bash
git reflog
# abc1234 HEAD@{0}: reset: moving to HEAD~3
# def5678 HEAD@{1}: commit: Added feature X     ← the work you thought you lost

git reset --hard def5678             # go back
git switch -c recovery def5678       # safer: recover onto a new branch
git reflog show --all
```

| | `git log` | `git reflog` |
|---|---|---|
| Shows | commits reachable from a ref | every position **HEAD** has held |
| Scope | shared, travels on clone/push | **local only**, never pushed |
| Sees orphaned commits | ❌ | ✅ |
| Use | review history | **recover from reset/rebase/branch -D** |

⚠️ Reflog entries expire (90 days reachable, 30 unreachable) and `git gc` then prunes the
objects. Recovery is not permanent — act promptly.

**Finding a lost commit with no reflog entry:**

```bash
git fsck --lost-found          # dangling commits/blobs
```

**Deliberately destroying history** (leaked secret — after rotating the credential):

```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
# For a secret already pushed: rewrite with git-filter-repo, force-push,
# and treat the secret as compromised regardless — it is in forks, PRs, and CI logs.
```

---

## 9. Senior-level tools

### `git bisect` — binary search for the breaking commit ⭐

```bash
git bisect start
git bisect bad                 # current commit is broken
git bisect good v1.4.0         # this tag was fine
# Git checks out the midpoint; test; then `git bisect good` or `git bisect bad`
git bisect reset

git bisect run pytest tests/test_auth.py   # ⭐ fully automated (exit 0 = good)
```

Finds the culprit among 1000 commits in ~10 steps.

### Submodules vs subtree

| | **Submodule** | **Subtree** |
|---|---|---|
| Stores | a *pointer* (SHA) to another repo | the actual files, merged in |
| Clone | needs `--recurse-submodules` | just works |
| Consumer burden | high — detached HEADs, easy to forget | none |
| Contributing back | natural | `git subtree push` |

```bash
git submodule add <url> libs/shared
git clone --recurse-submodules <url>
git submodule update --init --recursive
```

### Hooks

`.git/hooks/` — local, not versioned. `pre-commit`, `commit-msg`, `pre-push` client-side;
`pre-receive`, `post-receive` server-side (the only ones you can *enforce*).
Teams use the `pre-commit` framework or `core.hooksPath` to version them.

### Large repos

```bash
git clone --depth 1 <url>                 # shallow: CI clones
git clone --filter=blob:none <url>        # ⭐ blobless: full history, blobs on demand
git sparse-checkout set apps/web libs/ui  # monorepo: check out a subset
git maintenance start                     # background gc/prefetch
```

### Other sharp tools

```bash
git switch --detach <sha>             # look around at an old commit
git tag -a v1.2.0 -m "release"        # annotated (an object); -a matters for `describe`
git describe --tags                   # "v1.2.0-14-gabc1234" → build version strings
git shortlog -sn                      # commits per author
git range-diff main..old main..new    # ⭐ diff two versions of a rebased branch
git archive --format=tar HEAD | ...   # export tree without .git
```

---

## 10. `.gitignore` gotchas

```gitignore
*.log
!important.log        # negation
build/                # trailing slash = directories only
/config.local         # leading slash = repo root only
**/__pycache__/
```

⚠️ **.gitignore only affects untracked files.** A file already committed keeps being tracked:

```bash
git rm --cached file && git commit -m "stop tracking"
git check-ignore -v path/to/file     # ⭐ WHICH rule is ignoring this?
```

`.gitignore` is committed and shared; `.git/info/exclude` is local-only; `core.excludesFile`
(`~/.gitignore_global`) is for editor/OS junk — put `.DS_Store` and `.idea/` there, not in
project ignore files.
