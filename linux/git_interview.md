# Git — Interview Questions

> Commands and workflows live in **[git.md](git.md)**. This file is the *explaining* half.
> Answers are written the way you'd say them out loud: **claim first, then the why**.

---

### 1. What is Git? ⭐

A **distributed version control system**. Every clone is a full repository with complete
history — no central server is required to commit, branch, diff, or view history.

Internally it's a **directed acyclic graph (DAG) of immutable commits**. Each commit points to
its parent(s) and to a tree snapshot of the whole project, and is named by the hash of its
content — so a commit ID transitively verifies its entire history.

**Distributed vs centralised (SVN):** SVN needs the server for almost every operation and
branches are directory copies. Git branches are 41-byte pointer files, which is why branching
is instant and cheap.

---

### 2. What is `origin`? ⭐

**A conventional name, not a keyword.** It's the default alias `git clone` gives the URL it
cloned from. Nothing breaks if you rename it — `git remote rename origin upstream` is fine.

The pattern in fork-based workflows: `origin` = your fork, `upstream` = the source repo.
`main` and `origin/main` are two different refs — `origin/main` is a
**remote-tracking branch**, your local cache of where the remote was at last `fetch`.

---

### 3. `git fetch` vs `git pull`? ⭐

- **`fetch`** downloads objects and updates `origin/*` refs. Your working tree and local
  branches are **untouched** — completely safe, always.
- **`pull`** = `fetch` + **integrate** (`merge` by default, `rebase` with `--rebase`).

Habit worth having: `git fetch` then `git log --oneline HEAD..origin/main` to see what's
incoming *before* letting it touch your branch.

---

### 4. `reset` vs `revert` vs `restore`? ⭐⭐⭐

The single most common Git interview question.

| | **`git reset`** | **`git revert`** | **`git restore`** |
|---|---|---|---|
| Does what | moves the branch pointer | creates a **new inverse commit** | changes files only |
| History | **rewritten** | **appended to** — nothing lost | untouched |
| Safe on shared branch | ❌ **no** | ✅ **yes** | ✅ (local files only) |
| Use when | cleaning up local commits | undoing something already pushed | discarding edits |

**The three resets:**

```
git reset --soft  HEAD~1   → uncommit; changes stay STAGED
git reset --mixed HEAD~1   → uncommit; changes in working tree      (default)
git reset --hard  HEAD~1   → uncommit; changes DESTROYED  ⚠️
```

> Say this: *"Reset for private history, revert for public history."*
> Rewriting a branch others have pulled forces everyone into a painful recovery.

---

### 5. `merge` vs `rebase` — and when do you use each? ⭐⭐⭐

```
      A---B---C  main                A---B---C-------M  main    ← merge
           \                              \         /
            D---E---F  feature             D---E---F

                                    A---B---C---D'---E'---F'    ← rebase
```

| | **Merge** | **Rebase** |
|---|---|---|
| History | true, branching | linear, readable |
| Commits | preserved | **rewritten (new SHAs)** |
| Conflicts | resolved once | possibly **once per commit** |
| Traceability | merge commit records the integration | branch context lost |
| Safe on shared branch | ✅ | ❌ |

**How to answer:** *"Rebase my feature branch onto main to keep it current and clean while
it's still private; merge it into main — often `--no-ff` or squashed — so the integration
point is recorded. Never rebase anything that's been pushed and pulled by someone else."*

**The golden rule and why:** rebasing changes SHAs. A teammate who pulled the old commits now
has history that no longer exists upstream; their next pull creates duplicated commits and a
tangled merge.

---

### 6. What does `git cherry-pick` do? ⭐

Applies the **diff introduced by one commit** onto the current branch as a **new commit** with
a different SHA.

```
A---B---C---D  main         git switch main
     \                      git cherry-pick F
      E---F---G  feature
                            A---B---C---D---F'  main
```

**When:** backporting a hotfix from `main` to `release/1.4`, or rescuing one commit from an
abandoned branch.
**Cost:** the change now exists as two commits with different SHAs — a later merge of the two
branches can conflict. Use `git cherry-pick -x` so the new commit records its origin.

---

### 7. `git log` vs `git reflog`? ⭐⭐

- **`git log`** — commits **reachable** from a ref. Shared, travels on clone/push. Rewriting
  history makes commits vanish from it.
- **`git reflog`** — every position **HEAD** (or a branch) has held: commits, checkouts,
  resets, rebases, merges. **Local only, never pushed.**

The point: reflog sees **orphaned commits**, so it's the recovery tool.

```bash
git reflog
# def5678 HEAD@{1}: commit: Added feature X
git switch -c recovery def5678
```

⚠️ Entries expire (~90 days reachable / 30 unreachable), then `git gc` prunes the objects.

---

### 8. What is `HEAD`? What is a detached HEAD? ⭐

**`HEAD`** is a pointer to *"where you are"* — normally a **symbolic ref** to a branch
(`ref: refs/heads/main`), and that branch points to a commit.

**Detached HEAD** = HEAD points straight at a commit with no branch in between. Commits you
make there are reachable from nothing; switching away leaves them orphaned (recoverable via
reflog). Fix: `git switch -c new-branch` *before* moving away.

