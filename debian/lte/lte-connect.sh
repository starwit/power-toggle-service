#!/bin/bash

# Use lsusb to find the device id ("vendor:product")
DEVICE_ID="1bbb:00b6"

APN="internet.telekom"


function wait_for_modem_hardware() {
    # waiting until USB modem appears
    echo "Waiting for modem"
    until mmcli -m any &>/dev/null; do
        sleep 2
    done
}

function reset_modem() {
    echo "Resetting modem"
    usbreset "$DEVICE_ID"
}

echo "=== LTE Connect Script Starting ==="
reset_modem
wait_for_modem_hardware

echo "=== LTE Connect modem connected ==="
mmcli -m any

# get modem number
MODEM_ID=$(mmcli -m any -J | jq -r '.modem."dbus-path"' | grep -Po '\d+$')
echo "Using modem with id $MODEM_ID"

echo "=== LTE Connect enable modem ==="
mmcli -m $MODEM_ID -e

# Wait for the modem to be ready
for i in {1..10}; do
    state=$(mmcli -m $MODEM_ID -J | jq -r '.modem.generic.state')
    echo "Current modem state: $state"
    if [[ "$state" == "registered" || "$state" == "enabled" || "$state" == "connected" ]]; then
        echo "Modem is enabled."
        break
    fi
    echo "Waiting for modem to initialize..."
    sleep 3
done

echo "=== LTE Connect modem enabled ==="

echo "Connecting to APN $APN..."
mmcli -m $MODEM_ID --simple-connect="apn=$APN,ip-type=ipv4,allow-roaming=true" || {
    echo "Failed to connect modem."
    exit 1
}

# Wait for network registration
for i in {1..30}; do
    state=$( mmcli -m $MODEM_ID --output-json | jq -r '.modem.generic.state' )
    echo "Current modem state: $state"
    if [ "$state" == "connected" ]; then
        echo "✅ Modem is registered to network."
        break
    fi
    echo "Waiting for network registration..."
    sleep 3
done

echo "=== LTE Connect connection established ==="

sleep 1
# Fetch bearer info
BEARER_ID=$( mmcli -m $MODEM_ID -J | jq -r '.modem.generic.bearers[0]' | grep -Po '\d+$' )

echo "Using bearer with id $BEARER_ID"
mmcli -b $BEARER_ID

BEARER_IP=$( mmcli -b $BEARER_ID -J | jq -r '.bearer."ipv4-config".address' )
BEARER_GW=$( mmcli -b $BEARER_ID -J | jq -r '.bearer."ipv4-config".gateway' )
BEARER_IFACE=$( mmcli -b $BEARER_ID -J | jq -r '.bearer.status.interface' )
BEARER_IP_PREFIX=$( mmcli -b $BEARER_ID -J | jq -r '.bearer."ipv4-config".prefix' )
BEARER_DNS=$( mmcli -b $BEARER_ID -J | jq -r '.bearer."ipv4-config".dns | join (" ")' )

echo "Using IP info from bearer:"
echo "BEARER_IP: $BEARER_IP"
echo "BEARER_GW: $BEARER_GW"
echo "BEARER_IP_PREFIX: $BEARER_IP_PREFIX"
echo "BEARER_IFACE: $BEARER_IFACE"
echo "BEARER_DNS: $BEARER_DNS"

if [[ -z "$BEARER_IP" || -z "$BEARER_GW" || -z "$BEARER_IP_PREFIX" || -z "$BEARER_IFACE" || -z "$BEARER_DNS" ]]; then
    echo "❌ No valid IP info — aborting."
    exit 1
fi

echo "Setting up $BEARER_IFACE..."

# Configure interface                                                                                                                                                                                                                                                                                                       
ip addr flush dev $BEARER_IFACE
ip link set $BEARER_IFACE up
ip addr add $BEARER_IP/$BEARER_IP_PREFIX dev $BEARER_IFACE

echo "Setting DNS servers"
resolvectl dns $BEARER_IFACE $BEARER_DNS

echo "Setting default IP route"
ip route add default via $BEARER_GW

echo "Checking connection"
if ping -c 4 -W 1 1.1.1.1 >/dev/null; then
    echo "✅ Connection check successful!"
    exit 0
else
    echo "❌ Connection check failed!"
    exit 1
fi