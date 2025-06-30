import pandas as pd
import json
import os
from pathlib import Path

def gerar_bloco_viagens(df, filename='bloco_viagens.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    labels = df['Dia'].tolist()
    categorias = ['Curta', 'Media', 'Longa']
    # print("\n==== DataFrame recebido ====")
    # print(df.to_string())


    # Cores fixas para todas as linhas:
    cor_teste = '#17becf'     # Azul forte
    cor_ref = '#12094A'        # Vermelho forte

    # === Datasets para o gráfico TOTAL do dia ===
    df['Total Teste'] = df[[f'{cat} para teste' for cat in categorias]].sum(axis=1)
    df['Total Referencia'] = df[[f'{cat} para referência' for cat in categorias]].sum(axis=1)

    datasets_total = [
        {
            'label': 'Teste - Total',
            'data': df['Total Teste'].fillna(0).tolist(),
            'borderColor': cor_teste,
            'backgroundColor': cor_teste,
            'tension': 0.3,
            'fill': False,
            'pointRadius': 4,
            'pointHoverRadius': 6
        },
        {
            'label': 'Referência - Total',
            'data': df['Total Referencia'].fillna(0).tolist(),
            'borderColor': cor_ref,
            'backgroundColor': cor_ref,
            'tension': 0.3,
            'fill': False,
            'pointRadius': 4,
            'pointHoverRadius': 6
        }
    ]

    # === Datasets para os grupos (Curta / Media / Longa) ===
    blocos_datasets = {}
    for cat in categorias:
        datasets = [
            {
                'label': f'Teste - {cat}',
                'data': df[f'{cat} para teste'].fillna(0).tolist(),
                'borderColor': cor_teste,
                'backgroundColor': cor_teste,
                'tension': 0.3,
                'fill': False,
                'pointRadius': 4,
                'pointHoverRadius': 6
            },
            {
                'label': f'Referência - {cat}',
                'data': df[f'{cat} para referência'].fillna(0).tolist(),
                'borderColor': cor_ref,
                'backgroundColor': cor_ref,
                'tension': 0.3,
                'fill': False,
                'pointRadius': 4,
                'pointHoverRadius': 6
            }
        ]
        blocos_datasets[cat] = datasets

    # Início do HTML
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Análise de Viagens</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1"></script>
    <style>
    .chartjs-legend ul {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 8px 12px;
        display: inline-block;
    }
    .categoria {
        margin-bottom: 40px;
    }
    .titulo-wrapper {
        text-align: center;
        margin-bottom: 20px;
    }
    .titulo-categoria {
        font-family: 'Saira', sans-serif;
        font-size: 2.2em;
        font-weight: 800;
        color: transparent;
        background-image: linear-gradient(to right, #764ba2, #667eea);
        -webkit-background-clip: text;
        background-clip: text;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: none;
        border-radius: 0;
        padding: 10px 20px;
    }

    .grupo-selector {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .btn-grupo {
        padding: 8px 16px;
        border: none;
        border-radius: 20px;
        background-color: #f0f0f0;
        cursor: pointer;
        transition: all 0.3s;
        font-weight: bold;
    }
    .btn-grupo:hover {
        background-color: #d0d0d0;
    }
    .btn-grupo.active {
        background-color: #667eea;
        color: white;
    }
    .grupo {
        display: none;
    }
    .grupo.active {
        display: block;
    }
    .grafico-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .grafico-titulo-container {
        text-align: center;
        margin-bottom: 15px;
    }
    .grafico-titulo {
        font-size: 18px;
        font-weight: bold;
        color: #333;
    }
    .chart-wrapper {
        position: relative;
        height: 400px;
        width: 100%;
    }
    .zoom-controls {
        text-align: center;
        margin-top: 10px;
    }
    .zoom-instruction {
        text-align: center;
        font-size: 12px;
        color: #666;
        margin-top: 5px;
    }
    .metricas {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 15px;
        background-color: #0e0561;
    }
    .metrica-item {
        background: #f8f9fa;
        padding: 10px 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    /* Estilos para o hodômetro */
    .titulo-odometro {
        font-family: 'Saira', sans-serif;
        font-size: 2.4em;
        font-weight: 800;
        color: transparent;
        background-image: linear-gradient(to right, #764ba2, #667eea);
        -webkit-background-clip: text;
        background-clip: text;
        text-align: center;
        margin: 30px auto 20px auto;
        display: block;
        padding: 10px 20px;
        box-shadow: none;
        border-radius: 0;
    }


    .odometro-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 40px;
        margin-top: 20px;
    }
    .odometro-item {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        text-align: center;
        width: 320px;
        position: relative;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .odometro-item:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }

    .canvas-wrapper {
        position: relative;
        width: 100%;
        height: auto;
    }
    .canvas-wrapper canvas {
        display: block;
        margin: 0 auto;
    }
    .escala-text {
        position: absolute;
        font-size: 11px;
        color: #555;
        top: 85%;
        transform: translateY(-50%);
    }
    .escala-left {
        left: 10px;
    }
    .escala-right {
        right: 10px;
    }
    .valor {
        font-size: 18px;
        font-weight: bold;
        margin-top: 10px;
        color: #222;
        text-shadow: 0.5px 0.5px 1px rgba(0,0,0,0.15);
    }
    
    /* ESTILOS MELHORADOS PARA O BLOCO DE DIFERENÇA PERCENTUAL */
    .metric-box {
        background: rgba(255, 255, 255, 0.9);
        padding: 25px 30px;
        border-radius: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        text-align: center;
        margin-top: 25px;
        width: 100%;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 18px;
        padding: 2px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        mask-composite: exclude;
        -webkit-mask-composite: xor;
        opacity: 0.3;
        transition: opacity 0.3s ease;
    }
    
    .metric-box:hover::before {
        opacity: 0.6;
    }
    
    .metric-box h4 {
        font-size: 22px;
        font-weight: bold;
        margin: 0 0 15px 0;
        color: #2c3e50;
        text-shadow: 0.5px 0.5px 1px rgba(0,0,0,0.1);
        position: relative;
        z-index: 1;
    }
    
    .metric-box .valor-percentual {
        font-size: 32px;
        font-weight: 900;
        margin: 0;
        position: relative;
        z-index: 1;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    /* Classes dinâmicas para valores positivos e negativos */
    .metric-box.positivo {
        background: rgba(40, 167, 69, 0.15);
        border-color: rgba(40, 167, 69, 0.3);
    }
    
    .metric-box.positivo h4,
    .metric-box.positivo .valor-percentual {
        color: #155724;
    }
    
    .metric-box.positivo::before {
        background: linear-gradient(135deg, #28a745, #20c997);
    }
    
    .metric-box.negativo {
        background: rgba(220, 53, 69, 0.15);
        border-color: rgba(220, 53, 69, 0.3);
    }
    
    .metric-box.negativo h4,
    .metric-box.negativo .valor-percentual {
        color: #721c24;
    }
    
    .metric-box.negativo::before {
        background: linear-gradient(135deg, #dc3545, #e74c3c);
    }
    
    /* Efeito hover para o bloco */
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 25px rgba(0,0,0,0.18);
    }
    
    .metric-box.positivo:hover {
        box-shadow: 0 12px 25px rgba(40, 167, 69, 0.25);
    }
    
    .metric-box.negativo:hover {
        box-shadow: 0 12px 25px rgba(220, 53, 69, 0.25);
    }
    .faixa-legenda {
    text-align: center;
    font-size: 14px;
    color: #1010;
    margin-top: 10px;
    font-weight: 500;
    }

    </style>
</head>
<body>
"""

    # ========== Cálculo dos totais por categoria ==========
    total_teste = df['Total Teste'].sum()
    total_ref = df['Total Referencia'].sum()

    # Totais por categoria
    totais_por_categoria = {}
    for cat in categorias:
        totais_por_categoria[cat] = {
            'teste': df[f'{cat} para teste'].sum(),
            'referencia': df[f'{cat} para referência'].sum()
        }

    diferenca_percentual = ((total_teste - total_ref) / total_ref * 100) if total_ref != 0 else 0
    meta_esperada = 12000

    def calcular_alcance(valor, meta):
        return min((valor / meta) * 100, 100)

    def gerar_grafico_odometro(cor, label, valor_km, alcance, canvas_id):
        valor_km_str = f"{valor_km:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        dados = {
            'labels': ['Concluído', 'Restante'],
            'datasets': [
                {
                    'label': label,
                    'data': [alcance, 100 - alcance],
                    'backgroundColor': [cor, 'rgba(200,200,200,0.2)'],
                    'borderColor': ['#fff', '#fff'],
                    'circumference': 180,
                    'rotation': -90,
                }
            ]
        }

        return f"""
        <div class='odometro-item'>
            <h4>{label}</h4>
            <div class='canvas-wrapper'>
                <canvas id='{canvas_id}'></canvas>
                <div class='escala-text escala-left'>0 km</div>
                <div class='escala-text escala-right'>12.000 km</div>
            </div>
             <div class='valor'>{valor_km_str} km</div>
        </div>

        <script>
        (function() {{
            const canvas = document.getElementById('{canvas_id}');
            const ctx = canvas.getContext('2d');

            const chart = new Chart(ctx, {{
                type: 'doughnut',
                data: {json.dumps(dados)},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    cutout: '60%',
                    circumference: 180,
                    rotation: -90,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const km = ({valor_km}).toFixed(2);
                                    return context.dataset.label + ': ' + context.raw.toFixed(2) + '% (' + km + ' km)';
                                }}
                            }}
                        }}
                    }},
                    elements: {{
                        arc: {{
                            borderWidth: 1,
                            borderColor: '#fff'
                        }}
                    }}
                }}
            }});

            chart.update();

            // === Linha de meta nos 10.000 km ===
            function drawMetaLine() {{
                const centerX = canvas.width / 2;
                const centerY = canvas.height;
                const radius = Math.min(canvas.width, canvas.height) / 2 * 0.8;

                const percentMeta = 10000 / 50000; // 10k sobre 50k => 20%
                const angle = Math.PI * (1 - percentMeta);

                ctx.beginPath();
                ctx.moveTo(
                    centerX + (radius - 5) * Math.cos(angle),
                    centerY - (radius - 5) * Math.sin(angle)
                );
                ctx.lineTo(
                    centerX + (radius + 10) * Math.cos(angle),
                    centerY - (radius + 10) * Math.sin(angle)
                );
                ctx.strokeStyle = '#28a745';
                ctx.lineWidth = 3;
                ctx.setLineDash([4, 2]);
                ctx.stroke();
            }}

            drawMetaLine();
        }})();
        </script>
        """

    # ========== Parte 1: Gráficos de Hodômetro com Botões ==========
    html += f"""
