# In-Network GOOSE Encryption with eBPF-based Programmable Network Architecture

This project contains in-network GOOSE encryption with eBPF-based programmable network architecture as described in the paper:  

F. Holik, K. Mcilwraith, A. A. Shah and D. P. Pezaros, "In-Network GOOSE Encryption with eBPF-based Programmable Network Architecture," 2025 IEEE International Conference on Communications, Control, and Computing Technologies for Smart Grids (SmartGridComm), North York, ON, Canada, 2025, pp. 1-6, doi: 10.1109/SmartGridComm65349.2025.11204611. 

# Installation
BPFabric installation according to the instructions  
Setup of the GOOSE encryption project:  
git clone https://github.com/kylemc1935/GOOSE-encryption  
Follow the install instructions 
Dependencies: sudo apt install cmake libsodium-dev libsodium23 libpcap-dev  

Replace the c_switch_handle_S* files in the /src/mininet_setup folder   
Adjust the paths in the files (lines 9-10)   
build the project: ./build.sh  
Executable files are now in the /build folder   

# Configuration
Start softswitch:  
sudo ip link add veth1 type veth peer name veth2  
sudo ip link add veth3 type veth peer name veth4  
sudo ip link set dev veth1 up  
sudo ip link set dev veth2 up  
sudo ip link set dev veth3 up  
sudo ip link set dev veth4 up  
sudo ~/BPFabric/softswitch/softswitch --dpid=1 --controller="127.0.0.1:9000" --promiscuous veth1 veth3 enp1s0 enp2s0 enp3s0  

Start controller:  
cd ~/BPFabric/controller/  
./cli.py  

Install the eBPF function from the controller:  
1 add 0 goose_forwarder ../functions/goose_forwarder.o  

Start GEDSF on both switches (build folder):  
./switch1  
./switch2  
