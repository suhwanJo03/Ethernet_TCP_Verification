/*
 * echo.c - DMA buffer to TCP client transfer server
 * (Based on lwIP RAW API)
 */

#include <stdio.h>
#include <string.h>

#include "lwip/err.h"
#include "lwip/tcp.h"
#include "netif/xadapter.h"
#if defined (__arm__) || defined (__aarch64__)
#include "xil_printf.h"
#include "sleep.h"
#endif

struct netif echo_netif;

// TCP client PCB pointer
struct tcp_pcb *client_pcb = NULL;

#define FRAME_BYTES 921600  // Total frame size in bytes

/* Function to transfer DMA buffer to TCP */
int transfer_data(u8 *buffer) {
    // Check if client is connected
    if (client_pcb == NULL) {
        xil_printf("No client connected. Skipping transfer.\n\r");
        return -1;
    }

    err_t err;
    int remaining = FRAME_BYTES;
    int offset = 0;
    const int MAX_TCP_CHUNK = 1460;  // Maximum TCP payload size (close to MTU)

    xil_printf("Starting TCP transfer (%d bytes)...\n\r", FRAME_BYTES);

    while (remaining > 0) {
        // Decide the size of current chunk
        int chunk = (remaining > MAX_TCP_CHUNK) ? MAX_TCP_CHUNK : remaining;

        // Wait until TCP send buffer has enough space for the chunk
        while (tcp_sndbuf(client_pcb) < chunk) {
            xemacif_input(&echo_netif);  // Process incoming ACK packets
            usleep(100);                  // Small delay to avoid busy-wait
        }

        // Write chunk into TCP send buffer
        err = tcp_write(client_pcb, &buffer[offset], chunk, TCP_WRITE_FLAG_COPY);
        if (err != ERR_OK) {
            xil_printf("TCP write failed at offset %d: %d\n\r", offset, err);
            return -2;
        }

        // Flush TCP send buffer immediately
        err = tcp_output(client_pcb);
        if (err != ERR_OK) {
            xil_printf("TCP output failed: %d\n\r", err);
            return -3;
        }

        // Update counters
        offset += chunk;
        remaining -= chunk;
    }

    xil_printf("TCP transfer complete (%d bytes).\n\r", FRAME_BYTES);
    return 0;
}


/* Application startup message */
void print_app_header() {
#if (LWIP_IPV6==0)
    xil_printf("\n\r----- DMA to TCP Transfer Server -----\n\r");
#else
    xil_printf("\n\r----- DMA to TCP Transfer Server (IPv6) -----\n\r");
#endif
    xil_printf("Listening on port 6001\n\r");
    xil_printf("When client connects, DMA data will be sent.\n\r");
}

/* TCP receive callback (currently ignores incoming data) */
err_t recv_callback(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err) {
    if (p) pbuf_free(p);
    return ERR_OK;
}

/* TCP accept callback */
err_t accept_callback(void *arg, struct tcp_pcb *newpcb, err_t err) {
    xil_printf("TCP client connected.\n\r");

    client_pcb = newpcb;

    // Register receive callback if needed
    // tcp_recv(newpcb, recv_callback);

    return ERR_OK;
}

/* Initialize TCP server */
int start_application() {
    struct tcp_pcb *pcb;
    err_t err;
    unsigned port = 6001;

    pcb = tcp_new_ip_type(IPADDR_TYPE_ANY);
    if (!pcb) {
        xil_printf("Error creating PCB. Out of Memory\n\r");
        return -1;
    }

    err = tcp_bind(pcb, IP_ANY_TYPE, port);
    if (err != ERR_OK) {
        xil_printf("Unable to bind to port %d: err = %d\n\r", port, err);
        return -2;
    }

    pcb = tcp_listen(pcb);
    if (!pcb) {
        xil_printf("Out of memory while tcp_listen\n\r");
        return -3;
    }

    tcp_accept(pcb, accept_callback);

    xil_printf("TCP server started @ port %d\n\r", port);
    return 0;
}
