"""
Sistema de Análise de Pares TM10 vs TM-07/TM-08
Dashboard Streamlit Principal

Autor: Sistema Automatizado
Data: 2025
Versão: 1.0
"""

import streamlit as st
import sys
import os

# Adiciona diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DASHBOARDS, CORES
from paginas.dashboard_macro import pagina_macro
from paginas.detalhes_par import pagina_detalhes
from paginas.admin_uploads import pagina_admin

# ========== CONFIGURAÇÃO DA PÁGINA ==========
st.set_page_config(
    page_title="Sistema de Análise de Pares",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': """
        # Sistema de Análise de Pares
        
        **Versão:** 1.0
        
        Sistema completo para análise comparativa entre dispositivos TM10 e TM-07/TM-08.
        
        **Funcionalidades:**
        - Dashboard Macro com visão geral
        - Análise detalhada por par
        - Análise por tipo (GPS, Velocidade, Direção)
        - Sistema de comentários
        - Upload e gerenciamento de arquivos
        - Galeria de prints
        
        ---
        Desenvolvido com Streamlit 🎈
        """
    }
)

# ========== ESTILOS CSS CUSTOMIZADOS ==========
st.markdown(f"""
<style>
    /* Cores principais */
    :root {{
        --cor-primaria: {CORES['primaria']};
        --cor-sucesso: {CORES['sucesso']};
        --cor-erro: {CORES['erro']};
        --cor-aviso: {CORES['aviso']};
    }}
    
    /* Melhora visual dos cards de métricas */
    [data-testid="stMetricValue"] {{
        font-size: 28px;
        font-weight: bold;
    }}
    
    /* Espaçamento melhor */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* Botões mais bonitos */
    .stButton > button {{
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    
    /* Tabs mais destacadas */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }}
    
    /* Dividers mais suaves */
    hr {{
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid rgba(0,0,0,0.1);
    }}
    
    /* Expanders mais bonitos */
    .streamlit-expanderHeader {{
        font-weight: 600;
        border-radius: 8px;
    }}
    
    /* DataFrames mais legíveis */
    .dataframe {{
        font-size: 14px;
    }}
    
    /* Sidebar mais organizada */
    [data-testid="stSidebar"] {{
        background-color: #f8f9fa;
    }}
    
    /* Títulos com mais destaque */
    h1 {{
        font-weight: 700;
        margin-bottom: 0.5rem;
    }}
    
    h2 {{
        font-weight: 600;
        margin-top: 1rem;
    }}
    
    h3 {{
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# ========== INICIALIZAÇÃO DO SESSION STATE ==========
def inicializar_session_state():
    """Inicializa variáveis do session state"""
    if 'modo_visualizacao' not in st.session_state:
        st.session_state['modo_visualizacao'] = 'macro'
    
    if 'par_selecionado' not in st.session_state:
        st.session_state['par_selecionado'] = None
    
    if 'registro_selecionado' not in st.session_state:
        st.session_state['registro_selecionado'] = None
    
    if 'config_selecionada' not in st.session_state:
        st.session_state['config_selecionada'] = None


# ========== SIDEBAR ==========
def renderizar_sidebar():
    """Renderiza menu lateral"""
    
    with st.sidebar:
        st.title("🚗 Sistema de Análise")
        st.caption("TM10 vs TM-07/TM-08")
        
        st.divider()
        
        # Modo de visualização
        modo = st.radio(
            "**Modo de Visualização:**",
            ["📊 Dashboard Macro", "🔍 Análise Detalhada", "🔧 Admin - Uploads"],
            key="modo_radio"
        )
        
        st.divider()
        
        # Se estiver no modo de análise detalhada, mostra seleção de tipo
        dashboard_tipo = None
        if modo == "🔍 Análise Detalhada":
            st.markdown("**Tipo de Análise:**")
            
            dashboard_tipo = st.selectbox(
                "Selecione:",
                list(DASHBOARDS.keys()),
                format_func=lambda x: f"{DASHBOARDS[x]['icone']} {DASHBOARDS[x]['nome']}",
                label_visibility="collapsed"
            )
            
            # Descrição
            if dashboard_tipo:
                st.caption(DASHBOARDS[dashboard_tipo]['descricao'])
            
            st.divider()
        
        # Informações
        st.markdown("### 📚 Informações")
        
        with st.expander("ℹ️ Sobre o Sistema"):
            st.markdown("""
            **Sistema de Análise de Pares**
            
            Ferramenta completa para análise comparativa entre dispositivos de rastreamento.
            
            **Funcionalidades:**
            - 📊 Dashboard com visão macro
            - 🔍 Análise detalhada por par
            - 🗺️ Análise de GPS
            - 🚗 Análise de Velocidade
            - 🧭 Análise de Direção
            - 💬 Sistema de comentários
            - 📤 Upload de arquivos
            - 🖼️ Galeria de prints
            """)
        
        with st.expander("🎯 Como Usar"):
            st.markdown("""
            **Dashboard Macro:**
            - Visão geral de todos os pares
            - Filtros e busca
            - Exportação de relatórios
            
            **Análise Detalhada:**
            - Selecione o tipo de análise
            - Navegue pelos dados
            - Clique para ver detalhes
            
            **Admin - Uploads:**
            - Faça upload de imagens
            - Gerencie arquivos
            - Visualize galeria
            """)
        
        with st.expander("📖 Legenda"):
            st.markdown(f"""
            **Status:**
            - 🟢 **Verde**: Sem problemas
            - 🔴 **Vermelho**: Problema detectado
            - 🟡 **Amarelo**: Atenção necessária
            - 🔵 **Azul**: Informação
            
            **Tipos de Referência:**
            - **TM-07**: Rastreador modelo 07
            - **TM-08**: Rastreador modelo 08
            """)
        
        st.divider()
        
        # Estatísticas rápidas
        st.markdown("### 📈 Status do Sistema")
        
        # Tenta carregar dados para mostrar stats
        try:
            from componentes import carregar_csv
            from config import ANALISE_PARES_CONFIG
            
            dados = carregar_csv(ANALISE_PARES_CONFIG['csv'])
            
            if dados is not None and not dados.empty:
                col1, col2 = st.columns(2)
                
                col1.metric("Total Pares", len(dados))
                
                if 'problema_gps' in dados.columns:
                    problemas = (
                        dados['problema_gps'].sum() +
                        dados.get('problema_vel', pd.Series([0])).sum() +
                        dados.get('problema_dir', pd.Series([0])).sum()
                    )
                    col2.metric("Problemas", int(problemas))
        except:
            pass
        
        st.divider()
        
        # Footer
        st.caption("v1.0 | 2025")
        st.caption("Desenvolvido com Streamlit 🎈")
    
    return modo, dashboard_tipo


# ========== FUNÇÃO PRINCIPAL ==========
def main():
    """Função principal da aplicação"""
    
    # Inicializa session state
    inicializar_session_state()
    
    # Renderiza sidebar e captura seleções
    modo, dashboard_tipo = renderizar_sidebar()
    
    # Roteamento de páginas baseado no modo
    if modo == "📊 Dashboard Macro":
        # Reseta modo se estava em outra página
        if st.session_state['modo_visualizacao'] not in ['macro', 'detalhes_par']:
            st.session_state['modo_visualizacao'] = 'macro'
        
        # Se veio de detalhes de par, mostra par
        if st.session_state['modo_visualizacao'] == 'detalhes_par':
            pagina_detalhes()
        else:
            pagina_macro()
    
    elif modo == "🔍 Análise Detalhada":
        if dashboard_tipo:
            config = DASHBOARDS[dashboard_tipo]
            pagina_detalhes(config)
        else:
            st.warning("⚠️ Selecione um tipo de análise no menu lateral")
    
    elif modo == "🔧 Admin - Uploads":
        pagina_admin()
    
    # Footer da página principal
    st.divider()
    
    col_footer1, col_footer2, col_footer3 = st.columns(3)
    
    with col_footer1:
        st.caption("📧 Suporte: sistema@analise.com")
    
    with col_footer2:
        st.caption("📚 Documentação disponível no menu About")
    
    with col_footer3:
        st.caption(f"🕐 Última atualização: {st.session_state.get('ultima_atualizacao', 'N/A')}")


# ========== PONTO DE ENTRADA ==========
if __name__ == "__main__":
    main()

