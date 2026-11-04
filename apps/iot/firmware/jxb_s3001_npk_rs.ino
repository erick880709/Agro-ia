/*
 * AgroIA — Firmware de campo para el sensor de suelo JXBS-3001-NPK-RS
 * Épica E1 · TT-02 (integridad de la ingesta, RFP-AGROIA-003)
 *
 * Lee los registros Modbus RTU (función 0x03) del sensor 7-en-1 y publica
 * una trama JSON con:
 *   - los registros crudos decodificados (pH, VWC, temperatura, CE, N, P, K)
 *   - CRC validado con reintentos
 *   - hora NTP/RTC
 *   - versión de firmware
 *   - idempotencia (msg_id) para el buffer offline
 *
 * Conexionado (RS485, lógica 3,3 V del ESP32):
 *   - Alimentación del sensor: 12 V DC (variante de fábrica)
 *   - ESP32 (3,3 V lógico) <-> transceptor RS485 <-> bus A/B del sensor
 *   - Pin DE/RE del transceptor a GPIO 32 (control de dirección)
 *   - Modbus RTU 9600 8N1, dirección del sensor 0x01 por defecto
 *
 * IMPORTANTE (manual del fabricante):
 *   - No energizar el sensor al aire: insertar las agujas en suelo húmedo.
 *   - Retirar la capa superficial hasta la profundidad de lectura antes de
 *     insertar la sonda.
 *   - Evitar el sol directo sobre la sonda (temperatura espuria > 45 °C).
 */

#include <WiFi.h>
#include <time.h>

// ─────────────────────────── Configuración ───────────────────────────
#define FW_VERSION "1.0.0"

// WiFi / NTP
const char* WIFI_SSID = "AGROIA_CAMPO";
const char* WIFI_PASS = "CAMBIAR_EN_CAMPO";
const char* NTP_SERVER = "pool.ntp.org";
const long  GMT_OFFSET_SEC = -5 * 3600;   // Colombia (UTC-5)
const int   DAYLIGHT_OFFSET_SEC = 0;

// RS485 / Modbus
#define RS485_DIR_PIN   32     // DE/RE del transceptor
#define SERIAL_RX_PIN   16
#define SERIAL_TX_PIN   17
#define SENSOR_ADDR     0x01   // dirección por defecto (configurable en 0x0100)
#define BAUDIOS         9600

// Registros del JXBS-3001-NPK-RS (función 0x03, enteros de 16 bits)
#define REG_PH          0x0006  // escala 0,01
#define REG_HUMEDAD     0x0012  // escala 0,1 %  (VWC)
#define REG_TEMP        0x0013  // escala 0,1 °C (con signo)
#define REG_CE          0x0015  // µS/cm (resolución 10)
#define REG_N           0x001E  // mg/kg
#define REG_P           0x001F  // mg/kg
#define REG_K           0x0020  // mg/kg
#define REG_INICIO      REG_PH
#define REG_CANTIDAD    (REG_K - REG_PH + 1)  // 0x001B = 27 registros

// Reintentos y lecturas
#define MAX_REINTENTOS  3
#define LECTURAS_POR_PUNTO 3
#define TIMEOUT_MODBUS  200   // ms por sensor

// ─────────────────────────── Estado global ───────────────────────────
HardwareSerial modbus(1);
uint32_t msg_id = 0;           // idempotencia (se incrementa con cada envío)
bool hora_sincronizada = false;

// ─────────────────────────── CRC-16 Modbus ───────────────────────────
uint16_t crc16_modbus(const uint8_t* data, size_t len) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (int b = 0; b < 8; b++) {
      if (crc & 0x0001) crc = (crc >> 1) ^ 0xA001;
      else              crc >>= 1;
    }
  }
  return crc;
}

bool trama_crc_valida(const uint8_t* trama, size_t len) {
  if (len < 4) return false;
  uint16_t crc = crc16_modbus(trama, len - 2);
  uint16_t recibido = trama[len - 2] | (trama[len - 1] << 8);
  return crc == recibido;
}

// ─────────────────────────── Modbus RTU ───────────────────────────
bool leer_registros(uint8_t addr, uint16_t reg_inicio, uint16_t cantidad,
                    uint16_t* valores, uint16_t* n_leidos) {
  *n_leidos = 0;

  // Trama de petición: [addr][0x03][reg_hi][reg_lo][cant_hi][cant_lo][crc_lo][crc_hi]
  uint8_t trama[8];
  trama[0] = addr;
  trama[1] = 0x03;
  trama[2] = (reg_inicio >> 8) & 0xFF;
  trama[3] = reg_inicio & 0xFF;
  trama[4] = (cantidad >> 8) & 0xFF;
  trama[5] = cantidad & 0xFF;
  uint16_t crc = crc16_modbus(trama, 6);
  trama[6] = crc & 0xFF;
  trama[7] = (crc >> 8) & 0xFF;

  digitalWrite(RS485_DIR_PIN, HIGH);  // transmitir
  modbus.write(trama, 8);
  modbus.flush();
  digitalWrite(RS485_DIR_PIN, LOW);   // recibir

  // Respuesta esperada: [addr][0x03][byte_count][data...][crc_lo][crc_hi]
  uint8_t byte_count = cantidad * 2;
  size_t esperado = 3 + byte_count + 2;
  uint8_t resp[3 + 54 + 2] = {0};  // máx. 27 registros → 54 bytes de datos
  unsigned long inicio = millis();
  size_t pos = 0;
  while (pos < esperado && (millis() - inicio) < TIMEOUT_MODBUS) {
    while (modbus.available() && pos < sizeof(resp)) {
      resp[pos++] = modbus.read();
    }
  }

  if (pos < esperado) return false;               // timeout / respuesta corta
  if (!trama_crc_valida(resp, pos)) return false; // CRC inválido

  // Verificar eco de dirección y función
  if (resp[0] != addr || resp[1] != 0x03) return false;

  for (uint16_t i = 0; i < cantidad; i++) {
    valores[i] = (resp[3 + i * 2] << 8) | resp[3 + i * 2 + 1];
  }
  *n_leidos = cantidad;
  return true;
}

