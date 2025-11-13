# Power Toggle Service User's Manual
In this document, you'll find all information to run and to use MSU-Manager.

## App Configuration

After installation config file of service is located at /etc/msu-manager/settings.yaml. Here is an example of configuration file:

```yaml
log_level: INFO
udp_bind_address: 0.0.0.0 # bind address for service
udp_listen_port: 5151 # port for listener
shutdown_delay_s: 180 # shutdown delay in seconds
shutdown_command: ['sudo', 'shutdown', '-h', 'now'] # be careful if you want to test on your machine
```
## OS Configuration
_This should have been set up by the installation script._
In order to allow service to execute shutdown command without password prompt using sudo, you need to add following line to sudoers file. You can add and edit a sudoers file using visudo command.

```
sudo visudo -f /etc/sudoers.d/msu-manager
# Add the following line
# msumanager ALL=NOPASSWD: /usr/sbin/shutdown -h now
```

## Managing the Service
To see if service is running use the following command:
```bash
systemctl status msu-manager
```

Please refer to SystemD documentation for more info, on how to use services, e.g. https://wiki.archlinux.org/title/Systemd

## Network Protocol
This application receives UDP messages from HCU (Hardware Control Unit). This is a micro controller based device, that manages power, temperature and a number of other physical aspects. Both application parts thus need to follow a shared protocol.

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
    "key": "key",
    "value": "value"
}
```