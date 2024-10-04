#!/usr/bin/env python
import cmd
import os
import struct
import time 

from threading import Thread
from twisted.internet import reactor

from core import eBPFCoreApplication, set_event_handler, FLOOD
from core.packets import *

# The intro message to show at the top when running the program
banner = "-" * 80 + """
    eBPF Switch Controller Command Line Interface - Netlab 2024
    Simon Jouet <simon.jouet@gmail.com> - University of Glasgow
    SGSim Orchestration Addon
""" + '-' * 80 + '\n'

def tabulate(rows, headers=None):
    if not rows or len(rows) == 0:
        print('<Empty Table>')
        return

    # Find the largest possible value for each column
    columns_width = [ max([ len(str(row[i])) for row in rows ]) for i in range(len(rows[0])) ]

    # If there are headers check if headers is larger than content
    if headers:
        columns_width = [ max(columns_width[i], len(header)) for i, header in enumerate(headers) ]

    # Add two extra spaces to columns_width for prettiness
    columns_width = [ w+2 for w in columns_width ]

    # Generate the row format string and delimiter string
    row_format = '  '.join(['{{:>{}}}'.format(w) for w in columns_width ])
    row_delim  = [ '='*w for w in columns_width ]

    # Print the headers if necessary
    print('')
    if headers:
        print(row_format.format(*headers))

    # Print the rows
    print(row_format.format(*row_delim))
    for row in rows:
        print(row_format.format(*row))
    print(row_format.format(*row_delim))

class SwitchTableCli(cmd.Cmd):
    def __init__(self, connection, function_id, table_name):
        cmd.Cmd.__init__(self)
        self.connection = connection
        self.function_id = function_id
        self.table_name = table_name

    def do_list(self, line):
        self.connection.send(TableListRequest(index=self.function_id, table_name=self.table_name))

    def do_get(self, line):
        self.connection.send(TableEntryGetRequest(index=self.function_id, table_name=self.table_name, key=bytes.fromhex(line)))

    def do_update(self, line):
        args = line.split()
        if len(args) != 2:
            print("update <hex:key> <hex:value>")
            return

        self.connection.send(TableEntryInsertRequest(index=self.function_id, table_name=self.table_name, key=bytes.fromhex(args[0]), value=bytes.fromhex(args[1])))

    def do_delete(self, line):
        self.connection.send(TableEntryDeleteRequest(index=self.function_id, table_name=self.table_name, key=bytes.fromhex(line)))

    def emptyline(self):
         self.do_help(None)

class SwitchTablesCli(cmd.Cmd):
    def __init__(self, connection, function_id: int):
        cmd.Cmd.__init__(self)
        self.connection = connection
        self.function_id = function_id

    def do_list(self, line):
        self.connection.send(TablesListRequest(index=self.function_id))

    def default(self, line: str) -> None:
        args = line.split(maxsplit=1)

        if len(args) == 0:
            cmd.Cmd.default(self, line)
        else:
            try:
                SwitchTableCli(self.connection, self.function_id, args[0]).onecmd(args[1] if len(args) > 1 else '')
            except ValueError:
                cmd.Cmd.default(self, line)

    def emptyline(self):
         self.do_help(None)

class SwitchCLI(cmd.Cmd):
    def __init__(self, connection):
        cmd.Cmd.__init__(self)
        self.connection = connection

    def do_list(self, line: str):
        self.connection.send(FunctionListRequest())

    def do_add(self, line: str) -> None:
        args = line.split()

        # 1 add 0 test ../examples/learningswitch.o
        if len(args) != 3:
            print("invalid")
            return
        
        index, name, path = args

        if not os.path.isfile(path):
            print('Invalid file path')
            return

        with open(path, 'rb') as f:
            elf = f.read()
            self.connection.send(FunctionAddRequest(name=name, index=int(index), elf=elf))

    def do_remove(self, line: str) -> None:
        self.connection.send(FunctionRemoveRequest(index=int(line)))

    def do_table(self, line: str) -> None:
        args = line.split(maxsplit=1)

        if len(args) == 0:
            cmd.Cmd.default(self, line)
        else:
            try:
                function_id = int(args[0], 16)

                SwitchTablesCli(self.connection, function_id).onecmd(args[1] if len(args) > 1 else '')
            except ValueError:
                cmd.Cmd.default(self, line)


    def emptyline(self):
         self.do_help(None)

