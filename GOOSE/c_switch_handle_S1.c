#include <pcap.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#include "../encryption_timings/encryption_config.h"
#include "latency.h"

#define CAPTURE_IFACE "veth2"
#define SEND_IFACE "veth3"
#define ETHERNET_HEADER_LEN 14

const char *ENCRYPTION_LATENCY_LOG = "../data/mn_data/encryption_latency_log.csv";
FILE *encryption_latency_file;
encryption_mode_t enc_mode;

int packet_count = 0;
pcap_t *send_handle = NULL;
encryption_config_t *chosen_config;

//function which receives packets, encrypts and then sends over network
void packet_handler_encrypt(u_char *user, const struct pcap_pkthdr *header, const u_char *packet) {
    uint16_t ethertype = ntohs(*(uint16_t *)(packet + 12));
    if (ethertype != 0x88b8) { //ensure packet is of type GOOSE
        fprintf(stderr, "Non-GOOSE packet\n");
        return;
    }
    packet_count++;
    long start_time, elapsed;
    start_time = get_time_ns();

    if (chosen_config->mode == MODE_NONE) {
        int new_len = header->len + sizeof(struct timestamp_header);
        u_char *new_packet = malloc(new_len);
        if (!new_packet) {
            fprintf(stderr, "mem allocation error\n");
            return;
        }

        memcpy(new_packet, packet, ETHERNET_HEADER_LEN); //allocate memory and insert timestamp
        struct timestamp_header ts_hdr;
        clock_gettime(CLOCK_MONOTONIC, &ts_hdr.ts);

        memcpy(new_packet + ETHERNET_HEADER_LEN, &ts_hdr, sizeof(ts_hdr)); //copy packet over into new packet
        memcpy(new_packet + ETHERNET_HEADER_LEN + sizeof(ts_hdr), packet + ETHERNET_HEADER_LEN,header->len - ETHERNET_HEADER_LEN);

        elapsed = get_time_ns() - start_time;
        if (pcap_sendpacket(send_handle, new_packet, new_len) != 0) {
            fprintf(stderr, "error sending packet\n");
        }
        free(new_packet);
    } else {
        int new_len = 0;  //encrypt packet - [ eth hdr | timestamp/nonce | encrypted payload ]
        u_char *new_packet = build_encrypted_packet(packet, header->len, ETHERNET_HEADER_LEN,
                                                        &new_len, chosen_config);
        if(!new_packet) {
            fprintf(stderr, "failed to encrypt packet");
            return;
        }
        elapsed = get_time_ns() - start_time;
        if (pcap_sendpacket(send_handle, new_packet, new_len) != 0) { // send packet
            fprintf(stderr, "error sending packet");
        }
        free(new_packet);
    }

    /*if (packet_count > 10 && encryption_latency_file != NULL) {
        const char *if_none = (chosen_config->mode == MODE_NONE) ? //print 'alg, mode, latnecy' to file
                                mode_to_string(chosen_config->mode) :
                                chosen_config->name;
        fprintf(encryption_latency_file, "%s, %s, %ld\n", if_none, mode_to_string(chosen_config->mode), elapsed);
        fflush(encryption_latency_file);
    }*/
}

int main(int argc, char *argv[]){


    //get chosen config and setup latency file
    chosen_config = get_chosen_config(argc, argv);
    /*encryption_latency_file = fopen(ENCRYPTION_LATENCY_LOG, "a");
    if(!encryption_latency_file) {
        perror("failed to open latency file");
        exit(EXIT_FAILURE);
    }*/

    //configure capture handle
    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t *capture_handle = pcap_create(CAPTURE_IFACE, errbuf);
    if (capture_handle == NULL) {
        fprintf(stderr, "pcap_create failed: %s\n", errbuf);
        exit(EXIT_FAILURE);
    }

    if (pcap_set_buffer_size(capture_handle, 2*1024*1024) != 0) { //set buffer size to 2MB
        fprintf(stderr, "Error setting buffer size: %s\n", pcap_geterr(capture_handle));
    }

    if (pcap_set_immediate_mode(capture_handle, 1) != 0) { //set to immediate mode
        fprintf(stderr, "Error setting immediate mode: %s\n", pcap_geterr(capture_handle));
    }

    if (pcap_set_timeout(capture_handle, 10) != 0) {
        fprintf(stderr, "Error setting capture timeout: %s\n", pcap_geterr(capture_handle));
    }

    if (pcap_activate(capture_handle) < 0) { //activate hanlde
        fprintf(stderr, "Error activating capture handle: %s\n", pcap_geterr(capture_handle));
        pcap_close(capture_handle);
        exit(EXIT_FAILURE);
    }

    if (pcap_setdirection(capture_handle, PCAP_D_IN) != 0) { //set direction one way for this demo
        fprintf(stderr, "Error setting direction: %s\n", pcap_geterr(capture_handle));
        pcap_close(capture_handle);
        return EXIT_FAILURE;
    }

    //configure send handle similar to capture handle
    send_handle = pcap_create(SEND_IFACE, errbuf);
    if (send_handle == NULL) {
        fprintf(stderr, "pcap_create for send_handle failed: %s\n", errbuf);
        exit(EXIT_FAILURE);
    }
    if (pcap_set_buffer_size(send_handle, 2*1024*1024) != 0) {
        fprintf(stderr, "Error setting send_handle buffer size: %s\n", pcap_geterr(send_handle));
    }
    if (pcap_set_immediate_mode(send_handle, 1) != 0) {
        fprintf(stderr, "Error setting send_handle immediate mode: %s\n", pcap_geterr(send_handle));
    }
    if (pcap_set_timeout(send_handle, 10) != 0) {
        fprintf(stderr, "Error setting send_handle timeout: %s\n", pcap_geterr(send_handle));
    }
    if (pcap_activate(send_handle) < 0) {
        fprintf(stderr, "Error activating send_handle: %s\n", pcap_geterr(send_handle));
        pcap_close(send_handle);
        exit(EXIT_FAILURE);
    }

    // start packet capture
    if (pcap_loop(capture_handle, 0, packet_handler_encrypt, NULL) < 0){
        fprintf(stderr, "Error in capture loop: %s\n", pcap_geterr(capture_handle));
    }

    pcap_close(capture_handle);
    pcap_close(send_handle);
    //fclose(encryption_latency_file);
    //printf("Successfully closed CSV file.\n");

    return EXIT_SUCCESS;
}
