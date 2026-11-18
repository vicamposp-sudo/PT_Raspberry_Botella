import RPi as GPIO
import time
from picamera import PiCamera

# --- CONFIGURACIÓN DE PINES (GPIO / BCM) ---
TRIG_ENTRADA = 17
ECHO_ENTRADA = 27

TRIG_LLENADO = 22
ECHO_LLENADO = 23

SERVO_PIN = 18

LED_VERDE = 16
LED_ROJO = 20

# --- INICIALIZACIÓN GPIO ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(TRIG_ENTRADA, GPIO.OUT)
GPIO.setup(ECHO_ENTRADA, GPIO.IN)
GPIO.setup(TRIG_LLENADO, GPIO.OUT)
GPIO.setup(ECHO_LLENADO, GPIO.IN)

GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_ROJO, GPIO.OUT)

GPIO.setup(SERVO_PIN, GPIO.OUT)

# Configurar PWM para el Servo (50Hz)
pwm_servo = GPIO.PWM(SERVO_PIN, 50)
pwm_servo.start(0)

# Inicializar Cámara
camera = PiCamera()

# --- FUNCIONES AUXILIARES ---

def medir_distancia(trig_pin, echo_pin):
    """ Mide la distancia en cm usando un sensor ultrasónico HC-SR04 """
    GPIO.output(trig_pin, True)
    time.sleep(0.00001)
    GPIO.output(trig_pin, False)

    inicio = time.time()
    fin = time.time()

    while GPIO.input(echo_pin) == 0:
        inicio = time.time()

    while GPIO.input(echo_pin) == 1:
        fin = time.time()

    duracion = fin - inicio
    distancia = (duracion * 34300) / 2
    return distancia

def mover_servo(angulo):
    """ Cambia la posición del servomotor según el ángulo deseado (0° a 180°) """
    duty_cycle = 2 + (angulo / 18)
    GPIO.output(SERVO_PIN, True)
    pwm_servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    pwm_servo.ChangeDutyCycle(0)

def capturar_imagen(ruta_destino="captura.jpg"):
    """ Toma una foto con la cámara Pi """
    camera.resolution = (1024, 768)
    camera.capture(ruta_destino)
    print(f"[CAM] Foto capturada: {ruta_destino}")

def clasificar_objeto(ruta_imagen):
    """
    Simulación del motor de inferencia/clasificación.
    Reemplazar por modelo de Visión Computacional (OpenCV / TensorFlow Lite).
    Retorna True si es PET Aceptado, False si es Rechazado.
    """
    print("[IA] Analizando características de la botella...")
    time.sleep(1) # Simulación de tiempo de procesamiento
    es_pet_valida = True  # Modificar con la lógica real de detección
    return es_pet_valida

# --- BUCLE PRINCIPAL ---
try:
    print("Sistema Clasificador IoT Iniciado...")
    mover_servo(90) # Servo en posición neutral

    while True:
        # 1. Comprobar Nivel de Llenado del Depósito
        distancia_deposito = medir_distancia(TRIG_LLENADO, ECHO_LLENADO)
        
        if distancia_deposito < 5.0:  # Si está a menos de 5cm, el contenedor está lleno
            print("[ALERTA] Depósito de reciclaje LLENO. Vacíe el contenedor.")
            GPIO.output(LED_ROJO, True)
            GPIO.output(LED_VERDE, False)
            time.sleep(2)
            continue

        GPIO.output(LED_ROJO, False)

        # 2. Detección de ingreso de objeto
        distancia_entrada = medir_distancia(TRIG_ENTRADA, ECHO_ENTRADA)
        
        if distancia_entrada < 15.0: # Objeto detectado en la rampa/entrada
            print("\n[INFO] Objeto detectado. Procesando ciclo...")
            
            # Tomar foto
            nombre_foto = f"botella_{int(time.time())}.jpg"
            capturar_imagen(nombre_foto)

            # Clasificar objeto
            resultado = clasificar_objeto(nombre_foto)

            if resultado:
                print("[RESULTADO] -> BOTELA PET ACEPTADA")
                GPIO.output(LED_VERDE, True)
                mover_servo(45)  # Mover servo hacia compuerta Aceptados
            else:
                print("[RESULTADO] -> MATERIAL RECHAZADO")
                GPIO.output(LED_ROJO, True)
                mover_servo(135) # Mover servo hacia compuerta Rechazos

            time.sleep(2)

            # Restablecer actuadores
            GPIO.output(LED_VERDE, False)
            GPIO.output(LED_ROJO, False)
            mover_servo(90) # Volver a estado neutral
            
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n[STOP] Limpiando configuración GPIO y saliendo...")
    pwm_servo.stop()
    GPIO.cleanup()