#!/bin/bash
echo "start monitor experiment"
sudo sysctl -w net.ipv4.tcp_congestion_control=reno
python minitopo.py --exp exp1 \
        --btnSpeed 5 \
		--hs_bw 10 \
		--maxq 100 \
		--intf1 eth1 \
		--intf2 eth2 \

echo "cleaning up..."
killall -9 iperf ping
mn -c > /dev/null 2>&1
echo "end"
