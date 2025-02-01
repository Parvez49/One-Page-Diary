
### Use the ls -l command to see file permissions:
```commandline
ls -l filename
   -rw-r--r-- 1 parvez users  1234 Jan 31 12:00 myfile.txt
```

### Changing File Permissions (chmod)
```shell
chmod [permissions] filename
    (u:user(owner), g:group, o:others, a: all, r, w, x:execute)

chmod u+x myfile.txt  # Grant execute permission to the owner
chmod g-w myfile.txt  # Remove write permission for the group
chmod +x myscript.sh  # Make a file executable for everyone

```

### Changing File Ownership (chown)
```shell
chown user:group filename
chown -R parvez:developers mydirectory/

```

### Changing Group Ownership (chgrp)
```shell
chgrp developers myfile.txt

```