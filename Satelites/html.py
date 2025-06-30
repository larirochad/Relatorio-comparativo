import pandas as pd
import json
import os
from pathlib import Path

def gerar_bloco_satellite_estabilidade(df, filename='bloco_satellite_estabilidade.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    dias = df['Dia'].tolist()
    val_ref = df['Validos referencia'].fillna(0).tolist()
    val_teste = df['Validos teste'].fillna(0).tolist()
    inv_ref = df['Inválidos referencia'].fillna(0).tolist()
    inv_teste = df['Inválidos teste'].fillna(0).tolist()

    total_val_ref = sum(val_ref)
    total_val_teste = sum(val_teste)
    total_inv_ref = sum(inv_ref)
    total_inv_teste = sum(inv_teste)

    # Calcular diferença percentual
    diferenca_percentual = ((total_val_teste - total_val_ref) / total_val_ref * 100) if total_val_ref != 0 else 0

    datasets_linha = [
        {
            'label': 'Válidos Referência',
            'data': val_ref,
            'borderColor': "#12094A",
            'backgroundColor': '#12094A',
            'tension': 0.3,
            'fill': False,
            'pointRadius': 4,
            'pointHoverRadius': 6,
            'pointBackgroundColor': '#12094A',
            'pointBorderColor': '#12094A',
            'pointBorderWidth': 1,
            'hidden': False
        },
        {
            'label': 'Válidos Teste',
            'data': val_teste,
            'borderColor': '#17becf',
            'backgroundColor': '#17becf',
            'tension': 0.3,
            'fill': False,
            'pointRadius': 4,
            'pointHoverRadius': 6,
            'pointBackgroundColor': '#17becf',
            'pointBorderColor': '#17becf',
            'pointBorderWidth': 1,
            'hidden': False
        },
        {
            'label': 'Inválidos Referência',
            'data': inv_ref,
            'borderColor': 'red',
            'backgroundColor': 'red',
            'tension': 0.3,
            'fill': False,
            'pointRadius': 4,
            'pointHoverRadius': 6,
            'pointBackgroundColor': 'red',
            'pointBorderColor': 'red',
            'pointBorderWidth': 1,
            'hidden': True
        },
        {
            'label': 'Inválidos Teste',
            'data': inv_teste,
            'borderColor': 'darkorange',
            'backgroundColor': 'darkorange',
            'tension': 0.3,
            'fill': False,
            'pointRadius': 4,
            'pointHoverRadius': 6,
            'pointBackgroundColor': 'darkorange',
            'pointBorderColor': 'darkorange',
            'pointBorderWidth': 1,
            'hidden': True
        }
    ]

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Análise de Estabilidade de Satélites</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1"></script>
    <style>
    .categoria {{
        margin-bottom: 40px;
    }}
    .titulo-wrapper {{
        text-align: center;
        margin-bottom: 20px;
    }}
    .titulo-categoria {{
        display: inline-block;
        font-size: 24px;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 20px;
        color: white;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }}
    .filter-buttons button {{
        padding: 6px 15px;
        border: none;
        border-radius: 15px;
        font-size: 12px;
        cursor: pointer;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        font-weight: 500;
        transition: all 0.3s ease;
        margin: 2px;
    }}
    .filter-buttons button:hover {{
        transform: translateY(-1px);
        opacity: 0.9;
    }}
    .filter-buttons button.active {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    .filter-buttons {{
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-top: 10px;
        flex-wrap: wrap;
    }}
    .grafico-container {{
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}
    .grafico-titulo-container {{
        text-align: center;
        margin-bottom: 15px;
    }}
    .grafico-titulo {{
        font-size: 18px;
        font-weight: bold;
        color: #333;
    }}
    .chart-wrapper {{
        position: relative;
        height: 400px;
        width: 100%;
    }}
    .zoom-controls {{
        text-align: center;
        margin-top: 10px;
    }}

    .zoom-instruction {{
        text-align: center;
        font-size: 12px;
        color: #666;
        margin-top: 5px;
    }}
    .diferenca-container {{
        text-align: center;
        margin-top: 15px;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 8px;
        font-size: 14px;
    }}
    .diferenca-valor {{
        font-weight: bold;
        color: {'green' if diferenca_percentual >= 0 else 'red'};
    }}
    </style>
</head>
<body>

<div class='categoria'>
    <div class='titulo-wrapper'>
        <div class='titulo-categoria'>Análise de Estabilidade de Satélites</div>
    </div>

    <div class='grafico-container'>
        <button class='btn-maximizar' onclick="maximizeChart('canvas_sat_line')">🔍 Maximizar</button>
        <div class='grafico-titulo-container'><h3 class='grafico-titulo'>Evolução Diária - Satélites Válidos e Inválidos</h3></div>

        <div class='filter-buttons'>
            <button id="btn-validos" onclick="filtrarSat('canvas_sat_line', 'Válidos')">Válidos</button>
            <button id="btn-invalidos" onclick="filtrarSat('canvas_sat_line', 'Inválidos')">Inválidos</button>
            <button id="btn-todos" onclick="filtrarSat('canvas_sat_line', 'Todos')">Todos</button>
        </div>

        <div class='chart-wrapper'>
            <canvas id='canvas_sat_line'></canvas>
        </div>
        <div class='zoom-controls'>
            <button onclick="resetZoom('canvas_sat_line')">Reset Zoom</button>
        </div>
        <div class='zoom-instruction'>Use o scroll do mouse para zoom ou duplo clique para resetar</div>
    </div>

    <script>
    (function() {{
        const ctx = document.getElementById('canvas_sat_line').getContext('2d');
        const valRef = {json.dumps(val_ref)};
        const valTeste = {json.dumps(val_teste)};

        // Variável para controlar o filtro ativo
        let filtroAtivo = 'Válidos';
        
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(dias)},
                datasets: {json.dumps(datasets_linha)}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{ mode: 'index', intersect: false }},
                plugins: {{
                    legend: {{ 
                        display: true, 
                        position: 'top',
                        onClick: function(e, legendItem, legend) {{
                            const chart = legend.chart;
                            const index = legendItem.datasetIndex;
                            const dataset = chart.data.datasets[index];
                            
                            // Se houver filtro ativo, verifica se o dataset clicado pertence ao filtro
                            if (filtroAtivo !== 'Todos') {{
                                const pertenceAoFiltro = dataset.label.includes(filtroAtivo);
                                if (!pertenceAoFiltro) {{
                                    return; // Não permite interação com datasets que não pertencem ao filtro
                                }}
                            }}
                            
                            // Alterna a visibilidade normalmente
                            dataset.hidden = !dataset.hidden;
                            chart.update();
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const index = context.dataIndex;
                                const datasetIndex = context.datasetIndex;
                                const datasetLabel = context.dataset.label;
                                const value = context.raw;

                                if (datasetIndex === 0) {{
                                    const testeVal = valTeste[index];
                                    if (value !== 0) {{
                                        const diff = ((value - testeVal) / value) * 100;
                                        return `${{datasetLabel}}: ${{value}} (${{diff.toFixed(1)}}%)`;
                                    }}
                                }} else if (datasetIndex === 1) {{
                                    const refVal = valRef[index];
                                    if (refVal !== 0) {{
                                        const diff = ((value - refVal) / refVal) * 100;
                                        return `${{datasetLabel}}: ${{value}} (${{diff.toFixed(1)}}%)`;
                                    }}
                                }}
                                return `${{datasetLabel}}: ${{value}}`;
                            }}
                        }}
                    }},
                    zoom: {{
                        pan: {{ enabled: true, mode: 'xy' }},
                        zoom: {{
                            wheel: {{ enabled: true, speed: 0.1 }},
                            pinch: {{ enabled: true }},
                            drag: {{ enabled: true, backgroundColor: 'rgba(225,225,225,0.3)', borderWidth: 2 }},
                            mode: 'xy'
                        }}
                    }}
                }},
                scales: {{
                    x: {{ type: 'category', title: {{ display: true, text: 'DIAS', font: {{ weight: 'bold', size: 14 }}, color: '#222' }} }},
                    y: {{ title: {{ display: true, text: 'QUANTIDADE DE MENSAGENS', font: {{ weight: 'bold', size: 14 }}, color: '#222' }} }}
                }}
            }}
        }});

        window.charts = window.charts || {{}};
        window.charts['canvas_sat_line'] = chart;

        document.getElementById('canvas_sat_line').addEventListener('dblclick', function() {{
            chart.resetZoom();
        }});
    }})();
    </script>

    <script>
    function filtrarSat(chartId, tipo) {{
        const chart = window.charts[chartId];
        if (!chart) return;
        
        // Atualiza a variável de controle do filtro
        filtroAtivo = tipo;
        
        // Atualiza os botões
        document.getElementById('btn-validos').classList.remove('active');
        document.getElementById('btn-invalidos').classList.remove('active');
        document.getElementById('btn-todos').classList.remove('active');
        
        if (tipo === 'Válidos') {{
            document.getElementById('btn-validos').classList.add('active');
            chart.data.datasets.forEach((dataset) => {{
                dataset.hidden = !dataset.label.includes('Válidos');
            }});
        }} else if (tipo === 'Inválidos') {{
            document.getElementById('btn-invalidos').classList.add('active');
            chart.data.datasets.forEach((dataset) => {{
                dataset.hidden = !dataset.label.includes('Inválidos');
            }});
        }} else {{
            document.getElementById('btn-todos').classList.add('active');
            chart.data.datasets.forEach((dataset) => {{
                dataset.hidden = false; // Mostra todos os datasets
            }});
        }}
        
        chart.update();
    }}

    // Ativa o botão Válidos por padrão
    document.addEventListener('DOMContentLoaded', function() {{
        document.getElementById('btn-validos').classList.add('active');
        // Garante que o filtro seja aplicado mesmo que o gráfico ainda não esteja totalmente carregado
        setTimeout(() => filtrarSat('canvas_sat_line', 'Válidos'), 100);
    }});
    </script>

    <!-- Gráfico de Barras Horizontais com Porcentagem -->
    <div class='grafico-container' style="margin-top: 30px;">
        <button class='btn-maximizar' onclick="maximizeChart('canvas_sat_barras_validos')">🔍 Maximizar</button>
        <div class='grafico-titulo-container'><h3 class='grafico-titulo'>Total de Satélites Válidos (Referência x Teste)</h3></div>
        <div class='chart-wrapper'>
            <canvas id='canvas_sat_barras_validos'></canvas>
        </div>
        <div class='diferenca-container'>
            Diferença percentual: <span class='diferenca-valor'>{diferenca_percentual:.2f}%</span>
            <br>
            <small>Teste em relação ao Referência</small>
        </div>
    </div>

    <script>
    (function() {{
        const ctx = document.getElementById('canvas_sat_barras_validos').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['Válidos Referência', 'Válidos Teste'],
                datasets: [{{
                    label: 'Quantidade',
                    data: [{total_val_ref}, {total_val_teste}],
                    backgroundColor: ['#12094A', '#17becf'],
                    borderColor: ['#12094A', '#14a9b8'],
                    borderWidth: 1,
                    barThickness: 40
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.raw;
                            }},
                            afterLabel: function(context) {{
                                const refValue = {total_val_ref};
                                const testValue = {total_val_teste};
                                const diff = ((testValue - refValue) / refValue * 100).toFixed(2);
                                
                                if (context.dataIndex === 0) {{
                                    return 'Referência';
                                }} else {{
                                    return 'Diferença: ' + diff + '%';
                                }}
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'QUANTIDADE DE MENSAGENS',
                            font: {{ weight: 'bold', size: 14 }}
                        }},
                        ticks: {{
                            stepSize: 200
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: 'CATEGORIA',
                            font: {{ weight: 'bold', size: 14 }}
                        }}
                    }}
                }}
            }}
        }});
        window.charts = window.charts || {{}};
        window.charts['canvas_sat_barras_validos'] = chart;
    }})();

    </script>
</div>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # print(f"✅ Bloco de gráfico de satélites salvo em: {output_path.resolve()}")