//Written by Xicheng Li
#define V1MODEL_VERSION 20200408

// ======== IMPORT ========
#include <core.p4>
#include <v1model.p4>

// ======== CONSTANTS ========

const bit<16> TYPE_IPV4    = 0x0800;
const bit<16> TYPE_GOOSE   = 0x88B8;
const bit<16> TYPE_CONTROL = 0x88B9;

// ======== HEADERS ========

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16> etherType;
}

// per-packet metadata
struct metadata_t {    
    // debug trace
    bit<8> debug; // 0-255 unsigned
}

struct headers {
    ethernet_t   ethernet;
}

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata_t meta,
                inout standard_metadata_t standard_metadata
) {

    state start {
        meta.debug = 1;
        transition parse_ethernet;
    }

    state parse_ethernet {
        meta.debug = 2;

        packet.extract(hdr.ethernet);
        transition accept;
    } 
}

control MyVerifyChecksum(inout headers hdr,
                         inout metadata_t meta) {
    apply { }
}

control MyIngress(inout headers hdr,
                  inout metadata_t meta,
                  inout standard_metadata_t standard_metadata) {

    // default drop
    action drop() {
        mark_to_drop(standard_metadata);
    }

    // default forward
    action set_egress_port(egressSpec_t egressPort) {
        standard_metadata.egress_spec = egressPort;
    }

    table l2_forward {
        key = {
		    hdr.ethernet.dstAddr: exact;
		}

		actions = {
			set_egress_port;
			drop;
		}
        default_action = drop();
    }

    apply {
        if (hdr.ethernet.etherType == TYPE_GOOSE) {
            if (standard_metadata.ingress_port == 0)
                set_egress_port(1);
            else {
                if (standard_metadata.ingress_port == 2)
                    set_egress_port(0);
            }
        }
    }
}

control MyEgress(inout headers hdr,
                 inout metadata_t meta,
                 inout standard_metadata_t standard_metadata) {
    // egress match-action pipeline
    action drop() {
        mark_to_drop(standard_metadata);
    }

    apply {

    }
}

control MyComputeChecksum(inout headers hdr, inout metadata_t meta) {
    apply { }
}

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
    }
}

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
