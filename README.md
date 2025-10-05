# Power Toggle Service
A simple service to toggle power state of a device. 

## Usage

## Build

### Prerequisites
Things you need to build package.

* Python 
* Poetry
* build-essentials

### Build APT package
Makefile has target to build an APT package. Virtual environment is created by exporting Poetry dependencies into a requirements.txt file. APT is build like so:
```bash
poetry self add poetry-plugin-export
make build-deb
```

APT package can then be found in folder _target_. You can test installation using Docker, however SystemD (probably) won't work.
```bash
docker run -it --rm -v ./target:/app  jrei/systemd-ubuntu:latest bash
apt update && apt install -y /app/power-toggle-switch_0.0.1_all.deb
```
You can however test, if everyting is installed to the right place.