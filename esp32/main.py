import uasyncio as asyncio
import time
from machine import Pin, UART

STATUS_LED_PIN = 2
UART_BAUD = 9600
COMMAND_TIMEOUT_MS = 500
HOST = "0.0.0.0"
PORT = 80

led = Pin(STATUS_LED_PIN, Pin.OUT)
led.value(1)

uart = UART(2, baudrate=UART_BAUD, tx=Pin(17), rx=Pin(16))
last_command_ms = time.ticks_ms()
stop_sent = False

INDEX_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Control Remoto de la Grua</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; display: flex; flex-direction: column; min-height: 100vh; }
    header { padding: 18px 16px; text-align: center; background: #111827; box-shadow: 0 2px 12px rgba(0,0,0,.25); }
    h1 { margin: 0; font-size: 1.5rem; }
    .status { font-size: 0.95rem; margin-top: 6px; color: #93c5fd; }
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; padding: 20px; width: min(100%, 520px); margin: 0 auto; }
    .control-btn { border: none; border-radius: 16px; padding: 22px 10px; font-size: 1.05rem; font-weight: 700; color: #fff; background: linear-gradient(135deg,#2563eb,#7dd3fc); box-shadow: 0 10px 20px rgba(0,0,0,.25); cursor: pointer; transition: transform .15s ease, filter .15s ease; }
    .control-btn:active { transform: scale(0.97); filter: brightness(1.05); }
    .control-btn.stop { background: #dc2626; }
    .wide { grid-column: span 2; }
    footer { margin-top: auto; padding: 16px; text-align: center; font-size: 0.9rem; color: #94a3b8; }
  </style>
</head>
<body>
  <header>
    <h1>Panel de Control de Grua</h1>
    <div class="status" id="status">Estado: listo</div>
  </header>

  <main class="grid">
    <button class="control-btn" onclick="sendCommand('F')">Adelante</button>
    <button class="control-btn" onclick="sendCommand('B')">Atrás</button>
    <button class="control-btn" onclick="sendCommand('L')">Izquierda</button>
    <button class="control-btn" onclick="sendCommand('R')">Derecha</button>
    <button class="control-btn" onclick="sendCommand('U')">Subir</button>
    <button class="control-btn" onclick="sendCommand('D')">Bajar</button>
    <button class="control-btn stop wide" onclick="sendCommand('S')">Parar</button>
  </main>

  <footer>Usa el servidor web para enviar comandos UART de forma segura.</footer>

  <script>
    async function sendCommand(command) {
      try {
        const response = await fetch(`/cmd?m=${command}`);
        if (!response.ok) throw new Error('Error de red');
        document.getElementById('status').textContent = `Último comando: ${command}`;
      } catch (error) {
        document.getElementById('status').textContent = 'Error de conexión';
      }
    }
  </script>
</body>
</html>
"""


def get_index_html():
    try:
        with open('Index.html', 'r') as page:
            return page.read()
    except OSError:
        return INDEX_HTML


async def send_serial_command(cmd):
    global last_command_ms, stop_sent
    uart.write(cmd)
    last_command_ms = time.ticks_ms()
    stop_sent = False


async def handle_client(reader, writer):
    request_line = await reader.readline()
    if not request_line:
        await writer.aclose()
        return

    request = request_line.decode('utf-8')
    path = request.split(' ')[1]

    while True:
        header = await reader.readline()
        if not header or header == b'\r\n':
            break

    if path == '/':
        body = get_index_html()
        response = 'HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}'.format(len(body), body)
        writer.write(response.encode('utf-8'))
        await writer.drain()
        await writer.aclose()
        return

    if path.startswith('/cmd'):
        command = None
        if 'm=' in path:
            command = path.split('m=')[1].split('&')[0][:1].upper()

        if command in ('F', 'B', 'L', 'R', 'U', 'D', 'S'):
            await send_serial_command(command)
            body = '{{"status":"ok","command":"{}"}}'.format(command)
            response = 'HTTP/1.0 200 OK\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}'.format(len(body), body)
        else:
            body = '{{"status":"error","message":"Comando inválido"}}'
            response = 'HTTP/1.0 400 Bad Request\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}'.format(len(body), body)

        writer.write(response.encode('utf-8'))
        await writer.drain()
        await writer.aclose()
        return

    body = '<h1>404 No encontrado</h1>'
    response = 'HTTP/1.0 404 Not Found\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}'.format(len(body), body)
    writer.write(response.encode('utf-8'))
    await writer.drain()
    await writer.aclose()


async def watchdog():
    global stop_sent
    while True:
        await asyncio.sleep_ms(200)
        elapsed = time.ticks_diff(time.ticks_ms(), last_command_ms)
        if elapsed > COMMAND_TIMEOUT_MS and not stop_sent:
            uart.write('S')
            stop_sent = True


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    print('Servidor activo en http://{}:{}'.format(HOST, PORT))
    asyncio.create_task(watchdog())
    await server.wait_closed()


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
