import pandas as pd
from pathlib import Path
import json

def extrair_dados_mapa(input1, input2, match_path):
    """
    Extrai dados dos matches para serem usados no mapa integrado
    Retorna um dicionário JSON com os dados organizados por grupo
    """
    # Ler os dados
    def ler_csv(p):
        for e in ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']:
            try:
                return pd.read_csv(p, encoding=e, engine='python', on_bad_lines='warn')
            except:
                pass
        raise ValueError(f"Não foi possível ler o arquivo {p}")
    
    df1 = ler_csv(input1)
    df2 = ler_csv(input2)
    dfm = ler_csv(match_path)
    
    # Adicionar fonte
    df1['Fonte'] = 'Teste'
    df2['Fonte'] = 'Referência'
    df = pd.concat([df1, df2], ignore_index=True)
    
    # Detectar coluna de direção
    dir_col = None
    for col in ['Azimuth', 'Heading']:
        if col in df.columns:
            dir_col = col
            break
    
    if dir_col is None:
        return {'D1': [], 'D5': [], 'D10': []}
    
    # Organizar dados por grupo (D1, D5, D10)
    grupos_data = {
        'D1': [],
        'D5': [],
        'D10': []
    }
    
    # Processar cada match
    for _, row in dfm.iterrows():
        match_complete = str(row.get('Match_Complete', ''))
        if pd.isna(match_complete) or match_complete == 'nan':
            continue
        
        # Extrair tipo (T1, T5, T10)
        if match_complete.startswith('T1_'):
            grupo = 'D1'
        elif match_complete.startswith('T5_'):
            grupo = 'D5'
        elif match_complete.startswith('T10_'):
            grupo = 'D10'
        else:
            continue
        
        # Buscar dados correspondentes nos dataframes
        df_match = df[df['Match_Complete'] == match_complete]
        
        if len(df_match) < 2:
            continue
        
        teste = df_match[df_match['Fonte'] == 'Teste'].iloc[0]
        ref = df_match[df_match['Fonte'] == 'Referência'].iloc[0]
        
        # Extrair dados necessários
        try:
            dados_match = {
                'match_id': match_complete,
                'teste': {
                    'lat': float(teste['Latitude']),
                    'lon': float(teste['Longitude']),
                    'dir': float(teste[dir_col]),
                    'vel': float(teste.get('Velocidade', 0)),
                    'time': str(teste.get('GNSS UTC Time', ''))
                },
                'ref': {
                    'lat': float(ref['Latitude']),
                    'lon': float(ref['Longitude']),
                    'dir': float(ref[dir_col]),
                    'vel': float(ref.get('Velocidade', 0)),
                    'time': str(ref.get('GNSS UTC Time', ''))
                },
                'diff_angular': float(row.get('Diferença Angular', 0)) if 'Diferença Angular' in row else None
            }
            grupos_data[grupo].append(dados_match)
        except Exception as e:
            print(f"Erro ao processar match {match_complete}: {e}")
            continue
    
    return grupos_data


