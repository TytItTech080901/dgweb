#!/bin/bash
# 检测音频设备和支持的采样率

echo "=== 检测音频设备信息 ==="

# 1. 使用 arecord 列出录音设备
echo "1. 录音设备列表:"
arecord -l 2>/dev/null || echo "arecord 不可用"

echo -e "\n2. 播放设备列表:"
aplay -l 2>/dev/null || echo "aplay 不可用"

# 3. 检测默认设备支持的采样率
echo -e "\n3. 测试常用采样率支持情况:"

common_rates=(8000 16000 22050 44100 48000)

for rate in "${common_rates[@]}"; do
    echo -n "测试采样率 ${rate}Hz: "
    
    # 测试录音
    timeout 1 arecord -f S16_LE -c 1 -r $rate -d 0.1 /dev/null 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -n "录音✅ "
    else
        echo -n "录音❌ "
    fi
    
    # 测试播放（生成1秒静音并播放）
    timeout 1 aplay -f S16_LE -c 1 -r $rate /dev/zero 2>/dev/null &
    play_pid=$!
    sleep 0.1
    kill $play_pid 2>/dev/null
    wait $play_pid 2>/dev/null
    if [ $? -eq 0 ] || [ $? -eq 143 ]; then  # 143 是 SIGTERM 的退出码
        echo "播放✅"
    else
        echo "播放❌"
    fi
done

# 4. 使用 pactl 检测 PulseAudio 信息（如果可用）
echo -e "\n4. PulseAudio 设备信息:"
if command -v pactl &> /dev/null; then
    echo "录音设备:"
    pactl list sources short 2>/dev/null || echo "无法获取录音设备"
    
    echo -e "\n播放设备:"
    pactl list sinks short 2>/dev/null || echo "无法获取播放设备"
    
    # 获取默认设备信息
    echo -e "\n默认录音设备详细信息:"
    pactl info 2>/dev/null | grep "Default Source" || echo "无法获取默认录音设备"
    
    echo -e "\n默认播放设备详细信息:"  
    pactl info 2>/dev/null | grep "Default Sink" || echo "无法获取默认播放设备"
else
    echo "PulseAudio 不可用"
fi

# 5. 检查 ALSA 配置
echo -e "\n5. ALSA 设备信息:"
if [ -f /proc/asound/cards ]; then
    echo "声卡信息:"
    cat /proc/asound/cards
else
    echo "无 ALSA 设备信息"
fi

# 6. 使用 Python pyaudio 检测（如果安装了）
echo -e "\n6. Python PyAudio 检测:"
python3 -c "
import sys
try:
    import pyaudio
    p = pyaudio.PyAudio()
    
    print(f'设备总数: {p.get_device_count()}')
    
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f'录音设备 {i}: {info[\"name\"]} - 默认采样率: {info[\"defaultSampleRate\"]}Hz')
        if info['maxOutputChannels'] > 0:
            print(f'播放设备 {i}: {info[\"name\"]} - 默认采样率: {info[\"defaultSampleRate\"]}Hz')
    
    p.terminate()
    
except ImportError:
    print('PyAudio 未安装')
except Exception as e:
    print(f'PyAudio 检测出错: {e}')
" 2>/dev/null

echo -e "\n=== 检测完成 ==="
