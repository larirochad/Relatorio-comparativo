import pandas as pd
import json
import os
from pathlib import Path

def gerar_bloco_grafico(df, filename='bloco_eventos_diarios.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # df = pd.read_csv(csv_path)
    df['Dias'] = pd.to_datetime(df['Dias'], format='%d/%m/%Y')
    df['Dias'] = df['Dias'].dt.strftime('%d/%m/%Y')

    labels = df['Dias'].tolist()

    cores = [
        "#0e0561",   # periodica ref
        "#3ae8ff",   # periodida teste
        "#3b08b3",   # economico ref
        "#4ff9ff",   # economico teste 
        "#3c04d6",   # ign ref
        '#00bfff',   # ign teste
        "#2519CC",   # igf ref
        "#48d8f1ff",   # igf teste
        '#9370db',   # Roxo acinzentado
        '#000000'    # Preto
    ]

    cor_referencia = '#12094A'   # Azul Claro
    cor_teste = '#17becf'      # Azul Escuro

    # Gráfico de linha
    datasets_linhas = []
    for idx, col in enumerate(df.columns[1:]):  # Ignora a coluna 'Dias'
        datasets_linhas.append({
            "label": col,
            "data": df[col].tolist(),
            "borderColor": cores[idx % len(cores)],
            "backgroundColor": cores[idx % len(cores)].replace('1)', '0.1)'),
            "fill": False,
            "tension": 0.3,
            "pointRadius": 4,
            "pointHoverRadius": 6,
            "pointBackgroundColor": cores[idx % len(cores)],
            "pointBorderColor": cores[idx % len(cores)],
            "hidden": False
        })

    # Gráfico de barras
    colunas = df.columns[1:]
    totais = df[colunas].sum().to_dict()
    labels_totais = list(totais.keys())
    valores_totais = list(totais.values())

    # Aplicando a cor de forma condicional
    background_colors = []
    border_colors = []

    for label in labels_totais:
        if 'referencia' in label.lower():
            background_colors.append(cor_referencia)
            border_colors.append(cor_referencia)
        elif 'teste' in label.lower():
            background_colors.append(cor_teste)
            border_colors.append(cor_teste)
        else:
            # Fallback se não for nenhum dos dois (você pode alterar se quiser)
            background_colors.append('rgba(128, 128, 128, 1)')  # Cinza por exemplo
            border_colors.append('rgba(128, 128, 128, 1)')

    dataset_barras = [{
        "label": "Total por categoria",
        "data": valores_totais,
        "backgroundColor": background_colors,
        "borderColor": border_colors,
        "borderWidth": 1
    }]

    css_local = """
        <style>
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

        .zoom-controls button,
        .legend-controls button,
        .filter-buttons button {
            padding: 6px 15px;
            border: none;
            border-radius: 15px;
            font-size: 12px;
            cursor: pointer;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .zoom-controls button:hover,
        .legend-controls button:hover,
        .filter-buttons button:hover {
            transform: translateY(-1px);
            opacity: 0.9;
        }


        .legend-controls,
        .filter-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        
        .grafico-container {
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

        .grafico-container:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }
        body {
            background-color: #f8f9fa;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }

        .dashboard-container {
            padding: 20px;
            background-color: #f8f9fa;
            min-height: 100vh;
        }

        .grafico-titulo-container {
            display: flex;
            justify-content: center;
            width: 100%;
            margin-bottom: 25px;
        }

        .grafico-titulo {
            text-align: center;
            color: #495057;
            margin: 0;
            font-size: 2em;
            padding: 8px 20px;
            background: #f8f9fa;
            border-radius: 20px;
            display: inline-block;
        }
        
        /* Estilo específico para os botões de filtro */
        .filter-buttons button.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .titulo-wrapper {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }

        .titulo-categoria {
            font-size: 34px;
            font-weight: bold;
            color: white;
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 30px;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            text-align: center;
        }


        </style>
        """

    html = f"""{css_local}

    <!-- BLOCO DE GRÁFICO - INÍCIO -->
    <div class='dashboard-container'>
        <div class='categoria'>
            <div class='titulo-wrapper'>
                <div class='titulo-categoria'>Análise de Eventos</div>
            </div>
            <div class='grupo active' data-categoria='eventos_diarios' data-grupo='D0'>

                <div class='grafico-container'>
                    <button class='btn-maximizar' onclick="maximizeChart('linhaEventos')">🔍 Maximizar</button>
                    <div class='grafico-titulo-container'>
                        <h3 class='grafico-titulo'>Evolução Diária dos Eventos</h3>
                    </div>
                    
                    <div class='filter-buttons'>
                        <button id="btn-periodicas" onclick="filtrarCategoria('linhaEventos', 'Periódicas')">Periódicas</button>
                        <button id="btn-modo-economico" onclick="filtrarCategoria('linhaEventos', 'Modo econômico')">Modo econômico</button>
                        <button id="btn-ignicao-on" onclick="filtrarCategoria('linhaEventos', 'Ignição on')">Ignição on</button>
                        <button id="btn-ignicao-off" onclick="filtrarCategoria('linhaEventos', 'Ignição off')">Ignição off</button>
                    </div>
                    
                    <div class='chart-wrapper'>
                        <canvas id="linhaEventos"></canvas>
                    </div>
                    <div class='zoom-controls'>
                        <button onclick="resetZoom('linhaEventos')">Reset Zoom</button>
                    </div>
                    <div class='legend-controls'>
                        <button onclick="mostrarTodos('linhaEventos')">Mostrar Todos</button>
                        <button onclick="ocultarTodos('linhaEventos')">Ocultar Todos</button>
                    </div>
                    <div class='zoom-instruction'>Use o scroll do mouse para zoom ou duplo clique para resetar</div>
                </div>

                <div class='grafico-container'>
                    <button class='btn-maximizar' onclick="maximizeChart('barrasTotais')">🔍 Maximizar</button>
                    <div class='grafico-titulo-container'>
                        <h3 class='grafico-titulo'>Total de Eventos por Categoria</h3>
                    </div>
                    <div class='chart-wrapper'>
                        <canvas id="barrasTotais"></canvas>
                    </div>
                    <div class='zoom-controls'>
                        <button onclick="resetZoom('barrasTotais')">Reset Zoom</button>
                    </div>
                    <div class='zoom-instruction'>Use o scroll do mouse para zoom ou duplo clique para resetar</div>
                </div>

            </div>
        </div>
    </div>

    <script>
    // Sistema de controle de estado robusto
    let controleFiltros = {{
        filtroAtivo: null,
        estadoOriginal: {{}},
        estadoIndividual: {{}},
        estadoMostrarTodos: false,
        estadoOcultarTodos: false
    }};
    
    // Aguarda o carregamento completo do DOM e das dependências
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(function() {{
            if (typeof window.charts === 'undefined') {{
                window.charts = {{}};
            }}
            if (typeof Chart !== 'undefined' && Chart.register && typeof ChartZoom !== 'undefined') {{
                Chart.register(ChartZoom);
            }}
            const linhaCanvas = document.getElementById('linhaEventos');
            const barrasCanvas = document.getElementById('barrasTotais');

            if (linhaCanvas && !window.charts['linhaEventos']) {{
                window.charts['linhaEventos'] = new Chart(linhaCanvas.getContext('2d'), {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(labels)},
                        datasets: {json.dumps(datasets_linhas)}
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{ mode: 'index', intersect: false }},
                        plugins: {{
                            title: {{ display: false }},
                            legend: {{ 
                                position: 'top',
                                onClick: function(e, legendItem, legend) {{
                                    // INTERCEPTAR CLIQUE NA LEGENDA - VALIDAÇÃO SOBERANA
                                    const chartId = 'linhaEventos';
                                    const chart = window.charts[chartId];
                                    const datasetIndex = legendItem.datasetIndex;
                                    const dataset = chart.data.datasets[datasetIndex];
                                    
                                    // Se há filtro ativo, validar se o dataset pertence à categoria
                                    if (controleFiltros.filtroAtivo) {{
                                        const pertence = pertenceCategoria(dataset.label, controleFiltros.filtroAtivo);
                                        if (!pertence) {{
                                            // BLOQUEAR: Dataset não pertence à categoria filtrada
                                            console.log(`❌ Clique bloqueado: "${{dataset.label}}" não pertence à categoria "${{controleFiltros.filtroAtivo}}"`);
                                            return; // IMPEDIR a ação padrão
                                        }}
                                    }}
                                    
                                    // Permitir alternância apenas dentro da categoria (ou sem filtro)
                                    dataset.hidden = !dataset.hidden;
                                    controleFiltros.estadoIndividual[chartId][dataset.label] = !dataset.hidden;
                                    chart.update();
                                }}
                            }},
                            zoom: {{
                                pan: {{ enabled: true, mode: 'xy' }},
                                zoom: {{ wheel: {{ enabled: true }}, pinch: {{ enabled: true }}, drag: {{ enabled: true }}, mode: 'xy' }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                title: {{
                                    display: true,
                                    text: 'QUANTIDADE DE MENSAGENS',  
                                    font: {{
                                        size: 14,         
                                        weight: 'bold',   
                                        family: 'Arial'   
                                    }},
                                    color: '#000000'     
                                }},
                            }},
                            x: {{ 
                                title: {{ 
                                    display: true,
                                    text: 'DIAS',
                                    font: {{
                                        size: 14,
                                        weight: 'bold',
                                        family: 'Arial'
                                    }},
                                    color: '#000000'
                                }},
                            }}
                        }}
                    }}
                }});
                
                // Inicializar sistema de controle
                inicializarControle('linhaEventos');
                
                linhaCanvas.addEventListener('dblclick', function() {{
                    if(window.charts['linhaEventos']) {{
                        window.charts['linhaEventos'].resetZoom();
                    }}
                }});
            }}

            if (barrasCanvas && !window.charts['barrasTotais']) {{
                window.charts['barrasTotais'] = new Chart(barrasCanvas.getContext('2d'), {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(labels_totais)},
                        datasets: {json.dumps(dataset_barras)}
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            title: {{ display: false }},
                            legend: {{ display: false }},
                            zoom: {{
                                pan: {{ enabled: true, mode: 'xy' }},
                                zoom: {{ wheel: {{ enabled: true }}, pinch: {{ enabled: true }}, drag: {{ enabled: true }}, mode: 'xy' }}
                            }}
                        }},
                        scales: {{
                            y: {{ 
                                beginAtZero: true,
                                title: {{ 
                                    display: true,
                                    text: 'TOTAL',
                                    font: {{
                                        size: 14,
                                        weight: 'bold',
                                        family: 'Arial'
                                    }},
                                    color: '#000000'
                                 }},
                             }},
                            x: {{ 
                                title: {{ 
                                    display: true,
                                    text: 'CATEGORIA',
                                    font: {{
                                        size: 14,
                                        weight: 'bold',
                                        family: 'Arial'
                                    }},
                                    color: '#000000'
                                 }},
                            }}
                        }}
                    }}
                }});
                barrasCanvas.addEventListener('dblclick', function() {{
                    if(window.charts['barrasTotais']) {{
                        window.charts['barrasTotais'].resetZoom();
                    }}
                }});
            }}
        }}, 100);
    }});
    
    // Função para inicializar o sistema de controle
    function inicializarControle(chartId) {{
        const chart = window.charts[chartId];
        if (!chart) return;
        
        // Salvar estado original
        controleFiltros.estadoOriginal[chartId] = {{}};
        controleFiltros.estadoIndividual[chartId] = {{}};
        
        chart.data.datasets.forEach((dataset, index) => {{
            controleFiltros.estadoOriginal[chartId][index] = !dataset.hidden;
            controleFiltros.estadoIndividual[chartId][dataset.label] = !dataset.hidden;
        }});
    }}
    
    // Função para identificar se dataset pertence à categoria
    function pertenceCategoria(label, categoria) {{
        const labelLower = label.toLowerCase();
        
        switch(categoria) {{
            case 'Periódicas':
                return labelLower.includes('periódica') || labelLower.includes('periodica');
            case 'Modo econômico':
                return labelLower.includes('modo econômico') || labelLower.includes('modo economico');
            case 'Ignição on':
                return labelLower.includes('ignição ligada') || labelLower.includes('ignicao ligada') || 
                       labelLower.includes('ignição on') || labelLower.includes('ignicao on');
            case 'Ignição off':
                return labelLower.includes('ignição desligada') || labelLower.includes('ignicao desligada') ||
                       labelLower.includes('ignição off') || labelLower.includes('ignicao off');
            default:
                return false;
        }}
    }}
    
    // Função para atualizar visual dos botões
    function atualizarBotoes(categoriaAtiva = null) {{
        const botoes = document.querySelectorAll('.filter-buttons button');
        botoes.forEach(btn => {{
            btn.classList.remove('active');
        }});
        
        if (categoriaAtiva) {{
            const btnId = {{
                'Periódicas': 'btn-periodicas',
                'Modo econômico': 'btn-modo-economico', 
                'Ignição on': 'btn-ignicao-on',
                'Ignição off': 'btn-ignicao-off'
            }}[categoriaAtiva];
            
            if (btnId) {{
                const btn = document.getElementById(btnId);
                if (btn) btn.classList.add('active');
            }}
        }}
    }}
    
    // Função melhorada para filtrar categorias
    function filtrarCategoria(chartId, categoria) {{
        const chart = window.charts[chartId];
        if (!chart) return;

        // Resetar estados de mostrar/ocultar todos
        controleFiltros.estadoMostrarTodos = false;
        controleFiltros.estadoOcultarTodos = false;

        // Se a mesma categoria já está ativa, desativar filtro
        if (controleFiltros.filtroAtivo === categoria) {{
            limparFiltros(chartId);
            return;
        }}

        controleFiltros.filtroAtivo = categoria;

        // Aplicar filtro SOBERANO
        chart.data.datasets.forEach((dataset, index) => {{
            const pertence = pertenceCategoria(dataset.label, categoria);
            dataset.hidden = !pertence;
            // Salvar estado individual
            controleFiltros.estadoIndividual[chartId][dataset.label] = pertence;
        }});

        atualizarBotoes(categoria);
        chart.update();
        
        console.log(`✅ Filtro ativo: "${{categoria}}". Apenas datasets desta categoria podem ser manipulados.`);
    }}
    
    // Função para limpar filtros
    function limparFiltros(chartId) {{
        const chart = window.charts[chartId];
        if (!chart) return;
        
        controleFiltros.filtroAtivo = null;
        
        // Restaurar estado original
        chart.data.datasets.forEach((dataset, index) => {{
            dataset.hidden = !controleFiltros.estadoOriginal[chartId][index];
            controleFiltros.estadoIndividual[chartId][dataset.label] = controleFiltros.estadoOriginal[chartId][index];
        }});
        
        atualizarBotoes();
        chart.update();
        
        console.log(`🔄 Filtros limpos. Todos os controles liberados.`);
    }}
    
    // Função para mostrar todos (RESPEITANDO filtros ativos)
    function mostrarTodos(chartId) {{
        const chart = window.charts[chartId];
        if (!chart) return;

        controleFiltros.estadoMostrarTodos = true;
        controleFiltros.estadoOcultarTodos = false;

        if (controleFiltros.filtroAtivo) {{
            // FILTRO SOBERANO: Mostrar apenas os da categoria filtrada
            chart.data.datasets.forEach((dataset, index) => {{
                const pertence = pertenceCategoria(dataset.label, controleFiltros.filtroAtivo);
                if (pertence) {{
                    dataset.hidden = false;
                    controleFiltros.estadoIndividual[chartId][dataset.label] = true;
                }} else {{
                    // MANTER OCULTOS os que não pertencem à categoria
                    dataset.hidden = true;
                    controleFiltros.estadoIndividual[chartId][dataset.label] = false;
                }}
            }});
            console.log(`📊 "Mostrar Todos" aplicado APENAS à categoria: "${{controleFiltros.filtroAtivo}}"`);
        }} else {{
            // Sem filtro ativo: mostrar todos livremente
            chart.data.datasets.forEach((dataset, index) => {{
                dataset.hidden = false;
                controleFiltros.estadoIndividual[chartId][dataset.label] = true;
            }});
            console.log(`📊 "Mostrar Todos" aplicado a todos os datasets (sem filtro ativo)`);
        }}

        chart.update();
    }}

    // Função para ocultar todos (RESPEITANDO filtros ativos)
    function ocultarTodos(chartId) {{
        const chart = window.charts[chartId];
        if (!chart) return;

        controleFiltros.estadoMostrarTodos = false;
        controleFiltros.estadoOcultarTodos = true;

        if (controleFiltros.filtroAtivo) {{
            // FILTRO SOBERANO: Ocultar apenas os da categoria filtrada
            chart.data.datasets.forEach((dataset, index) => {{
                const pertence = pertenceCategoria(dataset.label, controleFiltros.filtroAtivo);
                if (pertence) {{
                    dataset.hidden = true;
                    controleFiltros.estadoIndividual[chartId][dataset.label] = false;
                }}
                // NÃO TOCAR nos que não pertencem à categoria (já estão ocultos)
            }});
            console.log(`📊 "Ocultar Todos" aplicado APENAS à categoria: "${{controleFiltros.filtroAtivo}}"`);
        }} else {{
            // Sem filtro ativo: ocultar todos livremente
            chart.data.datasets.forEach((dataset, index) => {{
                dataset.hidden = true;
                controleFiltros.estadoIndividual[chartId][dataset.label] = false;
            }});
            console.log(`📊 "Ocultar Todos" aplicado a todos os datasets (sem filtro ativo)`);
        }}

        chart.update();
    }}

    // Função para maximizar o gráfico
    function maximizeChart(chartId) {{
        const chart = window.charts[chartId];
        if (!chart) return;
        
        const canvas = document.getElementById(chartId);
        if (!canvas) return;
        
        if (canvas.style.position === 'fixed') {{
            // Restaurar tamanho normal
            canvas.style.position = '';
            canvas.style.top = '';
            canvas.style.left = '';
            canvas.style.width = '';
            canvas.style.height = '';
            canvas.style.zIndex = '';
            canvas.style.backgroundColor = '';
        }} else {{
            // Maximizar
            canvas.style.position = 'fixed';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100vw';
            canvas.style.height = '100vh';
            canvas.style.zIndex = '9999';
            canvas.style.backgroundColor = 'white';
        }}
        
        chart.resize();
    }}
    
    // Função para resetar o zoom
    function resetZoom(chartId) {{
        const chart = window.charts[chartId];
        if (chart && chart.resetZoom) {{
            chart.resetZoom();
        }}
    }}

    </script>

    <!-- BLOCO DE GRÁFICO - FIM -->
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # print(f"✅ Bloco de gráfico salvo em: {output_path.resolve()}")


# if __name__ == "__main__":
#     gerar_bloco_grafico(
#         csv_path='resumo_eventos_diarios.csv',
#         filename='bloco_eventos_diarios.html'
#     )