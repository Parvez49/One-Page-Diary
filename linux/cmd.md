## cat
  - cat stands for concatenate — it is a standard Unix command used to display or combine file contents.
  - It reads files from start to finish, and prints their contents to the standard output
  - Example:
	- cat file.txt -> This reads file.txt and prints its content to the screen.
	- cat file1 file2 -> Concatenates two files and prints output.
	- cat > file.txt  -> Takes input from keyboard and saves to file.
	- cat (no args)	  -> Reads input from keyboard (stdin)

--------Folder and file control-----------
####go to specific directory: cd (directory) ex:cd desktop
####show directory file: dir
####show directory file with hidden file:dir/a
####to show folder and file: tree
####make folder: mkdir (folder name) ex.mkdir new
####delete folder: rmdir (filder name) ex:rmdir new
####make file: echo >(file name) ex: echo a.txt
####open file name:file name ex: a.txt
####read file on cmd : type a.txt
####delete file: del a.txt
####delete folder with own file: rmdir /s new
####go to back folder: cd ..
####auto folder select: cd (tab press)
####go to desktop immediately: ../..

####copy file to file:copy a.txt b.txt
#### move a.txt b.txt (same for filder move)


####to show drive: wmic logicaldisk get name

run c program:  //install gcc compiler before c program run using cmd prompt
	:gcc -o hello hello.c  //here hello name used for creating hello.exe file