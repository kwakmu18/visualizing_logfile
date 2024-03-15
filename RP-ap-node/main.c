#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <netdb.h>
#include <unistd.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <time.h>
//File Handler
#include "FileHandler.h"

//UART defines
#define PORT0 "/dev/ttyUSB0"
#define BAUD_RATE 57600

#define NUMBER_OF_NODES 11

char node_maps[NUMBER_OF_NODES + 1];

int fd_port = 0;
FILE *logAP;
FILE *nodeInfo;

int main()
{
    unsigned char uart_buffer[128], char_buf[80];
    // unsigned char exeString[128];
    char input;
    uint16_t index = 0, size = 0;
    uint8_t number_of_node = 0;
    time_t timer;
    char time_buffer[50];
    struct tm* tm_info;

    remove(GRAPH_INFO);
    remove(LOG_AP);

    memset(&node_maps, 0, sizeof(node_maps));
    node_maps[NUMBER_OF_NODES] = '\0';

    fd_port = cnlab_open_serial_line(PORT0, BAUD_RATE);
    if(fd_port == -1){
	printf("SERIAL COMMUNICATION HAS PROBLEM! PLEASE TRY TO CONNECT AGAIN!\r\n");
	return 0;
    }
    printf("PORT0 = %d \r\n", fd_port);

    logAP = fopen(LOG_AP, "a");
    nodeInfo = fopen(GRAPH_INFO, "a");

    while(1){
	int len = serialDataAvail(fd_port);

        if(len == 0)
	    continue;

	for(int i = 0; i < len; i++) {
            input = serialGetchar(fd_port);
            uart_buffer[index++] = input;
        }
        if(input == '\n') {
	    uart_buffer[index] = '\0';
	    printf("PORT0: %s \r\n", uart_buffer);
	    fwrite(uart_buffer, strlen(uart_buffer), 1, logAP);
	    if(strstr(uart_buffer, "ZZIOT_READY") != NULL) {  // mkkim: Need to change initial READY message !!!
		break;   // break while loop
	    }
	}
    }

    while (1) {
    	printf("ZZIOT is ready: start now? (Y/N): \r\n");
    	scanf("%s", char_buf);
    	if (char_buf[0] == 'Y')
	    break;
    }

    size = cnlab_uart_send_bytes(fd_port, "START", 5);
    printf("Server sent START command \r\n");

    while(1){
	int len = serialDataAvail(fd_port);

        if(len == 0)
	    continue;

	for(int i = 0; i < len; i++) {
            input = serialGetchar(fd_port);
            uart_buffer[index++] = input;
        }

        if(input == '\n') {
	    uart_buffer[index] = '\0';
	    printf("PORT0: %s\r\n", uart_buffer);
	    fwrite(uart_buffer, strlen(uart_buffer), 1, logAP);
	    if(strncmp(uart_buffer, "N/", 2) == 0) {  // mkkim: Need to change initial READY message !!!
		char *token = strtok(uart_buffer, "/");
		token = strtok(NULL, "");
		char node_value = token[0];
		if(strchr(node_maps, node_value) == NULL){
		    node_maps[number_of_node++] = node_value;
		    fwrite(token, strlen(token), 1, nodeInfo);
		}
	    }
	}
	index = 0;

	if(number_of_node == NUMBER_OF_NODES){
	    printf("All NI received \r\n");
	    break;
	}
    }

    size = cnlab_uart_send_bytes(fd_port, "END-OF-STEP2", 12);
    printf("End-of-step2 \r\n");

    close(logAP);
    close(nodeInfo);

    return 0;
}
