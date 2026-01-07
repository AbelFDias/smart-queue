/*
 * Smart Queue - ESP8266 (NodeMCU) com LED de Alerta
 *
 * Funcionalidades:
 * - Lê teclado matricial 3x4 e envia "Tecla: X" via Serial
 * - Recebe "LED:1" / "LED:0" para ligar/desligar LED vermelho
 *
 * Pinagem (usar rótulos Dx da placa NodeMCU):
 *   Linhas (ROWS): D5, D6, D7, D3
 *   Colunas (COLS): D1, D2, D4
 *   LED: D8 (GPIO15)
 *
 * Notas de boot do ESP8266:
 * - D8 (GPIO15) deve ficar em LOW na arranque: o LED fica apagado inicialmente, está ok.
 * - Evita usar D0 (GPIO16) para keypad; D3 (GPIO0) é aceitável se não puxares para HIGH na arranque.
 */

#include <Keypad.h>

const byte ROWS = 4;
const byte COLS = 3;

char keys[ROWS][COLS] = {
  {'1','2','3'},
  {'4','5','6'},
  {'7','8','9'},
  {'*','0','#'}
};

// Pinagem para NodeMCU / ESP8266
byte rowPins[ROWS] = {D5, D6, D7, D3}; // lin 1..4
byte colPins[COLS] = {D1, D2, D4};      // col 1..3

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// LED de alerta
const int LED_PIN = D8; // GPIO15

void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); // LED apagado no arranque (necessário p/ boot)

  Serial.println("Arduino Smart Queue iniciado (ESP8266)");
  Serial.println("LED vermelho na porta D8");
  Serial.println(">>> Teclado Pronto (linhas D5/D6/D7/D3 | colunas D1/D2/D4) <<<");
}

void loop() {
  // Ler tecla pressionada
  char key = keypad.getKey();
  if (key) {
    Serial.print("Tecla: ");
    Serial.println(key);
  }

  // Ler comandos do PC para controlar LED
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "LED:1") {
      digitalWrite(LED_PIN, HIGH);  // Ligar LED
    } else if (cmd == "LED:0") {
      digitalWrite(LED_PIN, LOW);   // Desligar LED
    }
  }
}
