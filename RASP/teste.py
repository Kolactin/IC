from machine import ADC, Pin, PWM
import time

# --- Configuração de Entrada Analógica ---
# Pino ADC(0) mapeado para GP26. Este será a entrada (e.g., Potenciômetro)
SENSOR_PIN = 26
sensor_analogico = ADC(SENSOR_PIN)

# --- Configuração de Saída PWM (para o LED) ---
# Pino digital GP15 para o LED
LED_PIN = 15
led_pwm = PWM(Pin(LED_PIN))

# Configura a frequência do PWM (pode ser ajustada, 1000 Hz é um bom padrão)
led_pwm.freq(1000)

# O PWM do Pico utiliza valores de duty cycle de 0 a 65535 (16 bits)
# A leitura do ADC também é de 16 bits (0 a 65535)
# Portanto, a conversão é direta, pois ambas as escalas coincidem.

print(f"--- Dimmer Analógico Iniciado ---")
print(f"Leitura de Potenciômetro em GP{SENSOR_PIN} (ADC0)")
print(f"Controle de Brilho do LED em GP{LED_PIN} (PWM)")
print("Gire o potenciômetro para variar o brilho do LED!")

# --- Loop Principal ---
while True:
    # 1. Realiza a leitura do ADC (valor de 0 a 65535)
    leitura_bruta = sensor_analogico.read_u16()

    # 2. Converte a leitura para Tensão (apenas para exibição no console)
    CONVERSAO_FATOR = 3.3 / 65535
    tensao = leitura_bruta * CONVERSAO_FATOR

    # 3. Define o ciclo de trabalho (duty cycle) do PWM com o valor da leitura.
    # O valor lido (0-65535) é diretamente usado no PWM (0-65535).
    led_pwm.duty_u16(leitura_bruta)

    # 4. Imprime os dados para monitoramento
    print(
        f"ADC Bruto: {leitura_bruta:5d} | Tensão: {tensao:.2f}V | PWM Duty: {leitura_bruta:5d}"
    )

    # Pequena pausa para não sobrecarregar a porta serial
    time.sleep(0.05)