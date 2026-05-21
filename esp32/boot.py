import network
import time
from machine import Pin

LED_PIN = 2
STA_SSID = "TU_SSID"
STA_PASSWORD = "TU_PASSWORD"
CONNECT_TIMEOUT_MS = 20000

led = Pin(LED_PIN, Pin.OUT)
wlan = network.WLAN(network.STA_IF)


def blink(times=3, period_ms=200):
    for _ in range(times):
        led.value(1)
        time.sleep_ms(period_ms)
        led.value(0)
        time.sleep_ms(period_ms)


def connect_wifi(ssid=STA_SSID, password=STA_PASSWORD, timeout_ms=CONNECT_TIMEOUT_MS):
    wlan.active(True)
    if wlan.isconnected():
        led.value(1)
        return wlan

    wlan.connect(ssid, password)
    start = time.ticks_ms()
    while not wlan.isconnected() and time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        led.value(1)
        time.sleep_ms(150)
        led.value(0)
        time.sleep_ms(150)

    if wlan.isconnected():
        led.value(1)
    else:
        led.value(0)
    return wlan


connect_wifi()
