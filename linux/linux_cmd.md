### Folder and file control
- cd (directory) ex:cd desktop  // go to specific directory:
  - cd /  (root directory)
  - cd ~   (user home directory)
- ls or dir  // show directory contents
- ls or dir -a  // show directory contents with hidden contents
- ls -lha  // long list with hidden and permission and size
- tree // show drectory contents as a tree structures
- mkdir, rmdir (folder name) // make and delete directory
- touch, cat, nano, del (file name) // make, show and edit file content.
- copy a.txt b.txt, mv a.txt b.txt  // copy and move file
- cd .. // go backs

### cat
  - cat stands for concatenate — it is a standard Unix command used to display or combine file contents.
  - It reads files from start to finish, and prints their contents to the standard output
  - Example:
	- cat file.txt -> This reads file.txt and prints its content to the screen.
	- cat file1 file2 -> Concatenates two files and prints output.
	- cat > file.txt  -> Takes input from keyboard and saves to file.
	- cat (no args)	  -> Reads input from keyboard (stdin)

### Checking OS 
- uname -a 
- lsb_release -a
- cat /etc/os-release

### difference between sudo and su
- sudo: superuser do, su: substitute user (defaults to root)
- sudo: temporary root privileges, su: Switches user
- sudo apt install curl // install curl in system
- su - // switch to root user
- sudo usermod -aG sudo username  // Add a User to the sudo Group


### Useful Commands
- grep: stands for Global Regular Expression Print. It searches for a pattern in the input text
- ls | grep search_string
- grep -i(case insensitive), -c(count), -n(show line number), -r(recursive inside directories)
















