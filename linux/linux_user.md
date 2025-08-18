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
### File System in Linux:
---
The top directory is /.
- home
- etc
- var
- root
  - home directory for root user.
