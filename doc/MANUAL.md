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

## Network Messages
Following example shows, how a shutdown message is supposed to look like:

```json
{
    "state": "shutdown"
}
```