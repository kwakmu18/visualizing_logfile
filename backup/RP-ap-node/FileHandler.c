#include "FileHandler.h"
uint16_t total_schedule_packets = 0;
uint16_t max_path_length = 0;
uint32_t estimate_down_sched_time = 0;
clock_t start;
int msec;
const int trigger = 3975;
unsigned char rx_buffer[256];
unsigned int count = 0;
char input;

extern int fd_port;
extern FILE *logAP;

//For uptree information
link_path_t path;
uptree_info_list_t uptree_info;
//For uplink schedule
link_path_t uplink_path;
link_data_t uplink_data;
//For downlink schedule
link_path_t downlink_path;
link_data_t downlink_data;

double cnlab_convert_fixed_point_to_double(uint32_t value)
{
    return ((value >> SHIFT_AMOUNT) + (double)(value & SHIFT_MASK)/(1 << SHIFT_AMOUNT));
}
int cnlab_open_serial_line(char *port, uint16_t baud_rate)
{
    int fd;
    if ((fd = serialOpen (port,baud_rate)) < 0) {
        fprintf (stderr, "Unable to open serial device: %s\n", strerror (errno)) ;
        return -1 ;
    }
    if (wiringPiSetup () == -1) {
        fprintf (stdout, "Unable to start wiringPi: %s\n", strerror (errno)) ;
        return -1 ;
    }
	return fd;
}

uint16_t
cnlab_uart_send_bytes(int fd, const uint8_t *s, uint16_t len)
{
    uint16_t i = 0;
    while(i < len){
        serialPutchar(fd, *s++);
        i++;
    }
    serialPutchar(fd, (uint8_t)0x7f);
    return i;
}

static uint16_t calculateNumberOfPacket(path_data_t pathData, link_t path_link)
{
	uint16_t number_packets = 0;
	uint16_t transmission_size = path_link.number_trans * sizeof(uint16_t);
	uint8_t header_size = 9 + pathData.size + 3;
	uint16_t packet_size = header_size + transmission_size;
	if (packet_size <= MAX_BUFF_SIZE)
	{
		number_packets++;
	}else{
		uint8_t num_frags = 0;
		if (transmission_size % (((MAX_BUFF_SIZE - header_size) / sizeof(uint16_t)) * sizeof(uint16_t)) == 0)
		{
			num_frags = packet_size / MAX_BUFF_SIZE;
		}else{
			num_frags = packet_size / MAX_BUFF_SIZE + 1;
		}
		number_packets += num_frags;
	}
	return number_packets;
}

static void calculatePacketFollowPath(path_data_t pathData)
{
	link_t path_link;
	memset(&path_link, 0, sizeof(path_link));
	link_t *link = uplink_data.links;
	for (int j = 0; j < uplink_data.total_links; j++)
	{
		if (link->sender == pathData.data[pathData.size - 1] && link->receiver == pathData.data[pathData.size - 2])
		{
			path_link = *link;
			break;
		}
		link++;
	}
	max_path_length = MAX(max_path_length, pathData.size - 1);
	total_schedule_packets += calculateNumberOfPacket(pathData, path_link);
}

static void processRoutingPacket(const uint8_t *buf, uint16_t buflen)
{
    uint8_t cur_len = 0;
    printf("processRoutingPacket Size of packet: %d\r\n", buflen);
	uint8_t pathData_size = buf[1];
	printf("processRoutingPacket Size of Path: %d\r\n", pathData_size);
    cur_len+=2;
    uint8_t pathData[pathData_size];
	memset(&pathData, 0, sizeof(pathData));
	for (int i = 0; i < pathData_size; i++)
	{
		pathData[i] = buf[cur_len + i];
		printf("processRoutingPacket pathData %d\r\n", pathData[i]);
	}
	cur_len += pathData_size;
	uint8_t length = buf[cur_len];
	cur_len += 1;
    uptree_info_t uptree[length];
    memset(&uptree, 0, sizeof(uptree_info_t));
	for(int i = 0; i < length; i++){
		uptree[i].node = buf[cur_len];
		uptree[i].rank = (buf[cur_len + 1]|buf[cur_len + 2] << 8|buf[cur_len + 3] << 16|buf[cur_len + 4] << 24);
		uptree[i].primary_parent = buf[cur_len + 5];
		uptree[i].reserve_parent = buf[cur_len + 6];
		cur_len += 7;
		printf("processRoutingPacket Node %d Rank %f P_Parent %d R_Parent %d\n", uptree[i].node
		,cnlab_convert_fixed_point_to_double(uptree[i].rank), uptree[i].primary_parent,
		uptree[i].reserve_parent);
	}
}

