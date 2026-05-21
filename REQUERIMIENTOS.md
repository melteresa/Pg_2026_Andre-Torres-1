# Requerimientos del Programa

## 1. Objetivo

Desarrollar un sistema de control doble para una grúa pequeña donde un Arduino Nano gobierna los motores y un ESP32 provee una interfaz web remota.

## 2. Arquitectura y hardware

### Controlador A: Arduino Nano
- Rol: Actuador principal y procesador de señales de joystick
- Pines analógicos:
  - Joystick Carro (X): A0
  - Joystick Elevación (Y): A1
  - Joystick Giro: A2
- Driver TB6612FNG para motores DC N20:
  - Motor A (Carro): AIN1 -> D2, AIN2 -> D4, PWMA -> D3
  - Motor B (Elevación): BIN1 -> D7, BIN2 -> D8, PWMB -> D5
  - STBY: VCC 5V
- Driver DRV8825 para motor paso a paso Nema 17:
  - STEP -> D9
  - DIR -> D10
- Comunicación UART:
  - RX del Nano: D0 (conectado al TX del ESP32)

### Controlador B: ESP32 DevKit V1
- Rol: Interfaz web y transmisor de comandos hacia el Arduino
- Pines:
  - UART TX: GPIO 17 (a RX del Nano)
  - LED de estado: GPIO 2
- Comunicación:
  - UART a 9600 bps
  - WiFi para servir la interfaz web

## 3. Requerimientos funcionales

### Arduino Nano
- Implementar en `grua_arduino.ino`
- Leer joysticks analógicos en A0, A1, A2
- Controlar motores DC con TB6612FNG usando PWM
- Controlar motor paso a paso DRV8825 con velocidad suave
- Parsear comandos UART de un solo carácter:
  - `F`: Adelante
  - `B`: Atrás
  - `U`: Subir
  - `D`: Bajar
  - `L`: Giro izquierda
  - `R`: Giro derecha
  - `S`: Stop
- Combinar la intención del joystick y la intención de la web en la lógica de movimiento
- Detener automáticamente los motores si no se recibe un comando `S` o no hay actualizaciones durante el timeout

### ESP32 DevKit V1
- Implementar en `esp32/boot.py` y `esp32/main.py`
- Conexión WiFi estable y configurable
- Servidor web asíncrono con `uasyncio`
- Servir la interfaz de control en `/`
- Recibir eventos web y enviar comandos UART al Arduino:
  - `F`, `B`, `L`, `R`, `U`, `D`, `S`
- Controlar y encender `LED_STATUS` según estado del sistema
- Incluir watchdog o timeout que envíe comando `S` si no recibe comandos continuos

### Interfaz Web
- Archivo: `esp32/Index.html` o HTML embebido en `main.py`
- Botones grandes y responsivos para móvil
- Minimalista, colores oscuros y texto claro
- Uso de JavaScript `fetch` para peticiones AJAX sin recargar la página
- Feedback visual del último comando enviado

## 4. Requerimientos no funcionales

- Baudrate uniforme: 9600 bps en Arduino y ESP32
- Código MicroPython compatible con Thonny y ESP32
- Código Arduino compatible con IDE Arduino y `AccelStepper`
- Seguridad:
  - Timeout de parada automática
  - Comandos web válidos sólo para los 7 caracteres definidos
- Rendimiento:
  - Servidor web rápido para comandos en tiempo real
  - Motor paso a paso con movimiento suave y no bloqueante

## 5. Archivos y estructura

- `grua_arduino.ino`
- `esp32/boot.py`
- `esp32/main.py`
- `esp32/Index.html`

## 6. Configuración requerida

- Completar `STA_SSID` y `STA_PASSWORD` en `esp32/boot.py`
- Verificar cableado UART entre ESP32 y Nano
- Asegurar alimentación correcta para motores N20 y Nema 17
- Instalar biblioteca `AccelStepper` en Arduino IDE

## 7. Validación

- Probar conexión WiFi en ESP32
- Acceder al servidor web desde un navegador
- Verificar que cada botón web envía el comando correcto
- Confirmar recepción de comandos en Arduino Nano
- Validar que el timeout envía `S` y detiene los motores
