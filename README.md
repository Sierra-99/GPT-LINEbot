# Overview
---
- Description
  - LINE chatbot using ChatGPT API, developed with Flask.
- Environment
  - Ubuntu 22.04 VPS



# Requirements
---
- Python and pip installation
```zsh
$ sudo apt install python3 python3-pip
```

- Directory
```zsh
$ pwd
~/LINEbot

$ ls -a
.env  app.py  requirements.txt
```

- Installation of required packages
```zsh
$ sudo pip3 install -r requirements.txt
```

- Opening port 5000
	- The following are iptables commands.
```zsh
$ sudo iptables -A INPUT -p tcp --dport 5000 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

$ sudo iptables -A OUTPUT -p tcp --sport 5000 -m conntrack --ctstate ESTABLISHED -j ACCEPT
```

- Set the Webhook URL on the LINE Developers page.
	- If the domain name is example.com and the port number used is 5000, the webhook URL is https://example.com:5000/callback.



# Test in a local
---
## Run app.py
```zsh
$ sudo python3 app.py
```

## Create a daemon with systemd.
- Create systemd service.
```zsh
$ sudo vi /etc/systemd/system/myflaskapp.service
```

```zsh
[Unit]
Description=My Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/<path>/<to>/LINEbot
ExecStart=/usr/bin/python3 /<path>/<to>/LINEbot/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

- Make systemd recognise the service.
```zsh
$ sudo systemctl daemon-reload
```

- Start service.
```zsh
$ sudo systemctl start myflaskapp
```

- Check service status.
```zsh
$ sudo systemctl status myflaskapp
```

- Set to start automatically when the system is rebooted.
```zsh
$ sudo systemctl enable myflaskapp
```
