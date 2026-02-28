#include <Arduino.h>

// --- Struktur Data Tombol Arkade ---
struct ArcadeButton {
  const uint8_t btnPin;
  const uint8_t ledPin;
  const char* pressMsg;    // Pesan yang dikirim saat ditekan
  const char* releaseMsg;  // Pesan yang dikirim saat dilepas
  
  bool lastFlickerableState;
  bool currentState;
  unsigned long lastDebounceTime;
};

// Inisialisasi 4 Tombol & LED
ArcadeButton buttons[4] = {
  {8, 3, "PRESS_A", "RELEASE_A", HIGH, HIGH, 0},   // Tombol A (Hijau 1)
  {10, 5, "PRESS_S", "RELEASE_S", HIGH, HIGH, 0},  // Tombol S (Kuning 1)
  {4, 6, "PRESS_L", "RELEASE_L", HIGH, HIGH, 0},   // Tombol L (Hijau 2)
  {2, 7, "PRESS_K", "RELEASE_K", HIGH, HIGH, 0}    // Tombol K (Kuning 2)
};

const unsigned long debounceDelay = 15; // Waktu debounce 15ms
TaskHandle_t InputTaskHandle;

// --- FUNGSI TASK FREERTOS (1000Hz Polling) ---
void inputTask(void *pvParameters) {
  for (;;) {
    unsigned long currentMillis = millis();

    for (int i = 0; i < 4; i++) {
      bool reading = digitalRead(buttons[i].btnPin);

      // Filter noise mekanik (bouncing)
      if (reading != buttons[i].lastFlickerableState) {
        buttons[i].lastDebounceTime = currentMillis;
        buttons[i].lastFlickerableState = reading;
      }

      // Jika sinyal sudah stabil
      if ((currentMillis - buttons[i].lastDebounceTime) > debounceDelay) {
        if (reading != buttons[i].currentState) {
          buttons[i].currentState = reading;

          if (buttons[i].currentState == LOW) {
            // SAAT DITEKAN
            digitalWrite(buttons[i].ledPin, HIGH); // LED Nyala
            Serial.println(buttons[i].pressMsg);   // Kirim sinyal ke PC
          } else {
            // SAAT DILEPAS
            digitalWrite(buttons[i].ledPin, LOW);  // LED Mati
            Serial.println(buttons[i].releaseMsg); // Kirim sinyal ke PC
          }
        }
      }
    }
    
    // Polling rate 1ms (1000Hz) tanpa memblokir CPU
    vTaskDelay(pdMS_TO_TICKS(1)); 
  }
}

void setup() {
  Serial.begin(115200);
  
  // Inisialisasi Pin
  for (int i = 0; i < 4; i++) {
    pinMode(buttons[i].btnPin, INPUT_PULLUP);
    pinMode(buttons[i].ledPin, OUTPUT);
    digitalWrite(buttons[i].ledPin, LOW); 
  }

  // Jalankan FreeRTOS Task
  xTaskCreate(inputTask, "Scanner", 4096, NULL, 1, &InputTaskHandle);
}

void loop() {
  // Kosong, biarkan FreeRTOS bekerja di background
  vTaskDelay(pdMS_TO_TICKS(1000)); 
}