static void processPacket(const uint8_t *buf, uint16_t buflen)
{
	uint8_t cur_len = 0;
	printf("processPacket Size of packet: %d\r\n", buflen);
	uint8_t pathData_size = buf[1];
	printf("processPacket Size of Path: %d\r\n", pathData_size);
	uint8_t num_frags = buf[2] >> 4;
	printf("processPacket Frag Number: %d\r\n", num_frags);
	if (num_frags > 0)
	{
		uint8_t frag_index = buf[2] ^ (num_frags << 4);
		printf("processPacket Frag Index: %d\r\n", frag_index);
	}
	uint16_t sf_length = buf[3] | buf[4] << 8;
	printf("processPacket SF Length: %d\r\n", sf_length);
	uint32_t est_download_time = 0;
	est_download_time |= buf[5];
	est_download_time |= buf[6]<<8;
	est_download_time |= buf[7]<<16;
	est_download_time |= buf[8]<<24;
	printf("processPacket est_download_time: %d\r\n", est_download_time);
	cur_len += 9;
	uint8_t pathData[pathData_size];
	memset(&pathData, 0, sizeof(pathData));
	for (int i = 0; i < pathData_size; i++)
	{
		pathData[i] = buf[cur_len + i];
		printf("processPacket pathData %d\r\n", pathData[i]);
	}
	cur_len += pathData_size;
	link_t link;
	memset(&link, 0, sizeof(link_t));
	link.sender = buf[cur_len];
	link.receiver = buf[cur_len + 1];
	link.number_trans = buf[cur_len + 2];
	printf("processPacket (%d, %d, %d)\r\n", link.sender, link.receiver, link.number_trans);
	cur_len += 3;
	for (int j = 0; j < link.number_trans; j++)
	{
		link.data[j] = buf[cur_len] | (buf[cur_len + 1] << 8);
		uint16_t timeslot = link.data[j] >> 4;
		uint8_t channel = link.data[j] ^ (timeslot << 4);
		printf("processPacket (%d, %d)\n", timeslot, channel);
		cur_len += 2;
	}
}

static void createOnePacket(int fd, uint8_t packet_size, uint8_t packet_type, path_data_t pathData, link_t *path_link)
{
	uint8_t buf[packet_size * sizeof(uint8_t)];
	memset(&buf, 0, sizeof(buf));
	uint8_t buflen = 0;
	buf[0] = packet_type;
	buf[1] = pathData.size;
	buf[2] = 0;
	buf[3] = (uint8_t)SF_LENGTH;
	buf[4] = (uint8_t)(SF_LENGTH >> 8);
	buf[5] = estimate_down_sched_time;
	buf[6] = estimate_down_sched_time >> 8;
	buf[7] = estimate_down_sched_time >> 16;
	buf[8] = estimate_down_sched_time >> 24;
	printf("Link Config %d %d\r\n", buf[0], buf[1]);
	printf("SF Length: %d\r\n", SF_LENGTH);
	buflen += 9;
	for (int i = 0; i < pathData.size; i++)
	{
		buf[buflen + i] = pathData.data[i];
		printf("Path Data %d\r\n", buf[buflen + i]);
	}
	buflen += pathData.size;
	buf[buflen] = path_link->sender;
	buf[buflen + 1] = path_link->receiver;
	buf[buflen + 2] = path_link->number_trans;
	printf("(%d, %d, %d)\r\n", buf[buflen], buf[buflen + 1], buf[buflen + 2]);
	buflen += 3;
	for (int j = 0; j < path_link->number_trans; j++)
	{
		buf[buflen] = path_link->data[j];
		buf[buflen + 1] = path_link->data[j] >> 8;
		buflen += 2;
		uint16_t timeslot = path_link->data[j] >> 4;
		uint8_t channel = path_link->data[j] ^ (timeslot << 4);
		printf("(%d, %d)\n", timeslot, channel);
	}
	processPacket(buf, buflen);
	uint16_t size = cnlab_uart_send_bytes(fd, buf, buflen);
	printf("UART sent %d bytes\r\n", size);
	/*check response*/
		start = clock();
		int received = 0;
		do{
			msec = (clock() - start)*1000/ CLOCKS_PER_SEC;
			int size = serialDataAvail(fd_port);
			if(size != 0)
			{
				for(int i = 0; i < size; i++)
				{
					input = serialGetchar(fd_port);
					rx_buffer[count++] = input;
					if(input == '\n')
					{
						rx_buffer[--count] = '\0';
						printf("PORT0: %s\r\n", rx_buffer);
						if(strcmp(rx_buffer,"?REQSCHEDULE") == 0)
						{
							received = 1;
							break;
						}
						count = 0;
						memset(rx_buffer,0,256);
					}
				}
				if(received == 1){
					break;
				}
			}
		}while(msec < trigger);
		count = 0;
		memset(rx_buffer,0,256);
		delay(trigger - msec);
}

