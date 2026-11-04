"""Pruebas de decodificación Modbus del JXBS-3001-NPK-RS (TT-01/02/03)."""

from agroia_backend.services.decodificacion_modbus import (
    a_entero_con_signo,
    construir_trama,
    crc16_modbus,
    decodificar_para_sensor,
    decodificar_registros,
    verificar_crc_trama,
    verificar_variante,
)


# ───────────────────────── TT-01 · Decodificación ─────────────────────────

class TestEnteroConSigno:
    def test_temperatura_positiva(self):
        # 0x00EB = 235 → 23,5 °C
        assert a_entero_con_signo(0x00EB) == 235

    def test_temperatura_negativa(self):
        # 0xFF9B = -101 → -10,1 °C (complemento a dos)
        assert a_entero_con_signo(0xFF9B) == -101

    def test_limite_cero(self):
        assert a_entero_con_signo(0x0000) == 0


class TestDecodificarRegistros:
    def test_trama_completa(self):
        deco = decodificar_registros({
            0x0006: 514,     # pH 5,14
            0x0012: 253,     # 25,3 % VWC
            0x0013: 0x00EB,  # 23,5 °C
            0x0015: 420,     # 420 µS/cm
            0x001E: 30,
            0x001F: 8,
            0x0020: 90,
        })
        assert deco["ph"]["valor_escalado"] == 5.14
        assert deco["humedad"]["valor_escalado"] == 25.3
        assert deco["temperatura_suelo"]["valor_escalado"] == 23.5
        assert deco["ce_uscm"]["valor_escalado"] == 420.0
        assert deco["nitrogeno"]["valor_escalado"] == 30.0
        assert deco["fosforo"]["valor_escalado"] == 8.0
        assert deco["potasio"]["valor_escalado"] == 90.0

    def test_temperatura_negativa_escala(self):
        deco = decodificar_registros({0x0013: 0xFF9B})
        assert deco["temperatura_suelo"]["valor_escalado"] == -10.1

    def test_claves_en_texto_hex(self):
        deco = decodificar_registros({"0x0006": 710, "6": 700})
        # "0x0006" y "6" son la misma clave: la última pisará a la primera
        assert deco["ph"]["valor_crudo"] == 700

    def test_registro_desconocido_ignorado(self):
        deco = decodificar_registros({0x9999: 123})
        assert deco == {}


class TestDecodificarParaSensor:
    def test_payload_canonico_y_valor_crudo(self):
        payload = decodificar_para_sensor({
            0x0006: 514, 0x0012: 253, 0x0013: 0x00EB,
            0x0015: 420, 0x001E: 30, 0x001F: 8, 0x0020: 90,
        })
        assert payload["ph"] == 5.14
        assert payload["humedad"] == 25.3           # VWC, no "HR"
        assert payload["temperatura_suelo"] == 23.5
        assert payload["conductividad_electrica"] == 0.42  # µS/cm → dS/m
        assert payload["nitrogeno"] == 30.0
        assert payload["fosforo"] == 8.0
        assert payload["potasio"] == 90.0
        assert payload["valor_crudo"]["0x0006"] == 514
        assert payload["valor_crudo"]["0x0013"] == 0x00EB


# ───────────────────────── TT-02 · CRC-16 Modbus ─────────────────────────

class TestCrc16Modbus:
    def test_vector_conocido(self):
        # Vector publicado: 01 03 00 00 00 0A → CRC 0xCDC5 (lo=C5, hi=CD)
        crc = crc16_modbus(bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x0A]))
        assert crc == 0xCDC5

    def test_construir_y_verificar_trama(self):
        trama = construir_trama(1, 0x0006, 0x001B)
        assert verificar_crc_trama(trama) is True
        # 8 bytes: 6 de petición + 2 de CRC
        assert len(trama) == 8

    def test_trama_corrupta_detectada(self):
        trama = bytearray(construir_trama(1, 0x0006, 0x001B))
        trama[3] ^= 0xFF  # corromper el registro
        assert verificar_crc_trama(bytes(trama)) is False

    def test_trama_corta_rechazada(self):
        assert verificar_crc_trama(bytes([0x01, 0x03])) is False


# ───────────────────────── TT-03 · Prueba de variante ─────────────────────────

class TestVerificarVariante:
    def test_aceptada_con_las_cinco_variables(self):
        resultado = verificar_variante({
            0x0006: 514, 0x0015: 420, 0x001E: 30, 0x001F: 8, 0x0020: 90,
        })
        assert resultado["aceptado"] is True
        assert resultado["variables_faltantes"] == []

    def test_rechazada_si_falta_npk(self):
        resultado = verificar_variante({0x0006: 514, 0x0015: 420})
        assert resultado["aceptado"] is False
        assert set(resultado["variables_faltantes"]) == {
            "nitrogeno", "fosforo", "potasio",
        }

    def test_rechazada_sin_registros(self):
        resultado = verificar_variante({})
        assert resultado["aceptado"] is False
