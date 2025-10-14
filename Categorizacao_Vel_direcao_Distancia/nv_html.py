import pandas as pd
import json
import re
import os
import tempfile
import webbrowser
from datetime import datetime
import statistics
import math
from pathlib import Path

class ChartJSDashboardGenerator:
    def __init__(self):
        self.chart_counter = 0
        self.categories = {
            'distância': { 'name': 'Análise por Distância'},
            'velocidade': { 'name': 'Análise por Velocidade'},
            'direção': { 'name': 'Análise por Direção'}
        }
        self.colors = [
            'rgba(255, 99, 132, 1)','rgba(54, 162, 235, 1)','rgba(255, 205, 86, 1)',
            'rgba(75, 192, 192, 1)','rgba(153, 102, 255, 1)','rgba(255, 159, 64, 1)'
        ]
    
    def generate_chart_data(self, cfg):
        cid = f"canvas_{self.chart_counter}"
        mid = f"metrics_{self.chart_counter}"
        var = f"chart_{self.chart_counter}"
        ds = []

        for i, d in enumerate(cfg['datasets']):
            color = d.get('borderColor', self.colors[i % len(self.colors)])
            fill_option = d.get('fill', False)

            dataset = {
                'label': d['label'],
                'data': d['data'],
                'borderColor': d.get('borderColor', self.colors[i % len(self.colors)]),
                'backgroundColor': d.get('borderColor', self.colors[i % len(self.colors)]),
                'tension': 0.3,
                'fill': d.get('fill', False),
                'pointRadius': 4,
                'pointHoverRadius': 6,
                'pointBackgroundColor': d.get('pointBackgroundColor', d.get('borderColor', self.colors[i % len(self.colors)])),
                'pointBorderColor': d.get('pointBorderColor', d.get('borderColor', self.colors[i % len(self.colors)])),
            }
            ds.append(dataset)

        metrics_info = cfg.get('metrics_info', 'Dados disponíveis')

        out = {
            'canvas_id': cid, 'metrics_id': mid, 'chart_var': var,
            'title': cfg['titulo'], 'category': cfg['categoria'],
            'group': cfg['grupo'], 'labels': cfg['labels'],
            'datasets': ds, 'metrics_info': metrics_info
        }
        self.chart_counter += 1
        return out

    def generate_html_category(self, cat, charts):
        ci = self.categories[cat]
        groups = {}
        for c in charts: 
            groups.setdefault(c['group'], []).append(c)
        
        html = f"""
        <div class='categoria'>
            <div class='titulo-wrapper'>
                <div class='titulo-categoria'>{ci['name']}</div>
            </div>
            <div class='grupo-selector'>
        """
        
        group_titles = {
            'D1': 'Análise por diferença de tempo de 1s',
            'D5': 'Análise por diferença de tempo de 5s',
            'D10': 'Análise por diferença de tempo de 10s'
        }
        for g in groups:
            descricao = group_titles.get(g, g)
            html += f"<button onclick=\"mostrarGrupo('{g}','{cat}', '{descricao}')\" class='btn-grupo'>{g}</button>"

        html += "</div>"
        
        for i, (g, chs) in enumerate(groups.items()):
            active = ' active' if i == 0 else ''
            html += f"<div class='grupo{active}' data-categoria='{cat}' data-grupo='{g}'>"
            for c in chs:
                html += (
                    f"<div class='grafico-container'>"
                    f"<button class='btn-maximizar' onclick=\"maximizeChart('{c['canvas_id']}')\">🔍 Maximizar</button>"
                    f"<div class='grafico-titulo-container'>"
                    f"<h3 class='grafico-titulo'>{c['title']}</h3>"
                    f"</div>"
                    f"<div class='metricas' id='{c['metrics_id']}'>"
                    f"{c['metrics_info']}</div>"
                    f"<div class='chart-wrapper'><canvas id='{c['canvas_id']}' data-category='{c['category']}'></canvas></div>"
                    f"<div class='zoom-controls'>"
                    f"<button class='reset-btn' onclick=\"resetZoom('{c['canvas_id']}')\">Reset Zoom</button>"
                    f"</div>"
                    f"<div class='zoom-instruction'>Use o scroll do mouse para zoom, duplo clique para resetar ou clique direito em um ponto para copiar dados</div>"
                    f"</div>"
                )
            html += "</div>"
        html += "</div>"
        return html

    def generate_javascript_chart(self, c):
        labels = json.dumps(c['labels'])
        ds = json.dumps(c['datasets'])

        y_axis_label = {
            'distância': 'METROS (m)',
            'velocidade': 'VELOCIDADE (km/h)',
            'direção': 'DIREÇÃO (°)'
        }.get(c['category'], 'Valor')

        return f"""
        // Inicializa gráfico {c['canvas_id']}
        (function() {{
            const canvas = document.getElementById('{c['canvas_id']}');
            if (!canvas) {{
                console.error('Canvas {c['canvas_id']} não encontrado');
                return;
            }}
            
            const ctx = canvas.getContext('2d');
            const labels = {labels};
            const datasets = {ds};
            
            const {c['chart_var']} = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: datasets
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'nearest',
                        intersect: false
                    }},
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'top'
                        }},
                        zoom: {{
                            pan: {{
                                enabled: true,
                                mode: 'xy',
                                speed: 10,       
                                threshold: 10
                            }},
                            zoom: {{
                                wheel: {{
                                    enabled: true,
                                    speed: 0.1
                                }},
                                pinch: {{
                                    enabled: true
                                }},
                                drag:{{
                                    enabled: true, 
                                    backgroundColor: 'rgba(225,225,225,0.3)',
                                    borderWidth: 2                                 
                                }},
                                mode: 'xy'
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            type: 'category',
                            title: {{
                                display: true,
                                text: 'DIAS',
                                font: {{ weight: 'bold', size: 14 }},
                                color: '#222'             
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: '{y_axis_label}',
                                font: {{ weight: 'bold', size: 14}},
                                color: '#222'            
                            }}
                        }}
                    }}
                }}
            }});
            
            window.charts = window.charts || {{}};
            window.charts['{c['canvas_id']}'] = {c['chart_var']};

            // Adiciona evento de duplo clique para resetar zoom
            canvas.addEventListener('dblclick', function() {{
                {c['chart_var']}.resetZoom();
            }});

            // Adiciona evento de clique direito para copiar dados
            canvas.addEventListener('contextmenu', function(event) {{
                event.preventDefault();
                
                const canvasPosition = Chart.helpers.getRelativePosition(event, {c['chart_var']});
                const dataX = {c['chart_var']}.scales.x.getValueForPixel(canvasPosition.x);
                const dataY = {c['chart_var']}.scales.y.getValueForPixel(canvasPosition.y);
                
                if (dataX !== undefined && dataX !== null && dataX >= 0 && dataX < labels.length) {{
                    const dataIndex = Math.round(dataX);
                    const label = labels[dataIndex];
                    
                    // Coleta dados de todos os datasets para este ponto
                    const dadosPonto = [];
                    datasets.forEach((dataset, datasetIndex) => {{
                        if (dataset.data && dataset.data[dataIndex] !== undefined) {{
                            dadosPonto.push(dataset.label + ': ' + dataset.data[dataIndex]);
                        }}
                    }});
                    
                    const textoCompleto = 'Data/Hora: ' + label + '\\n' + dadosPonto.join('\\n');
                    
                    // Copia para clipboard
                    navigator.clipboard.writeText(textoCompleto).then(() => {{
                        showCopyNotification(event.pageX, event.pageY, 'Dados copiados!' + '\\n' + dadosPonto.length + ' valores');
                    }}).catch(err => {{
                        console.error('Erro ao copiar:', err);
                        showCopyNotification(event.pageX, event.pageY, 'Erro ao copiar', true);
                    }});
                }}
            }});
        }})();
        """

    def get_required_scripts(self):
        return """
        window.charts = {};
        let maximizedChartInstance = null;

        function showCopyNotification(x, y, message = '✓', isError = false) {
            const notification = document.createElement('div');
            notification.className = 'copy-notification';
            notification.style.position = 'fixed';
            notification.style.left = (x - 50) + 'px';
            notification.style.top = (y - 40) + 'px';
            notification.style.minWidth = '100px';
            notification.style.maxWidth = '200px';
            notification.style.padding = '12px 16px';
            notification.style.backgroundColor = isError ? '#f44336' : '#4CAF50';
            notification.style.color = '#fff';
            notification.style.borderRadius = '25px';
            notification.style.display = 'flex';
            notification.style.alignItems = 'center';
            notification.style.justifyContent = 'center';
            notification.style.fontSize = '14px';
            notification.style.fontWeight = 'bold';
            notification.style.zIndex = '99999';
            notification.style.pointerEvents = 'none';
            notification.style.boxShadow = isError ? '0 4px 20px rgba(244, 67, 54, 0.6)' : '0 4px 20px rgba(76, 175, 80, 0.6)';
            notification.style.border = isError ? '2px solid #d32f2f' : '2px solid #45a049';
            notification.style.textAlign = 'center';
            notification.style.lineHeight = '1.3';
            notification.style.whiteSpace = 'pre-line';
            
            if (message === '✓') {
                notification.innerHTML = '✓';
                notification.style.fontSize = '28px';
                notification.style.width = '50px';
                notification.style.height = '50px';
                notification.style.left = (x - 15) + 'px';
                notification.style.top = (y - 15) + 'px';
            } else {
                notification.innerHTML = message;
            }
            
            document.body.appendChild(notification);
            
            // Força reflow para ativar a animação
            void notification.offsetWidth;
            
            notification.style.transition = 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)';
            notification.style.transform = 'scale(0)';
            notification.style.opacity = '1';
            
            // Primeira animação: expande
            setTimeout(() => {
                notification.style.transform = 'scale(1)';
            }, 10);
            
            // Segunda animação: sobe e desaparece
            setTimeout(() => {
                notification.style.transform = 'scale(1.1) translateY(-60px)';
                notification.style.opacity = '0';
            }, message === '✓' ? 400 : 800);
            
            // Remove do DOM
            setTimeout(() => {
                notification.remove();
            }, message === '✓' ? 1200 : 1600);
        }

        function mostrarGrupo(grupo, categoria, descricao = '') {
            const grupos = document.querySelectorAll(`.grupo[data-categoria="${categoria}"]`);
            grupos.forEach(g => g.classList.remove('active'));

            const grupoSelecionado = document.querySelector(`.grupo[data-categoria="${categoria}"][data-grupo="${grupo}"]`);
            if (grupoSelecionado) {
                grupoSelecionado.classList.add('active');
            }

            if (descricao) {
                const titulos = grupoSelecionado.querySelectorAll('.grafico-titulo');
                titulos.forEach(t => t.textContent = descricao);
            }
        }

        function maximizeChart(chartId) {
            const originalChart = window.charts[chartId];
            if (!originalChart) return console.error('Gráfico não encontrado:', chartId);

            const canvasElem = document.getElementById(chartId);
            const titulo = canvasElem.closest('.grafico-container').querySelector('.grafico-titulo').textContent;
            
            let modal = document.getElementById('maximizedModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'maximizedModal';
                modal.className = 'modal';
                modal.innerHTML = `
                <div class="modal-content">
                    <span class="close-modal" onclick="closeModal()">&times;</span>
                    <h2 class="modal-titulo">${titulo}</h2>
                    <div class="modal-chart-container">
                        <canvas id="maximizedChart"></canvas>
                    </div>
                    <div class="legend-controls">
                        <button onclick="mostrarTodosMaximizado()">Mostrar Todos</button>
                        <button onclick="ocultarTodosMaximizado()">Ocultar Todos</button>
                    </div>
                </div>`;
                document.body.appendChild(modal);
            } else {
                modal.querySelector('.modal-titulo').textContent = titulo;
            }

            modal.style.display = 'block';

            const ctx = document.getElementById('maximizedChart').getContext('2d');
            if (maximizedChartInstance) maximizedChartInstance.destroy();

            maximizedChartInstance = new Chart(ctx, {
                type: 'line',
                data: JSON.parse(JSON.stringify(originalChart.data)),
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'nearest', intersect: false },
                    plugins: {
                        legend: { display: true, position: 'top' },
                        zoom: {
                            pan: {
                                enabled: true,
                                mode: 'xy'
                            },
                            zoom: {
                                wheel: {
                                    enabled: true,
                                    speed: 0.1
                                },
                                pinch: {
                                    enabled: true
                                },
                                drag: {
                                    enabled: true,
                                    backgroundColor: 'rgba(225,225,225,0.3)',
                                    borderWidth: 2
                                },
                                mode: 'xy'
                            }
                        }
                    },
                    scales: originalChart.options.scales
                }
            });
            
            const maximizedCanvas = document.getElementById('maximizedChart');
            maximizedCanvas.addEventListener('dblclick', function() {
                if (maximizedChartInstance) {
                    maximizedChartInstance.resetZoom();
                }
            });

            // Adiciona evento de clique direito para copiar dados no gráfico maximizado
            maximizedCanvas.addEventListener('contextmenu', function(event) {
                event.preventDefault();
                
                const canvasPosition = Chart.helpers.getRelativePosition(event, maximizedChartInstance);
                const dataX = maximizedChartInstance.scales.x.getValueForPixel(canvasPosition.x);
                const dataY = maximizedChartInstance.scales.y.getValueForPixel(canvasPosition.y);
                
                if (dataX !== undefined && dataX !== null && dataX >= 0 && dataX < maximizedChartInstance.data.labels.length) {
                    const dataIndex = Math.round(dataX);
                    const label = maximizedChartInstance.data.labels[dataIndex];
                    
                    // Coleta dados de todos os datasets para este ponto
                    const dadosPonto = [];
                    maximizedChartInstance.data.datasets.forEach((dataset, datasetIndex) => {
                        if (dataset.data && dataset.data[dataIndex] !== undefined) {
                            dadosPonto.push(dataset.label + ': ' + dataset.data[dataIndex]);
                        }
                    });
                    
                    const textoCompleto = 'Data/Hora: ' + label + '\\n' + dadosPonto.join('\\n');
                    
                    // Copia para clipboard
                    navigator.clipboard.writeText(textoCompleto).then(() => {
                        showCopyNotification(event.pageX, event.pageY, 'Dados copiados!' + '\\n' + dadosPonto.length + ' valores');
                    }).catch(err => {
                        console.error('Erro ao copiar:', err);
                        showCopyNotification(event.pageX, event.pageY, 'Erro ao copiar', true);
                    });
                }
            });
        }

        function closeModal() {
            const modal = document.getElementById('maximizedModal');
            if (modal) {
                modal.style.display = 'none';
            }
            
            if (maximizedChartInstance) {
                maximizedChartInstance.destroy();
                maximizedChartInstance = null;
            }
        }

        function resetZoom(chartId) {
            const chart = window.charts[chartId];
            if (chart && chart.resetZoom) {
                chart.resetZoom();
            }
        }

        function mostrarTodosMaximizado() {
            if (maximizedChartInstance) {
                maximizedChartInstance.data.datasets.forEach((ds, i) => {
                    maximizedChartInstance.setDatasetVisibility(i, true);
                });
                maximizedChartInstance.update();
            }
        }

        function ocultarTodosMaximizado() {
            if (maximizedChartInstance) {
                maximizedChartInstance.data.datasets.forEach((ds, i) => {
                    maximizedChartInstance.setDatasetVisibility(i, false);
                });
                maximizedChartInstance.update();
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            window.onclick = function(event) {
                const modal = document.getElementById('maximizedModal');
                if (event.target === modal) {
                    closeModal();
                }
            };
            
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Escape') {
                    closeModal();
                }
            });
        });
        """

    def get_required_styles(self):
        return """
        .grafico-titulo-container {
            display: flex;
            justify-content: center;
            width: 100%;
            margin-bottom: 15px;
        }

        .grafico-titulo {
            text-align: center;
            color: #495057;
            margin: 0;
            font-size: 1.4em;
            padding: 8px 20px;
            background: #f8f9fa;
            border-radius: 20px;
            display: inline-block;
        }

        .dashboard-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
            background-color: #f8f9fa;
            min-height: 100vh;
        }

        .dashboard-container h1, .dashboard-container h2 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }

        .titulo-wrapper {
            display: flex;
            justify-content: center;
            width: 100%;
            margin-bottom: 20px;
        }

        .dashboard-container .titulo-categoria {
            font-family: 'Saira', sans-serif;
            font-size: 2.4em;
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

        .dashboard-container .categoria {
            margin: 40px 0;
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .dashboard-container .grupo-selector {
            text-align: center;
            margin-bottom: 25px;
        }

        .dashboard-container .btn-grupo {
            margin: 5px;
            padding: 8px 20px;
            border: none;
            border-radius: 20px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
        }

        .dashboard-container .btn-grupo:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(79, 172, 254, 0.4);
        }

        .dashboard-container .grupo {
            display: none;
            flex-wrap: wrap;
            justify-content: center;
            gap: 30px;
            margin-bottom: 20px;
        }

        .dashboard-container .grupo.active {
            display: flex;
        }

        .dashboard-container .grafico-container {
            width: 100%;
            max-width: 900px;
            background: white;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            position: relative;
            text-align: center;
            border: 1px solid #e9ecef;
            transition: transform 0.3s ease;
        }

        .dashboard-container .grafico-container:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }

        .dashboard-container .metricas {
            font-weight: 600;
            margin-bottom: 15px;
            color: #6c757d;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
            font-size: 0.9em;
        }

        .dashboard-container .chart-wrapper {
            position: relative;
            height: 400px;
            width: 100%;
            margin-bottom: 15px;
        }

        .dashboard-container canvas {
            width: 100% !important;
            height: 100% !important;
        }

        .dashboard-container .zoom-controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 15px 0;
        }

        .dashboard-container .zoom-instruction {
            font-size: 12px;
            color: #868e96;
            margin-top: 10px;
            font-style: italic;
        }

        .btn-maximizar {
            position: absolute;
            top: 15px;
            right: 15px;
            padding: 8px 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            z-index: 10;
            transition: all 0.3s ease;
        }

        .btn-maximizar:hover {
            transform: scale(1.05);
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
            backdrop-filter: blur(5px);
        }

        .modal-content {
            background: white;
            margin: 2% auto;
            padding: 30px;
            border-radius: 20px;
            width: 90%;
            max-width: 95vw;
            max-height: 90vh;
            overflow: auto;
        }

        .close-modal {
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            float: right;
        }

        .modal-chart-container {
            width: 100%;
            height: 70vh;
            position: relative;
            margin-top: 20px;
        }

        .modal-titulo {
            margin: 0 0 20px 0;
            font-size: 1.5em;
            color: #333;
            text-align: center;
        }

        .legend-controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }

        .reset-btn {
            background-color: #8300FF !important;
            color: white !important;
            font-weight: 500;
            border: none;
            border-radius: 15px;
            padding: 6px 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .reset-btn:hover {
            transform: translateY(-1px);
            background-color: #6b00cc !important;
        }

        .copy-notification {
            animation: none !important;
        }
"""
    def get_cdn(self):
        return ['https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js',
                'https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js']
    
    def generate_dashboard(self, config):
        self.chart_counter = 0
        all_charts = []
        html_cats = []
        for cat, chs in config['categories'].items():
            darr = []
            for c in chs:
                c['categoria'] = cat
                c['titulo'] = c['titulo']
                c['grupo'] = c['grupo']
                cd = self.generate_chart_data(c)
                darr.append(cd)
                all_charts.append(cd)
            html_cats.append(self.generate_html_category(cat, darr))
        
        main_html = "<div class='dashboard-container'><h1>📊 Dashboard</h1>" + ''.join(html_cats) + "</div>"
        js_charts = ''.join(self.generate_javascript_chart(c) for c in all_charts)
        full_js = self.get_required_scripts() + "document.addEventListener('DOMContentLoaded',()=>{console.log('Inicializando dashboard...');setTimeout(()=>{" + js_charts + "console.log('Dashboard inicializado com sucesso!');},100)})"
        
        return {
            'css': self.get_required_styles(),
            'html': main_html,
            'js': full_js,
            'cdn': self.get_cdn()
        }

    def generate_modular_blocks(self, config):
        self.chart_counter = 0
        all_charts = []
        html_cats = []

        for cat, chs in config['categories'].items():
            darr = []
            for c in chs:
                c['categoria'] = cat
                c['titulo'] = c['titulo']
                c['grupo'] = c['grupo']
                cd = self.generate_chart_data(c)
                darr.append(cd)
                all_charts.append(cd)
            
            html_cats.append(self.generate_html_category(cat, darr))

        js_per_chart = []
        for c in all_charts:
            js_code = self.generate_javascript_chart(c)
            js_per_chart.append(f"<script>\n{js_code}\n</script>")

        cdn_block = "\n".join([f'<script src="{url}"></script>' for url in self.get_cdn()]) + "\n"
        css_block = f"<style>\n{self.get_required_styles()}\n</style>\n"
        html_final = f"<!-- Dashboard -->\n{''.join(html_cats)}\n<!-- /Dashboard -->\n\n" + "\n\n".join(js_per_chart)
        js_global = f"<script>\n{self.get_required_scripts()}\n</script>\n"

        return {
            'css': css_block,
            'html': html_final,
            'js': js_global,
            'cdn': cdn_block
        }

    def generate_single_chart_block(self, c):
        html = (
            f"<div class='grafico-container'>"
            f"<button class='btn-maximizar' onclick=\"maximizeChart('{c['canvas_id']}')\">🔍 Maximizar</button>"
            f"<div class='grafico-titulo-container'>"
            f"<h3 class='grafico-titulo'>{c['title']}</h3>"
            f"</div>"
            f"<div class='metricas' id='{c['metrics_id']}'>{c['metrics_info']}</div>"
            f"<div class='chart-wrapper'>"
            f"<canvas id='{c['canvas_id']}' data-category='{c['category']}'></canvas>"
            f"</div>"
            f"<div class='zoom-controls'>"
            f"<button class='reset-btn' onclick=\"resetZoom('{c['canvas_id']}')\">Reset Zoom</button>"
            f"</div>"
            f"<div class='zoom-instruction'>Use o scroll do mouse para zoom, duplo clique para resetar ou clique direito em um ponto para copiar dados</div>"
            f"</div>"
        )

        js_chart = self.generate_javascript_chart(c)
        return html, js_chart

    def save_single_chart_block(self, chart_config, output_path):
        html, js = self.generate_single_chart_block(chart_config)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('<style>\n')
            f.write(self.get_required_styles())
            f.write('\n</style>\n\n')

            for url in self.get_cdn():
                f.write(f'<script src="{url}"></script>\n')
            f.write('\n')

            f.write(html)
            f.write('\n\n')

            f.write('<script>\n')
            f.write(self.get_required_scripts())
            f.write(js)
            f.write('\n</script>\n')

        return output_path