static void createRoutingPacketToTransmit(path_data_t pathData, uptree_info_t *uptrees, uint8_t length)
{
    printf("Size of Path: %d\r\n", pathData.size);
    int packet_size = pathData.size + 3 + length*sizeof(uptree_info_t);
		uint8_t buf[packet_size*sizeof(uint8_t)];
		memset(&buf, 0, sizeof(buf));
        uint8_t buflen = 0;
		buf[0] = (uint8_t)ROUTING_UART_PACKET;
	    buf[1] = pathData.size;
        buflen += 2;
	    for (int j = 0; j < pathData.size; j++)
	    {
		    buf[buflen + j] = pathData.data[j];
		    printf("Path Data %d\r\n", buf[buflen + j]);
	    }
	    buflen += pathData.size;
		buf[buflen] = length;
		buflen += 1;
		for(int k = 0; k < length; k++){
			buf[buflen] = uptrees[k].node;
        	fixed_point_t rank = uptrees[k].rank;
        	buf[buflen + 1] = rank;
        	buf[buflen + 2] = rank >> 8;
        	buf[buflen + 3] = rank >> 16;
        	buf[buflen + 4] = rank >> 24;
        	buf[buflen + 5] = uptrees[k].primary_parent;
        	buf[buflen + 6] = uptrees[k].reserve_parent;
        	buflen+=7;
		}
        processRoutingPacket(buf, buflen);
        uint16_t size = cnlab_uart_send_bytes(fd_port, buf, buflen);
		printf("UART sent %d bytes\r\n", size);
		/*check response*/
		start = clock();
		int received = 0;
		do{
			msec = (clock() - start)*1000/ CLOCKS_PER_SEC;
			int size = serialDataAvail(fd_port);
			if(size != 0)
			{
				for(int i = 0; i < size; i++)
				{
					input = serialGetchar(fd_port);
					rx_buffer[count++] = input;
					if(input == '\n')
					{
						rx_buffer[--count] = '\0';
						printf("PORT0: %s\r\n", rx_buffer);
						if(strcmp(rx_buffer,"?REQROUTING") == 0)
						{
							received = 1;
							break;
						}
						count = 0;
						memset(rx_buffer,0,256);
					}
				}
				if(received == 1){
					break;
				}
			}
		}while(msec < trigger);
		count = 0;
		memset(rx_buffer,0,256);
		delay(trigger - msec);
}