<div class='categoria'>
    <div class='titulo-odometro'>Hodômetro - Progresso por Categoria</div>
    
    <!-- Botões para selecionar categoria -->
    <div class='grupo-selector'>
        <button onclick="mostrarGrupoHodometro('Total')" class='btn-grupo active' id='btn-hodometro-Total'>Total</button>
        <button onclick="mostrarGrupoHodometro('Curta')" class='btn-grupo' id='btn-hodometro-Curta'>Curtas</button>
        <button onclick="mostrarGrupoHodometro('Media')" class='btn-grupo' id='btn-hodometro-Media'>Médias</button>
        <button onclick="mostrarGrupoHodometro('Longa')" class='btn-grupo' id='btn-hodometro-Longa'>Longas</button>
    </div>

    <!-- Grupo Total -->
    <div class='grupo active' id='hodometro-Total'>
        <div class='odometro-container'>
            {gerar_grafico_odometro(cor_ref, "Referência", total_ref, calcular_alcance(total_ref, meta_esperada), 'canvas_total_ref')}
            {gerar_grafico_odometro(cor_teste, "Teste", total_teste, calcular_alcance(total_teste, meta_esperada), 'canvas_total_teste')}
        </div>
        <div class='metric-box' id='metric-box-total'>
            <h4>Diferença percentual entre os Hodômetros (%)</h4>
            <div class='valor-percentual' data-valor='{diferenca_percentual:.2f}'>{diferenca_percentual:.2f}%</div>
        </div>
    </div>
