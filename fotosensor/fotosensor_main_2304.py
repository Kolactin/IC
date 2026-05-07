import machine
import time
import network
import socket

wlan = network.WLAN(network.STA_IF)

'''
# --- Escaneando redes ---
redes = wlan.scan()
for rede in redes:
    print(f"Rede encontrada: {rede[0].decode('utf-8')}")
'''
    
# --- CONFIGURAÇÃO WI-FI ---
SSID = "Kolactin_2.4" 
PASSWORD = "@AJA2678"

# --- CONFIGURAÇÃO HARDWARE ---
adc = machine.ADC(26)

def conectar_wifi():
    wlan.active(True)
    print("Tentando conectar...")
    wlan.connect(SSID, PASSWORD)
    for _ in range(20):
        if wlan.isconnected(): return wlan.ifconfig()[0]
        time.sleep(1)
    return None

def enviar_pagina(cliente, valor_v):
    resistor = 100000
    corrente = 1000 * (valor_v / resistor)
    irradiancia = (corrente / 1000) / ((0.45) * (5.23*(10**-6)))
    '''
        I(W / m²) = corrente(A) / responsividade(A/W) * área do sensor(m²)

    ''' 
    parte1 = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <title>MONITORAMENTO - LABSOLAR</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: sans-serif; text-align: center; background: #121212; color: white; margin: 0; padding: 10px; }}
        .box {{ background: #1e1e1e; max-width: 900px; margin: auto; padding: 15px; border-radius: 15px; border: 1px solid #333; }}
        .v-container {{ display: flex; justify-content: space-around; margin-bottom: 10px; }}
        .card {{ background: #252525; padding: 10px; border-radius: 10px; min-width: 150px; border-bottom: 3px solid #00d4ff; }}
        .card.solar {{ border-bottom: 3px solid #f1c40f; }}
        .card.IV {{ border-bottom: 3px solid #9e1313; }}
        .v-grande {{ font-size: 30px; font-weight: bold; }}
        .v-v {{ color: #00d4ff; }} .v-p {{ color: #f1c40f; }} .v-i {{ color: #9e1313; }}
        
        // SLIDER
        .slider-container {{ margin: 20px 0; padding: 10px; background: #2a2a2a; border-radius: 10px; }}
        input[type=range] {{ width: 90%; accent-color: #29B01C; }}
        
        .grid-graficos {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }}
        @media (max-width: 600px) {{ .grid-graficos {{ grid-template-columns: 1fr; }} }}
        canvas {{ background: #1a1a1a; border-radius: 5px; padding: 5px; }}
    </style></head><body>
    <div class="box">
        <h1>MONITORAMENTO: LABSOLAR - UFBA</h1>
        <div class="v-container">
            <div class="card">
                <small>VOLTAGEM</small>
                <div class="v-grande v-v">{valor_v:.3f}V</div>
            </div>
            <div class="card solar">
                <small> IRRADIÂNCIA</small>
                <div class="v-grande v-p">{irradiancia:.4f} <small style="font-size:12px">kW/m²</small></div>
            </div>
            <div class="card IV">
                <small>CORRENTE</small>
                <div class="v-grande v-i">{corrente:.4f} <small style="font-size:12px">mA</small></div>
            </div>
        </div>
    """

    parte2 = """
        <div class="slider-container">
            <label id="labelSlider" style="color:#aaa">Histórico (Navegar no Tempo)</label><br>
            <input type="range" id="timeSlider" min="0" max="0" value="0" oninput="navegar(this.value)">
        </div>
        
        <div class="grid-graficos">
            <div><canvas id="chartV"></canvas></div>
            <div><canvas id="chartP"></canvas></div>
            <div><canvas id="chartI"></canvas></div>
        </div>
    </div>
    """

    parte3 = f"""
    <script>
        const VAL_V = {valor_v};
        const VAL_P = {irradiancia};
        const VAL_I = {corrente};
        const HORA = new Date().toLocaleTimeString();
        
        // 1. Persistência de Dados
        let historico = JSON.parse(localStorage.getItem('labsolar_v3')) || [];
        historico.push({{ v: VAL_V, p: VAL_P, i:VAL_I, t: HORA }});
        if(historico.length > 500) historico.shift();
        localStorage.setItem('labsolar_v3', JSON.stringify(historico));

        // 2. Configuração dos gráficos
        const config = (ctx, label, color, min, max, unit) => new Chart(ctx, {{
            type: 'line',
            data: {{ labels: [], datasets: [{{
                label: label, data: [], borderColor: color,
                backgroundColor: color+'22', fill: true, tension: 0.2, pointRadius: 0
            }}] }},
            options: {{ 
                animation: false,
                interaction: {{
                    mode: 'index',
                    intersect: false,
                }},
                scales: {{ 
                    y: {{ min: min, max: max, ticks: {{ color: '#888' }}, grid: {{ color: '#333' }} }},
                    x: {{ ticks: {{ color: '#888', maxRotation: 45 }} }}
                }},
                plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }}
            }}
        }});

        let chartV = config(document.getElementById('chartV'), 'Voltagem (V)', '#00d4ff', 0, 1);
        let chartP = config(document.getElementById('chartP'), 'Irradiância (kW/m²)', '#f1c40f', 0, 10);
        let chartI = config(document.getElementById('chartI'), 'Corrente (mA)', '#9e1313', 0, 10);

        // 3. Lógica de Sincronização
        function navegar(pos) {{
            pos = parseInt(pos);
            const jan = 20;
            const slider = document.getElementById('timeSlider');
            const estaNoPassado = pos < parseInt(slider.max);
            localStorage.setItem('pausado', estaNoPassado ? 'true' : '');
            document.getElementById('labelSlider').innerText = estaNoPassado ? "MODO HISTÓRICO (Pausado)" : "MODO AO VIVO";

            const recorte = historico.slice(pos, pos + jan);
            const labels = recorte.map(i => i.t);

            // Atualiza Gráfico de Voltagem
            chartV.data.labels = labels;
            chartV.data.datasets[0].data = recorte.map(i => i.v);
            chartV.update('none');

            // Atualiza Gráfico de Potência
            chartP.data.labels = labels;
            chartP.data.datasets[0].data = recorte.map(i => i.p);
            chartP.update('none');
            
            // Atualiza Gráfico de Corrente
            chartI.data.labels = labels;
            chartI.data.datasets[0].data = recorte.map(i => i.p);
            chartI.update('none');
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
    print(f"Conectado! Acesse no navegador: http://{ip}")
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 80))
    s.listen(1)
    while True:
        try:
            cl, addr = s.accept()
            cl.recv(1024)
            # Leitura ADC e correção de offset
            v = adc.read_u16() * (1 / 65535) - 0.015
            enviar_pagina(cl, v)
            cl.close()
        except:
            if 'cl' in locals(): cl.close()
else:
    print("Falha ao conectar no Wi-Fi.")