def get_media_info(medias, tipo, grupo_id):
    if not medias:
        return "error"
    
    if tipo == 'distância':
        media_dist = medias.get('Distância', {}).get(grupo_id)
        media_disc = medias.get('Discrepancia', {}).get(grupo_id)

        infos = []
        if media_dist is not None:
            infos.append(f"Média Distância: {round(media_dist, 2)}")
        if media_disc is not None:
            infos.append(f"Média Discrepância: {round(media_disc, 2)}")
        return " | ".join(infos) if infos else "Dados disponíveis"
    
    mapeamento_tipos = {
        'velocidade': 'Diferença de Velocidade', 
        'direção': 'Diferença Angular'
    }
    
    chave_media = mapeamento_tipos.get(tipo)
    if chave_media and chave_media in medias and grupo_id in medias[chave_media]:
        media_valor = medias[chave_media][grupo_id]
        return f"Média: {round(media_valor, 2)}"
    
    return "Dados disponíveis"

def save_modular_blocks(blocks, filename='bloco_dashboard.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)

    output_path = base_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(blocks['cdn'] + '\n\n')
        f.write(blocks['css'] + '\n\n')
        f.write(blocks['html'] + '\n\n')
        f.write(blocks['js'])

    return output_path

def out_html(input1, input2, match_path, tipo, template_path=None, medias=None, save_blocks=False):
    def ler(p):
        for e in ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']:
            try:
                return pd.read_csv(p, encoding=e, engine='python', on_bad_lines='warn')
            except:
                pass
        raise

    df1, df2, dfm = ler(input1), ler(input2), ler(match_path)
    df1['Fonte'] = 'Teste'
    df2['Fonte'] = 'Referência'
    df = pd.concat([df1, df2], ignore_index=True)

    if 'Discrepancia' in dfm.columns:
        dfm['Discrepancia'] = dfm['Discrepancia'].astype(str).str.replace('*', '', regex=False)
        dfm['Discrepancia'] = pd.to_numeric(dfm['Discrepancia'], errors='coerce')

    tipos = ['distância', 'velocidade', 'direção'] if tipo == 'todas' else [tipo]
    grupos = set()
    for m in dfm['Match_Complete'].dropna():
        r = re.match(r"(T)(\d+)_", str(m))
        if r:
            grupos.add(r.groups())
    grupos = sorted(grupos, key=lambda x: int(x[1]))

    cfg = {'categories': {}}
    for op in tipos:
        cfg['categories'][op] = []
        for t, g in grupos:
            key = f"{t}{g}_"
            sub = dfm[dfm['Match_Complete'].str.contains(key, na=False)]
            if sub.empty:
                continue

            ts = df[df['Match_Complete'].str.contains(key, na=False) & (df['Fonte'] == 'Teste')].copy()
            ts['GNSS UTC Time'] = pd.to_datetime(ts['GNSS UTC Time'], errors='coerce')
            labels = ts['GNSS UTC Time'].dt.strftime('%d/%m/%Y %H:%M:%S').tolist()
            legenda_mapeada = {
                'D1': 'Análise por diferença de tempo de 1s',
                'D5': 'Análise por diferença de tempo de 5s',
                'D10': 'Análise por diferença de tempo de 10s'
            }
            grupo_id = f"D{g}"
            legenda = legenda_mapeada.get(grupo_id, "Análise")

            metrics_info = get_media_info(medias, op, grupo_id)
            titulo = f"{legenda}"

            if op == 'distância' and 'Distância' in sub.columns:
                cfg['categories'][op].append({
                    'grupo': grupo_id,
                    'labels': labels,
                    'datasets': [
                        {
                            'label': f"Discrepância ({t}{g})",
                            'data': sub['Discrepancia'].astype(float).tolist(),
                            'borderColor': 'gold',
                            'backgroundColor': 'gold',
                            'pointColor': 'gold',
                            'fill': False  
                        }
                    ],
                    'titulo': titulo,
                    'metrics_info': metrics_info
                })

            if op == 'velocidade' and 'Velocidade' in df.columns:
                tr = ts['Velocidade'].astype(float).tolist()
                rf = df[df['Match_Complete'].str.contains(key, na=False) & (df['Fonte'] == 'Referência')]['Velocidade'].astype(float).tolist()
                diff = [abs(a - b) for a, b in zip(tr, rf)]
                cfg['categories'][op].append({
                    'grupo': grupo_id,
                    'labels': labels,
                    'datasets': [
                        {'label': 'Teste', 'data': tr, 'borderColor': '#17becf'},
                        {'label': 'Referência', 'data': rf, 'borderColor': '#12094A'},
                        {'label': 'Diferença', 'data': diff, 'borderColor': 'gold'}
                    ],
                    'titulo': titulo,
                    'metrics_info': metrics_info
                })

            if op == 'direção' and 'Diferença Angular' in dfm.columns:
                tr = ts['Azimuth' if 'Azimuth' in ts.columns else 'Heading'].astype(float).tolist()
                rf = df[(df['Match_Complete'].str.contains(key, na=False)) & (df['Fonte'] == 'Referência')]['Azimuth' if 'Azimuth' in df.columns else 'Heading'].astype(float).tolist()
                diff = sub['Diferença Angular'].astype(float).tolist()
                cfg['categories'][op].append({
                    'grupo': grupo_id,
                    'labels': labels,
                    'datasets': [
                        {'label': 'Teste', 'data': tr, 'borderColor': '#17becf'},
                        {'label': 'Referência', 'data': rf, 'borderColor': '#12094A'},
                        {'label': 'Diferença', 'data': diff, 'borderColor': 'gold'}
                    ],
                    'titulo': titulo,
                    'metrics_info': metrics_info
                })

    gen = ChartJSDashboardGenerator()
    
    if save_blocks:
        blocks = gen.generate_modular_blocks(cfg)
        combined_path = save_modular_blocks(blocks, filename='bloco_dashboard.html')
        return combined_path
    else:
        db = gen.generate_dashboard(cfg)
        output = template_path.replace('.html', '_with_dashboard.html') if template_path else tempfile.NamedTemporaryFile(delete=False, suffix='.html').name
        gen.insert_into_html_file(template_path, db, output)
        webbrowser.open(f"file://{os.path.abspath(output)}")
        return output