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


### To remove a file: 
 git rm ph.py (if we delete file by using git command then file will be deleted from both directory and git stage)

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
git branch -m <rename_branch_name> 
git push --set-upstream origin <rename_current_branch_in_remote>
```

### 1. What is Git?
Git is a distributed version control system (DVCS) that is used to track changes in source code.

### 2. What is origin in Git?
In Git, "origin" states to the default name offered to the remote repository from which local repository was cloned. Git origin is used as a reference to control fetches, pulls, and pushes.