def gerar_mapa_direcoes(input1, input2, match_path, output_path=None):
    """
    Gera um HTML interativo com mapa mostrando as posições e direções dos dispositivos
    agrupados por D1, D5 e D10 (match types)
    
    Args:
        input1: Path para CSV do dispositivo teste (match1)
        input2: Path para CSV do dispositivo referência (match2)
        match_path: Path para CSV com os matches (outputGeral.csv)
        output_path: Path para salvar o HTML (opcional)
    
    Returns:
        Path do arquivo HTML gerado
    """
    
    # Ler os dados
    def ler_csv(p):
        for e in ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']:
            try:
                return pd.read_csv(p, encoding=e, engine='python', on_bad_lines='warn')
            except:
                pass
        raise ValueError(f"Não foi possível ler o arquivo {p}")
    
    df1 = ler_csv(input1)
    df2 = ler_csv(input2)
    dfm = ler_csv(match_path)
    
    # Extrair trajetos completos (GTERI e ignições)
    def extrair_trajeto(df):
        trajeto = []
        # Verificar se existe coluna Parsed ou Event Type
        if 'Parsed' in df.columns:
            filtro = df['Parsed'].astype(str).str.contains('GTERI|GTIGN|GTIGF', case=False, na=False)
            df_filtrado = df[filtro]
        elif 'Event Type' in df.columns:
            filtro = df['Event Type'].astype(str).str.contains('GTERI|GTIGN|20|21|GTIGF', case=False, na=False)
            df_filtrado = df[filtro]
        else:
            # Se não tem coluna específica, tenta buscar em todas as colunas string
            df_filtrado = df
            
        for _, row in df_filtrado.iterrows():
            try:
                if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
                    ponto = {
                        'lat': float(row['Latitude']),
                        'lon': float(row['Longitude']),
                        'time': str(row.get('GNSS UTC Time', '')),
                        'vel': float(row.get('Velocidade', 0)) if pd.notna(row.get('Velocidade')) else 0
                    }
                    trajeto.append(ponto)
            except:
                continue
        return trajeto
    
    trajeto_teste = extrair_trajeto(df1)
    trajeto_ref = extrair_trajeto(df2)
    
    # Adicionar fonte
    df1['Fonte'] = 'Teste'
    df2['Fonte'] = 'Referência'
    df = pd.concat([df1, df2], ignore_index=True)
    
    # Detectar coluna de direção
    dir_col = None
    for col in ['Azimuth', 'Heading']:
        if col in df.columns:
            dir_col = col
            break
    
    if dir_col is None:
        raise ValueError("Coluna de direção (Azimuth ou Heading) não encontrada")
    
    # Organizar dados por grupo (D1, D5, D10)
    grupos_data = {
        'D1': [],
        'D5': [],
        'D10': []
    }
    
    # Processar cada match
    for _, row in dfm.iterrows():
        match_complete = str(row.get('Match_Complete', ''))
        if pd.isna(match_complete) or match_complete == 'nan':
            continue
        
        # Extrair tipo (T1, T5, T10)
        if match_complete.startswith('T1_'):
            grupo = 'D1'
        elif match_complete.startswith('T5_'):
            grupo = 'D5'
        elif match_complete.startswith('T10_'):
            grupo = 'D10'
        else:
            continue
        
        # Buscar dados correspondentes nos dataframes
        df_match = df[df['Match_Complete'] == match_complete]
        
        if len(df_match) < 2:
            continue
        
        teste = df_match[df_match['Fonte'] == 'Teste'].iloc[0]
        ref = df_match[df_match['Fonte'] == 'Referência'].iloc[0]
        
        # Extrair dados necessários
        try:
            dados_match = {
                'match_id': match_complete,
                'teste': {
                    'lat': float(teste['Latitude']),
                    'lon': float(teste['Longitude']),
                    'dir': float(teste[dir_col]),
                    'vel': float(teste.get('Velocidade', 0)),
                    'time': str(teste.get('GNSS UTC Time', ''))
                },
                'ref': {
                    'lat': float(ref['Latitude']),
                    'lon': float(ref['Longitude']),
                    'dir': float(ref[dir_col]),
                    'vel': float(ref.get('Velocidade', 0)),
                    'time': str(ref.get('GNSS UTC Time', ''))
                },
                'diff_angular': float(row.get('Diferença Angular', 0)) if 'Diferença Angular' in row else None
            }
            grupos_data[grupo].append(dados_match)
        except Exception as e:
            print(f"Erro ao processar match {match_complete}: {e}")
            continue
    
    # Gerar HTML
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mapa de Direções - Análise Comparativa</title>
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 15px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 1.3em;
        }}
        
        .controls {{
            padding: 10px;
            background: white;
            border-bottom: 2px solid #dee2e6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .btn-grupo-mapa {{
            padding: 8px 20px;
            border: none;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        .btn-grupo-mapa.active {{
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }}
        
        .btn-d1 {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}
        
        .btn-d5 {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }}
        
        .btn-d10 {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            color: white;
        }}
        
        .btn-trajeto {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 20px;
            border: none;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        .btn-trajeto.active {{
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }}
        
        .btn-grupo-mapa:hover, .btn-trajeto:hover {{
            transform: translateY(-2px);
        }}
        
        #map {{
            height: calc(100vh - 100px);
            width: 100%;
            float: left;
            transition: width 0.3s ease;
        }}
        
        .sidebar {{
            width: 280px;
            height: calc(100vh - 100px);
            position: fixed;
            right: -280px;
            top: 100px;
            background: white;
            overflow-y: auto;
            box-shadow: -2px 0 6px rgba(0,0,0,0.1);
            padding: 15px;
            transition: right 0.3s ease;
            z-index: 500;
        }}
        
        .sidebar.open {{
            right: 0;
        }}
        
        .sidebar-toggle {{
            position: fixed;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px 0 0 8px;
            padding: 15px 10px;
            cursor: pointer;
            font-size: 20px;
            box-shadow: -2px 2px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            z-index: 1001;
        }}
        
        .sidebar-toggle:hover {{
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            transform: translateY(-50%) translateX(-3px);
        }}
        
        .sidebar.open .sidebar-toggle {{
            right: 280px;
        }}
        
        .sidebar h3 {{
            margin: 0 0 15px 0;
            font-size: 16px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
        }}
        
        .day-filter {{
            margin-bottom: 20px;
        }}
        
        .day-checkbox {{
            display: flex;
            align-items: center;
            padding: 8px;
            margin: 5px 0;
            border-radius: 5px;
            transition: background 0.2s;
            cursor: pointer;
        }}
        
        .day-checkbox:hover {{
            background: #f0f0f0;
        }}
        
        .day-checkbox input[type="checkbox"] {{
            margin-right: 10px;
            cursor: pointer;
            width: 16px;
            height: 16px;
        }}
        
        .day-checkbox label {{
            cursor: pointer;
            flex: 1;
            font-size: 13px;
        }}
        
        .point-count {{
            font-size: 11px;
            color: #666;
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 10px;
            margin-left: 5px;
        }}
        
        .filter-section {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .filter-section.disabled {{
            opacity: 0.5;
            pointer-events: none;
        }}
        
        .btn-select-all {{
            background: #6c757d;
            color: white;
            border: none;
            padding: 5px 12px;
            border-radius: 5px;
            font-size: 12px;
            cursor: pointer;
            margin-right: 5px;
            margin-bottom: 10px;
        }}
        
        .btn-select-all:hover {{
            background: #5a6268;
        }}
        
        .legend {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 250px;
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 1000;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 13px;
        }}
        
        .legend-color {{
            width: 30px;
            height: 4px;
            margin-right: 10px;
            border-radius: 2px;
        }}
        
        .btn-clear {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 8px 20px;
            border: none;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .btn-clear:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }}
        
        .divider {{
            width: 1px;
            height: 30px;
            background: #dee2e6;
            margin: 0 5px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🗺️ Mapa de Análise de Direções</h1>
    </div>
    
    <div class="controls">
        <button class="btn-grupo-mapa btn-d1 active" onclick="mostrarGrupoMapa('D1', event)">
            D1 (1s) - {{d1_count}}
        </button>
        <button class="btn-grupo-mapa btn-d5" onclick="mostrarGrupoMapa('D5', event)">
            D5 (5s) - {{d5_count}}
        </button>
        <button class="btn-grupo-mapa btn-d10" onclick="mostrarGrupoMapa('D10', event)">
            D10 (10s) - {{d10_count}}
        </button>
        
        <div class="divider"></div>
        
        <button class="btn-trajeto" id="btnTrajetoTeste" onclick="toggleTrajeto('teste')">
            📍 Trajeto Teste ({{teste_count}})
        </button>
        <button class="btn-trajeto" id="btnTrajetoRef" onclick="toggleTrajeto('ref')">
            📍 Trajeto Referência ({{ref_count}})
        </button>
        
        <div class="divider"></div>
        
        <button class="btn-clear" onclick="limparMapa()">
            🗑️ Limpar
        </button>
    </div>
    
    <div id="map"></div>
    
    <!-- Legenda -->
    <div class="legend">
        <h4 style="margin-bottom: 10px; font-weight: bold;">Legenda</h4>
        <div class="legend-item">
            <div class="legend-color" style="background: #17becf;"></div>
            <span>Dispositivo Teste</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #12094A;"></div>
            <span>Dispositivo Referência</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #FF0000;"></div>
            <span>Linha de Direção</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #FF8C00;"></div>
            <span>Conexão entre Match</span>
        </div>
    </div>
    
    <div id="mapSidebar" class="sidebar">
        <button id="sidebarToggleBtn" class="sidebar-toggle" onclick="toggleSidebar()" title="Abrir Filtros de Trajeto">
            📅
        </button>
        <h3>📅 Filtros de Trajeto</h3>
        
        <div id="filterTeste" class="filter-section disabled">
            <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #17becf;">
                🔵 Trajeto Teste
            </h4>
            <button class="btn-select-all" onclick="selecionarTodosDias('teste', true)">Todos</button>
            <button class="btn-select-all" onclick="selecionarTodosDias('teste', false)">Nenhum</button>
            <div id="diasTeste" class="day-filter"></div>
        </div>
        
        <div id="filterRef" class="filter-section disabled">
            <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #12094A;">
                🟣 Trajeto Referência
            </h4>
            <button class="btn-select-all" onclick="selecionarTodosDias('ref', true)">Todos</button>
            <button class="btn-select-all" onclick="selecionarTodosDias('ref', false)">Nenhum</button>
            <div id="diasRef" class="day-filter"></div>
        </div>
    </div>
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <script>
        // Dados dos grupos
        const gruposData = {json.dumps(grupos_data, indent=2)};
        const trajetoTeste = {json.dumps(trajeto_teste, indent=2)};
        const trajetoRef = {json.dumps(trajeto_ref, indent=2)};
        
        // Inicializar mapa
        const map = L.map('map').setView([-15.7801, -47.9292], 4);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        let markers = [];
        let lines = [];
        let grupoAtual = 'D1';
        let trajetoTesteLayer = null;
        let trajetoRefLayer = null;
        let trajetoTesteAtivo = false;
        let trajetoRefAtivo = false;
        let zoomRealizado = {{}}; // Guarda se zoom foi feito para cada grupo
        let trajetoTestePorDia = {{}};
        let trajetoRefPorDia = {{}};
        let diasSelecionadosTeste = {{}};
        let diasSelecionadosRef = {{}};
        
        // Função para alternar sidebar
        function toggleSidebar() {{
            const sidebar = document.getElementById('mapSidebar');
            const toggleBtn = document.getElementById('sidebarToggleBtn');
            if (sidebar.classList.contains('open')) {{
                sidebar.classList.remove('open');
                toggleBtn.innerHTML = '📅';
                toggleBtn.title = 'Abrir Filtros de Trajeto';
            }} else {{
                sidebar.classList.add('open');
                toggleBtn.innerHTML = '✕';
                toggleBtn.title = 'Fechar Filtros';
            }}
        }}
        
        // Agrupar trajetos por dia
        function agruparTrajetoPorDia(trajeto) {{
            const porDia = {{}};
            trajeto.forEach(ponto => {{
                if (ponto.time) {{
                    const data = ponto.time.split(' ')[0]; // Extrai só a data (YYYY-MM-DD)
                    if (!porDia[data]) {{
                        porDia[data] = [];
                    }}
                    porDia[data].push(ponto);
                }}
            }});
            return porDia;
        }}
        
        // Criar checkboxes de dias
        function criarFiltrosDias(tipo) {{
            const porDia = tipo === 'teste' ? trajetoTestePorDia : trajetoRefPorDia;
            const containerId = tipo === 'teste' ? 'diasTeste' : 'diasRef';
            const container = document.getElementById(containerId);
            
            container.innerHTML = '';
            
            const dias = Object.keys(porDia).sort();
            dias.forEach(dia => {{
                const count = porDia[dia].length;
                const checkbox = document.createElement('div');
                checkbox.className = 'day-checkbox';
                checkbox.innerHTML = `
                    <input type="checkbox" id="${{tipo}}_${{dia}}" 
                           onchange="atualizarTrajetoDia('${{tipo}}', '${{dia}}', this.checked)" 
                           checked>
                    <label for="${{tipo}}_${{dia}}">${{dia}}</label>
                    <span class="point-count">${{count}}</span>
                `;
                container.appendChild(checkbox);
                
                // Inicializar como selecionado
                if (tipo === 'teste') {{
                    diasSelecionadosTeste[dia] = true;
                }} else {{
                    diasSelecionadosRef[dia] = true;
                }}
            }});
        }}
        
        // Selecionar/desselecionar todos os dias
        function selecionarTodosDias(tipo, selecionar) {{
            const porDia = tipo === 'teste' ? trajetoTestePorDia : trajetoRefPorDia;
            const dias = Object.keys(porDia);
            
            dias.forEach(dia => {{
                const checkbox = document.getElementById(`${{tipo}}_${{dia}}`);
                if (checkbox) {{
                    checkbox.checked = selecionar;
                    if (tipo === 'teste') {{
                        diasSelecionadosTeste[dia] = selecionar;
                    }} else {{
                        diasSelecionadosRef[dia] = selecionar;
                    }}
                }}
            }});
            
            // Redesenhar trajeto
            redesenharTrajeto(tipo);
        }}
        
        // Atualizar quando checkbox muda
        function atualizarTrajetoDia(tipo, dia, selecionado) {{
            if (tipo === 'teste') {{
                diasSelecionadosTeste[dia] = selecionado;
            }} else {{
                diasSelecionadosRef[dia] = selecionado;
            }}
            redesenharTrajeto(tipo);
        }}
        
        // Redesenhar trajeto com os dias selecionados
        function redesenharTrajeto(tipo) {{
            if (tipo === 'teste' && trajetoTesteAtivo) {{
                // Remover camadas antigas
                if (trajetoTesteLayer) {{
                    map.removeLayer(trajetoTesteLayer);
                }}
                // Remover marcadores antigos do trajeto teste
                markers = markers.filter(m => {{
                    if (m._trajeto === 'teste') {{
                        map.removeLayer(m);
                        return false;
                    }}
                    return true;
                }});
                
                // Adicionar novamente com filtros
                adicionarTrajetoNoMapa('teste');
            }} else if (tipo === 'ref' && trajetoRefAtivo) {{
                // Remover camadas antigas
                if (trajetoRefLayer) {{
                    map.removeLayer(trajetoRefLayer);
                }}
                // Remover marcadores antigos do trajeto ref
                markers = markers.filter(m => {{
                    if (m._trajeto === 'ref') {{
                        map.removeLayer(m);
                        return false;
                    }}
                    return true;
                }});
                
                // Adicionar novamente com filtros
                adicionarTrajetoNoMapa('ref');
            }}
        }}
        
        // Obter pontos filtrados por dias selecionados
        function obterPontosFiltrados(tipo) {{
            const porDia = tipo === 'teste' ? trajetoTestePorDia : trajetoRefPorDia;
            const diasSelecionados = tipo === 'teste' ? diasSelecionadosTeste : diasSelecionadosRef;
            
            const pontosFiltrados = [];
            Object.keys(diasSelecionados).forEach(dia => {{
                if (diasSelecionados[dia] && porDia[dia]) {{
                    pontosFiltrados.push(...porDia[dia]);
                }}
            }});
            
            return pontosFiltrados;
        }}
        
        // Função para calcular ponto final da linha de direção
        function calcularPontoFinal(lat, lon, azimute, distancia = 100) {{
            const R = 6371e3; // raio da Terra em metros
            const δ = distancia / R;
            const θ = azimute * Math.PI / 180;
            const φ1 = lat * Math.PI / 180;
            const λ1 = lon * Math.PI / 180;
            
            const φ2 = Math.asin(
                Math.sin(φ1) * Math.cos(δ) + 
                Math.cos(φ1) * Math.sin(δ) * Math.cos(θ)
            );
            const λ2 = λ1 + Math.atan2(
                Math.sin(θ) * Math.sin(δ) * Math.cos(φ1),
                Math.cos(δ) - Math.sin(φ1) * Math.sin(φ2)
            );
            
            return [φ2 * 180 / Math.PI, λ2 * 180 / Math.PI];
        }}
        
        function limparMapa() {{
            markers.forEach(m => map.removeLayer(m));
            lines.forEach(l => map.removeLayer(l));
            markers = [];
            lines = [];
            
            // Limpar trajetos
            if (trajetoTesteLayer) {{
                map.removeLayer(trajetoTesteLayer);
                trajetoTesteLayer = null;
                trajetoTesteAtivo = false;
                document.getElementById('btnTrajetoTeste').classList.remove('active');
                document.getElementById('filterTeste').classList.add('disabled');
            }}
            if (trajetoRefLayer) {{
                map.removeLayer(trajetoRefLayer);
                trajetoRefLayer = null;
                trajetoRefAtivo = false;
                document.getElementById('btnTrajetoRef').classList.remove('active');
                document.getElementById('filterRef').classList.add('disabled');
            }}
        }}
        
        // Função para adicionar trajeto no mapa
        function adicionarTrajetoNoMapa(tipo) {{
            const pontos = obterPontosFiltrados(tipo);
            const cor = tipo === 'teste' ? '#17becf' : '#12094A';
            const label = tipo === 'teste' ? 'Teste' : 'Referência';
            
            if (pontos.length === 0) {{
                alert(`Nenhum ponto selecionado para ${{label}}`);
                return;
            }}
            
            // Criar linha do trajeto
            const coords = pontos.map(p => [p.lat, p.lon]);
            const layer = L.polyline(coords, {{
                color: cor,
                weight: 2,
                opacity: 0.6
            }}).addTo(map);
            
            if (tipo === 'teste') {{
                trajetoTesteLayer = layer;
            }} else {{
                trajetoRefLayer = layer;
            }}
            
            // Adicionar marcadores
            pontos.forEach(ponto => {{
                const marker = L.circleMarker([ponto.lat, ponto.lon], {{
                    radius: 3,
                    fillColor: cor,
                    color: 'white',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.7
                }}).addTo(map);
                
                marker.bindPopup(`
                    <div style="font-family: Arial; font-size: 11px;">
                        <strong style="color: ${{cor}};">${{label}}</strong><br>
                        <strong>Lat/Lon:</strong> ${{ponto.lat.toFixed(6)}} ${{ponto.lon.toFixed(6)}}<br>
                        <strong>Vel:</strong> ${{ponto.vel.toFixed(2)}} km/h<br>
                        <strong>Hora:</strong> ${{ponto.time}}
                    </div>
                `);
                
                marker._trajeto = tipo; // Marca para poder filtrar depois
                markers.push(marker);
            }});
        }}
        
        function toggleTrajeto(tipo) {{
            if (tipo === 'teste') {{
                if (trajetoTesteAtivo) {{
                    // Remover trajeto
                    if (trajetoTesteLayer) {{
                        map.removeLayer(trajetoTesteLayer);
                        trajetoTesteLayer = null;
                    }}
                    // Remover marcadores do trajeto
                    markers = markers.filter(m => {{
                        if (m._trajeto === 'teste') {{
                            map.removeLayer(m);
                            return false;
                        }}
                        return true;
                    }});
                    
                    trajetoTesteAtivo = false;
                    document.getElementById('btnTrajetoTeste').classList.remove('active');
                    document.getElementById('filterTeste').classList.add('disabled');
                }} else {{
                    // Adicionar trajeto
                    if (trajetoTeste.length > 0) {{
                        trajetoTesteAtivo = true;
                        document.getElementById('btnTrajetoTeste').classList.add('active');
                        document.getElementById('filterTeste').classList.remove('disabled');
                        
                        adicionarTrajetoNoMapa('teste');
                    }} else {{
                        alert('Nenhum dado de trajeto disponível para Teste');
                    }}
                }}
            }} else if (tipo === 'ref') {{
                if (trajetoRefAtivo) {{
                    // Remover trajeto
                    if (trajetoRefLayer) {{
                        map.removeLayer(trajetoRefLayer);
                        trajetoRefLayer = null;
                    }}
                    // Remover marcadores do trajeto
                    markers = markers.filter(m => {{
                        if (m._trajeto === 'ref') {{
                            map.removeLayer(m);
                            return false;
                        }}
                        return true;
                    }});
                    
                    trajetoRefAtivo = false;
                    document.getElementById('btnTrajetoRef').classList.remove('active');
                    document.getElementById('filterRef').classList.add('disabled');
                }} else {{
                    // Adicionar trajeto
                    if (trajetoRef.length > 0) {{
                        trajetoRefAtivo = true;
                        document.getElementById('btnTrajetoRef').classList.add('active');
                        document.getElementById('filterRef').classList.remove('disabled');
                        
                        adicionarTrajetoNoMapa('ref');
                    }} else {{
                        alert('Nenhum dado de trajeto disponível para Referência');
                    }}
                }}
            }}
        }}
        
        function mostrarGrupoMapa(grupo, event) {{
            limparMapa();
            grupoAtual = grupo;
            
            // Atualizar botões
            document.querySelectorAll('.btn-grupo-mapa').forEach(btn => {{
                btn.classList.remove('active');
            }});
            if (event && event.target) {{
                event.target.classList.add('active');
            }} else {{
                // Fallback: marca o botão correspondente ao grupo
                const btnClasses = {{'D1': 'btn-d1', 'D5': 'btn-d5', 'D10': 'btn-d10'}};
                const btn = document.querySelector('.' + btnClasses[grupo]);
                if (btn) btn.classList.add('active');
            }}
            
            const dados = gruposData[grupo];
            if (!dados || dados.length === 0) {{
                alert(`Nenhum dado disponível para o grupo ${{grupo}}`);
                return;
            }}
            
            const bounds = [];
            
            dados.forEach(match => {{
                const {{ teste, ref, match_id, diff_angular }} = match;
                
                // Marcador Teste
                const markerTeste = L.circleMarker([teste.lat, teste.lon], {{
                    radius: 6,
                    fillColor: '#17becf',
                    color: 'white',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }}).addTo(map);
                
                markerTeste.bindPopup(`
                    <div style="font-family: Arial; font-size: 12px;">
                        <strong style="color: #17becf;">📍 Dispositivo Teste</strong><br>
                        <strong>Match ID:</strong> ${{match_id}}<br>
                        <strong>Lat/Lon:</strong> ${{teste.lat.toFixed(6)}} ${{teste.lon.toFixed(6)}}<br>
                        <strong>Direção:</strong> ${{teste.dir.toFixed(1)}}°<br>
                        <strong>Velocidade:</strong> ${{teste.vel.toFixed(2)}} km/h<br>
                        <strong>Hora:</strong> ${{teste.time}}
                        ${{diff_angular !== null ? '<br><strong>Dif. Angular:</strong> ' + diff_angular.toFixed(2) + '°' : ''}}
                        <br><br>
                        <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${{teste.lat}},${{teste.lon}}&heading=${{teste.dir}}" 
                           target="_blank" 
                           style="color: #17becf; text-decoration: none; font-weight: bold; padding: 5px 10px; background: #f0f8ff; border-radius: 5px; display: inline-block;">
                            🌍 Ver no Street View
                        </a>
                    </div>
                `);
                markers.push(markerTeste);
                bounds.push([teste.lat, teste.lon]);
                
                // Marcador Referência
                const markerRef = L.circleMarker([ref.lat, ref.lon], {{
                    radius: 6,
                    fillColor: '#12094A',
                    color: 'white',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }}).addTo(map);
                
                markerRef.bindPopup(`
                    <div style="font-family: Arial; font-size: 12px;">
                        <strong style="color: #12094A;">📍 Dispositivo Referência</strong><br>
                        <strong>Match ID:</strong> ${{match_id}}<br>
                        <strong>Lat/Lon:</strong> ${{ref.lat.toFixed(6)}} ${{ref.lon.toFixed(6)}}<br>
                        <strong>Direção:</strong> ${{ref.dir.toFixed(1)}}°<br>
                        <strong>Velocidade:</strong> ${{ref.vel.toFixed(2)}} km/h<br>
                        <strong>Hora:</strong> ${{ref.time}}
                        <br><br>
                        <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${{ref.lat}},${{ref.lon}}&heading=${{ref.dir}}" 
                           target="_blank" 
                           style="color: #12094A; text-decoration: none; font-weight: bold; padding: 5px 10px; background: #e8e4f3; border-radius: 5px; display: inline-block;">
                            🌍 Ver no Street View
                        </a>
                    </div>
                `);
                markers.push(markerRef);
                bounds.push([ref.lat, ref.lon]);
                
                // Linha de direção Teste
                const pontaTesteLine = calcularPontoFinal(teste.lat, teste.lon, teste.dir, 50);
                const lineTeste = L.polyline([
                    [teste.lat, teste.lon],
                    pontaTesteLine
                ], {{
                    color: '#FF0000',
                    weight: 3,
                    dashArray: '5, 5',
                    opacity: 0.9
                }}).addTo(map);
                lines.push(lineTeste);
                
                // Linha de direção Referência
                const pontaRefLine = calcularPontoFinal(ref.lat, ref.lon, ref.dir, 50);
                const lineRef = L.polyline([
                    [ref.lat, ref.lon],
                    pontaRefLine
                ], {{
                    color: '#FF0000',
                    weight: 3,
                    dashArray: '5, 5',
                    opacity: 0.9
                }}).addTo(map);
                lines.push(lineRef);
                
                // Linha conectando teste e referência
                const lineConexao = L.polyline([
                    [teste.lat, teste.lon],
                    [ref.lat, ref.lon]
                ], {{
                    color: '#FF8C00',
                    weight: 2,
                    opacity: 0.7,
                    dashArray: '8, 4'
                }}).addTo(map);
                lines.push(lineConexao);
            }});
            
            // Fazer zoom apenas se for a primeira vez que visualiza este grupo
            if (!zoomRealizado[grupo] && bounds.length > 0) {{
                map.fitBounds(bounds, {{ padding: [50, 50] }});
                zoomRealizado[grupo] = true;
            }}
        }}
        
        // Inicializar ao carregar
        document.addEventListener('DOMContentLoaded', function() {{
            // Agrupar trajetos por dia
            trajetoTestePorDia = agruparTrajetoPorDia(trajetoTeste);
            trajetoRefPorDia = agruparTrajetoPorDia(trajetoRef);
            
            // Criar filtros de dias
            criarFiltrosDias('teste');
            criarFiltrosDias('ref');
            
            // Mostrar D1 ao carregar
            setTimeout(() => {{
                const btn = document.querySelector('.btn-d1');
                if (btn) btn.click();
            }}, 100);
        }});
    </script>
</body>
</html>""".replace('{{d1_count}}', str(len(grupos_data['D1']))) \
      .replace('{{d5_count}}', str(len(grupos_data['D5']))) \
      .replace('{{d10_count}}', str(len(grupos_data['D10']))) \
      .replace('{{teste_count}}', str(len(trajeto_teste))) \
      .replace('{{ref_count}}', str(len(trajeto_ref)))
    
    # Salvar HTML
    if output_path is None:
        output_path = Path(__file__).parent.parent / 'temp_blocos' / 'mapa_direcoes.html'
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Mapa de direções gerado: {output_path}")
    print(f"   - D1: {len(grupos_data['D1'])} pontos")
    print(f"   - D5: {len(grupos_data['D5'])} pontos")
    print(f"   - D10: {len(grupos_data['D10'])} pontos")
    print(f"   - Trajeto Teste: {len(trajeto_teste)} pontos (GTERI + Ignições)")
    print(f"   - Trajeto Referência: {len(trajeto_ref)} pontos (GTERI + Ignições)")
    
    return str(output_path)


if __name__ == "__main__":
    # Teste
    base_dir = Path(__file__).parent
    gerar_mapa_direcoes(
        input1=base_dir / 'logs' / 'match1.csv',
        input2=base_dir / 'logs' / 'match2.csv',
        match_path=base_dir.parent / 'outputGeral.csv'
    )

