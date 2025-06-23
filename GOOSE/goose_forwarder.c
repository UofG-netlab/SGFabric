#include <linux/if_ether.h>
#include "ebpf_switch.h"

/*
Function which sends GOOSE messages from physical ports to the encryption / decryption stack via a virtual port. 
Combines simple forwarding. 
*/

#include <linux/if_ether.h>
#include "ebpf_switch.h"

struct bpf_map_def SEC("maps") inports = {
    .type = BPF_MAP_TYPE_HASH,
    .key_size = 6, // MAC address is the key
    .value_size = sizeof(uint32_t),
    .max_entries = 256,
};

uint64_t prog(struct packet *pkt)
{
    uint32_t *out_port;

    //No traffic from virtual port 1 
    if (pkt->metadata.in_port == 0 )
    {
        return DROP;
    }

    //Encrypted GOOSE
    if (pkt->metadata.in_port == 1  )
    {
        return PORT + 3;
    }

    //Traffic from physical ports and only GOOSE traffic 
    if (pkt->metadata.in_port == 2 && pkt->eth.h_proto == 47240) 
    {       
        return PORT;  // Forwards traffic to virtual port 0 to GEDSF
        //PORT + 1  
        //bpf_mirror(0, pkt, pkt->metadata.length); // Virtual port      
        //return DROP; 
    }

    // if the source is not a broadcast or multicast
    if ((pkt->eth.h_source[0] & 1) == 0)
    {
        // Update the port associated with the packet
        bpf_map_update_elem(&inports, pkt->eth.h_source, &pkt->metadata.in_port, 0);
    }

    // Flood if the destination is broadcast or multicast
    if (pkt->eth.h_dest[0] & 1)
    {
        return FLOOD;
    }

    // Lookup the output port
    if (bpf_map_lookup_elem(&inports, pkt->eth.h_dest, &out_port) == -1)
    {
        // If no entry was found flood
        return FLOOD;
    }

    return *out_port;
}
char _license[] SEC("license") = "GPL";
