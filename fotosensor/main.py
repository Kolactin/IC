import machine
import time
import network
import socket

# --- CONFIGURAÇÃO WI-FI ---
SSID = "FE EM DEUS  2.4G" 
PASSWORD = "DEUS1000"

# --- CONFIGURAÇÃO HARDWARE ---
adc = machine.ADC(26)

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    for _ in range(20):
        if wlan.isconnected(): return wlan.ifconfig()[0]
        time.sleep(1)
    return None

def enviar_pagina(cliente, valor_v):
    resistor = 10000
    potencia = (valor_v / resistor) * 1000 

    parte1 = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <title>LABSOLAR - monitoramento</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: sans-serif; text-align: center; background: #121212; color: white; padding: 10px; }}
        .box {{ background: #1e1e1e; max-width: 800px; margin: auto; padding: 20px; border-radius: 15px; border: 1px solid #333; }}
        .v-container {{ display: flex; justify-content: space-around; margin-bottom: 15px; }}
        .v-grande {{ font-size: 35px; color: #f1c40f; font-weight: bold; }}
        .unidade {{ font-size: 15px; color: #aaa; }}
        .slider-container {{ margin: 20px 0; padding: 10px; background: #2a2a2a; border-radius: 10px; }}
        input[type=range] {{ width: 90%; accent-color: #f1c40f; }}
        canvas {{ margin-top: 20px; }}
    </style></head><body>
    <div class="box">
        <h1>Monitoramento remoto LABSOLAR-UFBAh1>
        <div class="v-container">
            <div><small>TENSÃO</small><div class="v-grande">{valor_v:.3f}V</div></div>
            <div><small>POTÊNCIA ATUAL</small><div class="v-grande">{potencia:.3f}<span class="unidade"> kW/m²</span></div></div>
        </div>
    """

    parte2 = """
        <div class="slider-container">
            <label id="labelSlider">Navegar no histórico</label><br>
            <input type="range" id="timeSlider" min="0" max="0" value="0" oninput="navegar(this.value)">
        </div>
        <canvas id="graficoCorrente"></canvas>
    </div>
    """

    parte3 = f"""
    <script>
        const DADO_V = {valor_v};
        const DADO_P = {potencia};
        const HORA = new Date().toLocaleTimeString();
        
        let historico = JSON.parse(localStorage.getItem('labsolar_pot')) || [];
        historico.push({{ v: DADO_V, p: DADO_P, t: HORA }});
        if(historico.length > 500) historico.shift();
        localStorage.setItem('labsolar_pot', JSON.stringify(historico));

        const ctxP = document.getElementById('graficoCorrente').getContext('2d');
        let chartP = new Chart(ctxP, {{
            type: 'line',
            data: {{ labels: [], datasets: [{{
                label: 'Corrente (mA)', data: [],
                borderColor: '#f1c40f', backgroundColor: 'rgba(241, 196, 15, 0.1)',
                fill: true, tension: 0.3
            }}] }},
            options: {{ 
                animation: false,
                scales: {{ y: {{ min: 0, max: 1.5, title: {{ display: true, text: 'kW/m²', color: '#aaa' }} }} }}
            }}
        }});

        function navegar(pos) {{
            pos = parseInt(pos);
            const jan = 20;
            const slider = document.getElementById('timeSlider');
            
            const estaNoPassado = pos < parseInt(slider.max);
            localStorage.setItem('pausado', estaNoPassado ? 'true' : '');

            const dadosExibir = historico.slice(pos, pos + jan);
            chartP.data.labels = dadosExibir.map(i => i.t);
            chartP.data.datasets[0].data = dadosExibir.map(i => i.p);
            chartP.update('none');
            document.getElementById('labelSlider').innerText = estaNoPassado ? "MODO HISTÓRICO" : "AO VIVO";
        }}

        const slider = document.getElementById('timeSlider');
        if(historico.length > 20) {{
            slider.max = historico.length - 20;
            slider.value = slider.max;
        }}
        navegar(slider.value);

        setInterval(() => {{
            if(!localStorage.getItem('pausado')) location.reload();
        }}, 5000);
    </script></body></html>
    """
    
    cliente.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n')
    cliente.send(parte1)
    cliente.send(parte2)
    cliente.send(parte3)

# --- SERVIDOR ---
ip = conectar_wifi()
if ip:
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 80))
    s.listen(1)
    while True:
        try:
            cl, addr = s.accept()
            cl.recv(1024)
            v = adc.read_u16() * (1 / 65535) - 0.015
            enviar_pagina(cl, v)
            cl.close()
        except:
            if 'cl' in locals(): cl.close()