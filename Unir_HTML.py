import os
import re
from pathlib import Path
import pandas as pd
import base64

def extract_css_from_blocks(blocks):
    inline_css = []
    css_links = set()
    cleaned_blocks = []

    for block in blocks:
        # Extract inline styles
        styles = re.findall(r'<style.*?>(.*?)</style>', block, flags=re.DOTALL)
        inline_css.extend(styles)

        # Extract external stylesheets
        links = re.findall(r'<link.*?rel=["\']stylesheet["\'].*?>', block, flags=re.DOTALL)
        css_links.update(links)

        # Remove CSS from block
        clean_block = re.sub(r'<style.*?>.*?</style>', '', block, flags=re.DOTALL)
        clean_block = re.sub(r'<link.*?rel=["\']stylesheet["\'].*?>', '', clean_block, flags=re.DOTALL)
        cleaned_blocks.append(clean_block)

    return inline_css, css_links, cleaned_blocks

def extract_and_consolidate_scripts(blocks):
    scripts = []
    cleaned_blocks = []
    global_vars_patterns = [
        r'let\s+maximizedChartInstance\s*=\s*null\s*;',
        r'window\.charts\s*=\s*\{\s*\}\s*;',
        r'let\s+charts\s*=\s*window\.charts\s*;',
        r'window\.chartStates\s*=\s*\{\s*\}\s*;',
        r'let\s+chartStates\s*=\s*window\.chartStates\s*;',
    ]

    for block in blocks:
        # Extract all scripts from block
        found_scripts = re.findall(r'<script.*?>(.*?)</script>', block, flags=re.DOTALL)

        for script in found_scripts:
            # Remove duplicate global variables
            clean_script = script
            for pattern in global_vars_patterns:
                clean_script = re.sub(pattern, '', clean_script, flags=re.MULTILINE)
            scripts.append(clean_script.strip())

        # Remove all scripts from original block
        clean_block = re.sub(r'<script.*?>.*?</script>', '', block, flags=re.DOTALL)
        cleaned_blocks.append(clean_block)

    # Combine all remaining scripts into one
    final_script_block = ""
    if scripts:
        final_script_block = "<script>\n" + "\n\n".join(scripts) + "\n</script>\n"

    return final_script_block, cleaned_blocks

def get_device_info(df, device_function):
    """
    Extrai informações do dispositivo do DataFrame
    
    Args:
        df: DataFrame com dados do dispositivo
        device_function: String indicando "Teste" ou "Referência"
    
    Returns:
        dict com informações do dispositivo
    """
    if df is None or df.empty:
        return {
            'funcao': device_function,
            'tipo_dispositivo': 'N/A',
            'imei': 'N/A',
            'versao_firmware': 'N/A'
        }
    # Mapeamento de tipos de dispositivo
    tipo_mapping = {
        '802003': 'TM-10',
        '385349': 'TM-08',
        '83': 'TM-07'
    }
    
    # Extrair tipo de dispositivo
    tipo_dispositivo = 'N/A'
    tipo_raw = None
    if 'Tipo Dispositivo' in df.columns:
        tipos_unicos = df['Tipo Dispositivo'].dropna().unique()
        if len(tipos_unicos) > 0:
            try:
                tipo_int = int(float(tipos_unicos[0])) 
                tipo_raw = str(tipo_int)
            except:
                tipo_raw = str(tipos_unicos[0])  # fallback

            tipo_dispositivo = tipo_mapping.get(tipo_raw, f"Desconhecido ({tipo_raw})")
    # print(tipo_dispositivo)

    
    # Extrair IMEI (robusto): considera colunas equivalentes e aceita 10 dígitos para TM07
    imei = 'N/A'
    # Detecta a coluna de IMEI de forma tolerante
    imei_col = None
    for col in df.columns:
        nome_norm = str(col).strip().lower()
        if 'imei' in nome_norm:
            imei_col = col
            break
    if imei_col is None and 'IMEI' in df.columns:
        imei_col = 'IMEI'

    if imei_col is not None:
        import re
        imeis_unicos = df[imei_col].dropna().astype(str).unique()
        candidatos = set()
        # Para TM07, alguns arquivos têm 10 dígitos
        min_len = 10 if (tipo_raw == '83') else 12
        for val in imeis_unicos:
            for m in re.findall(r"\d{9,17}", val):  # captura sequências longas
                candidatos.add(m.lstrip('0') or m)
        candidatos = {c for c in candidatos if min_len <= len(c) <= 17}
        if candidatos:
            imei = ', '.join(sorted(candidatos, key=lambda x: (-len(x), x)))
   
    # Extrair Versão Firmware: converter formato hexa '0xHHLL' para 'H.LL' decimal (ex.: 0x0915 -> 9.21)
    versao_firmware = 'N/A'
    if 'Versão Firmware' in df.columns:
        import re
        def fw_hex_to_decimal_str(token):
            s = str(token).strip()
            m = re.search(r"0x([0-9a-fA-F]+)", s)
            if not m:
                return None
            hx = m.group(1)
            # usa os últimos 4 dígitos para major/minor (2 bytes)
            hx = hx[-4:].rjust(4, '0')
            major_hex, minor_hex = hx[:2], hx[2:]
            try:
                major = int(major_hex, 16)
                minor = int(minor_hex, 16)
                return f"{major}.{minor}"
            except ValueError:
                return None

        versoes_unicas = df['Versão Firmware'].dropna().astype(str).unique()
        convertidas = []
        for v in versoes_unicas:
            conv = fw_hex_to_decimal_str(v)
            if conv:
                convertidas.append(conv)
        if convertidas:
            # remove duplicatas mantendo ordem
            seen = set()
            dedup = []
            for c in convertidas:
                if c not in seen:
                    seen.add(c)
                    dedup.append(c)
            versao_firmware = ', '.join(dedup)
        elif len(versoes_unicas) > 0:
            versao_firmware = ', '.join([str(v) for v in versoes_unicas])
    
    return {
        'funcao': device_function,
        'tipo_dispositivo': tipo_dispositivo,
        'imei': imei,
        'versao_firmware': versao_firmware
    }