"""

    # Adicionar grupos para cada categoria
    for cat in categorias:
        teste_valor = totais_por_categoria[cat]['teste']
        ref_valor = totais_por_categoria[cat]['referencia']
        diferenca_cat = ((teste_valor - ref_valor) / ref_valor * 100) if ref_valor != 0 else 0
        
        html += f"""
    <!-- Grupo {cat} -->
    <div class='grupo' id='hodometro-{cat}'>
        <div class='odometro-container'>
            {gerar_grafico_odometro(cor_ref, f"Referência - {cat}", ref_valor, calcular_alcance(ref_valor, meta_esperada), f'canvas_{cat.lower()}_ref')}
            {gerar_grafico_odometro(cor_teste, f"Teste - {cat}", teste_valor, calcular_alcance(teste_valor, meta_esperada), f'canvas_{cat.lower()}_teste')}
        </div>
        <div class='metric-box' id='metric-box-{cat.lower()}'>
            <h4>Diferença percentual - {cat} (%)</h4>
            <div class='valor-percentual' data-valor='{diferenca_cat:.2f}'>{diferenca_cat:.2f}%</div>
        </div>
    </div>
"""

    html += """
</div>
"""

    # ========== Parte 2: Gráficos de Linha ==========
    html += """
<div class='categoria'>
    <div class='titulo-wrapper'>
        <div class='titulo-categoria'>Análise de Hodômetro por dia</div>
    </div>
    <div class='grupo-selector'>
        <button onclick="mostrarGrupo('Total','viagem', 'Total de Quilometragem por Dia')" class='btn-grupo active' id='btn-viagem-Total'>Total</button>
        <button onclick="mostrarGrupo('Curta','viagem', 'Viagens Curtas')" class='btn-grupo' id='btn-viagem-Curta'>Curtas</button>
        <button onclick="mostrarGrupo('Media','viagem', 'Viagens Médias')" class='btn-grupo' id='btn-viagem-Media'>Médias</button>
        <button onclick="mostrarGrupo('Longa','viagem', 'Viagens Longas')" class='btn-grupo' id='btn-viagem-Longa'>Longas</button>
    </div>