class MainCLI(cmd.Cmd):
    def __init__(self, application):
        cmd.Cmd.__init__(self)
        self.application = application

    def preloop(self):
        print(banner)
        self.do_help(None)

    def default(self, line):
        args = line.split()

        if len(args) == 0:
            cmd.Cmd.default(self, line)
        else:
            try:
                dpid = int(args[0], 16)

                if dpid in self.application.connections:
                    SwitchCLI(self.application.connections[dpid]).onecmd(' '.join(args[1:]))
                else:
                    print(f'Switch with dpid {dpid} is not connected.')
            except ValueError:
                cmd.Cmd.default(self, line)

    def do_connections(self, line):
        tabulate([ ('{:08X}'.format(k), c.version, c.connected_at) for k,c in self.application.connections.items() ], headers=['dpid', 'version', 'connected at'])

    def do_sgsim(self, line): 
        print(f'Installing SGSim orchestration functions...')
        if(len(self.application.connections) == 9): 
            print(f'All networking device connected. ')
            with open('../examples/learningswitch.o', 'rb') as f:
                print("Installing forwarding services...")
                elf = f.read() # Otherwise if read 9x - not enough data for ELF header error
                self.application.connections[1].send(FunctionAddRequest(name="learningswitch", index=1, elf=elf)) # DSS1                
                self.application.connections[2].send(FunctionAddRequest(name="learningswitch", index=1, elf=elf)) # DSS2
                self.application.connections[3].send(FunctionAddRequest(name="learningswitch", index=0, elf=elf)) # C
                self.application.connections[4].send(FunctionAddRequest(name="learningswitch", index=0, elf=elf)) # C
                self.application.connections[5].send(FunctionAddRequest(name="learningswitch", index=0, elf=elf)) # C
                self.application.connections[6].send(FunctionAddRequest(name="learningswitch", index=1, elf=elf)) # DPSGW
                self.application.connections[7].send(FunctionAddRequest(name="learningswitch", index=2, elf=elf)) # DPSRS
                self.application.connections[8].send(FunctionAddRequest(name="learningswitch", index=1, elf=elf)) # DPSHV
                self.application.connections[9].send(FunctionAddRequest(name="learningswitch", index=1, elf=elf)) # DPSMV
                time.sleep(1)    
                print("All forwarding services installed...")            

            with open('../examples/mirror.o', 'rb') as f:
                print("Installing mirroring service...")
                elf = f.read() 
                self.application.connections[1].send(FunctionAddRequest(name="mirror", index=0, elf=elf)) # DSS1                
                time.sleep(1)
                print("Mirroring service installed...")

            with open('../examples/block.o', 'rb') as f:
                print("Installing ACL service...")
                elf = f.read() 
                self.application.connections[6].send(FunctionAddRequest(name="acl", index=0, elf=elf))                 
                time.sleep(1)
                print("ACL service installed...")                

            with open('../examples/assetdisc.o', 'rb') as f:
                print("Installing Asset Discovery service...")
                elf = f.read() 
                self.application.connections[7].send(FunctionAddRequest(name="assetdisc", index=0, elf=elf))   
                self.application.connections[8].send(FunctionAddRequest(name="assetdisc", index=0, elf=elf))
                self.application.connections[9].send(FunctionAddRequest(name="assetdisc", index=0, elf=elf))
                self.application.connections[2].send(FunctionAddRequest(name="assetdisc", index=0, elf=elf))             
                time.sleep(1)
                print("ACL service installed...")              

            time.sleep(1)
            print("All functions installed...")
        else: 
            print(f'Could not verify connected devices. ')

    def emptyline(self):
         pass

    # def do_EOF(self, line):
    #     return True

class tablesCache():
    tablesDict = {} # DPID, Table 