def create_device_summary_html(df_raw1, df_raw2):
    device_teste = get_device_info(df_raw1, 'Teste')
    device_referencia = get_device_info(df_raw2, 'Referência')

    html = f"""
    <div class="tabela-container">
    <div class="grafico-container">
        <div class='grafico-titulo-container'>
            <h2 class='grafico-titulo'>Resumo Técnico dos Equipamentos</h2>
        </div>

        <table style='width: 100%; border-collapse: collapse; margin: 20px auto; font-size: 14px;'>
            <thead>
                <tr style='background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;'>
                    <th style='padding: 22px;  border: 1px solid #dee2e6; font-weight: bold; color: #495057;'>Dispositivo</th>
                    <th style='padding: 22px;  border: 1px solid #dee2e6; font-weight: bold; color: #495057;'>Nome Comercial</th>
                    <th style='padding: 22px;  border: 1px solid #dee2e6; font-weight: bold; color: #495057;'>IMEI</th>
                    <th style='padding: 22px;  border: 1px solid #dee2e6; font-weight: bold; color: #495057;'>Versão Firmware</th>
                </tr>
            </thead>
            <tbody>
                <tr style='border-bottom: 1px solid #dee2e6;'>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; color: #17becf; font-size: 16px;'>{device_teste['funcao']}</td>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px;'>{device_teste['tipo_dispositivo']}</td>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px; font-family: monospace;'>{device_teste['imei']}</td>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px; font-family: monospace;'>{device_teste['versao_firmware']}</td>
                </tr>
                <tr style='border-bottom: 1px solid #dee2e6;'>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px; color: #12094A;'>{device_referencia['funcao']}</td>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px;'>{device_referencia['tipo_dispositivo']}</td>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px; font-family: monospace;'>{device_referencia['imei']}</td>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px; font-family: monospace;'>{device_referencia['versao_firmware']}</td>
                </tr>
            </tbody>
        </table>
    </div>
    </div>

    """
    return html



