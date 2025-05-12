#!/bin/bash
# iOS兼容热点设置脚本 - 简化版
# filepath: /home/cat/Py-server/ios_hotspot.sh

# 确保WiFi未被屏蔽
rfkill unblock wifi
rfkill unblock all

# 停止可能影响的服务
systemctl stop NetworkManager 2>/dev/null
systemctl stop wpa_supplicant 2>/dev/null

# 彻底清理
killall hostapd 2>/dev/null
killall dnsmasq 2>/dev/null

# 设置WiFi接口
ip link set wlan0 down
sleep 2
ip addr flush dev wlan0
ip link set wlan0 up
sleep 2
ip addr add 10.42.0.1/24 dev wlan0

# 创建最简单的hostapd配置 - 使用最基本的设置以提高兼容性
cat > /tmp/ios_hostapd.conf << EOF
interface=wlan0
driver=nl80211
ssid=Lampbot
hw_mode=g
channel=1
auth_algs=1
wpa=2
wpa_passphrase=lampbot2025
wpa_key_mgmt=WPA-PSK
country_code=CN
IEEE80211ac=0
beacon_int=100
dtim_period=1
EOF

# 启动热点
echo "启动简化版iOS兼容热点..."
hostapd -B /tmp/ios_hostapd.conf

# 配置DHCP
cat > /tmp/simple_dnsmasq.conf << EOF
interface=wlan0
dhcp-range=10.42.0.2,10.42.0.20,255.255.255.0,1h
EOF

# 启动DHCP服务
dnsmasq -C /tmp/simple_dnsmasq.conf

# 启用NAT
iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE

# 最后显示状态
echo "热点启动完成："
echo "SSID: Lampbot"
echo "密码: lampbot2025"
echo "IP地址: 10.42.0.1"
echo
echo "iOS设备说明："
echo "1. 请确保iOS设备已开启WiFi和位置服务"
echo "2. 如果仍无法看到热点，请尝试重启iOS设备WiFi"
echo "3. 连接后访问: http://10.42.0.1:5002"
