#include <SPI.h>
#include <MFRC522.h>

// Pin definitions
#define RST_PIN 9      // Reset pin for RFID
#define SS_PIN 10      // Slave Select pin for RFID (SDA)
#define BUZZER_PIN 8   // Buzzer pin
#define LED_GREEN 7    // Green LED (Access Granted)
#define LED_RED 6      // Red LED (Access Denied)

// Initialize MFRC522
MFRC522 mfrc522(SS_PIN, RST_PIN);

// Variables
String lastUID = "";
unsigned long lastCardReadTime = 0;
const unsigned long cardReadCooldown = 2000; // 2 seconds cooldown between reads

void setup() {
  // Initialize Serial communication
  Serial.begin(9600);
  
  // Initialize SPI bus
  SPI.begin();
  
  // Initialize RFID reader
  mfrc522.PCD_Init();
  
  // Initialize pins
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  
  // Test sequence on startup
  startupSequence();
  
  // Send ready signal to PC
  Serial.println("ARD_READY");
  Serial.println("PPE System Ready - Tap your RFID card");
}

void loop() {
  // Check for new RFID cards
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    
    // Check cooldown to prevent multiple rapid reads
    if (millis() - lastCardReadTime > cardReadCooldown) {
      
      // Get UID from card
      String uid = getUID();
      
      // Send UID to PC via serial
      Serial.println("UID:" + uid);
      
      // Short beep to confirm card read
      tone(BUZZER_PIN,500);
      delay(500);
      noTone(BUZZER_PIN);
      
      // Flash green LED briefly to show card detected
      digitalWrite(LED_GREEN, HIGH);
      delay(100);
      digitalWrite(LED_GREEN, LOW);
      
      // Update last read time
      lastCardReadTime = millis();
      lastUID = uid;
      
      // Wait for PC response (access grant/deny will come via Serial)
      // The system will wait for command from PC
    }
    
    // Halt the card
    mfrc522.PICC_HaltA();
    
    // Stop encryption (for some cards)
    mfrc522.PCD_StopCrypto1();
  }
  
  // Check for commands from PC
  if (Serial.available() > 0) {
    String command = Serial.readString();
    command.trim();
    
    handleCommand(command);
  }
}

/**
 * Get UID from RFID card as a hex string
 */
String getUID() {
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    // Add leading zero if needed
    if (mfrc522.uid.uidByte[i] < 0x10) {
      uid += "0";
    }
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  return uid;
}

/**
 * Handle commands received from PC
 */
void handleCommand(String command) {
  if (command == "ACCESS_GRANTED" || command == "1") {
    // Access Granted - PPE Check Passed
    accessGranted();
  } 
  else if (command == "ACCESS_DENIED" || command == "0") {
    // Access Denied - PPE Check Failed
    accessDenied();
  }
  else if (command == "CARD_VALID") {
    // Card is valid in Firebase - short confirmation
    cardValidFeedback();
  }
  else if (command == "CARD_INVALID") {
    // Card is invalid - show error
    cardInvalidFeedback();
  }
  else if (command == "PING") {
    // Respond to ping from PC
    Serial.println("PONG");
  }
  else if (command == "RESET") {
    // Reset system
    resetSystem();
  }
}

/**
 * Access Granted sequence
 */
void accessGranted() {
  Serial.println("🔓 Access Granted - Door Opening");
  
  // Green LED pattern (success)
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_GREEN, HIGH);
    delay(100);
    digitalWrite(LED_GREEN, LOW);
    delay(100);
  }
  
  // Success beep pattern (rising tone)
  tone(BUZZER_PIN, 1000, 200);
  delay(200);
  tone(BUZZER_PIN, 1500, 300);
  delay(300);
  
  // Keep green LED on for 2 seconds
  digitalWrite(LED_GREEN, HIGH);
  delay(2000);
  digitalWrite(LED_GREEN, LOW);
  
  Serial.println("✅ Access Granted Complete");
}

/**
 * Access Denied sequence
 */
void accessDenied() {
  Serial.println("🔒 Access Denied - PPE Check Failed");
  
  // Red LED pattern (error)
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_RED, HIGH);
    tone(BUZZER_PIN, 1000, 1500);
    delay(200);
    digitalWrite(LED_RED, LOW);
    delay(100);
  }
  
  // Keep red LED on for 1 second
  digitalWrite(LED_RED, HIGH);
  delay(1000);
  digitalWrite(LED_RED, LOW);
}

/**
 * Card valid feedback (short confirmation)
 */
void cardValidFeedback() {
  digitalWrite(LED_GREEN, HIGH);
  tone(BUZZER_PIN, 800, 100);
  delay(150);
  digitalWrite(LED_GREEN, LOW);
}

/**
 * Card invalid feedback
 */
void cardInvalidFeedback() {
  digitalWrite(LED_RED, HIGH);
  tone(BUZZER_PIN, 700, 200);
  delay(200);
  digitalWrite(LED_RED, LOW);
  delay(100);
  digitalWrite(LED_RED, HIGH);
  tone(BUZZER_PIN, 700, 200);
  delay(200);
  digitalWrite(LED_RED, LOW);
}

/**
 * Startup sequence - test all components
 */
void startupSequence() {
  Serial.println("Running startup sequence...");
  
  // Test buzzer
  tone(BUZZER_PIN, 500, 300);
  delay(300);
  tone(BUZZER_PIN, 1000, 300);
  delay(300);
  tone(BUZZER_PIN, 1500, 400);
  delay(400);
  
  // Test LEDs
  digitalWrite(LED_GREEN, HIGH);
  delay(200);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, HIGH);
  delay(200);
  digitalWrite(LED_RED, LOW);
  
  // Test both LEDs together
  digitalWrite(LED_GREEN, HIGH);
  digitalWrite(LED_RED, HIGH);
  delay(300);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
  
  Serial.println("Startup complete - System ready");
}

/**
 * Reset system
 */
void resetSystem() {
  Serial.println("System resetting...");
  
  // Turn off all outputs
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
  tone(BUZZER_PIN, 1000, 200);
  delay(200);
  noTone(BUZZER_PIN);
  
  // Reset RFID
  mfrc522.PCD_Init();
  
  // Beep to indicate reset
  tone(BUZZER_PIN, 1000, 200);
  delay(200);
  tone(BUZZER_PIN, 800, 200);
  delay(200);
  tone(BUZZER_PIN, 600, 200);
  
  Serial.println("System reset complete");
  Serial.println("ARD_READY");
}

/**
 * Function to check if card is still present (optional)
 * Useful for door open/close logic
 */
bool isCardPresent() {
  return mfrc522.PICC_IsNewCardPresent();
}
