# Overview
---
- ChatGPT APIを利用したLINE botを、Flaskで開発
- 実行環境は、Ubuntu 22.04 VPS



# Requirements
---
- Pythonとpipのインストール
```zsh
$ sudo apt install python3 python3-pip
```

- ディレクトリ
```zsh
$ pwd
~/LINE

$ ls -a
.env  app.py  requirements.txt
```

- 必要なパッケージのインストール
```zsh
$ sudo pip3 install -r requirements.txt
```

- ポート5000番の開放
	- 以下は、iptablesのコマンド
```zsh
$ sudo iptables -A INPUT -p tcp --dport 5000 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

$ sudo iptables -A OUTPUT -p tcp --sport 5000 -m conntrack --ctstate ESTABLISHED -j ACCEPT
```

- LINE Developersページにて、Webhook URLを設定。
	- ドメイン名が example.com で、サーバー上のポート番号が 5000 の場合、Webhook URLは https://example.com:5000/callback となります。



# Usage
---
## app.pyを実行
```zsh
$ sudo python3 app.py
```

## systemdでデーモン化
- systemdサービスを作成
```zsh
$ sudo vi /etc/systemd/system/myflaskapp.service
```

```zsh
[Unit]
Description=My Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/home/sierra/LINE
ExecStart=/usr/bin/python3 /home/sierra/LINE/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

- systemdにサービスを認識させる
```zsh
$ sudo systemctl daemon-reload
```

- サービスを起動
```zsh
$ sudo systemctl start myflaskapp
```

- サービスの状態を確認
```zsh
sudo systemctl status myflaskapp
```

- システムの再起動時に、自動的に起動するよう設定
```zsh
$ sudo systemctl enable myflaskapp
```
