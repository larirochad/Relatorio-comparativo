"""
Componentes reutilizáveis para o dashboard de análise de pares
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from PIL import Image
import glob
import os
import json
from datetime import datetime
from config import CORES, VISUALIZACAO, MENSAGENS, COMENTARIOS_FILE


# ========== FUNÇÕES DE CARREGAMENTO DE DADOS ==========

@st.cache_data(ttl=3600)
def carregar_csv(caminho_csv):
    """
    Carrega CSV com cache para melhor performance
    
    Args:
        caminho_csv: Caminho do arquivo CSV
        
    Returns:
        DataFrame do pandas ou None se erro
    """
    try:
        if os.path.exists(caminho_csv):
            df = pd.read_csv(caminho_csv)
            return df
        else:
            st.warning(f"Arquivo não encontrado: {caminho_csv}")
            return None
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {str(e)}")
        return None


def salvar_comentarios(comentarios):
    """
    Salva comentários no arquivo JSON
    
    Args:
        comentarios: Lista de comentários
    """
    try:
        dados = {
            "comentarios": comentarios,
            "metadata": {
                "versao": "1.0",
                "ultima_atualizacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        with open(COMENTARIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar comentários: {str(e)}")
        return False


def carregar_comentarios():
    """
    Carrega comentários do arquivo JSON
    
    Returns:
        Lista de comentários
    """
    try:
        if os.path.exists(COMENTARIOS_FILE):
            with open(COMENTARIOS_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                return dados.get("comentarios", [])
        return []
    except Exception as e:
        st.error(f"Erro ao carregar comentários: {str(e)}")
        return []


# ========== COMPONENTES VISUAIS ==========

def mostrar_metricas_resumo(dados, colunas_metricas):
    """
    Mostra métricas de resumo em cards
    
    Args:
        dados: DataFrame com os dados
        colunas_metricas: Lista de colunas para calcular métricas
    """
    if dados is None or dados.empty:
        st.warning(MENSAGENS["sem_dados"])
        return
    
    # Cria colunas para as métricas
    cols = st.columns(len(colunas_metricas) + 2)
    
    # Total de registros
    cols[0].metric("📊 Total Registros", len(dados))
    
    # Problemas encontrados (se coluna 'problema' existir)
    if 'problema' in dados.columns:
        problemas = dados['problema'].sum() if dados['problema'].dtype == bool else len(dados[dados['problema'] == True])
        percentual = (problemas / len(dados) * 100) if len(dados) > 0 else 0
        cols[1].metric(
            "⚠️ Problemas", 
            problemas,
            delta=f"{percentual:.1f}%",
            delta_color="inverse"
        )
    
    # Outras métricas personalizadas
    for i, coluna in enumerate(colunas_metricas, start=2):
        if coluna in dados.columns and i < len(cols):
            if pd.api.types.is_numeric_dtype(dados[coluna]):
                valor = dados[coluna].sum()
                cols[i].metric(f"📈 {coluna.title()}", f"{valor:.1f}")


def criar_badge_status(status, texto=""):
    """
    Cria um badge colorido de status
    
    Args:
        status: 'sucesso', 'erro', 'aviso', 'info'
        texto: Texto do badge
        
    Returns:
        HTML do badge
    """
    cores_badge = {
        'sucesso': CORES['sucesso'],
        'erro': CORES['erro'],
        'aviso': CORES['aviso'],
        'info': CORES['info']
    }
    
    cor = cores_badge.get(status, CORES['secundaria'])
    
    html = f"""
    <span style="
        background-color: {cor};
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin: 2px;
    ">
        {texto}
    </span>
    """
    return html


def tabela_clicavel_universal(config_dashboard, key_prefix=""):
    """
    Cria tabela interativa com filtros e botões clicáveis
    
    Args:
        config_dashboard: Dicionário de configuração do dashboard
        key_prefix: Prefixo para keys do Streamlit (evitar duplicação)
    """
    # Carrega dados
    dados = carregar_csv(config_dashboard['csv'])
    
    if dados is None or dados.empty:
        st.warning(MENSAGENS["sem_dados"])
        return
    
    # Mostra métricas de resumo
    st.subheader(f"{config_dashboard['icone']} {config_dashboard['nome']}")
    st.caption(config_dashboard['descricao'])
    
    mostrar_metricas_resumo(dados, config_dashboard.get('metricas', []))
    
    st.divider()
    
    # Filtros
    with st.expander("🔍 Filtros", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        filtros_aplicados = {}
        
        # Filtro por Par ID
        if 'par_id' in dados.columns:
            pares_disponiveis = ['Todos'] + sorted(dados['par_id'].unique().tolist())
            par_selecionado = col1.selectbox(
                "Par ID",
                pares_disponiveis,
                key=f"{key_prefix}_filtro_par"
            )
            if par_selecionado != 'Todos':
                filtros_aplicados['par_id'] = par_selecionado
        
        # Filtro por Problema
        if 'problema' in dados.columns:
            problema_filtro = col2.selectbox(
                "Tipo",
                ['Todos', 'Apenas Problemas', 'Sem Problemas'],
                key=f"{key_prefix}_filtro_problema"
            )
            if problema_filtro == 'Apenas Problemas':
                filtros_aplicados['problema'] = True
            elif problema_filtro == 'Sem Problemas':
                filtros_aplicados['problema'] = False
        
        # Busca por texto
        busca = col3.text_input(
            "🔎 Buscar",
            placeholder="Digite para buscar...",
            key=f"{key_prefix}_busca"
        )
    
    # Aplica filtros
    dados_filtrados = dados.copy()
    
    for coluna, valor in filtros_aplicados.items():
        dados_filtrados = dados_filtrados[dados_filtrados[coluna] == valor]
    
    if busca:
        # Busca em todas as colunas de texto
        mask = dados_filtrados.astype(str).apply(
            lambda row: row.str.contains(busca, case=False, na=False).any(),
            axis=1
        )
        dados_filtrados = dados_filtrados[mask]
    
    # Mostra total após filtros
    st.caption(f"📊 Mostrando {len(dados_filtrados)} de {len(dados)} registros")
    
    # Tabela com botões
    colunas_exibir = config_dashboard.get('colunas_exibir', config_dashboard['colunas_principais'])
    
    # Limita registros para não sobrecarregar
    dados_paginados = dados_filtrados.head(VISUALIZACAO['itens_por_pagina'])
    
    for idx, row in dados_paginados.iterrows():
        with st.container():
            col_info, col_btn = st.columns([4, 1])
            
            with col_info:
                # Cria resumo da linha
                info_texto = " | ".join([
                    f"**{col}:** {row[col]}" 
                    for col in colunas_exibir 
                    if col in row.index
                ])
                st.markdown(info_texto)
                
                # Badge de problema se existir
                if 'problema' in row.index and row['problema']:
                    st.markdown(
                        criar_badge_status('erro', '⚠️ PROBLEMA'),
                        unsafe_allow_html=True
                    )
            
            with col_btn:
                # Botão para ver detalhes
                if st.button(
                    "📋 Ver Detalhes",
                    key=f"{key_prefix}_btn_{idx}",
                    use_container_width=True
                ):
                    # Salva no session_state
                    st.session_state['registro_selecionado'] = row.to_dict()
                    st.session_state['config_selecionada'] = config_dashboard
                    st.session_state['modo_visualizacao'] = 'detalhes'
                    st.rerun()
            
            st.divider()
    
    # Aviso se há mais registros
    if len(dados_filtrados) > VISUALIZACAO['itens_por_pagina']:
        st.info(f"ℹ️ Mostrando apenas {VISUALIZACAO['itens_por_pagina']} primeiros registros. Use os filtros para refinar a busca.")


def mostrar_detalhes_universais(config_dashboard, registro):
    """
    Mostra detalhes completos de um registro
    
    Args:
        config_dashboard: Configuração do dashboard
        registro: Dicionário com dados do registro
    """
    # Cabeçalho
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title(f"{config_dashboard['icone']} Detalhes - {config_dashboard['nome']}")
        st.caption(f"ID: {registro.get(config_dashboard['coluna_id'], 'N/A')}")
    
    with col2:
        if st.button("◀️ Voltar", use_container_width=True):
            st.session_state['modo_visualizacao'] = 'lista'
            st.session_state.pop('registro_selecionado', None)
            st.rerun()
    
    st.divider()
    
    # Tabs
    tabs = ["📊 Dados", "📷 Prints"]
    
    if config_dashboard.get('tem_mapa') and 'lat' in registro and 'lon' in registro:
        tabs.append("🗺️ Mapa")
    
    tabs.append("💬 Comentários")
    
    tab_objs = st.tabs(tabs)
    
    # Tab 1: Dados
    with tab_objs[0]:
        st.subheader("📋 Informações Completas")
        
        # Mostra todos os campos em cards
        cols = st.columns(2)
        for i, (chave, valor) in enumerate(registro.items()):
            with cols[i % 2]:
                # Formata valor
                if pd.isna(valor):
                    valor_formatado = "N/A"
                elif isinstance(valor, (int, float)):
                    valor_formatado = f"{valor:.2f}" if isinstance(valor, float) else str(valor)
                else:
                    valor_formatado = str(valor)
                
                st.metric(chave.replace('_', ' ').title(), valor_formatado)
    
    # Tab 2: Prints
    with tab_objs[1]:
        mostrar_prints_automatico(
            config_dashboard,
            registro.get(config_dashboard['coluna_id'])
        )
    
    # Tab 3: Mapa (se aplicável)
    tab_idx = 2
    if config_dashboard.get('tem_mapa') and 'lat' in registro and 'lon' in registro:
        with tab_objs[tab_idx]:
            mostrar_mapa_automatico(
                registro['lat'],
                registro['lon'],
                f"{config_dashboard['nome']} - {registro.get(config_dashboard['coluna_id'])}"
            )
        tab_idx += 1
    
    # Tab final: Comentários
    with tab_objs[tab_idx]:
        mostrar_sistema_comentarios(
            config_dashboard['coluna_id'],
            registro.get(config_dashboard['coluna_id'])
        )


def mostrar_prints_automatico(config_dashboard, id_registro):
    """
    Busca e exibe automaticamente prints relacionados
    
    Args:
        config_dashboard: Configuração do dashboard
        id_registro: ID do registro para buscar prints
    """
    st.subheader("📷 Galeria de Imagens")
    
    if not id_registro:
        st.warning(MENSAGENS["sem_prints"])
        return
    
    pasta_prints = config_dashboard['pasta_prints']
    
    # Padrões de busca
    padroes = [
        os.path.join(pasta_prints, f"*{id_registro}*"),
        os.path.join(pasta_prints, f"{id_registro}", "*"),
        os.path.join(pasta_prints, "**", f"*{id_registro}*"),
    ]
    
    # Busca imagens
    imagens_encontradas = []
    for padrao in padroes:
        imagens_encontradas.extend(glob.glob(padrao, recursive=True))
    
    # Filtra apenas imagens
    extensoes_validas = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
    imagens = [
        img for img in imagens_encontradas
        if os.path.splitext(img)[1].lower() in extensoes_validas
    ]
    
    if not imagens:
        st.info(MENSAGENS["sem_prints"])
        return
    
    st.caption(f"🖼️ {len(imagens)} imagens encontradas")
    
    # Exibe em galeria
    cols_por_linha = VISUALIZACAO['colunas_galeria']
    
    for i in range(0, len(imagens), cols_por_linha):
        cols = st.columns(cols_por_linha)
        
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(imagens):
                with col:
                    try:
                        img = Image.open(imagens[idx])
                        st.image(
                            img,
                            caption=os.path.basename(imagens[idx]),
                            use_container_width=True
                        )
                        
                        # Botão de download
                        with open(imagens[idx], 'rb') as f:
                            st.download_button(
                                "⬇️ Download",
                                f.read(),
                                file_name=os.path.basename(imagens[idx]),
                                key=f"download_{idx}_{id_registro}"
                            )
                    except Exception as e:
                        st.error(f"Erro ao carregar: {os.path.basename(imagens[idx])}")


def mostrar_mapa_automatico(lat, lon, titulo="Local"):
    """
    Cria mapa interativo com Folium
    
    Args:
        lat: Latitude
        lon: Longitude
        titulo: Título do marcador
    """
    st.subheader("🗺️ Localização")
    
    try:
        # Converte para float se necessário
        lat = float(lat)
        lon = float(lon)
        
        # Cria mapa
        mapa = folium.Map(
            location=[lat, lon],
            zoom_start=VISUALIZACAO['zoom_padrao_mapa'],
            width=VISUALIZACAO['largura_mapa'],
            height=VISUALIZACAO['altura_mapa']
        )
        
        # Adiciona marcador
        folium.Marker(
            [lat, lon],
            popup=titulo,
            tooltip=titulo,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(mapa)
        
        # Exibe mapa
        st_folium(mapa, width=VISUALIZACAO['largura_mapa'], height=VISUALIZACAO['altura_mapa'])
        
        # Coordenadas
        col1, col2 = st.columns(2)
        col1.metric("Latitude", f"{lat:.6f}")
        col2.metric("Longitude", f"{lon:.6f}")
        
    except Exception as e:
        st.error(f"Erro ao criar mapa: {str(e)}")


def criar_grafico_comparativo(dados_teste, dados_referencia, titulo, label_teste="TM10", label_ref="Referência"):
    """
    Cria gráfico comparativo interativo
    
    Args:
        dados_teste: Lista/Series com dados do teste
        dados_referencia: Lista/Series com dados da referência
        titulo: Título do gráfico
        label_teste: Label da linha de teste
        label_ref: Label da linha de referência
        
    Returns:
        Figura Plotly
    """
    fig = go.Figure()
    
    # Linha de teste
    fig.add_trace(go.Scatter(
        y=dados_teste,
        mode='lines+markers',
        name=label_teste,
        line=dict(color=CORES['erro'], width=2),
        marker=dict(size=6)
    ))
    
    # Linha de referência
    fig.add_trace(go.Scatter(
        y=dados_referencia,
        mode='lines+markers',
        name=label_ref,
        line=dict(color=CORES['sucesso'], width=2),
        marker=dict(size=6)
    ))
    
    # Layout
    fig.update_layout(
        title=titulo,
        xaxis_title="Índice",
        yaxis_title="Valor",
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig


def mostrar_sistema_comentarios(tipo_registro, id_registro):
    """
    Sistema de comentários para registros
    
    Args:
        tipo_registro: Tipo do registro (ex: 'match_id', 'par_id')
        id_registro: ID específico do registro
    """
    st.subheader("💬 Comentários e Observações")
    
    # Carrega comentários existentes
    todos_comentarios = carregar_comentarios()
    
    # Filtra comentários deste registro
    comentarios_registro = [
        c for c in todos_comentarios
        if c.get('tipo') == tipo_registro and c.get('id') == str(id_registro)
    ]
    
    # Formulário para novo comentário
    with st.form(f"form_comentario_{id_registro}"):
        st.write("✍️ Adicionar novo comentário")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            novo_comentario = st.text_area(
                "Comentário",
                placeholder="Digite sua observação aqui...",
                height=100,
                label_visibility="collapsed"
            )
        
        with col2:
            autor = st.text_input("Autor", placeholder="Seu nome")
            categoria = st.selectbox(
                "Categoria",
                ["Observação", "Problema", "Solução", "Dúvida"]
            )
        
        submit = st.form_submit_button("💾 Salvar Comentário", use_container_width=True)
        
        if submit:
            if novo_comentario.strip():
                # Cria novo comentário
                comentario_obj = {
                    "tipo": tipo_registro,
                    "id": str(id_registro),
                    "texto": novo_comentario,
                    "autor": autor if autor else "Anônimo",
                    "categoria": categoria,
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": datetime.now().timestamp()
                }
                
                todos_comentarios.append(comentario_obj)
                
                if salvar_comentarios(todos_comentarios):
                    st.success(MENSAGENS["sucesso_comentario"])
                    st.rerun()
                else:
                    st.error(MENSAGENS["erro_comentario"])
            else:
                st.warning("Por favor, digite um comentário")
    
    st.divider()
    
    # Exibe comentários existentes
    if comentarios_registro:
        st.write(f"📝 {len(comentarios_registro)} comentário(s)")
        
        for coment in sorted(comentarios_registro, key=lambda x: x.get('timestamp', 0), reverse=True):
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Badge de categoria
                    cat_cores = {
                        "Observação": "info",
                        "Problema": "erro",
                        "Solução": "sucesso",
                        "Dúvida": "aviso"
                    }
                    st.markdown(
                        criar_badge_status(
                            cat_cores.get(coment.get('categoria', 'info'), 'info'),
                            coment.get('categoria', 'Observação')
                        ),
                        unsafe_allow_html=True
                    )
                    
                    st.write(coment.get('texto', ''))
                    st.caption(f"👤 {coment.get('autor', 'Anônimo')} - 📅 {coment.get('data', 'N/A')}")
                
                st.divider()
    else:
        st.info("Nenhum comentário ainda. Seja o primeiro a comentar!")


def mostrar_loading(mensagem="Carregando..."):
    """
    Mostra indicador de loading
    
    Args:
        mensagem: Mensagem a exibir
    """
    return st.spinner(mensagem)

