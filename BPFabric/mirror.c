#include <linux/if_ether.h>
#include "ebpf_switch.h"

uint64_t prog(struct packet *pkt)
{
    if (pkt->metadata.in_port == 2) //def: 1
    {
        //Now anything from RTU mirrored to IDS (port numbers do not correspond to Mininet topo!) 
        bpf_mirror(1, pkt, 1000); // def: 2, 100         
    }
  
    return NEXT;
}
char _license[] SEC("license") = "GPL";