"""

    # === Bloco Total ===
    html += f"""
    <div class='grupo active' data-categoria='viagem' data-grupo='Total'>
        <div class='grafico-container'>
            <div class='grafico-titulo-container'><h3 class='grafico-titulo'>Total de Quilometragem por Dia</h3></div>
            <div class='metricas' id='metrics_viagem_total'></div>
            <div class='chart-wrapper'>
                <canvas id='canvas_viagem_total'></canvas>
            </div>
            <div class='zoom-controls'>
                <button onclick="resetZoom('canvas_viagem_total')">Reset Zoom</button>
            </div>
            <div class='zoom-instruction'>Use o scroll do mouse para zoom ou duplo clique para resetar</div>
        </div>
    </div>
    <script>
    (function() {{
        const ctx = document.getElementById('canvas_viagem_total').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(labels)},
                datasets: {json.dumps(datasets_total)}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{ mode: 'nearest', intersect: false }},
                plugins: {{
                    legend: {{ display: true, position: 'top' }},
                    zoom: {{
                        pan: {{ enabled: true, mode: 'xy', speed: 10, threshold: 10 }},
                        zoom: {{
                            wheel: {{ enabled: true, speed: 0.1 }},
                            pinch: {{ enabled: true }},
                            drag: {{ enabled: true, backgroundColor: 'rgba(225,225,225,0.3)', borderWidth: 2 }},
                            mode: 'xy'
                        }}
                    }}
                }},
                scales: {{
                    x: {{ type: 'category', title: {{ display: true, text: 'DIAS', font: {{ weight: 'bold', size: 14 }}, color: '#222',  family: 'Saira, sans-serif' }} }},
                    y: {{ title: {{ display: true, text: 'QUILOMETRAGEM (km)', font: {{ weight: 'bold', size: 14 }}, color: '#222',  family: 'Saira, sans-serif' }} }}
                }}
            }}
        }});
        window.charts = window.charts || {{}};
        window.charts['canvas_viagem_total'] = chart;
        document.getElementById('canvas_viagem_total').addEventListener('dblclick', function() {{
            chart.resetZoom();
        }});
    }})();
    </script>
    """

    # === Blocos Curtas / Médias / Longas ===
    legenda_textos = {
        "Curta": "Faixa de distância: 0 km até 2 km",
        "Media": "Faixa de distância: 2 km até 50 km",
        "Longa": "Faixa de distância: acima de 50 km"
        }

    for idx, cat in enumerate(categorias):
        chart_id = f"canvas_viagem_{idx}"
        metric_id = f"metrics_viagem_{idx}"
        titulo = f"Viagens {cat}s por Dia"
        legenda_texto = legenda_textos.get(cat, "")

        html += f"""
        <div class='grupo' data-categoria='viagem' data-grupo='{cat}'>
            <div class='grafico-container'>
                <div class='grafico-titulo-container'><h3 class='grafico-titulo'>{titulo}{legenda_texto}</h3></div>
                <div class="metricas" id="metrics_viagem_total"><p>{legenda_texto}</p></div>
                <div class='faixa-legenda' id='faixa_{cat.lower()}'>{legenda_texto}</div>
                <div class='chart-wrapper'>
                    <canvas id='{chart_id}'></canvas>
                </div>
                <div class='zoom-controls'>
                    <button onclick="resetZoom('{chart_id}')">Reset Zoom</button>
                </div>
                <div class='zoom-instruction'>Use o scroll do mouse para zoom ou duplo clique para resetar</div>
            </div>
        </div>
        <script>
        (function() {{
            const ctx = document.getElementById('{chart_id}').getContext('2d');
            const chart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: {json.dumps(blocos_datasets[cat])}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'nearest', intersect: false }},
                    plugins: {{
                        legend: {{ display: true, position: 'top' }},
                        zoom: {{
                            pan: {{ enabled: true, mode: 'xy', speed: 10, threshold: 10 }},
                            zoom: {{
                                wheel: {{ enabled: true, speed: 0.1 }},
                                pinch: {{ enabled: true }},
                                drag: {{ enabled: true, backgroundColor: 'rgba(225,225,225,0.3)', borderWidth: 2 }},
                                mode: 'xy'
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{ type: 'category', title: {{ display: true, text: 'DIAS', font: {{ weight: 'bold', size: 14 }}, color: '#222',  family: 'Saira, sans-serif' }} }},
                        y: {{ title: {{ display: true, text: 'QUILOMETRAGEM (km)', font: {{ weight: 'bold', size: 14 }}, color: '#222',  family: 'Saira, sans-serif' }} }}
                    }}
                }}
            }});
            window.charts = window.charts || {{}};
            window.charts['{chart_id}'] = chart;
            document.getElementById('{chart_id}').addEventListener('dblclick', function() {{
                chart.resetZoom();
            }});
        }})();
        </script>
    """


    html += """
