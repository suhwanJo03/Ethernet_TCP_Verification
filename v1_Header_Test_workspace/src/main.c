#include "xparameters.h"
#include "xil_printf.h"
#include "xil_cache.h"
#include "xaxidma.h"
#include "sleep.h"

#include "netif/xadapter.h"
#include "lwip/init.h"
#include "lwip/tcp.h"
#include "platform.h"

#include "frame1.h"
#include "frame2.h"

extern int start_application();   // echo.c
extern int transfer_data();       // echo.c

#define WIDTH            320
#define HEIGHT           180
#define INPUT_CHANNEL    16
#define OUTPUT_CHANNEL   12
#define PIXELS           (WIDTH * HEIGHT)
#define FRAME_BYTES      (PIXELS * INPUT_CHANNEL)

#define DMA_DEV_ID       XPAR_AXIDMA_0_DEVICE_ID

extern struct netif echo_netif;
extern struct tcp_pcb *client_pcb;
u8 rx_buffer1[FRAME_BYTES] __attribute__((aligned(64)));
u8 rx_buffer2[FRAME_BYTES] __attribute__((aligned(64)));

u32 checkHalted(u32 baseAddress, u32 offset) {
    return (XAxiDma_ReadReg(baseAddress, offset)) & XAXIDMA_HALTED_MASK;
}

int main() {
    ip_addr_t ipaddr, netmask, gw;
    unsigned char mac[6] = { 0x00, 0x0a, 0x35, 0x00, 0x01, 0x02 };
    XAxiDma_Config *myDmaConfig;
    XAxiDma myDma;
    u32 status;

    init_platform();

    IP4_ADDR(&ipaddr, 192, 168, 1, 20);
    IP4_ADDR(&netmask, 255, 255, 255, 0);
    IP4_ADDR(&gw, 192, 168, 1, 1);

    lwip_init();
    if (!xemac_add(&echo_netif, &ipaddr, &netmask, &gw, mac, XPAR_PSU_ETHERNET_3_BASEADDR)) {
        xil_printf("Failed to add network interface.\n\r");
        return -1;
    }

    netif_set_default(&echo_netif);
    netif_set_up(&echo_netif);
    platform_enable_interrupts();

    xil_printf("Board IP: %d.%d.%d.%d\n\r", ip4_addr1(&ipaddr), ip4_addr2(&ipaddr),
                ip4_addr3(&ipaddr), ip4_addr4(&ipaddr));

    myDmaConfig = XAxiDma_LookupConfigBaseAddr(XPAR_AXI_DMA_0_BASEADDR);
    status = XAxiDma_CfgInitialize(&myDma, myDmaConfig);
    if (status != XST_SUCCESS) {
        xil_printf("DMA initialization failed\r\n");
        return -1;
    }
    xil_printf("DMA initialization success..\r\n");

    status = checkHalted(XPAR_AXI_DMA_0_BASEADDR, 0x4);
    xil_printf("Status before data transfer: %0x\r\n", status);

    // TCP
    start_application();
    xil_printf("System ready.\n\r");

    // Wait until a client connects
    xil_printf("Waiting for client connection...\n\r");
    while (client_pcb == NULL) {
        xemacif_input(&echo_netif);  // Process incoming packets
        usleep(1000);                 // Small delay to avoid busy-wait
    }
    xil_printf("Client connected. Starting DMA transfer...\n\r");

    // FRAME 1
    xil_printf("\n--- Sending frame 1 ---\n\r");
    /************* FRAME 1 *************/
    xil_printf("=== FRAME 1 START ===\r\n");
    // Cache flush
    Xil_DCacheFlushRange((UINTPTR)frame1_data, FRAME_BYTES);
    // S2MM
    status = XAxiDma_SimpleTransfer(&myDma, (UINTPTR)rx_buffer1, FRAME_BYTES, XAXIDMA_DEVICE_TO_DMA);
    if (status != XST_SUCCESS) {
        xil_printf("FRAME 1 DMA Transfer setup failed (channel: S2MM)\r\n");
    }
    // MM2S
    status = XAxiDma_SimpleTransfer(&myDma, (UINTPTR)frame1_data, FRAME_BYTES, XAXIDMA_DMA_TO_DEVICE);
    if (status != XST_SUCCESS) {
        xil_printf("FRAME 1 DMA Transfer setup failed (channel: MM2S)\r\n");
    }
    // Busy
    xil_printf("Waiting for FRAME 1 DMA completion...\r\n");
    while(XAxiDma_Busy(&myDma, XAXIDMA_DMA_TO_DEVICE));
    while(XAxiDma_Busy(&myDma, XAXIDMA_DEVICE_TO_DMA));
    xil_printf("MM2S Busy? %d  S2MM Busy? %d\r\n",
               XAxiDma_Busy(&myDma, XAXIDMA_DMA_TO_DEVICE),
               XAxiDma_Busy(&myDma, XAXIDMA_DEVICE_TO_DMA));
    // Cache invalidate
    Xil_DCacheInvalidateRange((UINTPTR)rx_buffer1, FRAME_BYTES);

    transfer_data(rx_buffer1);
    usleep(10000);  // 1000ms delay

    // FRAME 2
    xil_printf("\n--- Sending frame 2 ---\n\r");
    /************* FRAME 2 *************/
    xil_printf("=== FRAME 2 START ===\r\n");
    // Cache flush
    Xil_DCacheFlushRange((UINTPTR)frame2_data, FRAME_BYTES);
    // S2MM
    status = XAxiDma_SimpleTransfer(&myDma, (UINTPTR)rx_buffer2, FRAME_BYTES, XAXIDMA_DEVICE_TO_DMA);
    if (status != XST_SUCCESS) {
        xil_printf("FRAME 2 DMA Transfer setup failed (channel: S2MM)\r\n");
    }
    // MM2S
    status = XAxiDma_SimpleTransfer(&myDma, (UINTPTR)frame2_data, FRAME_BYTES, XAXIDMA_DMA_TO_DEVICE);
    if (status != XST_SUCCESS) {
        xil_printf("FRAME 2 DMA Transfer setup failed (channel: MM2S)\r\n");
    }
    // Busy
    xil_printf("Waiting for FRAME 2 DMA completion...\r\n");
    while(XAxiDma_Busy(&myDma, XAXIDMA_DMA_TO_DEVICE));
    while(XAxiDma_Busy(&myDma, XAXIDMA_DEVICE_TO_DMA));
    xil_printf("MM2S Busy? %d  S2MM Busy? %d\r\n",
               XAxiDma_Busy(&myDma, XAXIDMA_DMA_TO_DEVICE),
               XAxiDma_Busy(&myDma, XAXIDMA_DEVICE_TO_DMA));
    // Cache invalidate
    Xil_DCacheInvalidateRange((UINTPTR)rx_buffer2, FRAME_BYTES);

    transfer_data(rx_buffer2);
    tcp_output(client_pcb);         // flush
    usleep(10000);                  // 10ms

    tcp_close(client_pcb);

    xil_printf("All frames transmitted.\n\r");

    cleanup_platform();
    return 0;
}
