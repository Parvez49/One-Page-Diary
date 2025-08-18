### Command to see file permissions:
```commandline
ls -l filename
   -rw-r--r-- 1 parvez users  1234 Jan 31 12:00 myfile.txt
```

### 1. Structure of Permission Strings
---

Each permission string consists of 10 characters:
   ```
      Type  Owner   Group   Others
      -     r w x   r - x   r - x
      d     r w x   r - x   r - x
      -     r w -   r - -   r - -
   ```

- Type:
   -  -(reqular file: txt, jpg, mp4, or user uses files)
   -  d: directory
   -  l: A pointer to another file or directory
   -  s: socket file(inter-process communication)
   -  c,b: character and block device that represent hardware or virtual devices, read-write data by character and block
  
- Owner, Group, Others
   - r, w, x: read, write, execute(execute means: Run if it's a program/script, or enter if it's a directory)
   - r-x means Can read and Execute but not write.

### Changing File Permissions (chmod)
---

There are main two ways to set permissions:
- Numeric (Octal) mode
  ```
    Permission  Binary  Value 
    ----------  ------  ----- 
        r        100      4     
        w        010      2     
        x        001      1     
        -        000      0     
  ```
  - Add the values to get total permission: 7(4+2+1: rwx), 6(4+2, rw-), 5(4+1, r-x), 4(4, r--), 0(0, ---, no permission).
  - chmod [OWNER][GROUP][OTHERS] <file_name>
  - chmod 755 <file_name> -> rwx for owner, rx for Group and others.
  - chmod -R 755 <directory> -> change permissions all files and subdirectories inside directory.
  - chmod -Rv 755 myfolder  -> Verbose: show what’s being changed
  - chmod -Rc 755 myfolder  -> Only show actual changes
  - chmod --reference=ref.txt target.txt -> Copy permissions from another file

- Symbolic Mode
  - Who: u(owner/user), g(group), o(others), a(all)
  - Action: +(add), -(remove), =(set exact)
  - Permission: r(read), w(write), x(execute)
  - chmod u+x <file_name>  -> Add execute permission to the owner
  - chmod ug+rw <file_name> -> Add read, write permissions to owner and group


### Changing File Ownership (chown)
---
- chown [new_owner] <file_or_directory>
- chown <owner>:<group> myfile.txt -> Change Both Owner and Group


### Changing Group Ownership (chgrp)
---
- chgrp [new_group] <file_or_directory>  -> (file or directory belong to a single group at a time)
- chgrp <group> myfile.txt
