# Power Toggle Service User's Manual
In this document, you'll find all information to run and to use Power Toggle Service.

## Configuration

After installation config file of service is located at /etc/msu-manager/settings.yaml. Here is an example of configuration file:

```yaml
log_level: INFO
bind_address: 0.0.0.0 # bind address for service
udp_port: 5151 # port for listener
shutdown_timeout: 180 # shutdown delay in seconds
```

To see if service is running use the following command:
```bash
systemctl status msu-manager
```

Please refer to SystemD documentation for more info, on how to use services, e.g. https://wiki.archlinux.org/title/Systemd

## Network Protocol
This application receives UDP messages from MSU Controller. This is a micro controller based device, that manages power, temperature and a number of other physical aspects. Both application parts thus need to follow a shared protocol.

Protocol is composed of the following messages:

```json
{
    "command": "SHUTDOWN"
}

{
    "command": "RESUME"
}

{
    "command": "HEARTBEAT",
    "version" : "0.0.3"
}

{
    "command": "LOG",
    "values": [
        {
            "key": "temp1",
            "value" : "42,0"
        },
        {
            "key": "temp2",
            "value" : "42,0"
        }
    ]
}
```