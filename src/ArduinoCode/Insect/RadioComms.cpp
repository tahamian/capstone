#include "RadioComms.h"

//#define nodeID 1
#define retry 10

RF24 radio(7,8);
RF24Network network(radio);

bool init_conn = false;

void RadioComms::init(unsigned int nodeID) {
  Serial.begin(115200);
  radio.begin();
  network.begin(100, nodeID);
  Serial.println("Starting insect...");
}


void RadioComms::update() {
  network.update();
  payloadMsg payload;
  if (! init_conn){
    safeSend(INIT,&payload,0);
    Serial.println("Connected");
    init_conn = true;
  }
  else{
  while(network.available()){
    RF24NetworkHeader header;
    payloadMsg payload;
    network.read(header,&payload, sizeof(payloadMsg));
    switch (header.type){
      case INIT:
        handle_init(&header, &payload);
        safeSend(INIT, &payload, retry);
        break;
      case TEMP_TYPE:
        handle_temp(&header, &payload);
        break;
      case MOTOR_READY:
        handle_get_gyro(&header, &payload);
        break;
      case MOTOR_TYPE:
        memcpy(&newSettings, &payload.data, sizeof(newSettings));
        Serial.println(newSettings.state);
//        handle_move_motor(&header, &payload);
        break;
      default:
        Serial.println("UNKNOWN MESSAGE TYPE");
        break;
    }
  }
}
}

void RadioComms::handle_temp(RF24NetworkHeader *header, payloadMsg *payload){
  Serial.println("Handling temp_type");
  float temp = 20.00;
  dtostrf(temp,12,20,(payload->data));
  // safeSend(GET_GYRO_TYPE, payload, retry);
}

void RadioComms::handle_set_gyro (RF24NetworkHeader *header, payloadMsg *payload) {
  float degree = atof(payload->data);
  Serial.println(degree);

}

void RadioComms::handle_get_gyro (RF24NetworkHeader *header, payloadMsg *payload) {
  Serial.println("Handling get gyro");
  float degree = 90.0012312312313;
  dtostrf(degree,12,20,(payload->data));
  // safeSend(SET_GYRO_TYPE,payload, retry);
}

void RadioComms::handle_init(RF24NetworkHeader *header, payloadMsg *payload){
  Serial.println("Handling init_type");
  // initData init;
  // init.msgID = -1;
  // memcpy(payload->data,&init,sizeof(payload->data));
  safeSend(INIT, payload, retry);
}

void RadioComms::handle_move_motor(RF24NetworkHeader *header, payloadMsg *payload){
  Serial.println("Handling move_type");
  //motor.setMotor(FORWARD);
  safeSend(MOTOR_TYPE, payload, retry);
}

void RadioComms::safeSend(char type, payloadMsg *payload, int tryAgain ){
  while (!sendToMaster(type,payload)){
    Serial.println("Failed to send");
    delay(100);
  }
}

bool RadioComms::sendToMaster (char type, payloadMsg *payload) {
  RF24NetworkHeader header(0,type);
  return network.write(header, payload, sizeof(*payload));
}
