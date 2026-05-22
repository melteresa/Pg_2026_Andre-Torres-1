"""
main.py - Servidor web y gestor de UART para ESP32
Levanta servidor en puerto 80, recibe comandos web y los envía al Arduino
"""

import uasyncio as asyncio
import time
from machine import Pin, UART

# ==================== CONFIGURACIÓN ====================
STATUS_LED_PIN = 2
UART_BAUD = 9600
UART_TX = 17          # GPIO17 -> RX del Arduino Nano
UART_RX = 16          # GPIO16 <- TX del Arduino Nano (opcional, para lectura)
COMMAND_TIMEOUT_MS = 800  # Timeout para envío automático de STOP

HOST = "0.0.0.0"
PORT = 80

# ==================== INICIALIZACIÓN ====================
led = Pin(STATUS_LED_PIN, Pin.OUT)
led.on()  # Encendido mientras corre

# UART: comunicación con Arduino Nano
uart = UART(2, baudrate=UART_BAUD, tx=Pin(UART_TX), rx=Pin(UART_RX), timeout=100)

# Variables de control
last_command_time = time.ticks_ms()
stop_sent = False

print("[MAIN] UART configurada: TX=GPIO17, RX=GPIO16, Baudrate=9600 bps")

# ==================== FUNCIONES AUXILIARES ====================
def validate_command(cmd):
    """Valida que el comando sea uno de los permitidos"""
    valid = ('F', 'B', 'L', 'R', 'U', 'D', 'S')
    return cmd.upper() in valid if len(cmd) == 1 else False

async def send_uart_command(cmd):
    """Envía comando al Arduino por UART"""
    global last_command_time, stop_sent
    
    if validate_command(cmd):
        cmd_upper = cmd.upper()
        uart.write(cmd_upper)
        print(f"[UART] Enviado: {cmd_upper}")
        last_command_time = time.ticks_ms()
        stop_sent = False
        return True
    return False

async def load_html_file():
    """Carga el HTML del archivo, fallback a HTML embebido"""
    try:
        with open('Index.html', 'r') as f:
            content = f.read()
            print("[HTML] Cargado desde Index.html")
            return content
    except OSError:
        print("[HTML] Index.html no encontrado, usando fallback")
        return get_fallback_html()

def get_fallback_html():
    """HTML fallback si el archivo no existe"""
    return """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control de Grúa</title>
    <style>
        body { background: #0a1929; color: #e8f4f8; font-family: Arial; margin: 0; }
        .container { max-width: 500px; margin: 20px auto; text-align: center; }
        h1 { color: #00a8e8; }
        .btn { padding: 15px 20px; margin: 5px; font-size: 16px; border: none; border-radius: 8px; 
               background: #0080d0; color: white; cursor: pointer; transition: 0.2s; }
        .btn:hover { background: #0098e8; }
        .btn.stop { background: #d42426; }
        .status { margin: 20px 0; padding: 10px; background: #1a4a6c; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ Control de Grúa</h1>
        <div class="status" id="status">Conectado</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <button class="btn" onclick="send('F')">⬆️ Adelante</button>
            <button class="btn" onclick="send('B')">⬇️ Atrás</button>
            <button class="btn" onclick="send('L')">⬅️ Izq</button>
            <button class="btn" onclick="send('R')">➡️ Der</button>
            <button class="btn" onclick="send('U')">⬆️ Subir</button>
            <button class="btn" onclick="send('D')">⬇️ Bajar</button>
            <button class="btn stop" onclick="send('S')" style="grid-column: 1/-1;">🛑 STOP</button>
        </div>
    </div>
    <script>
        async function send(cmd) {
            try {
                const res = await fetch('/command', { method: 'POST', body: cmd });
                if (res.ok) document.getElementById('status').textContent = 'Comando: ' + cmd;
            } catch (e) { document.getElementById('status').textContent = 'Error'; }
        }
    </script>
</body>
</html>"""

# ==================== SERVIDOR HTTP ====================
async def handle_client(reader, writer):
    """Maneja solicitudes HTTP"""
    try:
        request_line = await reader.readline()
        if not request_line:
            await writer.aclose()
            return
        
        request = request_line.decode('utf-8').strip()
        print(f"[HTTP] {request}")
        
        # Parsear ruta y método
        parts = request.split(' ')
        method = parts[0]
        path = parts[1] if len(parts) > 1 else '/'
        
        # Leer headers
        while True:
            header = await reader.readline()
            if not header or header == b'\r\n':
                break
        
        # Leer body si es POST
        body = b''
        if method == 'POST':
            while True:
                chunk = await reader.read(1)
                if not chunk:
                    break
                body += chunk
        
        # ========== RUTAS ==========
        
        # GET / -> Servir HTML
        if path == '/' and method == 'GET':
            html = await load_html_file()
            response = f"""HTTP/1.0 200 OK\r
Content-Type: text/html; charset=utf-8\r
Content-Length: {len(html)}\r
Connection: close\r
\r
{html}"""
            writer.write(response.encode())
            await writer.drain()
            await writer.aclose()
            return
        
        # POST /command -> Recibir comando
        if path == '/command' and method == 'POST':
            cmd = body.decode('utf-8').strip()
            
            if await send_uart_command(cmd):
                response_body = '{"status":"ok","command":"' + cmd.upper() + '"}'
                response = f"""HTTP/1.0 200 OK\r
Content-Type: application/json\r
Content-Length: {len(response_body)}\r
Connection: close\r
\r
{response_body}"""
            else:
                response_body = '{"status":"error","message":"Comando inválido"}'
                response = f"""HTTP/1.0 400 Bad Request\r
Content-Type: application/json\r
Content-Length: {len(response_body)}\r
Connection: close\r
\r
{response_body}"""
            
            writer.write(response.encode())
            await writer.drain()
            await writer.aclose()
            return
        
        # 404
        response_body = '<h1>404 No encontrado</h1>'
        response = f"""HTTP/1.0 404 Not Found\r
Content-Type: text/html\r
Content-Length: {len(response_body)}\r
Connection: close\r
\r
{response_body}"""
        writer.write(response.encode())
        await writer.drain()
        await writer.aclose()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        await writer.aclose()

# ==================== WATCHDOG ====================
async def watchdog():
    """
    Monitorea timeout: envía STOP automático si no hay comandos
    Útil para seguridad en caso de desconexión web
    """
    global stop_sent
    
    while True:
        await asyncio.sleep_ms(300)
        elapsed = time.ticks_diff(time.ticks_ms(), last_command_time)
        
        if elapsed > COMMAND_TIMEOUT_MS and not stop_sent:
            uart.write('S')
            print("[WATCHDOG] STOP automático (timeout)")
            stop_sent = True

# ==================== MAIN ====================
async def main():
    """Corre el servidor web y el watchdog"""
    print("\n" + "="*50)
    print("🏗️  SERVIDOR ESP32 - CONTROL DE GRÚA")
    print("="*50)
    print(f"[HTTP] Servidor iniciado en http://0.0.0.0:{PORT}")
    print(f"[UART] Escuchando comandos en GPIO17 @ {UART_BAUD} bps")
    print("="*50 + "\n")
    
    # Inicia servidor
    server = await asyncio.start_server(handle_client, HOST, PORT)
    
    # Inicia watchdog
    asyncio.create_task(watchdog())
    
    # Espera indefinidamente
    await server.wait_closed()

# ==================== INICIO ====================
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n[MAIN] Servidor detenido por usuario")
    led.off()
except Exception as e:
    print(f"[ERROR] {e}")
    led.off()

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
