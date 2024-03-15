#ifndef __FILE_HANDLER_H__
#define __FILE_HANDLER_H__
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <time.h>

//Wiring Pi Libraries
#include <wiringPi.h>
#include <wiringSerial.h>
#define ORCHESTRA_SF_LENGTH 53
#define TIME_SLOT_LENGTH 15
#define SF_LENGTH 691
#define MAX_CTRL_PACKET_TRANSMISSION 5

//Fixed Point Handler
#define ACCURACY 5
#define SHIFT_AMOUNT 16
#define SHIFT_MASK ((1 << SHIFT_AMOUNT) - 1)

#define MAX_BUFF_SIZE 90
#define MAX(x,y) (((x) > (y)) ? (x) : (y))

#define GRAPH_INFO "/home/pi/eval_test/graph_info.txt"
#define LOG_AP "/home/pi/eval_test/logAP.txt"
#define PATH_INFO "/home/pi/eval_test/path_information.txt"
#define UPTREE_INFO "/home/pi/eval_test/uptree_information.txt"
#define DOWNLINK_INFO "/home/pi/eval_test/downlink_scheduling_information.txt"
#define UPLINK_INFO "/home/pi/eval_test/scheduling_information.txt"
#define BATTERY_INFO "/home/pi/eval_test/used_battery_information.txt"
typedef uint32_t fixed_point_t;
enum PACKET_TYPE {
    ROUTING_UART_PACKET,
    DOWNSCHEDULE_UART_PACKET,
	UPSCHEDULE_UART_PACKET,
};
//Path Information
struct path_data
{
	uint8_t size;
	uint8_t data[128];
}__attribute__((__packed__));
typedef struct path_data path_data_t;

struct link_path
{
	uint8_t totalPath;
	path_data_t pathData[128];
}__attribute__((__packed__));
typedef struct link_path link_path_t;
//Tree information
struct uptree_info
{
    uint8_t node;
    fixed_point_t rank;
    uint8_t primary_parent;
    uint8_t reserve_parent;
}__attribute__((__packed__));
typedef struct uptree_info uptree_info_t;

struct uptree_info_list
{
    uint8_t size;
    uptree_info_t uptreeData[128];

}__attribute__((__packed__));
typedef struct uptree_info_list uptree_info_list_t;
//Scheduling Information
struct link
{
	uint8_t sender;
	uint8_t receiver;
	uint8_t number_trans;
	uint16_t data[255];
}__attribute__((__packed__));
typedef struct link link_t;

struct link_data
{
	uint8_t total_links;
	link_t links[255];
}__attribute__((__packed__));
typedef struct link_data link_data_t;

//Function
int cnlab_open_serial_line(char *port, uint16_t baud_rate);
uint16_t cnlab_uart_send_bytes(int fd, const uint8_t *s, uint16_t len);
void processFiles();
#endif /* __FILE_HANDLER_H__ */