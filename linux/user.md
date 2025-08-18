### Types of Users:
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





## cat
  - cat stands for concatenate — it is a standard Unix command used to display or combine file contents.
  - It reads files from start to finish, and prints their contents to the standard output
  - Example:
	- cat file.txt -> This reads file.txt and prints its content to the screen.
	- cat file1 file2 -> Concatenates two files and prints output.
	- cat > file.txt  -> Takes input from keyboard and saves to file.
	- cat (no args)	  -> Reads input from keyboard (stdin)

### Folder and file control
- cd (directory) ex:cd desktop  // go to specific directory:
- ls or dir  // show directory contents
- ls or dir -a  // show directory contents with hidden contents
- ls -lha  // long list with hidden and permission and size
- tree // show drectory contents as a tree structures
- mkdir, rmdir (folder name) // make and delete directory
- touch, cat, nano, del (file name) // make, show and edit file content.
- copy a.txt b.txt, mv a.txt b.txt  // copy and move file
- cd .. // go back