class eBPFCLIApplication(eBPFCoreApplication):
    """
        Controller application that will start a interactive CLI.
    """
    assetDiscoveryCache = tablesCache() 

    def run(self):
        
        Thread(target=reactor.run, kwargs={'installSignalHandlers': 0}).start()

        try:
            MainCLI(self).cmdloop()
        except KeyboardInterrupt:
            print("\nGot keyboard interrupt. Exiting...")
        finally:
            reactor.callFromThread(reactor.stop)

    @set_event_handler(Header.TABLES_LIST_REPLY)
    def tables_list_reply(self, connection, pkt):
        tabulate([ (e.table_name, TableDefinition.TableType.Name(e.table_type), e.key_size, e.value_size, e.max_entries) for e in pkt.entries ], headers=['name', 'type', 'key size', 'value size', 'max entries'])

    @set_event_handler(Header.TABLE_LIST_REPLY)
    def table_list_reply(self, connection, pkt):
        if pkt.entry.table_name == "assetdisc":
            self.asset_disc_list(connection.dpid, pkt) # Collecting data for Asset Discovery service 
            return 
    
        entries = []

        if pkt.entry.table_type in [TableDefinition.HASH, TableDefinition.LPM_TRIE]:
            item_size = pkt.entry.key_size + pkt.entry.value_size
            fmt = "{}s{}s".format(pkt.entry.key_size, pkt.entry.value_size)

            for i in range(pkt.n_items):
                key, value = struct.unpack_from(fmt, pkt.items, i * item_size)
                entries.append((key.hex(), value.hex()))

        elif pkt.entry.table_type == TableDefinition.ARRAY:
            item_size = pkt.entry.value_size
            fmt = "{}s".format(pkt.entry.value_size)

            for i in range(pkt.n_items):
                value = struct.unpack_from(fmt, pkt.items, i * item_size)[0]
                entries.append((i, value.hex()))

        tabulate(entries, headers=["Key", "Value"])

    @set_event_handler(Header.TABLE_ENTRY_GET_REPLY)
    def table_entry_get_reply(self, connection, pkt):
        tabulate([(pkt.key.hex(), pkt.value.hex())], headers=["Key", "Value"])

    def asset_disc_list(self, dpid, pkt):
        os.system('clear')
        entries = []
        
        item_size = pkt.entry.key_size + pkt.entry.value_size
        fmt = "{}s{}s".format(pkt.entry.key_size, pkt.entry.value_size)

        for i in range(pkt.n_items):
            key, value = struct.unpack_from(fmt, pkt.items, i * item_size)
            entries.append((key.hex(), value.hex()))        

        self.assetDiscoveryCache.tablesDict[""] = entries 
        print("Table logged")
        #tabulate(entries, headers=["Key", "Value"])
    
    @set_event_handler(Header.NOTIFY)
    def notify_event(self, connection, pkt):        
        #print(f'\n[{connection.dpid}] Received notify event {pkt.id}, data length {pkt.data}')
        #print(pkt.data.hex())
        vendor = ''
        if pkt.data.hex() == '30b216000004':
            vendor = 'Hitachi'
        if pkt.data.hex() == 'b4b15a000001':
            vendor = 'Siemens'  
        #print(f'\n[{eBPFCLIApplication.get_switch_name(connection.dpid)}] IED device detected with MAC: {pkt.data.hex()} ({vendor})')
        connection.send(TableListRequest(index=0, table_name="assetdisc"))


    @set_event_handler(Header.PACKET_IN)
    def packet_in(self, connection, pkt):
        print(f"\n[{connection.dpid}] Received packet in {pkt.data.hex()}")

    @set_event_handler(Header.FUNCTION_LIST_REPLY)
    def function_list_reply(self, connection, pkt):
        tabulate([ (e.index or 0, e.name, e.counter or 0) for e in pkt.entries ], headers=['index', 'name', 'counter'])

    @set_event_handler(Header.FUNCTION_ADD_REPLY)
    def function_add_reply(self, connection, pkt):
        if pkt.status == FunctionAddReply.FunctionAddStatus.INVALID_STAGE:
            print("Cannot add a function at this index")
        elif pkt.status == FunctionAddReply.FunctionAddStatus.INVALID_FUNCTION:
            print("Unable to install this function")
        else:
            print("Function has been installed")

    @set_event_handler(Header.FUNCTION_REMOVE_REPLY)
    def function_remove_reply(self, connection, pkt):
        if pkt.status == FunctionAddReply.FunctionAddStatus.INVALID_STAGE:
            print("Cannot remove a function at this index")
        else:
            print("Function has been removed")

    def get_switch_name(dpid): 
        switch_name = ""; 
        match dpid: 
            case 1: 
                switch_name = "DSS1 GW"
            case 2: 
                switch_name = "DSS2 GW"
            case 3: 
                switch_name = "WAN R1"
            case 4: 
                switch_name = "WAN R2"
            case 5: 
                switch_name = "CONTROL SW"
            case 6: 
                switch_name = "DPS GW"
            case 7: 
                switch_name = "DPS RS"
            case 8: 
                switch_name = "DPS HV"
            case 9: 
                switch_name = "DPS MV"
            case _:
                switch_name = "unknown"   
        return switch_name

if __name__ == '__main__':
    eBPFCLIApplication().run()
