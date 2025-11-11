#!/bin/bash

# Use lsusb to find the device id ("vendor:product")
# DEVICE_ID="1bbb:00b6"
# APN="internet.telekom"
# WWAN_IFACE="wwan0"

# Read configuration parameters from command line arguments or environment variables
DEVICE_ID=${1:-$DEVICE_ID}
APN=${2:-$APN}
WWAN_IFACE=${3:-$WWAN_IFACE}

# Exit if not all parameters are set
if [[ -z "$DEVICE_ID" || -z "$APN" || -z "$WWAN_IFACE" ]]; then
    echo "Usage: $0 <device_id> <apn> <wwan_iface>"
    echo "Or set DEVICE_ID, APN, and WWAN_IFACE environment variables."
    exit 1
fi

main() {

    echo "=== LTE Connect Script Starting ==="

    # Check if we already have a connection
    if check_connection; then
        echo "Already connected, exiting."
        exit 0
    fi

    wait_for_modem_hardware

    # Check if mbim driver has been loaded
    if ! is_mbim_driver_active; then
        echo "MBIM driver is not active, rebinding modem."
        rebind_modem
        wait_for_modem_hardware
    else
        echo "MBIM driver is active."
    fi

    reset_modem
    wait_for_modem_hardware

    echo "=== LTE Connect modem connected ==="
    mmcli -m any

    # get modem number
    MODEM_ID=$(get_modem_id)
    echo "Using modem with id $MODEM_ID"

    echo "=== LTE Connect enable modem ==="
    mmcli -m $MODEM_ID -e

    wait_for_modem_ready

    echo "=== LTE Connect modem enabled ==="

    echo "Connecting to APN $APN..."
    mmcli -m $MODEM_ID --simple-connect="apn=$APN,ip-type=ipv4,allow-roaming=true" || {
        echo "Failed to connect modem."
        exit 1
    }

    wait_for_modem_connected

    echo "=== LTE Connect connection established ==="

    sleep 1
    # Fetch bearer info
    BEARER_ID=$( mmcli -m $MODEM_ID -J | jq -r '.modem.generic.bearers[0]' | grep -Po '\d+$' )

    echo "Using bearer with id $BEARER_ID"
    mmcli -b $BEARER_ID

    BEARER_IP=$( mmcli -b $BEARER_ID -J | jq -r '.bearer."ipv4-config".address' )
    BEARER_GW=$( mmcli -b $BEARER_ID -J | jq -r '.bearer."ipv4-config".gateway' )
    BEARER_IP_PREFIX=$( mmcli -b $BEARER_ID -J | jq -r '.bearer."ipv4-config".prefix' )
    BEARER_DNS=$( mmcli -b $BEARER_ID -J | jq -r '.bearer."ipv4-config".dns | join (" ")' )

    echo "Using IP info from bearer:"
    echo "BEARER_IP: $BEARER_IP"
    echo "BEARER_GW: $BEARER_GW"
    echo "BEARER_IP_PREFIX: $BEARER_IP_PREFIX"
    echo "BEARER_DNS: $BEARER_DNS"

    if [[ -z "$BEARER_IP" || -z "$BEARER_GW" || -z "$BEARER_IP_PREFIX" || -z "$BEARER_DNS" ]]; then
        echo "❌ No valid IP info — aborting."
        exit 1
    fi

    echo "Setting up $WWAN_IFACE..."

    # Configure interface
    ip addr flush dev $WWAN_IFACE
    ip link set $WWAN_IFACE up
    ip addr add $BEARER_IP/$BEARER_IP_PREFIX dev $WWAN_IFACE

    echo "Setting DNS servers"
    resolvectl dns $WWAN_IFACE $BEARER_DNS

    echo "Setting default IP route"
    ip route add default via $BEARER_GW

    check_connection
    exit $?
}

check_connection() {
    echo "Checking connection on $WWAN_IFACE"
    if ping -c 1 -W 0.5 -I $WWAN_IFACE 1.1.1.1 >/dev/null; then
        echo "✅ Connection check successful!"
        return 0
    else
        echo "❌ Connection check failed!"
        return 1
    fi
}

wait_for_modem_hardware() {
    echo "Waiting for modem to register..."
    for i in {1..20}; do
        echo "Checking for modem (attempt $i)..."
        if mmcli -m any &>/dev/null; then
            echo "Modem detected."
            return
        fi
        sleep 2
    done
    echo "Modem not detected. Giving up."
    exit 1
}

wait_for_modem_ready() {
    # Wait for the modem to be ready
    for i in {1..10}; do
        state=$(get_modem_state)
        echo "Current modem state: $state"
        if [[ "$state" == "registered" || "$state" == "enabled" || "$state" == "connected" ]]; then
            echo "Modem is ready."
            return
        fi
        sleep 2
    done
    echo "Modem is not ready. Giving up."
    exit 1
}

wait_for_modem_connected() {
    # Wait for the modem to be connected
    for i in {1..30}; do
        state=$(get_modem_state)
        echo "Current modem state: $state"
        if [ "$state" == "connected" ]; then
            echo "✅ Modem is registered to network."
            return
        fi
        sleep 2
    done
    echo "Modem failed to connect. Giving up."
    exit 1
}

reset_modem() {
    echo "Resetting modem $DEVICE_ID"
    usbreset "$DEVICE_ID"
}

rebind_modem() {
    USB_PATH=$(get_usb_id)
    echo "Rebinding modem at USB path $USB_PATH"
    echo "$USB_PATH" > /sys/bus/usb/drivers/usb/unbind
    echo "$USB_PATH" > /sys/bus/usb/drivers/usb/bind
}

is_mbim_driver_active() {
    mmcli -m any -J | jq -e '.modem.generic.drivers[] | select(. == "cdc_mbim")' >/dev/null 2>&1
}

get_usb_id() {
    mmcli -m any -J | jq -r '.modem.generic.device' | grep -Po '[0-9\-]+$'
}

get_modem_id() {
    mmcli -m any -J | jq -r '.modem."dbus-path"' | grep -Po '\d+$'
}

get_modem_state() {
    mmcli -m any -J | jq -r '.modem.generic.state'
}

main