#!/bin/bash

function wait_for_modem_hardware() {
    # waiting until USB modem appears
    echo "Waiting for modem to appear..."
    until mmcli -m any &>/dev/null; do
        sleep 2
    done
}

function rebind_usb() {
    # Wait for modem firmware to settle
    sleep 10

    DEVPATH="3-5"

    # Reload relevant USB drivers
    modprobe -r cdc_ether cdc_ncm option || true
    sleep 1
    modprobe cdc_ether cdc_ncm option || true

    # Rebind the USB device
    if [ -e "/sys/bus/usb/drivers/usb/$DEVPATH" ]; then
    echo "$DEVPATH" | tee /sys/bus/usb/drivers/usb/unbind
    sleep 1
    echo "$DEVPATH" | tee /sys/bus/usb/drivers/usb/bind
    fi

    # Give it a few seconds to settle
    sleep 5

    systemctl restart ModemManager

    # Trigger ModemManager rescan
    /usr/bin/mmcli --scan-modems
}


echo "=== LTE Connect Script Starting ==="
rebind_usb
wait_for_modem_hardware

echo "=== LTE Connect modem connected ==="
mmcli -m any

# get modem number
IFS='/ ' read -r _ _ _ mm _ mn mt < <(mmcli -L)
echo "using modem number $mn"

APN="internet.telekom"
MODEM=$mn
IFACE="wwan0"

echo "=== LTE Connect enable modem ==="
mmcli -m $MODEM -e
sleep 3

# Wait for the modem to be ready
for i in {1..10}; do
    state=$(mmcli -m $MODEM --output-json | jq -r '.modem.generic.state')
    echo "Current modem state: $state"
    if [[ "$state" == "registered" || "$state" == "enabled" || "$state" == "connected" ]]; then
        echo "Modem is enabled."
        break
    fi
    echo "Waiting for modem to initialize..."
    sleep 3
done

echo "=== LTE Connect modem enabled ==="

# Double check data ports exist
if ! mmcli -m $MODEM | grep -q "ports:"; then
    echo "No data port found — trying to re-enable modem..."
    mmcli -m $MODEM -d
    sleep 2
    mmcli -m $MODEM -e
    sleep 5
fi

echo "=== LTE Connect modem dataport detected ==="

echo "Connecting to APN $APN..."
mmcli -m $MODEM --simple-connect="apn=$APN,ip-type=ipv4,allow-roaming=true" || {
    echo "Failed to connect modem."
    exit 1
}

echo "=== LTE Connect connect modem ==="

# Wait for network registration
for i in {1..30}; do
    state=$(mmcli -m $MODEM --output-json | jq -r '.modem.generic.state')
    echo "Current modem state: $state"
    if [ $state == "registered" ] || [ $state == "connected" ]; then
        echo "✅ Modem is registered to network."
        break
    fi
    echo "Waiting for network registration..."
    sleep 3
done

sleep 1
# Fetch bearer info
echo "==== getting bearer number ===="                                                                                                                           │       valid_lft forever preferred_lft forever
bearer=$(mmcli -m $MODEM --output-json | jq --raw-output -r '.modem.generic.bearers.[0]')
BEARER=${bearer: -1}
echo "using bearer $BEARER"

echo "==== getting bearer info ===="
mmcli -b $BEARER 2>/dev/null
info=$(mmcli -b $BEARER 2>/dev/null)
IP=$(echo "$info" | awk '/address:/{print $3}')
GW=$(echo "$info" | awk '/gateway:/{print $3}')
PREFIX=$(echo "$info" | awk '/prefix:/{print $3}')                                                                                                                                                                                                                                                                           

# retry getting values
if [[ -z "$IP" || -z "$GW" || -z "$PREFIX" ]]; then
    echo "Failed to get IP/gateway/prefix. Waiting 5s and retrying..."
    sleep 5
    info=$(mmcli -b $BEARER 2>/dev/null)
    IP=$(echo "$info" | awk '/address:/{print $3}')
    GW=$(echo "$info" | awk '/gateway:/{print $3}')
    PREFIX=$(echo "$info" | awk '/prefix:/{print $3}')
fi

if [[ -z "$IP" || -z "$GW" || -z "$PREFIX" ]]; then
    echo "❌ Still no valid IP info — aborting."
    echo "$info"
    exit 1
fi

# get DNS servers
DNS1=$(mmcli -b 1 --output-json | jq --raw-output -r '.bearer.["ipv4-config"].dns[0]')
DNS2=$(mmcli -b 1 --output-json | jq --raw-output -r '.bearer.["ipv4-config"].dns[1]')


echo "Assigning IP ${IP}/${PREFIX}, gateway ${GW}, and DNS ${DNS1} / ${DNS2} to ${IFACE}..."

# Configure interface                                                                                                                                                                                                                                                                                                       
ip addr flush dev $IFACE
ip link set $IFACE up
ip addr add ${IP}/${PREFIX} dev $IFACE
ip route add default via ${GW} || echo "Warning: Route already exists"
resolvectl dns $IFACE $DNS1 $DNS2