static void createPacketToTransmit(uint8_t packet_type, path_data_t pathData, link_t path_link)
{
	printf("Size of Path: %d\r\n", pathData.size);
	uint16_t transmission_size = path_link.number_trans * sizeof(uint16_t);
	printf("Size of transmission: %d\r\n", transmission_size);
	uint8_t header_size = 9 + pathData.size + 3;
	uint16_t packet_size = header_size + transmission_size;
	printf("Size of Packet: %d\r\n", packet_size);
	if (packet_size <= MAX_BUFF_SIZE)
	{
		createOnePacket(fd_port, packet_size, packet_type, pathData, &path_link);
	}else{
		uint8_t num_frags = 0;
		if (transmission_size % (((MAX_BUFF_SIZE - header_size) / sizeof(uint16_t)) * sizeof(uint16_t)) == 0)
		{
			num_frags = packet_size / MAX_BUFF_SIZE;
		}else{
			num_frags = packet_size / MAX_BUFF_SIZE + 1;
		}
		printf("Divide packet to %d parts\r\n", num_frags);
		uint8_t frag_size = header_size + (transmission_size / (num_frags * sizeof(uint16_t))) * sizeof(uint16_t);
		printf("Size of frag %d\r\n", frag_size);
		for (int frag_index = 1; frag_index <= num_frags; frag_index++)
		{
			uint8_t buf[frag_size * sizeof(uint8_t)];
			memset(&buf, 0, sizeof(buf));
			uint8_t buflen = 0;
			buf[0] = packet_type;
			buf[1] = pathData.size;
			buf[2] = (num_frags << 4) | frag_index;
			buf[3] = (uint8_t)SF_LENGTH;
			buf[4] = (uint8_t)(SF_LENGTH >> 8);
			buf[5] = estimate_down_sched_time;
			buf[6] = estimate_down_sched_time >> 8;
			buf[7] = estimate_down_sched_time >> 16;
			buf[8] = estimate_down_sched_time >> 24;
			printf("Link Config %d %d\r\n", buf[0], buf[1]);
			printf("SF Length: %d\r\n", SF_LENGTH);
			buflen += 9;
			for (int path = 0; path < pathData.size; path++)
			{
				buf[buflen + path] = pathData.data[path];
				printf("Path Data %d\r\n", buf[buflen + path]);
			}
			buflen += pathData.size;
			buf[buflen] = path_link.sender;
			buf[buflen + 1] = path_link.receiver;
			uint8_t num_frag_trans = 0;
			uint8_t is_odd = 0;
			if (path_link.number_trans % num_frags == 0)
			{
				num_frag_trans = path_link.number_trans / num_frags;
			}else{
				if (frag_index == num_frags)
				{
					is_odd = 1;
					num_frag_trans = path_link.number_trans % (path_link.number_trans / num_frags + 1);
				}else{
					num_frag_trans = path_link.number_trans / num_frags + 1;
				}
			}
			buf[buflen + 2] = num_frag_trans;
			printf("(%d, %d, %d)\r\n", buf[buflen], buf[buflen + 1], buf[buflen + 2]);
			buflen += 3;
			for (int j = 0; j < num_frag_trans; j++)
			{
				if (is_odd)
				{
					buf[buflen] = path_link.data[j + (frag_index - 1) * (path_link.number_trans / num_frags + 1)];
					buf[buflen + 1] = path_link.data[j + (frag_index - 1) * (path_link.number_trans / num_frags + 1)] >> 8;
					buflen += 2;
					uint16_t timeslot = path_link.data[j + (frag_index - 1) * (path_link.number_trans / num_frags + 1)] >> 4;
					uint8_t channel = path_link.data[j + (frag_index - 1) * (path_link.number_trans / num_frags + 1)] ^ (timeslot << 4);
					printf("(%d, %d)\n", timeslot, channel);
				}else{
					buf[buflen] = path_link.data[j + (frag_index - 1) * num_frag_trans];
					buf[buflen + 1] = path_link.data[j + (frag_index - 1) * num_frag_trans] >> 8;
					buflen += 2;
					uint16_t timeslot = path_link.data[j + (frag_index - 1) * num_frag_trans] >> 4;
					uint8_t channel = path_link.data[j + (frag_index - 1) * num_frag_trans] ^ (timeslot << 4);
					printf("(%d, %d)\n", timeslot, channel);
				}
			}
			processPacket(buf, buflen);
			uint16_t size = cnlab_uart_send_bytes(fd_port, buf, buflen);
			printf("UART sent %d bytes\r\n", size);
			/*check response*/
			start = clock();
			int received = 0;
			do{
				msec = (clock() - start)*1000/ CLOCKS_PER_SEC;
				int size = serialDataAvail(fd_port);
				if(size != 0)
				{
					for(int i = 0; i < size; i++)
					{
						input = serialGetchar(fd_port);
						rx_buffer[count++] = input;
						if(input == '\n')
						{
							rx_buffer[--count] = '\0';
							printf("PORT0: %s\r\n", rx_buffer);
							if(strcmp(rx_buffer,"?REQSCHEDULE") == 0)
							{
								received = 1;
								break;
							}
							count = 0;
							memset(rx_buffer,0,256);
						}
					}
					if(received == 1){
						break;
					}
				}
			}while(msec < trigger);
			count = 0;
			memset(rx_buffer,0,256);
			delay(trigger - msec);
		}
	}
}

