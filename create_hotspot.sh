#!/bin/bash
# 脚本用于启动WiFi热点 - 使用create_ap方法
# 路径：/home/cat/Py-server/create_hotspot.sh

# 确保WiFi未被屏蔽
echo "解除WiFi屏蔽..."
rfkill unblock wifi
rfkill unblock all

# 停止可能会干扰的服务
echo "停止可能干扰的服务..."
systemctl stop hostapd 2>/dev/null
systemctl stop dnsmasq 2>/dev/null

# 检查create_ap是否已安装
if ! command -v create_ap &> /dev/null; then
    echo "create_ap 未安装，尝试使用基本方法创建热点..."
    
    # 基本方法：使用hostapd和dnsmasq
    # 配置wlan0接口
    ip link set wlan0 down
    ip addr flush dev wlan0
    ip link set wlan0 up
    ip addr add 10.42.0.1/24 dev wlan0
    
    # 使用hostapd启动热点
    echo "interface=wlan0
driver=nl80211
ssid=Lampbot
hw_mode=g
channel=1
country_code=CN
auth_algs=1
wpa=2
wpa_passphrase=lampbot2025
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP CCMP
rsn_pairwise=CCMP" > /tmp/hostapd_simple.conf
    
    hostapd -B /tmp/hostapd_simple.conf
    
    # 设置热点信息
    HOTSPOT_IP="10.42.0.1"
else
    # 使用create_ap创建热点 (对iOS更友好)
    echo "使用create_ap创建iOS兼容热点..."
    
    # 确定外部接口
    EXT_IF=$(ip route | grep default | awk '{print $5}')
    if [ -z "$EXT_IF" ]; then
        echo "警告: 无法确定外部接口，使用无网络共享模式"
        create_ap --no-virt -n wlan0 Lampbot lampbot2025 &
    else
        echo "使用 $EXT_IF 作为外部接口"
        create_ap -n $EXT_IF wlan0 Lampbot lampbot2025 &
    fi
    
    # 等待热点启动
    sleep 5
    
    # 获取热点IP地址
    HOTSPOT_IP=$(ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
fi

# 显示热点信息
echo "======== WiFi热点状态摘要 ========"
echo "SSID: Lampbot"
echo "密码: lampbot2025"
echo "IP地址: $HOTSPOT_IP"
echo "Flask服务地址: http://$HOTSPOT_IP:5002"
echo "===================================="
echo "热点已创建，请使用iOS设备尝试连接"
echo "确保设备的位置服务已开启，这对于iOS设备扫描WiFi很重要"

# 确保Flask服务器端口可访问
iptables -A INPUT -i wlan0 -p tcp --dport 5002 -j ACCEPT

# 启动DHCP服务器
cat > /tmp/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=10.42.0.2,10.42.0.20,255.255.255.0,24h
dhcp-option=3,10.42.0.1
dhcp-option=6,8.8.8.8,8.8.4.4
server=8.8.8.8
server=8.8.4.4
log-queries
log-dhcp
EOF

# 检查是否有其他进程在使用端口53
if lsof -i :53 > /dev/null; then
    echo "警告: 端口53已被占用，可能影响DHCP服务"
    lsof -i :53
fi

# 尝试启动dnsmasq，忽略可能的错误
dnsmasq -C /tmp/dnsmasq.conf || echo "DHCP服务器启动可能有问题，但继续尝试创建热点"

# 杀掉任何已经运行的hostapd实例
killall hostapd 2>/dev/null
sleep 2

# 检查是否有驱动问题
DRIVER_NAME=$(lspci -k | grep -A 3 -i network | grep "Kernel driver" | awk '{print $3}')
if [ -n "$DRIVER_NAME" ]; then
    echo "WiFi驱动: $DRIVER_NAME"
    if lsmod | grep "$DRIVER_NAME" > /dev/null; then
        echo "WiFi驱动已加载"
    else
        echo "警告: WiFi驱动未加载，尝试加载"
        modprobe $DRIVER_NAME || echo "无法加载WiFi驱动"
    fi
fi

# 使用hostapd启动热点 - 增加调试选项
echo "正在启动iOS兼容热点..."
hostapd -dd /home/cat/Py-server/hostapd.conf > /tmp/hostapd.log 2>&1 &
HOSTAPD_PID=$!

# 等待热点启动
sleep 5

# 检查hostapd是否运行
if ps -p $HOSTAPD_PID > /dev/null; then
    echo "热点启动成功 (PID: $HOSTAPD_PID)"
else
    echo "热点启动失败，尝试不使用调试模式再次启动"
    hostapd /home/cat/Py-server/hostapd.conf > /tmp/hostapd.log 2>&1 &
    HOSTAPD_PID=$!
    sleep 3
    
    if ps -p $HOSTAPD_PID > /dev/null; then
        echo "热点启动成功 (PID: $HOSTAPD_PID)"
    else
        echo "热点启动失败，请检查日志: /tmp/hostapd.log"
        cat /tmp/hostapd.log
        exit 1
    fi
fi

# 显示热点信息
echo "WiFi热点已创建："
echo "SSID: Lampbot"
echo "密码: lampbot2025"
echo "IP地址: 10.42.0.1"
echo "日志文件: /tmp/hostapd.log"

# 启用NAT
echo "设置网络转发..."
iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE
iptables -A FORWARD -i eth1 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i wlan0 -o eth1 -j ACCEPT

# 确保所有移动设备都可以正常访问
iptables -A INPUT -i wlan0 -p tcp --dport 5002 -j ACCEPT
iptables -A INPUT -i wlan0 -p udp --dport 5002 -j ACCEPT

# 启用IP转发
echo 1 > /proc/sys/net/ipv4/ip_forward

# 为了解决iOS设备连接问题，我们设置arp代理和IPv6选项
echo 1 > /proc/sys/net/ipv4/conf/all/proxy_arp
echo 2 > /proc/sys/net/ipv6/conf/all/accept_ra

# 禁用网络电源管理，防止WiFi休眠
iwconfig wlan0 power off 2>/dev/null || echo "无法禁用WiFi电源管理"

# 提供最终状态摘要
echo "======== WiFi热点状态摘要 ========"
echo "SSID: Lampbot"
echo "密码: lampbot2025"
echo "IP地址: 10.42.0.1"
echo "频道: $(grep channel /home/cat/Py-server/hostapd.conf | cut -d= -f2)"
echo "Flask服务地址: http://10.42.0.1:5002"
echo "===================================="
echo "使用iOS设备时，请确保WiFi设置中已启用位置服务"
echo "检查热点运行状态: ps aux | grep hostapd"
echo "若连接有问题请查看日志: cat /tmp/hostapd.log"
