import pandas as pd
import json
import os
from pathlib import Path

def gerar_bloco_grafico_conexao(df, filename='bloco_conexao_gprs.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    labels = df['Tipo de Rede'].tolist()
    dados_teste = df['Teste'].tolist()
    dados_ref = df['Referencia'].tolist()
    dados_total = [(t + r) for t, r in zip(dados_teste, dados_ref)]
    cores = ['#FF6384', '#36A2EB', "#00870D"]

    html = f"""
<div class='categoria'>
    <div class='titulo-wrapper'>
        <div class='titulo-categoria'>Conexão GPRS por Tipo de Rede</div>
    </div>

    <div class='grafico-container'>
            <div style='display: flex; justify-content: space-between; gap: 20px;'>
                <div style='width: 48%; display: flex; flex-direction: column; align-items: center;'>
                    <div style='text-align: center; font-weight: bold; margin-bottom: 5px;'>Teste</div>
                    <div style='width: 100%; height: 300px;'>
                        <canvas id="barrasTeste"></canvas>
                    </div>
                </div>
                <div style='width: 48%; display: flex; flex-direction: column; align-items: center;'>
                    <div style='text-align: center; font-weight: bold; margin-bottom: 5px;'>Referência</div>
                    <div style='width: 100%; height: 300px;'>
                        <canvas id="barrasRef"></canvas>
                    </div>
                </div>
            </div>
        <div style='margin-top: 30px; height: 350px;'>
            <canvas id="pizzaTotal"></canvas>
        </div>
    </div>

    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        if (typeof window.charts === 'undefined') window.charts = {{}};
        if (typeof Chart !== 'undefined' && Chart.register && typeof ChartZoom !== 'undefined') {{
            Chart.register(ChartZoom);
        }}

        var cores = {json.dumps(cores)};

        // Gráfico de barras - Teste
        var ctxTeste = document.getElementById('barrasTeste').getContext('2d');
        window.charts['barrasTeste'] = new Chart(ctxTeste, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: 'Teste',
                    data: {json.dumps(dados_teste)},
                    backgroundColor: cores,
                    borderColor: cores,
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}

        }});

        // Gráfico de barras - Referência
        var ctxRef = document.getElementById('barrasRef').getContext('2d');
        window.charts['barrasRef'] = new Chart(ctxRef, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: 'Referência',
                    data: {json.dumps(dados_ref)},
                    backgroundColor: cores,
                    borderColor: cores,
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}

        }});

        // Gráfico de pizza - Total
        var ctxPizza = document.getElementById('pizzaTotal').getContext('2d');
        window.charts['pizzaTotal'] = new Chart(ctxPizza, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: 'Total Geral',
                    data: {json.dumps(dados_total)},
                    backgroundColor: cores,
                    borderColor: cores,
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.raw;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(2) + '%';
                                return label + ': ' + value + ' (' + percentage + ')';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    }});
    </script>
</div>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # print(f"✅ Bloco GPRS salvo em: {output_path}")
    return output_path