static void processRoutingData(path_data_t pathData)
{
    int i = 0;
	int length = 0;
    uptree_info_t uptrees[pathData.size];
    memset(&uptrees, 0, sizeof(uptrees));
    while(i < pathData.size)
    {
    uptree_info_t *uptree = uptree_info.uptreeData;
        for(int j = 0; j < uptree_info.size; j++){
            if(uptree->node == pathData.data[i])
            {
                uptrees[length++] = *uptree;
                memset(uptree, 0, sizeof(uptree_info_t));
            }
			uptree++;
        }
        i++;
    }
    createRoutingPacketToTransmit(pathData, uptrees, length);
}

static void processDataFollowDownlinkPath(path_data_t pathData)
{
	link_t path_link;
	memset(&path_link, 0, sizeof(path_link));
	link_t *link = downlink_data.links;
	for (int j = 0; j < downlink_data.total_links; j++)
	{
		if (link->sender == pathData.data[pathData.size - 2] && link->receiver == pathData.data[pathData.size - 1])
		{
			path_link = *link;
			memset(link, 0, sizeof(link_t));
		}
		link++;
	}
	createPacketToTransmit((uint8_t)DOWNSCHEDULE_UART_PACKET, pathData, path_link);
}

static void processDataFollowUplinkPath(path_data_t pathData)
{
	link_t path_link;
	memset(&path_link, 0, sizeof(path_link));
	link_t *link = uplink_data.links;
	for (int j = 0; j < uplink_data.total_links; j++)
	{
		if (link->sender == pathData.data[pathData.size - 1] && link->receiver == pathData.data[pathData.size - 2])
		{
			path_link = *link;
			memset(link, 0, sizeof(link_t));
		}
		link++;
	}
	createPacketToTransmit((uint8_t)UPSCHEDULE_UART_PACKET, pathData, path_link);
}

