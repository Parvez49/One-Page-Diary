# git command


### Git Initialization
```
 git init
```

### git account:
	git config --global user.name "your/user_name"
	git config --global user.email "yourmail@mail.com"
	git config --global --list (to check login user name and email address)

### git Track
```
 git add ph.py
 git add . (to add all untract file)
```

### git Commit 
```
 git commit -m "comments"(to save editing history on a file)

 # commit with previous commit 
 git commit --amend --no-edit     // --no-edit for similar commit message
 git push --force                 // to push updated commit 


```

### git log
```
 git log
 git log --oneline
 git show (commit id)
 
 git diff
 git diff --staged (when we add all file and commit then git diff return null)
 git diff (id) (id) (that means git return difference between two commit)
```

### To restore a file:
$ git restore <file>    // Restore a file from the last commit
$ git restore .         // Restore all changes from the last commit

### To remove a file: 
$ git rm ph.py (if we delete file by using git command then file will be deleted from both directory and git stage)
$ git rm --cached <file_name>    // to remove files from the working directory and the staging area.

version control(if we add two or more commit then we think that our previous version or commit was better than last commit)
####To control version: git checkout (id) ph.py (id means whice version we want)





### Working with github.
```
Create github repository on github first
copy link from repository and

####to clone:git clone (link) (this create folder on directory)
####To push from local repository to github repository: git push -u origin master

-------------------------------------------------------------------------

to upload a repository
…or create a new repository on the command line
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:Parvez49/Programming.git
git push -u origin master

…or push an existing repository from the command line
git remote add origin git@github.com:Parvez49/Programming.git
git branch -M main
git push -u origin main
```

## git branch
```
git checkout -b <branch_name>         // to create and move new branch
git checkout --orphan <branch_name>   // to create empty commit new branch with existing files and folders.
git rm -rf .                          // to remove all files and folders
$ git branch -m <rename_branch_name>
$ git branch -m <old_branch_name> <new_branch_name>
git push --set-upstream origin <rename_current_branch_in_remote>
$ git push origin --delete <branch-name>  // To delete a remote branch
```

### git stash
The git stash is a command used to temporarily save changes that are not yet ready to be committed. It allows developers to switch branches or work on something else without losing their progress. 
```
$ git stash         // Save current changes
$ git stash list    // View stashes
$ git stash pop     // Reapply the most recent stash and remove it from stash history
$ git stash apply   // Reapply a stash without removing it from history
$ git stash drop stash@{n} // Delete a specific stash
```

### 1. What is Git?
Git is a distributed version control system (DVCS) that is used to track changes in source code.

### 2. What is origin in Git?
In Git, "origin" states to the default name offered to the remote repository from which local repository was cloned. Git origin is used as a reference to control fetches, pulls, and pushes.

### 3. What is the purpose of the git clean command?
The git clean command is used to erase ignored files from the working directory of Git repository.

### 4. How do you revert a commit that has already been pushed and made public?
to revert a commit that has been pushed and made public, follow these steps:
```
$ git checkout <branch-name>  // Checkout the Branch: Switch to the branch where you want to revert the commit.
$ git log                     // Find the Commit to Revert: Use 'git log' to find the commit hash of the commit you want to revert.
$ git revert <commit-hash>    // Revert the Commit: Use 'git revert' followed by the commit hash of the commit you want to revert.
$ git push origin <branch-name>
```

### 5. Explain the difference between reverting and resetting?
- git reset: Moves the HEAD pointer to a previous commit, removing changes from the commit history. It can modify staged and working directory changes.
- git revert: Creates a new commit that undoes changes from a previous commit without modifying commit history. It is safer when working in a shared repository.

### 6. What is the difference between git reflog and log?
- git log: Displays commit history of a repository, Only shows commits in the current branch history, Does not track changes outside commit history, Used to review past commits and changes.
- git reflog: Tracks movements of HEAD and branch changes, Shows all references, even those not in branch history, Can help recover lost commits, Used to restore lost branches or commits.

### 7. What is the HEAD in Git?
HEAD in Git is a reference to the latest commit on the currently checked-out branch.

### 8. Explain the difference between 'git merge' and 'git rebase' and when you would use each?
```
A --- B --- C  (main)
         \
          D --- E --- F  (feature-branch)
	  
- git merge: Combines two branches and creates a merge commit.
  A --- B --- C --- M  (main)
         \       /
          D --- E --- F  (feature-branch)
- git rebase: Reapplies commits from one branch on top of another, creating a linear history.
  A --- B --- C --- D' --- E' --- F'  (main)
```
### 9. What is the purpose of git cherry-pick?
```
A --- B --- C --- D  (main)
         \
          E --- F --- G  (feature-branch)

git checkout main
git cherry-pick F
After this, the history becomes:

A --- B --- C --- D --- F'  (main)
         \
          E --- F --- G  (feature-branch)
```




