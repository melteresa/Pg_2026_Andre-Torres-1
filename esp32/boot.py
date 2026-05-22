"""
boot.py - Configuración inicial del ESP32
Se ejecuta al iniciar, configura WiFi y el entorno
"""

import network
import time
from machine import Pin

# ==================== CONFIGURACIÓN ====================
STA_SSID = "TU_RED_WIFI"           # ⚠️ Cambia esto
STA_PASSWORD = "TU_CONTRASEÑA"     # ⚠️ Cambia esto
AP_SSID = "Grua_Control"
AP_PASSWORD = "12345678"
CONNECT_TIMEOUT_MS = 15000

# ==================== LED DE ESTADO ====================
LED_STATUS = Pin(2, Pin.OUT)
LED_STATUS.off()

def blink_led(times=1, duration_ms=300):
    """Parpadea el LED para indicar estado"""
    for _ in range(times):
        LED_STATUS.on()
        time.sleep_ms(duration_ms)
        LED_STATUS.off()
        time.sleep_ms(duration_ms)

# ==================== CONEXIÓN WIFI ====================
def connect_wifi():
    """Intenta conectar a WiFi en modo Station"""
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    if not sta.isconnected():
        print(f"[WIFI] Conectando a {STA_SSID}...")
        sta.connect(STA_SSID, STA_PASSWORD)
        
        start = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > CONNECT_TIMEOUT_MS:
                print("[WIFI] ❌ Timeout de conexión")
                return False
            
            LED_STATUS.toggle()
            time.sleep_ms(300)
    
    if sta.isconnected():
        LED_STATUS.on()
        print("[WIFI] ✅ Conectado a WiFi")
        print(f"[WIFI] IP: {sta.ifconfig()[0]}")
        blink_led(3, 200)
        return True
    
    return False

def setup_ap():
    """Configura Punto de Acceso si WiFi falla"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASSWORD)
    print(f"[AP] Punto de acceso creado: {AP_SSID}")
    print(f"[AP] IP: {ap.ifconfig()[0]}")

# ==================== INICIO ====================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🏗️  BOOT ESP32 - CONTROL DE GRÚA")
    print("="*50)
    
    # Intenta WiFi, si falla crea AP
    if not connect_wifi():
        setup_ap()
    
    print("\n[BOOT] Iniciando main.py...")
    print("="*50 + "\n")
