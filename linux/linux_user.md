## Types of Users:
---
- Root User
  - UID:0, username: root, 
- System User
  - UID(1-999), created by software installation.
- Regular user
  - UID(1000-above), for real user

### Manage Reqular User
---
```
  $ sudo useradd <user_name>     -> add or delete user only root or sudo privileges(member of sudo or wheel group)
  $ sudo useradd -m <user_name>  -> With home directory
  $ sudo passwd <user_name>      -> set password
  $ su – <user_name>             -> login/switch user
  $ su -                         -> switch root user
  $ whoami                       -> gives current user name
  $ id <user_name>               -> verify the user
  $ groups <user_name>           -> verify groups list

  $ sudo userdel <user_name>     -> does not delete the user's home directory or files
  $ sudo userdel -r <user_name>  -> delete the user's home directory or files  
```

### User Groups
types of group
- Primary group: each user’s primary group has the same name as the user.
- Secondary group: A user can belong to multiple secondary groups.
- ```
    $ sudo groupadd <groupname>  // To create a group
    $ sudo usermod -aG <groupname> <username>  // To add a user to a group
    $ groups <username>  // To see which groups a user belongs to
    $ sudo deluser <username> <groupname>  // To remove a user from a group

  ```

### File System in Linux:
---
The top directory is /.
- home
- etc
- var
- root
  - home directory for root user.
