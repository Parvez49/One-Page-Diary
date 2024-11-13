

# necessary package for ubuntu mysql
```
sudo apt-get update
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

# To change root password
```
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_new_password';
FLUSH PRIVILEGES;
```


# to import database. 
```
sudo nano /etc/mysql/my.cnf:   // if need
	[mysqld]
	max_allowed_packet = 64M

mysql -u root -p emrphase3 < /tmp/emrphase3.sql 
```