void processFiles()
{
    FILE *fp;
    char line[128];
    char *token;
	char *end_token;
    memset(&path,0, sizeof(path));
    memset(&uptree_info, 0, sizeof(uptree_info));
    memset(&uplink_path, 0, sizeof(uplink_path));
	memset(&uplink_data, 0, sizeof(uplink_data));
	memset(&downlink_path, 0, sizeof(downlink_path));
    memset(&downlink_data, 0, sizeof(downlink_data));
    //path information
    fp = fopen(PATH_INFO, "r");
    while(fgets(line, 128, fp)){
        token = strtok(line, ",");
        while(token != NULL)
        {
            path.pathData[path.totalPath].data[path.pathData[path.totalPath].size++] = atoi(token);
            token = strtok(NULL, ",");
        }
        path.totalPath++;
    }
    printf("Total Path %d\r\n", path.totalPath);
    for(int i = 0; i < path.totalPath; i++){
        for(int j = 0; j < path.pathData[i].size; j++) {
            printf("%d ", path.pathData[i].data[j]);
        }
        printf("\n");
    }
    fclose(fp);
    //Uptree information
    fp = fopen(UPTREE_INFO, "r");
    while(fgets(line, 128, fp)){
        token = strtok(line, ",");
        uptree_info.uptreeData[uptree_info.size].node = atoi(token);
        token = strtok(NULL, ",");
        float rank = atof(token);
        uptree_info.uptreeData[uptree_info.size].rank = (1 << SHIFT_AMOUNT);
        uptree_info.uptreeData[uptree_info.size].rank *= rank;
        token = strtok(NULL, ",");
        uptree_info.uptreeData[uptree_info.size].primary_parent = atoi(token);
        token = strtok(NULL, ",");
        uptree_info.uptreeData[uptree_info.size].reserve_parent = atoi(token);
        token = strtok(NULL, ",");
        uptree_info.size++;
    }

    for(int i = 0; i < uptree_info.size; i++){
        printf("Node %d Rank %f P_Parent %d R_Parent %d\r\n"
        ,uptree_info.uptreeData[i].node, cnlab_convert_fixed_point_to_double(uptree_info.uptreeData[i].rank)
        ,uptree_info.uptreeData[i].primary_parent, uptree_info.uptreeData[i].reserve_parent);

    }
    fclose(fp);
	//Downtree Information
	fp = fopen(DOWNLINK_INFO, "r");
	while(fgets(line, 128, fp)){
        printf("%s", line);
        token = strtok_r(line, "[]", &end_token);
        uint8_t path_size = atoi(token);
        token = strtok_r(end_token, "[]", &end_token);
        char *token2 = strtok(token, ",");
        downlink_path.pathData[downlink_path.totalPath].size = path_size;
        for(int i = 0; i < path_size; i++){
            downlink_path.pathData[downlink_path.totalPath].data[i] = atoi(token2);
            token2 = strtok(NULL, ",");
        }
        token = strtok_r(end_token, "[]", &end_token);
        char *token3 = strtok(token, ",");
        downlink_data.links[downlink_data.total_links].sender = atoi(token3);
        token3 = strtok(NULL, ",");
        downlink_data.links[downlink_data.total_links].receiver = atoi(token3);
        token3 = strtok(NULL, ",");
        int nums_trans = atoi(token3);
        downlink_data.links[downlink_data.total_links].number_trans = nums_trans;
        token3 = strtok(NULL, ",");
        token = strtok_r(end_token, "[]", &end_token);
        char *token4 = strtok_r(token, "()", &end_token);
        for(int i = 0; i < nums_trans; i++) {
            char *token5 = strtok(token4, ",");
            uint16_t timeslot = atoi(token5);
            downlink_data.links[downlink_data.total_links].data[i] |= (timeslot << 4);
            token5 = strtok(NULL, ",");
            uint8_t channel = atoi(token5);
            downlink_data.links[downlink_data.total_links].data[i] |= channel;
            token5 = strtok(NULL, ",");
            token4 = strtok_r(end_token, "()", &end_token);
        }
		downlink_path.totalPath++;
        downlink_data.total_links++;
	}
	printf("Total Downlink Path %d\n", downlink_path.totalPath);
    for(int i = 0; i < downlink_path.totalPath; i++){
        for(int j = 0; j < downlink_path.pathData[i].size; j++) {
            printf("%d ", downlink_path.pathData[i].data[j]);
        }
        printf("\n");
    }
    for(int i = 0; i < downlink_data.total_links; i++){
        printf("%d->%d:%d\n",downlink_data.links[i].sender ,downlink_data.links[i].receiver, downlink_data.links[i].number_trans);
        for(uint8_t j = 0; j < downlink_data.links[i].number_trans; j++){
		    uint16_t timeslot = downlink_data.links[i].data[j] >> 4;
		    uint8_t channel = downlink_data.links[i].data[j] ^ (timeslot << 4);
            printf("(%d,%d)\n", timeslot, channel);
	    }
    }
	fclose(fp);
    //Scheduling Information
    fp = fopen(UPLINK_INFO, "r");
    while(fgets(line, 128, fp)){
        token = strtok_r(line, "[]", &end_token);
        uint8_t path_size = atoi(token);
        token = strtok_r(end_token, "[]", &end_token);
        char *token2 = strtok(token, ",");
        uplink_path.pathData[uplink_path.totalPath].size = path_size;
        for(int i = 0; i < path_size; i++){
            uplink_path.pathData[uplink_path.totalPath].data[i] = atoi(token2);
            token2 = strtok(NULL, ",");
        }
        token = strtok_r(end_token, "[]", &end_token);
        char *token3 = strtok(token, ",");
        uplink_data.links[uplink_data.total_links].sender = atoi(token3);
        token3 = strtok(NULL, ",");
        uplink_data.links[uplink_data.total_links].receiver = atoi(token3);
        token3 = strtok(NULL, ",");
        int nums_trans = atoi(token3);
        uplink_data.links[uplink_data.total_links].number_trans = nums_trans;
        token3 = strtok(NULL, ",");
        token = strtok_r(end_token, "[]", &end_token);
        char *token4 = strtok_r(token, "()", &end_token);
        for(int i = 0; i < nums_trans; i++) {
            char *token5 = strtok(token4, ",");
            uint16_t timeslot = atoi(token5);
            uplink_data.links[uplink_data.total_links].data[i] |= (timeslot << 4);
            token5 = strtok(NULL, ",");
            uint8_t channel = atoi(token5);
            uplink_data.links[uplink_data.total_links].data[i] |= channel;
            token5 = strtok(NULL, ",");
            token4 = strtok_r(end_token, "()", &end_token);
        }
        uplink_path.totalPath++;
        uplink_data.total_links++;
    }
	fclose(fp);
    printf("Total Uplink Path %d\n", uplink_path.totalPath);
    for(int i = 0; i < uplink_path.totalPath; i++){
        for(int j = 0; j < uplink_path.pathData[i].size; j++) {
            printf("%d ", uplink_path.pathData[i].data[j]);
        }
        printf("\n");
    }
    for(int i = 0; i < uplink_data.total_links; i++){
        printf("%d->%d:%d\n",uplink_data.links[i].sender ,uplink_data.links[i].receiver, uplink_data.links[i].number_trans);
        for(uint8_t j = 0; j < uplink_data.links[i].number_trans; j++){
		    uint16_t timeslot = uplink_data.links[i].data[j] >> 4;
		    uint8_t channel = uplink_data.links[i].data[j] ^ (timeslot << 4);
            printf("(%d,%d)\n", timeslot, channel);
	    }
    }
	//Battery information
	char buffer[128];
	fp = fopen(BATTERY_INFO, "r");
	logAP = fopen(LOG_AP, "a");
    while(fgets(buffer, 128, fp)){
        printf("%s", buffer);
		fwrite(buffer, strlen(buffer), 1, logAP);
    }
    fclose(fp);
	fclose(logAP);
	printf("Number total routing packets %d\r\n", path.totalPath);
	for(int i = 0; i < path.totalPath; i++)
    {
        printf("Routing Path %d\r\n", i + 1);
        processRoutingData(path.pathData[i]);
    }
	for (int i = 0; i < downlink_path.totalPath; i++)
	{
		calculatePacketFollowPath(downlink_path.pathData[i]);
	}
    for (int i = 0; i < uplink_path.totalPath; i++)
	{
		calculatePacketFollowPath(uplink_path.pathData[i]);
	}
    printf("Number total schedule packets %d\r\n", total_schedule_packets);
	estimate_down_sched_time = total_schedule_packets*trigger + max_path_length*MAX_CTRL_PACKET_TRANSMISSION*ORCHESTRA_SF_LENGTH*TIME_SLOT_LENGTH;
    printf("Estimate download schedule time : %ld\r\n", estimate_down_sched_time/TIME_SLOT_LENGTH);

	for (int i = 0; i < uplink_path.totalPath; i++)
	{
		printf("Uplink Path %d\r\n", i + 1);
		processDataFollowUplinkPath(uplink_path.pathData[i]);
	}
	
	for (int i = 0; i < downlink_path.totalPath; i++)
	{
		printf("Downlink Path %d\r\n", i + 1);
		processDataFollowDownlinkPath(downlink_path.pathData[i]);
	}
}