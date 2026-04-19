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
    print("Conectando ao Wi-Fi...")
    for _ in range(20):
        if wlan.isconnected(): return wlan.ifconfig()[0]
        time.sleep(1)
    return None

def enviar_pagina(cliente, valor_atual):
    parte1 = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <title>LABSOLAR - Histórico com Hora</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; text-align: center; background: #121212; color: white; padding: 20px; }}
        .box {{ background: #1e1e1e; max-width: 800px; margin: auto; padding: 20px; border-radius: 15px; border: 1px solid #333; }}
        .v-container {{ display: flex; justify-content: space-around; margin-bottom: 20px; }}
        .v-grande {{ font-size: 45px; color: #00ff88; font-weight: bold; }}
        .v-hist {{ font-size: 25px; color: #00d4ff; border-left: 2px solid #444; padding-left: 20px; }}
        .slider-container {{ margin: 30px 0; padding: 15px; background: #2a2a2a; border-radius: 10px; }}
        input[type=range] {{ width: 90%; accent-color: #00d4ff; }}
        .info-hora {{ color: #00d4ff; font-weight: bold; font-family: monospace; }}
        button {{ background: #ff4444; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; margin-top: 10px; }}
    </style></head><body>
    <div class="box">
        <h1>LABSOLAR - UFBA</h1>
        <div class="v-container">
            <div><small>AGORA</small><div class="v-grande">{valor_atual:.3f}V</div></div>
            <div><small>NO PONTO SELECIONADO</small>
                <div id="v-selecionada" class="v-hist">---</div>
                <div id="h-selecionada" class="info-hora">--:--:--</div>
            </div>
        </div>
    """
    
    parte2 = """
        <div class="slider-container">
            <label id="labelSlider">Navegar no histórico</label><br>
            <input type="range" id="timeSlider" min="0" max="0" value="0" oninput="navegar(this.value)">
            <br><button onclick="limparDados()">Limpar Tudo</button>
        </div>
        <canvas id="grafico"></canvas>
    </div>
    """
    
    parte3 = f"""
    <script>
        const VALOR_REDE = {valor_atual};
        const AGORA = new Date().toLocaleTimeString(); // Pega a hora do seu PC/Celular

        // 1. CARREGAR E SALVAR DADOS (Objeto: {{v: valor, t: tempo}})
        let historico = JSON.parse(localStorage.getItem('labsolar_v2')) || [];
        
        // Adiciona novo registro com timestamp
        historico.push({{ v: VALOR_REDE, t: AGORA }});
        if(historico.length > 500) historico.shift();
        localStorage.setItem('labsolar_v2', JSON.stringify(historico));

        // 2. CONFIGURAR GRÁFICO
        const ctx = document.getElementById('grafico').getContext('2d');
        let chart = new Chart(ctx, {{
            type: 'line',
            data: {{ labels: [], datasets: [{{
                label: 'Tensão (V)', data: [],
                borderColor: '#00d4ff', backgroundColor: 'rgba(0, 212, 255, 0.1)',
                fill: true, tension: 0.2
            }}] }},
            options: {{ animation: false, scales: {{ y: {{ min: 0, max: 1.2 }} }} }}
        }});

        // 3. NAVEGAÇÃO
        function navegar(posicao) {{
            posicao = parseInt(posicao);
            const janela = 20;
            const dadosExibir = historico.slice(posicao, posicao + janela);
            
            const ultimoItem = dadosExibir[dadosExibir.length - 1];
            document.getElementById('v-selecionada').innerText = ultimoItem.v.toFixed(3) + "V";
            document.getElementById('h-selecionada').innerText = "Hora: " + ultimoItem.t;
            document.getElementById('labelSlider').innerText = "Ponto: " + (posicao + 1) + " de " + historico.length;

            chart.data.labels = dadosExibir.map(item => item.t); // Usa as horas salvas como labels
            chart.data.datasets[0].data = dadosExibir.map(item => item.v);
            chart.update('none');
        }}

        function limparDados() {{
            if(confirm("Apagar todo o histórico?")) {{
                localStorage.removeItem('labsolar_v2');
                location.reload();
            }}
        }}

        // Inicializar
        const slider = document.getElementById('timeSlider');
        if(historico.length > 20) {{
            slider.max = historico.length - 20;
            slider.value = historico.length - 20;
        }}
        navegar(slider.value);

        setTimeout(() => {{ location.reload(); }}, 5000);
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
    print(f"LABSOLAR UFBA Ativo: http://{ip}")

    while True:
        try:
            cl, addr = s.accept()
            cl.recv(1024)
            v = adc.read_u16() * (1 / 65535) - 0.015
            enviar_pagina(cl, v)
            cl.close()
        except Exception as e:
            if 'cl' in locals(): cl.close()