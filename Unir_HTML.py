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
        # '379526': 'TM-08',
        '385349': 'TM-08',
        '83': 'TM-07'
    }
    
    # Extrair tipo de dispositivo
    tipo_dispositivo = 'N/A'
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

    
    # Extrair IMEI
    imei = 'N/A'
    if 'IMEI' in df.columns:
        imeis_unicos = df['IMEI'].dropna().unique()
        if len(imeis_unicos) > 0:
            imei = ', '.join([
                str(int(float(i))) if isinstance(i, (str, float, int)) and str(i).replace('.', '', 1).isdigit()
                else str(i)
                for i in imeis_unicos
            ])
   
    # Extrair Versão Firmware
    versao_firmware = 'N/A'
    if 'Versão Firmware' in df.columns:
        versoes_unicas = df['Versão Firmware'].dropna().unique()
        if len(versoes_unicas) > 0:
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



def unir_blocos(df_raw1, df_raw2):
    blocks_dir = Path(__file__).parent / "temp_blocos"
    output_file = Path(__file__).parent / "dashboard_final.html"
    
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

    # Combine all parts
    final_html = html_header
    final_html += device_summary_html        # Tabela de resumo técnico
    final_html += "\n".join(clean_blocks)    # HTML blocks without <style> and <script>
    final_html += "\n"
    final_html += global_scripts             # Consolidated scripts
    final_html += "\n"
    final_html += html_footer                # Close HTML with global JS + modal

    # Write final file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)

    # print(f"Success: Dashboard '{output_file}' generated successfully!")

# if __name__ == "__main__":
#     unir_blocos(df_raw1, df_raw2)