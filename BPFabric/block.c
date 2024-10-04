#include <linux/if_ether.h>
#include "ebpf_switch.h"

uint64_t prog(struct packet *pkt, unsigned len)
{
    // If the packet is from the IDS (port 0) drop it
    if (pkt->metadata.in_port == 1) // Stop GOOSE and SV traffic leaving the substation
    {
        return DROP;
    }    

    return NEXT;
}
char _license[] SEC("license") = "GPL";
