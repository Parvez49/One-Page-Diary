## SSH (Secure Shell):
  is a network protocol used to securely connect to and control remote computers over a network — usually over the internet.

### authorized_keys: 
  Holds the list of public keys that are allowed to connect to user account without a password.

### id_rsa: 
  The public key is derived from this.
### id_rsa.pub:
  Used to verify that a connecting client holds the matching private key.


## -------------------------- SSH GIT GITHUB ---------------------------
- $ ls -al ~/.ssh   // to check ssh list in pc
- $ ssh-keygen -t rsa -b 4096 -C "user@example.com" -f ~/.ssh/user  // to generating ssh command
- or 
- $ ssh-keygen -t ed25519 -C "user@example.com" -f ~/.ssh/user  // more faster than rsa
- $ cat ~/.ssh/user.pub     // To display the content of your SSH public key
- save user.pub content to github SSH and GPG settings


### Multiple github authentication
- $ ssh-keygen -t rsa -b 4096 -C "user@example.com" -f ~/.ssh/user2
- or
- $ ssh-keygen -t ed25519 -C "user2@example.com" -f ~/.ssh/user2  // more faster than rsa
- configure config file
```
$ nano ~/.ssh/config
	# GitHub account 1
	Host github.com   # for git alise user name
	    HostName github.com
	    User git
	    IdentityFile ~/.ssh/user
	    IdentitiesOnly yes

	# GitHub account 2
	Host github-user2
	    HostName github.com
	    User git
	    IdentityFile ~/.ssh/user2
	    IdentitiesOnly yes
```
- test connection setup: $ ssh -T git@github.com
- test conncetion setup for github account 2: $ ssh -T git@github-user2
- change github repository ssh command to clone and push from github account 2
  ```
	$ git clone git@github-user2:<github-username/repo.git>
	# for existing repository
	$ git remote -v
	$ git remote set-url origin git@github-user2:<github-username/repo.git>

  ```

## SSH Connection Flow (Local_PC → Server_PC)
   1. Generate SSH Key Pair on Local_PC (if not exists)
		```bash
			$ ssh-keygen -t rsa -b 4096 -C "root@dev" -f ~/.ssh/dev_pc // Creates ~/.ssh/dev_pc and ~/.ssh/dev_pc.pub
			$ ssh-keygen -t ed25519 -C "root@dev" -f ~/.ssh/dev_pc
		```
   2. Copy Public Key to Server_PC
		```
      		$ ssh-copy-id -i ~/.ssh/dev_pc.pub <server_user>@<server_ip>  // Adds Local_PC's public key to Server_PC's ~/.ssh/authorized_keys
	  	```
   3. Connect to Server_PC
		```
      		$ ssh <server_user>@<server_ip>  // Authenticates using the private key (~/.ssh/dev_pc)
		```
   4. Connect to server_pc by alise.
		- 
		```
			# configure config file
			Host myserver
				HostName <server_ip>
				User <server_user>
				IdentityFile ~/.ssh/dev_pc
		```
		- run: $ ssh myserver