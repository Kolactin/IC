#include <OneWire.h>
#include <DallasTemperature.h>

#define NUM_MEDIDAS 50 // Número de medidas a serem realizadas
#define ONE_WIRE_BUS 2

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

int baudRate = 9600; // Taxa de comunicação
int dt = 1; // Delay (ms) entre 2 aquisições de dados
int dt_medidas = 10; // Delay (ms) entre 2 medições de pontos I-V
int dt_IVadj = 10; // delay (ms) para estabelecer nova corrente e tensão no IVadjust()
float valor_lum = 0.0; //primeiro valor lido pelo sensor de luz
//int pinCC = 4; // Define o pino digital para conectar o módulo
float a = 1.01; // Fator de conversão (expoente) da lei de potência
float b = 2.44; // Fator de conversão (coeficiente) da lei de potência
boolean flag = true;
int IVcontrol = 3;
float coef_V = 4.8/1024.0;
float Ri = 0.2; //resistência para medição teste da corrente
float Rsensor0 = pow(10, 6);
float Rsensor = 1000.0;
int count = 0; //variável contadora para o loop da luminosidade
float soma_lum = 0;
float soma_temp = 0;
int valor_menu;
float V_ganho = 6.54;
int Ndados = 200;
float tempC;
float I_tracking = 1.0e-2; // limiar de corrente para iniciar as medidas

float mediaCorrente[502];
float mediaTensao[502];
int indice = 0; // Índice para armazenar os valores médios

void GetLightInt(){
  count = 0;
  while (count<NUM_MEDIDAS){
    valor_lum = analogRead(A3);
    delay(dt);
    soma_lum += valor_lum;
    count+=1;
  }
  soma_lum = soma_lum/float(NUM_MEDIDAS);
  soma_lum = soma_lum*coef_V*Rsensor/Rsensor0;
  soma_lum = pow (soma_lum/b , 1.0/a);
  Serial.print(soma_lum,4);
  Serial.print(" ");
}

void GetModTemp(int indice){
  int jj;
  jj = indice / 10;
  jj = 10*jj;
  if (jj == indice) {
    sensors.requestTemperatures();
    tempC = sensors.getTempCByIndex(0);
  }

/*  Serial.print(jj);
  Serial.print(" ");
  Serial.print(indice);
  Serial.print(" # "); */
  Serial.print(tempC,2);
  Serial.print(" ");
}

void I0tracking() {
  int Npontos = 10;
  float mediaCorrenteValor = 0.0;
  float somaCorrente = 0.0;

  Serial.println("Inicio de I0tracking");
  while (mediaCorrenteValor < I_tracking) {
  digitalWrite(IVcontrol, HIGH);
  delay(dt);
  digitalWrite(IVcontrol, LOW);
  
  somaCorrente = 0.0;
  for (count = 0; count < Npontos; count++) {
    int corrente = analogRead(A0);
    somaCorrente += float(corrente);
    delay(dt);
  }
  mediaCorrenteValor = somaCorrente*coef_V / (float(Npontos)*Ri);
  }
}

void IVadjust() {
  digitalWrite(IVcontrol, HIGH);
  delay(dt_IVadj);
  digitalWrite(IVcontrol, LOW);
}

void GetIV(){  // Realizar as medidas de corrente e tensão e calcular os valores médios
  float somaCorrente = 0.0;
  float somaTensao = 0.0;

  for (count = 0; count < NUM_MEDIDAS; count++) {
    int corrente = analogRead(A0);
    int tensao = analogRead(A1);

// Somar as medidas de corrente e tensão
     somaCorrente += float(corrente);
     somaTensao += float(tensao);

    delay(dt);
  }

  // Calcular o valor médio da corrente e tensão
  float mediaCorrenteValor = somaCorrente*coef_V / Ri / float(NUM_MEDIDAS);
  float mediaTensaoValor = somaTensao*coef_V*V_ganho / float(NUM_MEDIDAS);

// Armazenar os valores médios na matriz
  mediaCorrente[indice] = mediaCorrenteValor;
  mediaTensao[indice] = mediaTensaoValor;

  // Exibir os valores médios
  Serial.print(" ");
//  Serial.print("Corrente media: ");
  Serial.print(mediaCorrenteValor,4);
  Serial.print(" ");
//  Serial.print("Tensao media: ");
  Serial.println(mediaTensaoValor,4);
  
  if (mediaTensaoValor<5) {
  return 1;

  else {
    mediaTensaoValor == 0;
  }
}

void CCmod() {

}

void setup() {
  Serial.begin(baudRate);
  pinMode(IVcontrol, OUTPUT);
  digitalWrite(IVcontrol, LOW);
  while (!Serial) {
  }
  delay(1000);
}

void loop() {
  while (Serial.available() != 2) { // Verifica se há pelo menos 2 bytes disponíveis para leitura
  }
  int  number = 0;
  char digit = Serial.read(); // Lê um caractere da porta serial
  if (isdigit(digit)) { // Verifica se o caractere é um dígito numérico
       number = number * 10 + (digit - '0'); // Converte o caractere em um dígito numérico e adiciona ao número
  }
  if (number == 1) {
    I0tracking();
    Serial.print("indice, PHI, T, I, V");
    while (indice < Ndados){
      Serial.print(indice);
      Serial.print(" ");
      IVadjust();
      delay(dt_medidas);
      GetLightInt();
      GetModTemp(indice);
      GetIV();
      indice = indice+1;
  }
  }

  while (1 == 1) {} // loop infinito
}
