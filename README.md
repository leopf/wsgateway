# wsgateway

The `wsgateway` package allows you to tunnel network traffix (TCP) through websocket connections.

A websocket gateway has 3 components.
1. A gateway server, which is accessible by both, the machine you want to access and the machine you want to use to access the other.
2. A provider, which is a machine you want to connect to.
3. A client...

## Installation
run:
```
pip install git+https://github.com/leopf/wsgateway.git
```

## gateway setup

### Setting up a service

A service can to be created at `/lib/systemd/system/mywsgateway.service`.

This can inlcude the following. The settings may be adjusted to your needs.

```
[Unit]
Description=My Websocket Gateway
After=syslog.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/
ExecStart=/usr/bin/python3 /usr/local/bin/wsgw-gateway --password [your password] --port 8000
Restart=always
RestartSec=3
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
```

after that you can run:

1. `sudo systemctl daemon-reload`
2. `sudo systemctl enable mywsgateway.service`
3. `sudo systemctl start mywsgateway.service`

### configuring a nginx reverse proxy

example:
```
server {
    server_name gw.example.com;

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;

        proxy_pass http://wsgw-backend;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    listen [::]:80; 
    listen 80;
}

upstream wsgw-backend {
    server localhost:8000;
}
```

## client usage

First you have to create a profile file. In this example it will be called `profile.ini`. 

```
[remote]
provider = my-computer
port = 22
hostname = localhost

[local]
port = 9999

[gateway]
url = ws://gw.example.com/
password = [your password]
```

then you can run the client with: `wsgw-client --profile profile.ini`

After that you can create an ssh connection to your remote machine by connectiong to localhost:9999.

## provider usage
In order for a client to connect to a provider, the provider needs to be running.

This can be done using the following command:
```
wsgw-provider --provider-name "my-computer" --gateway-url "ws://gw.example.com/" --gateway-password [your password]
```