int16_t a_entero_con_signo(uint16_t v) {
  return (v & 0x8000) ? (int16_t)(v - 0x10000) : (int16_t)v;
}

// ─────────────────────────── NTP / RTC ───────────────────────────
void sincronizar_hora() {
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);
  struct tm tiempo;
  if (getLocalTime(&tiempo, 10000)) {
    hora_sincronizada = true;
  }
}

String iso8601_actual() {
  struct tm t;
  if (getLocalTime(&t, 0)) {
    char buf[32];
    snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02d-05:00",
             t.tm_year + 1900, t.tm_mon + 1, t.tm_mday,
             t.tm_hour, t.tm_min, t.tm_sec);
    return String(buf);
  }
  return String("");  // sin hora: el backend usa su propio timestamp
}

// ─────────────────────────── Medición ───────────────────────────
struct Medicion {
  float ph, vwc, temperatura, ce_uscm, n, p, k;
  bool valida;
};

Medicion medir() {
  Medicion m = {0, 0, 0, 0, 0, 0, 0, false};

  uint16_t valores[REG_CANTIDAD] = {0};
  float suma_ph = 0, suma_vwc = 0, suma_t = 0, suma_ce = 0,
        suma_n = 0, suma_p = 0, suma_k = 0;
  int lecturas_ok = 0;

  for (int intento = 0; intento < MAX_REINTENTOS && lecturas_ok < LECTURAS_POR_PUNTO;
       intento++) {
    uint16_t n_leidos = 0;
    uint16_t buf[REG_CANTIDAD] = {0};
    if (!leer_registros(SENSOR_ADDR, REG_INICIO, REG_CANTIDAD, buf, &n_leidos)) {
      continue;  // CRC inválido o timeout: reintentar
    }
    // Índices dentro del bloque leído
    int iPH = REG_PH - REG_INICIO, iH = REG_HUMEDAD - REG_INICIO,
        iT = REG_TEMP - REG_INICIO, iCE = REG_CE - REG_INICIO,
        iN = REG_N - REG_INICIO, iP = REG_P - REG_INICIO, iK = REG_K - REG_INICIO;
    suma_ph  += buf[iPH] * 0.01f;
    suma_vwc += buf[iH] * 0.1f;
    suma_t   += a_entero_con_signo(buf[iT]) * 0.1f;
    suma_ce  += buf[iCE];
    suma_n   += buf[iN];
    suma_p   += buf[iP];
    suma_k   += buf[iK];
    lecturas_ok++;
    delay(150);  // tiempo de estabilización entre réplicas
  }

  if (lecturas_ok > 0) {
    m.ph = suma_ph / lecturas_ok;
    m.vwc = suma_vwc / lecturas_ok;
    m.temperatura = suma_t / lecturas_ok;
    m.ce_uscm = suma_ce / lecturas_ok;
    m.n = suma_n / lecturas_ok;
    m.p = suma_p / lecturas_ok;
    m.k = suma_k / lecturas_ok;
    m.valida = true;
  }
  return m;
}

// ─────────────────────────── Publicación ───────────────────────────
// En esta versión, el ESP32 publica la trama por Serial (o HTTP). El envío
// HTTP a la API (POST /api/v1/iot/sensor/raw) y el buffer offline con
// idempotencia se implementan sobre el mismo JSON de abajo.
#define HOSTNAME_APLICA "esp32-npk-001"  // reemplazar por el ID único del equipo

String serializar_trama(const Medicion& m) {
  String t = String("{\"device_id\":\"") + String(HOSTNAME_APLICA) +
             "\",\"firmware\":\"" + FW_VERSION +
             "\",\"msg_id\":" + String(msg_id++) +
             ",\"timestamp\":\"" + iso8601_actual() + "\"";
  if (m.valida) {
    t += ",\"ph\":" + String(m.ph, 2) +
         ",\"humedad\":" + String(m.vwc, 1) +
         ",\"temperatura_suelo\":" + String(m.temperatura, 1) +
         ",\"ce_uscm\":" + String(m.ce_uscm, 0) +
         ",\"nitrogeno\":" + String(m.n, 0) +
         ",\"fosforo\":" + String(m.p, 0) +
         ",\"potasio\":" + String(m.k, 0);
  }
  t += "}";
  return t;
}

// ─────────────────────────── Setup / Loop ───────────────────────────
void setup() {
  Serial.begin(115200);
  pinMode(RS485_DIR_PIN, OUTPUT);
  digitalWrite(RS485_DIR_PIN, LOW);

  modbus.begin(BAUDIOS, SERIAL_8N1, SERIAL_RX_PIN, SERIAL_TX_PIN);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long wifi_inicio = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - wifi_inicio) < 15000) {
    delay(500);
  }
  if (WiFi.status() == WL_CONNECTED) {
    sincronizar_hora();
  }
  // Sin WiFi: se sigue midiendo y el buffer offline conserva la idempotencia.
}

void loop() {
  Medicion m = medir();
  String trama = serializar_trama(m);
  Serial.println(trama);

  // TODO(campo): publicar por HTTP con reintentos y buffer offline.
  // El buffer guarda la trama con su msg_id; al reconectar, reenvía sin
  // duplicar (el backend es idempotente por msg_id).

  delay(15 * 60 * 1000UL);  // intervalo por defecto: 15 min (ajustable)
}