</div>

<script>
// Função para aplicar estilos dinâmicos aos blocos de diferença percentual
function aplicarEstilosDinamicos() {
    // Seleciona todos os blocos de diferença percentual
    const metricBoxes = document.querySelectorAll('.metric-box');
    
    metricBoxes.forEach(box => {
        const valorElement = box.querySelector('.valor-percentual');
        if (valorElement) {
            const valor = parseFloat(valorElement.getAttribute('data-valor'));
            
            // Remove classes anteriores
            box.classList.remove('positivo', 'negativo');
            
            // Aplica classe baseada no valor
            if (valor >= 0) {
                box.classList.add('positivo');
            } else {
                box.classList.add('negativo');
            }
        }
    });
}

// Função para mostrar grupos do hodômetro
function mostrarGrupoHodometro(categoria) {
    // Remove classe active de todos os botões do hodômetro
    document.querySelectorAll('[id^="btn-hodometro-"]').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Adiciona classe active ao botão selecionado
    document.getElementById(`btn-hodometro-${categoria}`).classList.add('active');
    
    // Esconde todos os grupos do hodômetro
    document.querySelectorAll('[id^="hodometro-"]').forEach(grupo => {
        grupo.classList.remove('active');
    });
    
    // Mostra o grupo selecionado
    document.getElementById(`hodometro-${categoria}`).classList.add('active');
    
    // Reaplica os estilos dinâmicos após mudança de grupo
    setTimeout(aplicarEstilosDinamicos, 100);
}

// Função para mostrar grupos dos gráficos de linha
function mostrarGrupo(grupo, categoria, titulo) {
    // Remove classe active de todos os botões da categoria viagem
    document.querySelectorAll('[id^="btn-viagem-"]').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Adiciona classe active ao botão selecionado
    document.getElementById(`btn-viagem-${grupo}`).classList.add('active');
    
    // Esconde todos os grupos da mesma categoria
    document.querySelectorAll(`.grupo[data-categoria='${categoria}']`).forEach(el => {
        el.classList.remove('active');
    });
    
    // Mostra o grupo selecionado
    document.querySelector(`.grupo[data-categoria='${categoria}'][data-grupo='${grupo}']`).classList.add('active');
    
    // Atualiza o título do gráfico se necessário
    const tituloElement = document.querySelector(`.grupo[data-categoria='${categoria}'][data-grupo='${grupo}'] .grafico-titulo`);
    if (tituloElement && titulo) {
        tituloElement.textContent = titulo;
    }
}

function resetZoom(chartId) {
    if (window.charts && window.charts[chartId]) {
        window.charts[chartId].resetZoom();
    }
}

// Aplica os estilos dinâmicos quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    aplicarEstilosDinamicos();
});

// Também aplica quando a janela é redimensionada (para garantir)
window.addEventListener('resize', function() {
    setTimeout(aplicarEstilosDinamicos, 200);
});
</script>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # print(f"✅ Bloco combinado de gráficos (hodômetro + linhas) salvo em: {output_path.resolve()}")