# SGFabric
Modified files from SGSim and BPFabric to build an emulated Smart Grid network controlled by eBPF functions.    
Contains glue files which have to be added to SGSim and BPFabric (or have to replace original files).    

# Requirements
Requires current version of BPFabric and SGSim.  
Dashboard requires Gradient Able Flask. 

# Installation
BPFabric:  
git clone https://github.com/UofG-netlab/BPFabric  
apt-get install gcc-multilib protobuf-compiler protobuf-c-compiler libprotobuf-c-dev libprotobuf-dev clang-14 git python3-protobuf python3-twisted clang  
cd BPFabric  
make   

SGSim:  
apt-get install mininet  
git clone https://github.com/filipholik/SmartGridSim   
unzip SmartGridSim/comlib_dps.zip -d SmartGridSim  
unzip SmartGridSim/comlib_dss.zip -d SmartGridSim  

Dashboard:  
git clone https://github.com/app-generator/flask-gradient-able.git  
sudo apt install python3-virtualenv  
virtualenv env  
source env/bin/activate  
pip3 install -r requirements.txt  
export FLASK_APP=run.py  
export FLASK_ENV=development  
flask run  
(pip install requests)  

SGFabric:  
git clone https://github.com/filipholik/SGFabric  
Add / replace corresponding files in BPFabric, SmartGridSim and Dashboard.     
sudo apt install python3-flask  

# Topology 
![SGFabric topology](https://github.com/filipholik/SGFabric/blob/main/SGFabric.png)

# Usage


Printing maps tables:  
8 table 0 list   
8 table 0 assetdisc list  

Read Scripts/guide.txt for further instructions. 