def unir_blocos(df_raw1, df_raw2, dados_mapa=None, trajeto_teste=None, trajeto_ref=None):
    blocks_dir = Path(__file__).parent / "temp_blocos"
    output_file = Path(__file__).parent / "dashboard_final.html"
    
    # Se não houver dados do mapa, usa vazio
    if dados_mapa is None:
        dados_mapa = {'D1': [], 'D5': [], 'D10': []}
    
    # Se não houver dados de trajeto, usa vazio
    if trajeto_teste is None:
        trajeto_teste = []
    if trajeto_ref is None:
        trajeto_ref = []
    
    if not os.path.exists(blocks_dir):
        print(f"Error: Directory '{blocks_dir}' not found!")
        return
    
    # Define manual order of files
    html_files = [
        str(blocks_dir / "bloco_viagens.html"),
        str(blocks_dir / "bloco_dashboard.html"),
        str(blocks_dir / "bloco_eventos_diarios.html"),
        str(blocks_dir / "bloco_conexao_gprs.html"),
        str(blocks_dir / "bloco_satellite_estabilidade.html"),
    ]

    if not html_files:
        print(f"Error: No HTML files found in '{blocks_dir}'!")
        return

    # Global CSS - Adicionei os novos estilos para a logo e título
    global_css =  """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f8f9fa;
        min-height: 100vh;
        padding: 20px;
    }
    
    .dashboard-container { 
        max-width: 1200px;
        margin: 0 auto;
    }
    .logo-container {
        text-align: center; 
        margin-bottom: 40px; 
    }

    .logo-wrapper {
        background-color: #e6e6fa;
        border-radius: 50px;
        box-shadow: 0 4px 20px rgba(102, 51, 153, 0.2);
        padding: 30px 100px;
        margin: 0 auto;
        
        display: block;
        max-width: 90%;    
        width: 90%;
    }
        
    .logo-image {
        max-width: 350px;
        height: auto;
    }
    
    .dashboard-title {
        font-family: 'Saira', sans-serif;
        background: linear-gradient(135deg, #e6e6fa 0%, #d8bfd8 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-size: 2.5em;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(102, 51, 153, 0.2);
        display: inline-block;
        padding: 15px 30px;

        
        border-radius: 20px;
        box-shadow: 0 6px 20px rgba(102, 51, 153, 0.15);
        margin: 0 0 30px 0;
        text-align: center;
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
        margin: 0 auto 40px auto;
    }
    
    .grafico-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    
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
        font-size: 1.8em; 
        padding: 10px 25px;
        background: #f8f9fa;
        border-radius: 20px;
        display: inline-block;
    }
    
    .chart-wrapper {
        position: relative;
        height: 600px;
        width: 100%;
        margin-bottom: 15px;
    }
    
    canvas { 
        width: 100% !important; 
        height: 100% !important; 
    }
    
    .zoom-controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 15px 0;
    }
    
    .zoom-controls button {
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
    
    .zoom-controls button:hover {
        transform: translateY(-1px);
        opacity: 0.9;
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

    /* Modal para gráfico maximizado */
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
    .grafico-container h4 {
        margin-bottom: 8px;
    }

    .grafico-container div {
        margin-top: 4px;
    }
    .tabela-container {
    background: white;
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    overflow-x: auto;
    }
    
    /* Botão flutuante do mapa */
    .btn-mapa-direcoes {
        position: fixed;
        bottom: 30px;
        right: 30px;
        padding: 15px 25px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-decoration: none;
        border-radius: 50px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.5);
        transition: all 0.3s ease;
        z-index: 999;
        cursor: pointer;
        border: none;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .btn-mapa-direcoes:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.7);
    }
    
    .btn-mapa-direcoes:active {
        transform: translateY(-1px) scale(1.03);
    }
    
    /* Modal do Mapa */
    .modal-mapa {
        display: none;
        position: fixed;
        z-index: 2000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.9);
        backdrop-filter: blur(5px);
    }
    
    .modal-mapa.active {
        display: block;
    }
    
    .modal-mapa-content {
        background: white;
        margin: 1% auto;
        border-radius: 15px;
        width: 98%;
        height: 96vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    
    .modal-mapa-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .modal-mapa-header h2 {
        margin: 0;
        font-size: 1.8em;
    }
    
    .close-modal-mapa {
        color: white;
        font-size: 35px;
        font-weight: bold;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    
    .close-modal-mapa:hover {
        transform: scale(1.2);
    }
    
    .mapa-controls {
        padding: 15px;
        background: white;
        border-bottom: 2px solid #dee2e6;
        display: flex;
        justify-content: center;
        gap: 15px;
        flex-wrap: wrap;
        align-items: center;
    }
    
    .btn-grupo-mapa {
        padding: 10px 25px;
        border: none;
        border-radius: 25px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        color: white;
    }
    
    .btn-grupo-mapa.active {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .btn-d1 {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .btn-d5 {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .btn-d10 {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    
    .btn-clear-mapa {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .btn-grupo-mapa:hover, .btn-clear-mapa:hover {
        transform: translateY(-2px);
    }
    
    .mapa-busca-container {
        padding: 15px;
        background: #f8f9fa;
        border-bottom: 1px solid #dee2e6;
        display: flex;
        justify-content: center;
        gap: 10px;
        align-items: center;
    }
    
    .input-busca-match {
        padding: 10px 15px;
        border: 2px solid #667eea;
        border-radius: 20px;
        font-size: 14px;
        width: 250px;
        outline: none;
        transition: all 0.3s ease;
    }
    
    .input-busca-match:focus {
        border-color: #764ba2;
        box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
    }
    
    .btn-buscar-match {
        padding: 10px 25px;
        border: none;
        border-radius: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .btn-buscar-match:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    .mapa-info-panel {
        background: #fff3cd;
        padding: 10px 20px;
        text-align: center;
        border-bottom: 1px solid #ffc107;
        font-size: 13px;
        color: #856404;
    }
    
    #mapContainer {
        flex: 1;
        position: relative;
        background: #e0e0e0;
    }
    
    .mapa-legenda h4 {
        margin: 0 0 10px 0;
        font-weight: bold;
    }
    
    .legenda-item {
        display: flex;
        align-items: center;
        margin: 8px 0;
        font-size: 13px;
    }
    
    .legenda-color {
        width: 30px;
        height: 4px;
        margin-right: 10px;
        border-radius: 2px;
    }
    
    /* Sidebar de filtros do mapa */
    .mapa-sidebar {
        width: 280px;
        position: absolute;
        right: -280px;
        top: 0;
        bottom: 0;
        background: white;
        overflow-y: auto;
        box-shadow: -2px 0 6px rgba(0,0,0,0.1);
        padding: 15px;
        z-index: 500;
        transition: right 0.3s ease;
    }
    
    .mapa-sidebar.open {
        right: 0;
    }
    
    .mapa-sidebar-toggle {
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
        z-index: 2001;
    }
    
    .mapa-sidebar-toggle:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-50%) translateX(-3px);
    }
    
    .mapa-sidebar.open .mapa-sidebar-toggle {
        right: 280px;
    }
    
    .mapa-sidebar h3 {
        margin: 0 0 15px 0;
        font-size: 16px;
        color: #333;
        border-bottom: 2px solid #667eea;
        padding-bottom: 8px;
    }
    
    .mapa-day-filter {
        margin-bottom: 20px;
    }
    
    .mapa-day-checkbox {
        display: flex;
        align-items: center;
        padding: 8px;
        margin: 5px 0;
        border-radius: 5px;
        transition: background 0.2s;
        cursor: pointer;
    }
    
    .mapa-day-checkbox:hover {
        background: #f0f0f0;
    }
    
    .mapa-day-checkbox input[type="checkbox"] {
        margin-right: 10px;
        cursor: pointer;
        width: 16px;
        height: 16px;
    }
    
    .mapa-day-checkbox label {
        cursor: pointer;
        flex: 1;
        font-size: 13px;
    }
    
    .mapa-point-count {
        font-size: 11px;
        color: #666;
        background: #e9ecef;
        padding: 2px 6px;
        border-radius: 10px;
        margin-left: 5px;
    }
    
    .mapa-filter-section {
        margin-bottom: 20px;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 8px;
    }
    
    .mapa-filter-section.disabled {
        opacity: 0.5;
        pointer-events: none;
    }
    
    .mapa-btn-select-all {
        background: #6c757d;
        color: white;
        border: none;
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 12px;
        cursor: pointer;
        margin-right: 5px;
        margin-bottom: 10px;
    }
    
    .mapa-btn-select-all:hover {
        background: #5a6268;
    }
    
    #mapContainer {
        width: 100%;
        transition: width 0.3s ease;
    }
    
    .mapa-legenda {
        position: absolute;
        bottom: 20px;
        left: 20px;
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        z-index: 1000;
        max-width: 250px;
    }

    """

    # Global JavaScript
    global_js = """
        // Global variables
        window.charts = window.charts || {};
        let charts = window.charts;
        let maximizedChartInstance = null;

        // Function to maximize charts
        function maximizeChart(chartId) {
            const originalChart = charts[chartId];
            if (!originalChart) return console.error('Chart not found:', chartId);
            
            const modal = document.getElementById('maximizedModal');
            const modalTitle = document.getElementById('modalTitle');
            
            // Update modal title
            modalTitle.textContent = document.querySelector('#' + chartId).closest('.grafico-container').querySelector('.grafico-titulo').textContent;
            
            modal.style.display = 'block';
            
            const ctx = document.getElementById('maximizedChart').getContext('2d');
            if (maximizedChartInstance) maximizedChartInstance.destroy();
            
            // Create copy of data maintaining current visibility
            const chartData = JSON.parse(JSON.stringify(originalChart.data));
            
            maximizedChartInstance = new Chart(ctx, {
                type: originalChart.config.type,
                data: chartData,
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

            // Sync dataset visibility
            originalChart.data.datasets.forEach((dataset, index) => {
                const isVisible = originalChart.getDatasetMeta(index).visible !== false;
                maximizedChartInstance.setDatasetVisibility(index, isVisible);
            });
            maximizedChartInstance.update();
            
            // Add double click event to reset zoom
            const maximizedCanvas = document.getElementById('maximizedChart');
            maximizedCanvas.addEventListener('dblclick', function() {
                if (maximizedChartInstance) {
                    maximizedChartInstance.resetZoom();
                }
            });
        }

        // Function to close modal
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
        
        // Function to reset zoom
        function resetZoom(chartId) {
            const chart = charts[chartId];
            if (chart && chart.resetZoom) {
                chart.resetZoom();
            }
        }
        """

    # JavaScript do Mapa
    import json
    mapa_js = f"""
        <script>
        // Dados do mapa
        const dadosMapaGlobal = {json.dumps(dados_mapa)};
        const trajetoTeste = {json.dumps(trajeto_teste)};
        const trajetoRef = {json.dumps(trajeto_ref)};
        let mapaLeaflet = null;
        let marcadoresMapa = [];
        let linhasMapa = [];
        let trajetoTesteLayer = null;
        let trajetoRefLayer = null;
        let trajetoTesteAtivo = false;
        let trajetoRefAtivo = false;
        let zoomRealizado = {{}};
        let trajetoTestePorDia = {{}};
        let trajetoRefPorDia = {{}};
        let diasSelecionadosTeste = {{}};
        let diasSelecionadosRef = {{}};
        
        // Agrupar trajetos por dia
        function agruparTrajetoPorDia(trajeto) {{
            const porDia = {{}};
            trajeto.forEach(ponto => {{
                if (ponto.time) {{
                    const data = ponto.time.split(' ')[0];
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
            
            if (!container) return;
            container.innerHTML = '';
            
            const dias = Object.keys(porDia).sort();
            dias.forEach(dia => {{
                const count = porDia[dia].length;
                const checkbox = document.createElement('div');
                checkbox.className = 'mapa-day-checkbox';
                checkbox.innerHTML = `
                    <input type="checkbox" id="${{tipo}}_${{dia}}" 
                           onchange="atualizarTrajetoDia('${{tipo}}', '${{dia}}', this.checked)" 
                           checked>
                    <label for="${{tipo}}_${{dia}}">${{dia}}</label>
                    <span class="mapa-point-count">${{count}}</span>
                `;
                container.appendChild(checkbox);
                
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
                if (trajetoTesteLayer) {{
                    mapaLeaflet.removeLayer(trajetoTesteLayer);
                }}
                marcadoresMapa = marcadoresMapa.filter(m => {{
                    if (m._trajeto === 'teste') {{
                        mapaLeaflet.removeLayer(m);
                        return false;
                    }}
                    return true;
                }});
                
                adicionarTrajetoNoMapa('teste');
            }} else if (tipo === 'ref' && trajetoRefAtivo) {{
                if (trajetoRefLayer) {{
                    mapaLeaflet.removeLayer(trajetoRefLayer);
                }}
                marcadoresMapa = marcadoresMapa.filter(m => {{
                    if (m._trajeto === 'ref') {{
                        mapaLeaflet.removeLayer(m);
                        return false;
                    }}
                    return true;
                }});
                
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
        
        // Função para adicionar trajeto no mapa
        function adicionarTrajetoNoMapa(tipo) {{
            const pontos = obterPontosFiltrados(tipo);
            const cor = tipo === 'teste' ? '#17becf' : '#12094A';
            const label = tipo === 'teste' ? 'Teste' : 'Referência';
            
            if (pontos.length === 0) {{
                alert(`Nenhum ponto selecionado para ${{label}}`);
                return;
            }}
            
            const coords = pontos.map(p => [p.lat, p.lon]);
            const layer = L.polyline(coords, {{
                color: cor,
                weight: 2,
                opacity: 0.6
            }}).addTo(mapaLeaflet);
            
            if (tipo === 'teste') {{
                trajetoTesteLayer = layer;
            }} else {{
                trajetoRefLayer = layer;
            }}
            
            pontos.forEach(ponto => {{
                const marker = L.circleMarker([ponto.lat, ponto.lon], {{
                    radius: 3,
                    fillColor: cor,
                    color: 'white',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.7
                }}).addTo(mapaLeaflet);
                
                marker.bindPopup(`
                    <div style="font-family: Arial; font-size: 11px;">
                        <strong style="color: ${{cor}};">${{label}}</strong><br>
                        <strong>Lat/Lon:</strong> ${{ponto.lat.toFixed(6)}} ${{ponto.lon.toFixed(6)}}<br>
                        <strong>Vel:</strong> ${{ponto.vel.toFixed(2)}} km/h<br>
                        <strong>Hora:</strong> ${{ponto.time}}
                    </div>
                `);
                
                marker._trajeto = tipo;
                marcadoresMapa.push(marker);
            }});
        }}
        
        // Função para alternar sidebar
        function toggleSidebar() {{
            const sidebar = document.getElementById('mapaSidebar');
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
        
        // Atualizar contadores
        document.getElementById('countD1').textContent = dadosMapaGlobal.D1.length;
        document.getElementById('countD5').textContent = dadosMapaGlobal.D5.length;
        document.getElementById('countD10').textContent = dadosMapaGlobal.D10.length;
        document.getElementById('countTeste').textContent = trajetoTeste.length;
        document.getElementById('countRef').textContent = trajetoRef.length;
        
        function abrirModalMapa() {{
            const modal = document.getElementById('modalMapa');
            modal.classList.add('active');
            
            // Inicializar mapa se ainda não existe
            if (!mapaLeaflet) {{
                // Agrupar trajetos por dia
                trajetoTestePorDia = agruparTrajetoPorDia(trajetoTeste);
                trajetoRefPorDia = agruparTrajetoPorDia(trajetoRef);
                
                // Criar filtros de dias
                criarFiltrosDias('teste');
                criarFiltrosDias('ref');
                
                setTimeout(() => {{
                    mapaLeaflet = L.map('mapContainer').setView([-15.7801, -47.9292], 4);
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        maxZoom: 19,
                        attribution: '© OpenStreetMap contributors'
                    }}).addTo(mapaLeaflet);
                    
                    // Carregar D1 automaticamente
                    document.getElementById('btnD1').click();
                }}, 100);
            }}
        }}
        
        function fecharModalMapa() {{
            const modal = document.getElementById('modalMapa');
            modal.classList.remove('active');
        }}
        
        function limparMapaDirecoes() {{
            marcadoresMapa.forEach(m => mapaLeaflet.removeLayer(m));
            linhasMapa.forEach(l => mapaLeaflet.removeLayer(l));
            marcadoresMapa = [];
            linhasMapa = [];
            
            // Limpar trajetos
            if (trajetoTesteLayer) {{
                mapaLeaflet.removeLayer(trajetoTesteLayer);
                trajetoTesteLayer = null;
                trajetoTesteAtivo = false;
                document.getElementById('btnTrajetoTeste').classList.remove('active');
                const filterTeste = document.getElementById('filterTeste');
                if (filterTeste) filterTeste.classList.add('disabled');
            }}
            if (trajetoRefLayer) {{
                mapaLeaflet.removeLayer(trajetoRefLayer);
                trajetoRefLayer = null;
                trajetoRefAtivo = false;
                document.getElementById('btnTrajetoRef').classList.remove('active');
                const filterRef = document.getElementById('filterRef');
                if (filterRef) filterRef.classList.add('disabled');
            }}
        }}
        
        function toggleTrajeto(tipo) {{
            if (tipo === 'teste') {{
                if (trajetoTesteAtivo) {{
                    // Remover trajeto
                    if (trajetoTesteLayer) {{
                        mapaLeaflet.removeLayer(trajetoTesteLayer);
                        trajetoTesteLayer = null;
                    }}
                    marcadoresMapa = marcadoresMapa.filter(m => {{
                        if (m._trajeto === 'teste') {{
                            mapaLeaflet.removeLayer(m);
                            return false;
                        }}
                        return true;
                    }});
                    
                    trajetoTesteAtivo = false;
                    document.getElementById('btnTrajetoTeste').classList.remove('active');
                    const filterTeste = document.getElementById('filterTeste');
                    if (filterTeste) filterTeste.classList.add('disabled');
                }} else {{
                    // Adicionar trajeto
                    if (trajetoTeste.length > 0) {{
                        trajetoTesteAtivo = true;
                        document.getElementById('btnTrajetoTeste').classList.add('active');
                        const filterTeste = document.getElementById('filterTeste');
                        if (filterTeste) filterTeste.classList.remove('disabled');
                        
                        adicionarTrajetoNoMapa('teste');
                    }} else {{
                        alert('Nenhum dado de trajeto disponível para Teste');
                    }}
                }}
            }} else if (tipo === 'ref') {{
                if (trajetoRefAtivo) {{
                    // Remover trajeto
                    if (trajetoRefLayer) {{
                        mapaLeaflet.removeLayer(trajetoRefLayer);
                        trajetoRefLayer = null;
                    }}
                    marcadoresMapa = marcadoresMapa.filter(m => {{
                        if (m._trajeto === 'ref') {{
                            mapaLeaflet.removeLayer(m);
                            return false;
                        }}
                        return true;
                    }});
                    
                    trajetoRefAtivo = false;
                    document.getElementById('btnTrajetoRef').classList.remove('active');
                    const filterRef = document.getElementById('filterRef');
                    if (filterRef) filterRef.classList.add('disabled');
                }} else {{
                    // Adicionar trajeto
                    if (trajetoRef.length > 0) {{
                        trajetoRefAtivo = true;
                        document.getElementById('btnTrajetoRef').classList.add('active');
                        const filterRef = document.getElementById('filterRef');
                        if (filterRef) filterRef.classList.remove('disabled');
                        
                        adicionarTrajetoNoMapa('ref');
                    }} else {{
                        alert('Nenhum dado de trajeto disponível para Referência');
                    }}
                }}
            }}
        }}
        
        function calcularPontoFinal(lat, lon, azimute, distancia = 50) {{
            const R = 6371e3;
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
        
        function mostrarGrupoMapa(grupo, event) {{
            if (!mapaLeaflet) return;
            
            limparMapaDirecoes();
            
            // Atualizar botões
            document.querySelectorAll('.btn-grupo-mapa').forEach(btn => {{
                btn.classList.remove('active');
            }});
            if (event && event.target) {{
                event.target.classList.add('active');
            }}
            
            const dados = dadosMapaGlobal[grupo];
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
                }}).addTo(mapaLeaflet);
                
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
                marcadoresMapa.push(markerTeste);
                bounds.push([teste.lat, teste.lon]);
                
                // Marcador Referência
                const markerRef = L.circleMarker([ref.lat, ref.lon], {{
                    radius: 6,
                    fillColor: '#12094A',
                    color: 'white',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }}).addTo(mapaLeaflet);
                
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
                marcadoresMapa.push(markerRef);
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
                }}).addTo(mapaLeaflet);
                linhasMapa.push(lineTeste);
                
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
                }}).addTo(mapaLeaflet);
                linhasMapa.push(lineRef);
                
                // Linha conectando teste e referência
                const lineConexao = L.polyline([
                    [teste.lat, teste.lon],
                    [ref.lat, ref.lon]
                ], {{
                    color: '#FF8C00',
                    weight: 2,
                    opacity: 0.7,
                    dashArray: '8, 4'
                }}).addTo(mapaLeaflet);
                linhasMapa.push(lineConexao);
            }});
            
            // Fazer zoom apenas se for a primeira vez que visualiza este grupo
            if (!zoomRealizado[grupo] && bounds.length > 0) {{
                mapaLeaflet.fitBounds(bounds, {{ padding: [50, 50] }});
                zoomRealizado[grupo] = true;
            }}
        }}
        
        // Função para buscar match no mapa
        function buscarMatchNoMapa() {{
            const termoBusca = document.getElementById('buscaMatch').value.trim().toUpperCase();
            
            if (!termoBusca) {{
                alert('Por favor, digite um Match ID para buscar (ex: T1_5)');
                return;
            }}
            
            if (!mapaLeaflet) {{
                alert('Por favor, abra o mapa primeiro clicando em um dos grupos (D1, D5 ou D10)');
                return;
            }}
            
            // Determinar o grupo baseado no termo de busca
            let grupo = '';
            if (termoBusca.startsWith('T1_')) grupo = 'D1';
            else if (termoBusca.startsWith('T5_')) grupo = 'D5';
            else if (termoBusca.startsWith('T10_')) grupo = 'D10';
            else {{
                alert('Formato inválido! Use: T1_X, T5_X ou T10_X (ex: T1_5)');
                return;
            }}
            
            // Buscar o match nos dados
            const dados = dadosMapaGlobal[grupo];
            const matchEncontrado = dados.find(m => m.match_id === termoBusca);
            
            if (!matchEncontrado) {{
                alert(`Match "${{termoBusca}}" não encontrado no grupo ${{grupo}}`);
                return;
            }}
            
            // Garantir que o grupo correto está carregado
            const btnGrupo = document.getElementById('btn' + grupo.replace('D', 'D'));
            if (btnGrupo && !btnGrupo.classList.contains('active')) {{
                // Limpar e carregar o grupo correto
                limparMapaDirecoes();
                document.querySelectorAll('.btn-grupo-mapa').forEach(btn => btn.classList.remove('active'));
                btnGrupo.classList.add('active');
                
                // Recarregar dados do grupo
                mostrarGrupoMapa(grupo);
            }}
            
            // Centralizar no match encontrado
            const {{ teste, ref }} = matchEncontrado;
            const centerLat = (teste.lat + ref.lat) / 2;
            const centerLon = (teste.lon + ref.lon) / 2;
            
            mapaLeaflet.setView([centerLat, centerLon], 18);
            
            // Destacar os marcadores com animação
            setTimeout(() => {{
                marcadoresMapa.forEach(marker => {{
                    const markerLatLng = marker.getLatLng();
                    if ((Math.abs(markerLatLng.lat - teste.lat) < 0.00001 && Math.abs(markerLatLng.lng - teste.lon) < 0.00001) ||
                        (Math.abs(markerLatLng.lat - ref.lat) < 0.00001 && Math.abs(markerLatLng.lng - ref.lon) < 0.00001)) {{
                        marker.openPopup();
                    }}
                }});
            }}, 500);
        }}
        
        // Permitir busca com Enter
        document.addEventListener('DOMContentLoaded', function() {{
            const inputBusca = document.getElementById('buscaMatch');
            if (inputBusca) {{
                inputBusca.addEventListener('keypress', function(event) {{
                    if (event.key === 'Enter') {{
                        buscarMatchNoMapa();
                    }}
                }});
            }}
        }});
        
        // Fechar modal com ESC
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                fecharModalMapa();
            }}
        }});
        </script>
    """

    # HTML footer with modal and global JS
    html_footer = f"""
        </div>

        <div id="maximizedModal" class="modal">
            <div class="modal-content">
                <span class="close-modal" onclick="closeModal()">&times;</span>
                <h2 class="modal-titulo" id="modalTitle">Maximized Chart</h2>
                    <div class="modal-chart-container">
                        <canvas id="maximizedChart"></canvas>
                        <div class="zoom-controls">
                            <button onclick="if (maximizedChartInstance) maximizedChartInstance.resetZoom();">Reset Zoom</button>
                        </div>
                    </div>
            </div>
        </div>

        <script>{global_js}</script>
        
        <script>
        // Initialize events when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {{
            // Close modal when clicking outside
            window.onclick = function(event) {{
                const modal = document.getElementById('maximizedModal');
                if (event.target === modal) {{
                    closeModal();
                }}
            }};
            
            // Close modal with ESC key
            document.addEventListener('keydown', function(event) {{
                if (event.key === 'Escape') {{
                    closeModal();
                }}
            }});
        }});
        </script>
        
        {mapa_js}
    </body>
    </html>"""

    # Read and include blocks
    blocks = []
    for file in html_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    blocks.append(f"<!-- Block: {os.path.basename(file)} -->\n{content}\n")
        except FileNotFoundError:
            print(f"Warning: File '{file}' not found. Skipping...")

    # Process blocks
    inline_css, css_links, blocks_without_css = extract_css_from_blocks(blocks)
    global_scripts, clean_blocks = extract_and_consolidate_scripts(blocks_without_css)

    PNG_FILE = Path(__file__).parent / "logo-golfleet-cor.png"

        
    # HTML header
    html_header = f"""<!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Comparativo</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Saira:wght@600;700;800&display=swap" rel="stylesheet">
        
        <!-- Leaflet CSS e JS -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

        <!-- Global CSS -->
        <style>{global_css}</style>

        <!-- Inline CSS from blocks -->
        <style>
        {"\n".join(inline_css)}
        </style>
    </head>
    <body>
        <div class='dashboard-container'>
            <!-- Logo com fundo roxo -->
            <div class="logo-container">
                <div class="logo-wrapper">
                        <img src="https://conteudo.golfleet.com.br/wp-content/uploads/2022/03/Logo-principal-2.png" alt="" class="logo-image">
                </div>
            </div>
            
            <!-- Título com gradiente -->
            <div style="text-align: center; width: 100%;">
                <h1 class="dashboard-title">📊 Dashboard de análise comparativo</h1>
            </div>
            
        """

    # Criar HTML do resumo técnico dos equipamentos
    device_summary_html = create_device_summary_html(df_raw1, df_raw2)
    
    # Criar botão flutuante para mapa de direções
    mapa_button_html = """
    <!-- Botão Flutuante do Mapa -->
    <button onclick="abrirModalMapa()" class="btn-mapa-direcoes" title="Abrir Mapa de Direções Interativo">
        🗺️ Mapa
    </button>
    
    <!-- Modal do Mapa -->
    <div id="modalMapa" class="modal-mapa">
        <div class="modal-mapa-content">
            <div class="modal-mapa-header" style="padding: 10px 20px;">
                <h2 style="font-size: 1.3em; margin: 0;">🗺️ Mapa de Análise de Direções</h2>
                <span class="close-modal-mapa" onclick="fecharModalMapa()">&times;</span>
            </div>
            
            <div class="mapa-controls" style="padding: 10px;">
                <button class="btn-grupo-mapa btn-d1 active" onclick="mostrarGrupoMapa('D1', event)" id="btnD1" style="padding: 8px 20px; font-size: 13px;">
                    D1 (1s) - <span id="countD1">0</span>
                </button>
                <button class="btn-grupo-mapa btn-d5" onclick="mostrarGrupoMapa('D5', event)" id="btnD5" style="padding: 8px 20px; font-size: 13px;">
                    D5 (5s) - <span id="countD5">0</span>
                </button>
                <button class="btn-grupo-mapa btn-d10" onclick="mostrarGrupoMapa('D10', event)" id="btnD10" style="padding: 8px 20px; font-size: 13px;">
                    D10 (10s) - <span id="countD10">0</span>
                </button>
                
                <div style="width: 1px; height: 30px; background: #dee2e6; margin: 0 5px;"></div>
                
                <button class="btn-grupo-mapa" onclick="toggleTrajeto('teste')" id="btnTrajetoTeste" style="padding: 8px 20px; font-size: 13px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    📍 Trajeto Teste (<span id="countTeste">0</span>)
                </button>
                <button class="btn-grupo-mapa" onclick="toggleTrajeto('ref')" id="btnTrajetoRef" style="padding: 8px 20px; font-size: 13px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    📍 Trajeto Referência (<span id="countRef">0</span>)
                </button>
                
                <div style="width: 1px; height: 30px; background: #dee2e6; margin: 0 5px;"></div>
                
                <button class="btn-grupo-mapa btn-clear-mapa" onclick="limparMapaDirecoes()" style="padding: 8px 20px; font-size: 13px;">
                    🗑️ Limpar
                </button>
            </div>
            
            <div class="mapa-busca-container" style="padding: 10px;">
                <input type="text" id="buscaMatch" placeholder="Buscar Match (ex: T1_5)" class="input-busca-match">
                <button onclick="buscarMatchNoMapa()" class="btn-buscar-match">
                    🔍 Buscar
                </button>
            </div>
            
            <div id="mapContainer"></div>
            
            <div id="mapaSidebar" class="mapa-sidebar">
                <button id="sidebarToggleBtn" class="mapa-sidebar-toggle" onclick="toggleSidebar()" title="Abrir Filtros de Trajeto">
                    📅
                </button>
                <h3>📅 Filtros de Trajeto</h3>
                
                <div id="filterTeste" class="mapa-filter-section disabled">
                    <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #17becf;">
                        🔵 Trajeto Teste
                    </h4>
                    <button class="mapa-btn-select-all" onclick="selecionarTodosDias('teste', true)">Todos</button>
                    <button class="mapa-btn-select-all" onclick="selecionarTodosDias('teste', false)">Nenhum</button>
                    <div id="diasTeste" class="mapa-day-filter"></div>
                </div>
                
                <div id="filterRef" class="mapa-filter-section disabled">
                    <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #12094A;">
                        🟣 Trajeto Referência
                    </h4>
                    <button class="mapa-btn-select-all" onclick="selecionarTodosDias('ref', true)">Todos</button>
                    <button class="mapa-btn-select-all" onclick="selecionarTodosDias('ref', false)">Nenhum</button>
                    <div id="diasRef" class="mapa-day-filter"></div>
                </div>
            </div>
            
            <div class="mapa-legenda">
                <h4>Legenda</h4>
                <div class="legenda-item">
                    <div class="legenda-color" style="background: #17becf;"></div>
                    <span>Dispositivo Teste</span>
                </div>
                <div class="legenda-item">
                    <div class="legenda-color" style="background: #12094A;"></div>
                    <span>Dispositivo Referência</span>
                </div>
                <div class="legenda-item">
                    <div class="legenda-color" style="background: #FF0000;"></div>
                    <span>Linha de Direção</span>
                </div>
                <div class="legenda-item">
                    <div class="legenda-color" style="background: #FF8C00;"></div>
                    <span>Conexão entre Match</span>
                </div>
            </div>
        </div>
    </div>
    """

    # Separar blocos para inserir o mapa ANTES do bloco_dashboard
    blocos_antes_mapa = []
    blocos_depois_mapa = []
    encontrou_dashboard = False
    
    for block in clean_blocks:
        # Viagens vem antes do mapa
        if 'bloco_viagens' in block or 'Análise de Viagens' in block:
            blocos_antes_mapa.append(block)
        # Dashboard e outros vêm depois do mapa
        elif 'bloco_dashboard' in block or 'Análise por Distância' in block or 'Análise por Velocidade' in block or 'Análise por Direção' in block:
            blocos_depois_mapa.append(block)
            encontrou_dashboard = True
        # Outros blocos vêm depois do dashboard
        elif encontrou_dashboard:
            blocos_depois_mapa.append(block)
        else:
            # Qualquer outro bloco antes do dashboard
            blocos_antes_mapa.append(block)

    # Combine all parts
    final_html = html_header
    final_html += device_summary_html                    # Tabela de resumo técnico
    final_html += "\n".join(blocos_antes_mapa)          # Blocos antes do mapa (viagens)
    final_html += "\n"
    final_html += mapa_button_html                       # Botão para mapa de direções (ANTES das análises)
    final_html += "\n"
    final_html += "\n".join(blocos_depois_mapa)         # Blocos após o mapa (dashboard + outros)
    final_html += "\n"
    final_html += global_scripts                         # Consolidated scripts
    final_html += "\n"
    final_html += html_footer                            # Close HTML with global JS + modal

    # Write final file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)

    # print(f"Success: Dashboard '{output_file}' generated successfully!")

# if __name__ == "__main__":
#     unir_blocos(df_raw1, df_raw2)