`HEAD~1` = first parent. `HEAD^2` = **second** parent (only meaningful on a merge commit).

---

### 9. How do you undo a commit that's already public? ⭐⭐

**`git revert`** — never `reset` + force-push on a shared branch.

```bash
git switch main
git log --oneline            # find the SHA
git revert <sha>             # creates an inverse commit
git push origin main
```

Reverting a **merge** needs `-m` to say which parent is mainline:
`git revert -m 1 <merge-sha>` (1 = the branch you merged *into*).

⚠️ Follow-up they'll ask: after reverting a merge, re-merging that branch won't restore the
code — Git thinks it's already merged. You must revert the revert.

---

### 10. What is `git stash` and where do stashes live? ⭐

Temporarily shelves uncommitted work (tracked files by default; `-u` for untracked) so you can
switch context with a clean tree.

Stashes are **real commits** on the hidden `refs/stash` ref — which is why a dropped stash is
often recoverable with `git fsck --lost-found`.

```bash
git stash push -m "wip: auth refactor"
git stash list
git stash pop            # apply + remove
git stash apply          # apply, keep
git stash branch fix stash@{0}   # ⭐ when the base has moved on
```

---

### 11. `git clean` — what does it remove?

**Untracked** files. Not ignored ones unless you add `-x`.

```bash
git clean -nd     # ⭐ ALWAYS dry-run first
git clean -fd     # remove untracked files + directories
git clean -fdx    # also remove IGNORED files ⚠️ (kills .env, venv/, node_modules/)
```

---

### 12. `git merge --squash` vs `--no-ff` vs fast-forward? ⭐⭐

- **Fast-forward** — no divergence, so Git just moves the pointer. No merge commit, no record
  the branch existed.
- **`--no-ff`** — forces a merge commit even when FF is possible. Keeps the feature branch
  visible and makes it revertible as one unit.
- **`--squash`** — collapses the branch into **one** commit on the target, with **no merge
  record**. Clean `main`, but the branch's individual commits are gone and Git doesn't know
  it was merged (so `git branch -d` will complain).

---

### 13. How would you find the commit that introduced a bug? ⭐⭐

**`git bisect`** — binary search over history. ~10 tests to find a culprit among 1000 commits.

```bash
git bisect start
git bisect bad                  # now
git bisect good v1.4.0          # last known-good
# test each checkout → git bisect good / bad
git bisect reset
git bisect run pytest tests/test_x.py   # ⭐ automated
```

Also worth naming: **`git log -S "func_name"`** (pickaxe — commits that added/removed that
string) and **`git blame -w -C`** (ignore whitespace, follow moved code).

---

### 14. Someone committed a secret. What now? ⭐⭐

**Order matters — say this sequence:**

1. **Rotate the credential immediately.** It is compromised; it exists in clones, forks, PR
   views, and CI logs. Everything else is cleanup.
2. Remove from history: `git filter-repo` (or BFG). `filter-branch` is deprecated.
3. Force-push and have everyone **re-clone** — rewritten history breaks existing clones.
4. Prevent: `pre-commit` secret scanning, push protection, `.gitignore` the config file.

Saying "just `git rm` and commit" fails the question — the blob is still in history.

---

### 15. Merge conflicts — how do you handle them?

Git can't decide when the **same region** of a file changed on both sides.

```bash
git status                          # "both modified"
git diff --name-only --diff-filter=U
# resolve, then
git add file && git rebase --continue     # or: git merge --continue
git merge --abort                          # bail out
```

Two things that impress:
- **`merge.conflictstyle = zdiff3`** — shows the **common ancestor** in the marker block, so
  you can see what each side actually changed rather than guessing.
- **`rerere`** — Git records your resolution and replays it automatically next time. Essential
  when repeatedly rebasing a long-lived branch.

⚠️ In a **rebase**, `--ours` is the upstream branch and `--theirs` is your commits — inverted
from a merge, because rebase replays your work onto their base.

---

### 16. Rapid fire

| Question | Answer |
|---|---|
| Commits = diffs or snapshots? | **Snapshots.** Diffs are computed on demand. |
| Why is branching cheap? | A branch is a **file containing one SHA**, not a copy. |
| `git diff A..B` vs `A...B` | `..` direct comparison; **`...` vs the merge base** (what a PR adds). |
| Lightweight vs annotated tag | Annotated is a real object (tagger, message, signable) — use for releases. |
| `--force` vs `--force-with-lease` | Lease **refuses if the remote moved** since your last fetch. Always use lease. |
| What does `git gc` do? | Packs loose objects, **prunes unreachable ones** — this is what finally deletes data. |
| Can you enforce hooks? | Only **server-side** (`pre-receive`). Client hooks are local and bypassable with `--no-verify`. |
| `.gitignore` on a tracked file? | **No effect.** `git rm --cached` first. |
| What's the index? | A real file (`.git/index`) holding the **staged snapshot**. |
| Shallow clone tradeoff | Fast CI clones, but `log`, `blame`, `bisect` and merge-base are crippled. |
| How to fix a bad commit *message* on `main`? | It's history — `revert` can't fix messages; amend+force-push only if the team agrees. |
