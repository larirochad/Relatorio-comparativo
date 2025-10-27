"""
Página de Dashboard Macro - Visão Geral de Todos os Pares
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Adiciona diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ANALISE_PARES_CONFIG, CORES, VISUALIZACAO
from componentes import carregar_csv, mostrar_metricas_resumo, criar_badge_status


def pagina_macro():
    """
    Página principal com visão macro de todos os pares
    """
    st.title("📊 Dashboard Macro - Análise de Pares")
    st.caption("Visão geral consolidada de todos os pares analisados")
    
    # Carrega dados
    dados_pares = carregar_csv(ANALISE_PARES_CONFIG['csv'])
    
    if dados_pares is None or dados_pares.empty:
        st.error("❌ Nenhum dado de análise de pares encontrado")
        return
    
    # ========== SEÇÃO 1: KPIs PRINCIPAIS ==========
    st.subheader("📈 Indicadores Principais")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Total de pares
    total_pares = len(dados_pares)
    col1.metric("🚗 Total de Pares", total_pares)
    
    # Problemas GPS
    if 'problema_gps' in dados_pares.columns:
        problemas_gps = dados_pares['problema_gps'].sum()
        perc_gps = (problemas_gps / total_pares * 100) if total_pares > 0 else 0
        col2.metric(
            "🗺️ Problemas GPS",
            problemas_gps,
            f"{perc_gps:.1f}%",
            delta_color="inverse"
        )
    
    # Problemas Velocidade
    if 'problema_vel' in dados_pares.columns:
        problemas_vel = dados_pares['problema_vel'].sum()
        perc_vel = (problemas_vel / total_pares * 100) if total_pares > 0 else 0
        col3.metric(
            "🚗 Problemas Velocidade",
            problemas_vel,
            f"{perc_vel:.1f}%",
            delta_color="inverse"
        )
    
    # Problemas Direção
    if 'problema_dir' in dados_pares.columns:
        problemas_dir = dados_pares['problema_dir'].sum()
        perc_dir = (problemas_dir / total_pares * 100) if total_pares > 0 else 0
        col4.metric(
            "🧭 Problemas Direção",
            problemas_dir,
            f"{perc_dir:.1f}%",
            delta_color="inverse"
        )
    
    # Distância total
    if 'distancia_km' in dados_pares.columns:
        distancia_total = dados_pares['distancia_km'].sum()
        col5.metric("📏 Distância Total", f"{distancia_total:.1f} km")
    
    st.divider()
    
    # ========== SEÇÃO 2: GRÁFICOS DE ANÁLISE ==========
    st.subheader("📊 Análise Visual")
    
    col_grafico1, col_grafico2 = st.columns(2)
    
    with col_grafico1:
        # Gráfico: Distribuição de problemas
        st.markdown("#### Distribuição de Problemas por Tipo")
        
        problemas_data = {
            'Tipo': ['GPS', 'Velocidade', 'Direção'],
            'Quantidade': [
                dados_pares['problema_gps'].sum() if 'problema_gps' in dados_pares.columns else 0,
                dados_pares['problema_vel'].sum() if 'problema_vel' in dados_pares.columns else 0,
                dados_pares['problema_dir'].sum() if 'problema_dir' in dados_pares.columns else 0
            ]
        }
        
        fig_problemas = px.bar(
            problemas_data,
            x='Tipo',
            y='Quantidade',
            color='Tipo',
            color_discrete_map={
                'GPS': CORES['erro'],
                'Velocidade': CORES['aviso'],
                'Direção': CORES['info']
            },
            text='Quantidade'
        )
        
        fig_problemas.update_layout(
            showlegend=False,
            height=350,
            xaxis_title="",
            yaxis_title="Quantidade de Pares"
        )
        
        st.plotly_chart(fig_problemas, use_container_width=True)
    
    with col_grafico2:
        # Gráfico: Distribuição por tipo de referência
        st.markdown("#### Distribuição por Tipo de Referência")
        
        if 'tipo_ref' in dados_pares.columns:
            tipo_ref_counts = dados_pares['tipo_ref'].value_counts().reset_index()
            tipo_ref_counts.columns = ['Tipo', 'Quantidade']
            
            fig_tipo = px.pie(
                tipo_ref_counts,
                values='Quantidade',
                names='Tipo',
                color_discrete_sequence=[CORES['primaria'], CORES['sucesso']]
            )
            
            fig_tipo.update_layout(height=350)
            
            st.plotly_chart(fig_tipo, use_container_width=True)
        else:
            st.info("Dados de tipo de referência não disponíveis")
    
    st.divider()
    
    # ========== SEÇÃO 3: TIMELINE DE ANÁLISES ==========
    if 'inicio_analise' in dados_pares.columns:
        st.subheader("📅 Timeline de Análises")
        
        # Converte para datetime
        dados_pares['inicio_analise_dt'] = pd.to_datetime(
            dados_pares['inicio_analise'],
            errors='coerce'
        )
        
        # Agrupa por data
        timeline = dados_pares.groupby(
            dados_pares['inicio_analise_dt'].dt.date
        ).size().reset_index(name='quantidade')
        timeline.columns = ['Data', 'Quantidade']
        
        fig_timeline = px.line(
            timeline,
            x='Data',
            y='Quantidade',
            markers=True,
            line_shape='spline'
        )
        
        fig_timeline.update_layout(
            height=300,
            xaxis_title="Data",
            yaxis_title="Análises Realizadas",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        st.divider()
    
    # ========== SEÇÃO 4: FILTROS E BUSCA ==========
    st.subheader("🔍 Buscar e Filtrar Pares")
    
    with st.expander("Filtros Avançados", expanded=False):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        # Filtro por tipo de referência
        tipos_disponiveis = ['Todos']
        if 'tipo_ref' in dados_pares.columns:
            tipos_disponiveis += sorted(dados_pares['tipo_ref'].unique().tolist())
        
        tipo_filtro = col_f1.selectbox("Tipo Referência", tipos_disponiveis)
        
        # Filtro por problemas
        problema_filtro = col_f2.selectbox(
            "Problemas",
            ['Todos', 'Com Problemas', 'Sem Problemas']
        )
        
        # Filtro por distância
        if 'distancia_km' in dados_pares.columns:
            distancia_min = col_f3.number_input(
                "Distância Mínima (km)",
                min_value=0.0,
                value=0.0
            )
            
            distancia_max = col_f4.number_input(
                "Distância Máxima (km)",
                min_value=0.0,
                value=float(dados_pares['distancia_km'].max())
            )
        
        # Busca por texto
        busca_texto = st.text_input(
            "🔎 Buscar por Placa, IMEI ou Observação",
            placeholder="Digite para buscar..."
        )
    
    # Aplica filtros
    dados_filtrados = dados_pares.copy()
    
    if tipo_filtro != 'Todos':
        dados_filtrados = dados_filtrados[dados_filtrados['tipo_ref'] == tipo_filtro]
    
    if problema_filtro == 'Com Problemas':
        if all(col in dados_filtrados.columns for col in ['problema_gps', 'problema_vel', 'problema_dir']):
            dados_filtrados = dados_filtrados[
                (dados_filtrados['problema_gps']) |
                (dados_filtrados['problema_vel']) |
                (dados_filtrados['problema_dir'])
            ]
    elif problema_filtro == 'Sem Problemas':
        if all(col in dados_filtrados.columns for col in ['problema_gps', 'problema_vel', 'problema_dir']):
            dados_filtrados = dados_filtrados[
                (~dados_filtrados['problema_gps']) &
                (~dados_filtrados['problema_vel']) &
                (~dados_filtrados['problema_dir'])
            ]
    
    if 'distancia_km' in dados_filtrados.columns:
        dados_filtrados = dados_filtrados[
            (dados_filtrados['distancia_km'] >= distancia_min) &
            (dados_filtrados['distancia_km'] <= distancia_max)
        ]
    
    if busca_texto:
        mask = dados_filtrados.astype(str).apply(
            lambda row: row.str.contains(busca_texto, case=False, na=False).any(),
            axis=1
        )
        dados_filtrados = dados_filtrados[mask]
    
    # ========== SEÇÃO 5: TABELA DE PARES ==========
    st.subheader(f"📋 Lista de Pares ({len(dados_filtrados)} encontrados)")
    
    # Botão de exportar
    col_exp1, col_exp2 = st.columns([1, 4])
    
    with col_exp1:
        if st.button("📥 Exportar CSV", use_container_width=True):
            csv = dados_filtrados.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "⬇️ Download CSV",
                csv,
                f"analise_pares_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
    
    # Tabela interativa
    for idx, row in dados_filtrados.iterrows():
        with st.container():
            col_info, col_metricas, col_badges, col_btn = st.columns([2, 2, 2, 1])
            
            with col_info:
                st.markdown(f"### 🚗 {row.get('placa', 'N/A')}")
                st.caption(f"**Par ID:** {row.get('par_id', 'N/A')}")
                st.caption(f"**TM10:** {row.get('imei_tm10', 'N/A')}")
                st.caption(f"**Ref:** {row.get('imei_ref', 'N/A')} ({row.get('tipo_ref', 'N/A')})")
            
            with col_metricas:
                st.metric("🛣️ Viagens", row.get('qt_viagens', 0))
                st.metric("📏 Distância", f"{row.get('distancia_km', 0):.1f} km")
            
            with col_badges:
                st.write("**Status:**")
                
                # Badge GPS
                if row.get('problema_gps', False):
                    st.markdown(
                        criar_badge_status('erro', '🗺️ GPS'),
                        unsafe_allow_html=True
                    )
                
                # Badge Velocidade
                if row.get('problema_vel', False):
                    st.markdown(
                        criar_badge_status('aviso', '🚗 VEL'),
                        unsafe_allow_html=True
                    )
                
                # Badge Direção
                if row.get('problema_dir', False):
                    st.markdown(
                        criar_badge_status('info', '🧭 DIR'),
                        unsafe_allow_html=True
                    )
                
                # Se não tem problemas
                if not any([
                    row.get('problema_gps', False),
                    row.get('problema_vel', False),
                    row.get('problema_dir', False)
                ]):
                    st.markdown(
                        criar_badge_status('sucesso', '✅ OK'),
                        unsafe_allow_html=True
                    )
            
            with col_btn:
                if st.button(
                    "📋 Detalhes",
                    key=f"btn_par_{idx}",
                    use_container_width=True
                ):
                    # Salva no session_state e redireciona
                    st.session_state['par_selecionado'] = row.to_dict()
                    st.session_state['modo_visualizacao'] = 'detalhes_par'
                    st.rerun()
            
            # Observações se existirem
            if 'observacoes_gerais' in row.index and pd.notna(row['observacoes_gerais']):
                st.caption(f"💬 {row['observacoes_gerais']}")
            
            st.divider()
    
    # Paginação info
    if len(dados_filtrados) == 0:
        st.info("ℹ️ Nenhum par encontrado com os filtros aplicados")


if __name__ == "__main__":
    pagina_macro()

