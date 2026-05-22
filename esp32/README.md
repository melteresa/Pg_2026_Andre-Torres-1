# 🏗️ ESP32 - Control de Grúa

## 📋 Instrucciones de instalación

### 1. **Preparar el ESP32**

- Instala **MicroPython** en tu ESP32 DevKit V1
- Descarga desde: https://micropython.org/download/esp32/
- Usa **Thonny IDE** o **esptool.py** para flashear

### 2. **Copiar archivos**

Sube estos archivos al ESP32 usando Thonny o WebREPL:

```
boot.py      → raíz del ESP32
main.py      → raíz del ESP32
Index.html   → raíz del ESP32 (opcional, puede ir embebido)
```

### 3. **Configurar WiFi**

Edita `boot.py` y reemplaza:

```python
STA_SSID = "TU_RED_WIFI"        # ← Tu red WiFi
STA_PASSWORD = "TU_CONTRASEÑA"  # ← Tu contraseña
```

### 4. **Hardware**

**UART Configuration:**
- GPIO17 (TX) → RX del Arduino Nano
- GPIO16 (RX) ← TX del Arduino Nano (opcional para recibir)
- Baudrate: **9600 bps**

**LED de estado:**
- GPIO2 → LED (parpadea durante boot)

### 5. **Iniciar**

1. Reinicia el ESP32 (botón RESET)
2. Espera 10-15 segundos a que se conecte
3. Abre navegador: `http://[IP_DEL_ESP32]`
4. Los botones estarán activos cuando el servidor esté listo

---

## 📡 Protocolo UART

El ESP32 envía comandos al Arduino como **caracteres individuales**:

| Comando | Función |
|---------|---------|
| `F` | Forward (Adelante) |
| `B` | Backward (Atrás) |
| `L` | Left (Izquierda) |
| `R` | Right (Derecha) |
| `U` | Up (Subir) |
| `D` | Down (Bajar) |
| `S` | Stop (Parar) |

**Timeout automático:** Si no recibe comandos en 800ms, envía `S` automáticamente

---

## 🔍 Troubleshooting

| Problema | Solución |
|----------|----------|
| No se conecta a WiFi | Verifica SSID/PASSWORD en boot.py |
| Web no carga | Abre consola Thonny, revisa logs de error |
| No envía comandos al Arduino | Verifica GPIO17 conectado a RX del Arduino |
| Botones no responden | Recarga la página web (F5) |

---

## 📝 Logs esperados

```
==================================================
🏗️  BOOT ESP32 - CONTROL DE GRÚA
==================================================
[WIFI] Conectando a mi_red...
[WIFI] ✅ Conectado a WiFi
[WIFI] IP: 192.168.1.100

==================================================
🏗️  SERVIDOR ESP32 - CONTROL DE GRÚA
==================================================
[HTTP] Servidor iniciado en http://0.0.0.0:80
[UART] Escuchando comandos en GPIO17 @ 9600 bps
==================================================

[HTML] Cargado desde Index.html
[HTTP] GET /
[HTTP] POST /command
[UART] Enviado: F
```

---

## 🚀 Próximos pasos

Después de verificar que el ESP32 funciona:
1. Implementa `grua_arduino.ino` en el Arduino Nano
2. Carga la interfaz `Index.html` en la carpeta raíz del ESP32
3. Prueba comandos desde el navegador
