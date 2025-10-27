"""
Página de Detalhes do Par - Análise Detalhada de um Par Específico
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys
import glob
from PIL import Image

# Adiciona diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DASHBOARDS, CORES, VISUALIZACAO, HTMLS_DIR
from componentes import (
    carregar_csv, 
    mostrar_prints_automatico,
    mostrar_mapa_automatico,
    criar_grafico_comparativo,
    mostrar_sistema_comentarios,
    criar_badge_status
)


def pagina_detalhes(config_dashboard=None):
    """
    Página de detalhes de análise (GPS, Velocidade ou Direção)
    
    Args:
        config_dashboard: Configuração do dashboard selecionado
    """
    # Se vier de navegação do macro, usa modo_visualizacao
    if st.session_state.get('modo_visualizacao') == 'detalhes_par':
        pagina_detalhes_par()
    elif config_dashboard:
        pagina_detalhes_analise(config_dashboard)
    else:
        st.warning("⚠️ Selecione um tipo de análise no menu lateral")


def pagina_detalhes_par():
    """
    Detalhes completos de um par (todas as análises)
    """
    par_selecionado = st.session_state.get('par_selecionado')
    
    if not par_selecionado:
        st.warning("⚠️ Nenhum par selecionado")
        if st.button("◀️ Voltar ao Dashboard"):
            st.session_state['modo_visualizacao'] = 'macro'
            st.rerun()
        return
    
    # ========== CABEÇALHO ==========
    col_header1, col_header2 = st.columns([4, 1])
    
    with col_header1:
        st.title(f"🚗 {par_selecionado.get('placa', 'N/A')}")
        st.caption(f"Par ID: {par_selecionado.get('par_id', 'N/A')}")
    
    with col_header2:
        if st.button("◀️ Voltar", use_container_width=True):
            st.session_state['modo_visualizacao'] = 'macro'
            st.session_state.pop('par_selecionado', None)
            st.rerun()
    
    st.divider()
    
    # ========== INFORMAÇÕES DO PAR ==========
    st.subheader("📊 Informações do Par")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("🆔 IMEI TM10", par_selecionado.get('imei_tm10', 'N/A'))
    col2.metric("🆔 IMEI Referência", par_selecionado.get('imei_ref', 'N/A'))
    col3.metric("📱 Tipo Referência", par_selecionado.get('tipo_ref', 'N/A'))
    col4.metric("🛣️ Viagens", par_selecionado.get('qt_viagens', 0))
    
    col5, col6, col7, col8 = st.columns(4)
    
    col5.metric("📏 Distância", f"{par_selecionado.get('distancia_km', 0):.1f} km")
    
    # Badges de status
    with col6:
        st.write("**GPS:**")
        status_gps = 'erro' if par_selecionado.get('problema_gps', False) else 'sucesso'
        texto_gps = '❌ Problema' if par_selecionado.get('problema_gps', False) else '✅ OK'
        st.markdown(criar_badge_status(status_gps, texto_gps), unsafe_allow_html=True)
    
    with col7:
        st.write("**Velocidade:**")
        status_vel = 'erro' if par_selecionado.get('problema_vel', False) else 'sucesso'
        texto_vel = '❌ Problema' if par_selecionado.get('problema_vel', False) else '✅ OK'
        st.markdown(criar_badge_status(status_vel, texto_vel), unsafe_allow_html=True)
    
    with col8:
        st.write("**Direção:**")
        status_dir = 'erro' if par_selecionado.get('problema_dir', False) else 'sucesso'
        texto_dir = '❌ Problema' if par_selecionado.get('problema_dir', False) else '✅ OK'
        st.markdown(criar_badge_status(status_dir, texto_dir), unsafe_allow_html=True)
    
    st.divider()
    
    # ========== TABS PRINCIPAIS ==========
    tabs = st.tabs([
        "🗺️ GPS",
        "🚗 Velocidade",
        "🧭 Direção",
        "📊 Dados Brutos",
        "📄 Dashboard HTML",
        "💬 Observações Gerais"
    ])
    
    par_id = par_selecionado.get('par_id')
    
    # TAB 1: GPS
    with tabs[0]:
        mostrar_tab_gps(par_id)
    
    # TAB 2: Velocidade
    with tabs[1]:
        mostrar_tab_velocidade(par_id)
    
    # TAB 3: Direção
    with tabs[2]:
        mostrar_tab_direcao(par_id)
    
    # TAB 4: Dados Brutos
    with tabs[3]:
        mostrar_tab_dados_brutos(par_id)
    
    # TAB 5: Dashboard HTML
    with tabs[4]:
        mostrar_tab_html(par_id, par_selecionado.get('placa', 'N/A'))
    
    # TAB 6: Observações
    with tabs[5]:
        st.subheader("💬 Observações Gerais do Par")
        
        if par_selecionado.get('observacoes_gerais'):
            st.info(par_selecionado.get('observacoes_gerais'))
        
        mostrar_sistema_comentarios('par_id', par_id)


def mostrar_tab_gps(par_id):
    """Conteúdo da tab de GPS"""
    st.subheader("🗺️ Análise GPS")
    
    # Carrega dados GPS do par
    dados_gps = carregar_csv(DASHBOARDS['gps']['csv'])
    
    if dados_gps is None or dados_gps.empty:
        st.warning("Nenhum dado GPS disponível")
        return
    
    # Filtra pelo par
    dados_par = dados_gps[dados_gps['par_id'] == par_id]
    
    if dados_par.empty:
        st.info("Nenhum dado GPS encontrado para este par")
        return
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    total_registros = len(dados_par)
    problemas = dados_par['problema'].sum() if 'problema' in dados_par.columns else 0
    
    col1.metric("📊 Total Registros", total_registros)
    col2.metric("⚠️ Problemas", problemas)
    
    if 'discrepancia' in dados_par.columns:
        col3.metric("📏 Dispersão Média", f"{dados_par['discrepancia'].mean():.2f}m")
        col4.metric("📏 Dispersão Máxima", f"{dados_par['discrepancia'].max():.2f}m")
    
    st.divider()
    
    # Prints
    st.markdown("#### 📷 Prints de Dispersão GPS")
    mostrar_prints_automatico(DASHBOARDS['gps'], par_id)
    
    st.divider()
    
    # Lista de matches problemáticos
    st.markdown("#### ⚠️ Matches com Problemas")
    
    if 'problema' in dados_par.columns:
        matches_problema = dados_par[dados_par['problema'] == True]
        
        if not matches_problema.empty:
            st.caption(f"🔴 {len(matches_problema)} matches problemáticos encontrados")
            
            for idx, row in matches_problema.head(10).iterrows():
                with st.expander(f"📍 {row.get('match_id', 'N/A')} - {row.get('datetime', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Informações:**")
                        st.write(f"- Discrepância: {row.get('discrepancia', 0):.2f}m")
                        st.write(f"- Velocidade: {row.get('velocidade', 0):.2f} km/h")
                        st.write(f"- Direção: {row.get('direcao', 0):.2f}°")
                        if 'observacao' in row.index:
                            st.write(f"- Observação: {row.get('observacao', 'N/A')}")
                    
                    with col2:
                        # Mapa se tiver coordenadas
                        if 'lat' in row.index and 'lon' in row.index:
                            if pd.notna(row['lat']) and pd.notna(row['lon']):
                                mostrar_mapa_automatico(
                                    row['lat'],
                                    row['lon'],
                                    f"Match {row.get('match_id')}"
                                )
        else:
            st.success("✅ Nenhum problema GPS detectado!")
    
def mostrar_tab_velocidade(par_id):
    """Conteúdo da tab de velocidade"""
    st.subheader("🚗 Análise de Velocidade")
    
    # Carrega dados de velocidade
    dados_vel = carregar_csv(DASHBOARDS['velocidade']['csv'])
    
    if dados_vel is None or dados_vel.empty:
        st.warning("Nenhum dado de velocidade disponível")
        return
    
    # Filtra pelo par
    dados_par = dados_vel[dados_vel['par_id'] == par_id]
    
    if dados_par.empty:
        st.info("Nenhum dado de velocidade encontrado para este par")
        return
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    total_registros = len(dados_par)
    problemas = dados_par['problema'].sum() if 'problema' in dados_par.columns else 0
    
    col1.metric("📊 Total Registros", total_registros)
    col2.metric("⚠️ Discrepâncias", problemas)
    
    if 'diferenca' in dados_par.columns:
        col3.metric("📈 Diferença Média", f"{dados_par['diferenca'].mean():.2f} km/h")
        col4.metric("📈 Diferença Máxima", f"{dados_par['diferenca'].max():.2f} km/h")
    
    st.divider()
    
    # Gráfico comparativo
    if 'teste' in dados_par.columns and 'referencia' in dados_par.columns:
        st.markdown("#### 📊 Gráfico Comparativo TM10 vs Referência")
        
        fig = criar_grafico_comparativo(
            dados_par['teste'].head(50),
            dados_par['referencia'].head(50),
            "Velocidade: TM10 vs Referência",
            "TM10",
            "Referência"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Prints
    st.markdown("#### 📷 Prints de Discrepâncias")
    mostrar_prints_automatico(DASHBOARDS['velocidade'], par_id)
    
    st.divider()
    
    # Matches com problemas
    st.markdown("#### ⚠️ Matches com Diferença > 20 km/h")
    
    if 'problema' in dados_par.columns:
        matches_problema = dados_par[dados_par['problema'] == True]
        
        if not matches_problema.empty:
            st.caption(f"🔴 {len(matches_problema)} matches problemáticos")
            
            # Tabela
            colunas_exibir = ['match_id', 'datetime', 'teste', 'referencia', 'diferenca']
            colunas_disponiveis = [col for col in colunas_exibir if col in matches_problema.columns]
            
            st.dataframe(
                matches_problema[colunas_disponiveis].head(20),
                use_container_width=True
            )
        else:
            st.success("✅ Nenhuma discrepância de velocidade detectada!")


def mostrar_tab_direcao(par_id):
    """Conteúdo da tab de direção"""
    st.subheader("🧭 Análise de Direção")
    
    # Carrega dados de direção
    dados_dir = carregar_csv(DASHBOARDS['direcao']['csv'])
    
    if dados_dir is None or dados_dir.empty:
        st.warning("Nenhum dado de direção disponível")
        return
    
    # Filtra pelo par
    dados_par = dados_dir[dados_dir['par_id'] == par_id]
    
    if dados_par.empty:
        st.info("Nenhum dado de direção encontrado para este par")
        return
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    total_registros = len(dados_par)
    problemas = dados_par['problema'].sum() if 'problema' in dados_par.columns else 0
    
    col1.metric("📊 Total Registros", total_registros)
    col2.metric("⚠️ Discrepâncias", problemas)
    
    if 'diferenca' in dados_par.columns:
        col3.metric("📐 Diferença Média", f"{dados_par['diferenca'].mean():.2f}°")
        col4.metric("📐 Diferença Máxima", f"{dados_par['diferenca'].max():.2f}°")
    
    st.divider()
    
    # Gráfico comparativo
    if 'teste' in dados_par.columns and 'referencia' in dados_par.columns:
        st.markdown("#### 📊 Gráfico Comparativo de Direções")
        
        fig = criar_grafico_comparativo(
            dados_par['teste'].head(50),
            dados_par['referencia'].head(50),
            "Direção: TM10 vs Referência",
            "TM10",
            "Referência"
        )
        
        fig.update_yaxes(title_text="Direção (graus)")
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Prints
    st.markdown("#### 📷 Prints de Pontos Discrepantes")
    mostrar_prints_automatico(DASHBOARDS['direcao'], par_id)
    
    st.divider()
    
    # Matches com problemas
    st.markdown("#### ⚠️ Matches com Diferença > 90°")
    
    if 'problema' in dados_par.columns:
        matches_problema = dados_par[dados_par['problema'] == True]
        
        if not matches_problema.empty:
            st.caption(f"🔴 {len(matches_problema)} matches problemáticos")
            
            # Tabela
            colunas_exibir = ['match_id', 'datetime', 'teste', 'referencia', 'diferenca', 'velocidade']
            colunas_disponiveis = [col for col in colunas_exibir if col in matches_problema.columns]
            
            st.dataframe(
                matches_problema[colunas_disponiveis].head(20),
                use_container_width=True
            )
        else:
            st.success("✅ Nenhuma discrepância de direção detectada!")


def mostrar_tab_dados_brutos(par_id):
    """Conteúdo da tab de dados brutos"""
    st.subheader("📊 Dados Brutos Consolidados")
    
    st.info("💡 Aqui você pode visualizar e baixar todos os dados brutos deste par")
    
    # Seletor de tipo de dado
    tipo_dado = st.selectbox(
        "Selecione o tipo de dado:",
        ['GPS', 'Velocidade', 'Direção']
    )
    
    # Carrega dados baseado na seleção
    if tipo_dado == 'GPS':
        dados = carregar_csv(DASHBOARDS['gps']['csv'])
    elif tipo_dado == 'Velocidade':
        dados = carregar_csv(DASHBOARDS['velocidade']['csv'])
    else:
        dados = carregar_csv(DASHBOARDS['direcao']['csv'])
    
    if dados is not None and not dados.empty:
        # Filtra pelo par
        dados_par = dados[dados['par_id'] == par_id]
        
        if not dados_par.empty:
            st.caption(f"📊 {len(dados_par)} registros encontrados")
            
            # Filtro por data
            with st.expander("🔍 Filtros"):
                if 'datetime' in dados_par.columns:
                    col1, col2 = st.columns(2)
                    
                    # Converte para datetime
                    dados_par['datetime_dt'] = pd.to_datetime(dados_par['datetime'], errors='coerce')
                    
                    with col1:
                        data_inicio = st.date_input(
                            "Data Início",
                            value=dados_par['datetime_dt'].min()
                        )
                    
                    with col2:
                        data_fim = st.date_input(
                            "Data Fim",
                            value=dados_par['datetime_dt'].max()
                        )
                    
                    # Aplica filtro
                    dados_par = dados_par[
                        (dados_par['datetime_dt'].dt.date >= data_inicio) &
                        (dados_par['datetime_dt'].dt.date <= data_fim)
                    ]
            
            # Mostra dados
            st.dataframe(dados_par, use_container_width=True, height=400)
            
            # Estatísticas
            st.markdown("#### 📈 Estatísticas Descritivas")
            st.dataframe(dados_par.describe(), use_container_width=True)
            
            # Download
            csv = dados_par.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 Download CSV",
                csv,
                f"dados_{tipo_dado.lower()}_par_{par_id}.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info(f"Nenhum dado de {tipo_dado} encontrado para este par")
    else:
        st.warning(f"Dados de {tipo_dado} não disponíveis")


def mostrar_tab_html(par_id, placa):
    """Conteúdo da tab de HTML"""
    st.subheader("📄 Dashboard HTML Completo")
    
    st.info("💡 Aqui seria exibido o HTML completo gerado externamente")
    
    # Busca arquivo HTML
    html_files = glob.glob(os.path.join(HTMLS_DIR, f"*{par_id}*.html"))
    
    if not html_files:
        html_files = glob.glob(os.path.join(HTMLS_DIR, f"*{placa}*.html"))
    
    if html_files:
        html_file = html_files[0]
        
        st.success(f"✅ HTML encontrado: {os.path.basename(html_file)}")
        
        # Botão de download
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        st.download_button(
            "📥 Download HTML",
            html_content,
            f"dashboard_par_{par_id}.html",
            "text/html",
            use_container_width=True
        )
        
        st.divider()
        
        # Embed HTML (limitado pelo Streamlit)
        st.markdown("#### 🖥️ Visualização")
        st.caption("⚠️ Preview limitado - Baixe o arquivo para visualização completa")
        
        # Usa components para embed
        import streamlit.components.v1 as components
        components.html(html_content, height=600, scrolling=True)
        
    else:
        st.warning(f"📄 Nenhum arquivo HTML encontrado para o par {par_id}")
        st.caption(f"Procurado em: {HTMLS_DIR}")


def pagina_detalhes_analise(config_dashboard):
    """
    Detalhes de uma análise específica (quando vindo do modo análise detalhada)
    """
    st.title(f"{config_dashboard['icone']} {config_dashboard['nome']}")
    st.caption(config_dashboard['descricao'])
    
    st.divider()
    
    # Usa componente universal
    from componentes import tabela_clicavel_universal, mostrar_detalhes_universais
    
    # Se tem registro selecionado, mostra detalhes
    if st.session_state.get('registro_selecionado') and st.session_state.get('modo_visualizacao') == 'detalhes':
        mostrar_detalhes_universais(
            config_dashboard,
            st.session_state['registro_selecionado']
        )
    else:
        # Senão, mostra tabela
        tabela_clicavel_universal(config_dashboard, key_prefix=config_dashboard['icone'])


if __name__ == "__main__":
    pagina_detalhes()

