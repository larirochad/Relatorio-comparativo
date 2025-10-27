"""
Página de Administração - Upload e Gerenciamento de Arquivos
"""

import streamlit as st
import pandas as pd
import os
import sys
from PIL import Image
import shutil
from datetime import datetime
import json
import requests

# Adiciona diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import UPLOAD_CONFIG, PRINTS_DIR, TIPOS_ARQUIVO_PERMITIDOS, THRESHOLDS, MENSAGENS
from componentes import carregar_csv, criar_badge_status


def pagina_admin():
    """
    Página principal de administração de uploads
    """
    st.title("🔧 Administração - Uploads e Arquivos")
    st.caption("Gerencie uploads de imagens, documentos e dados")
    
    st.divider()
    
    # Tabs principais
    tabs = st.tabs([
        "📤 Upload Individual",
        "📦 Upload em Massa",
        "🔗 Upload via URL",
        "🖼️ Galeria de Prints"
    ])
    
    with tabs[0]:
        tab_upload_individual()
    
    with tabs[1]:
        tab_upload_massa()
    
    with tabs[2]:
        tab_upload_url()
    
    with tabs[3]:
        tab_galeria()


def tab_upload_individual():
    """Tab de upload individual de arquivos"""
    st.subheader("📤 Upload Individual")
    st.caption("Faça upload de um arquivo por vez com controle total")
    
    # Formulário de upload
    with st.form("form_upload_individual", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleção de par
            par_id = st.text_input(
                "Par ID *",
                placeholder="Ex: 1, 2, 3...",
                help="ID do par ao qual o arquivo pertence"
            )
            
            # Categoria
            categoria = st.selectbox(
                "Categoria *",
                UPLOAD_CONFIG['categorias'],
                help="Tipo de análise/categoria do arquivo"
            )
            
            # Match ID (opcional)
            match_id = st.text_input(
                "Match ID (opcional)",
                placeholder="Ex: T1_37, V1_12...",
                help="ID específico do match, se aplicável"
            )
        
        with col2:
            # Nome customizado
            nome_arquivo = st.text_input(
                "Nome do Arquivo (opcional)",
                placeholder="Deixe vazio para manter original",
                help="Nome customizado para salvar o arquivo"
            )
            
            # Descrição
            descricao = st.text_area(
                "Descrição/Observação",
                placeholder="Digite observações sobre este arquivo...",
                height=100
            )
        
        # Upload do arquivo
        st.divider()
        arquivo = st.file_uploader(
            "Selecione o arquivo",
            type=['png', 'jpg', 'jpeg', 'gif', 'pdf', 'csv', 'xlsx'],
            help=f"Tamanho máximo: {THRESHOLDS['arquivo_max_size'] / 1024 / 1024:.0f}MB"
        )
        
        # Preview
        if arquivo:
            st.markdown("#### 👁️ Preview")
            
            extensao = os.path.splitext(arquivo.name)[1].lower()
            
            if extensao in TIPOS_ARQUIVO_PERMITIDOS['imagens']:
                try:
                    img = Image.open(arquivo)
                    st.image(img, caption=arquivo.name, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro ao carregar preview: {str(e)}")
            else:
                st.info(f"📄 Arquivo: {arquivo.name} ({arquivo.size / 1024:.1f} KB)")
            
            # Reset file pointer
            arquivo.seek(0)
        
        # Botão de submit
        submit = st.form_submit_button("💾 Salvar Arquivo", use_container_width=True)
        
        if submit:
            if not par_id:
                st.error("❌ Par ID é obrigatório!")
            elif not arquivo:
                st.error("❌ Selecione um arquivo!")
            elif arquivo.size > THRESHOLDS['arquivo_max_size']:
                st.error(f"❌ Arquivo muito grande! Máximo: {THRESHOLDS['arquivo_max_size'] / 1024 / 1024:.0f}MB")
            else:
                # Salva arquivo
                sucesso = salvar_arquivo_individual(
                    arquivo,
                    par_id,
                    categoria,
                    match_id,
                    nome_arquivo,
                    descricao
                )
                
                if sucesso:
                    st.success(MENSAGENS['sucesso_upload'])
                    st.balloons()
                else:
                    st.error(MENSAGENS['erro_upload'])


def salvar_arquivo_individual(arquivo, par_id, categoria, match_id, nome_custom, descricao):
    """
    Salva arquivo individual no sistema
    
    Args:
        arquivo: Arquivo do Streamlit
        par_id: ID do par
        categoria: Categoria do arquivo
        match_id: ID do match (opcional)
        nome_custom: Nome customizado (opcional)
        descricao: Descrição
        
    Returns:
        True se sucesso
    """
    try:
        # Define caminho
        pasta_destino = os.path.join(PRINTS_DIR, categoria, str(par_id))
        os.makedirs(pasta_destino, exist_ok=True)
        
        # Define nome do arquivo
        if nome_custom:
            extensao = os.path.splitext(arquivo.name)[1]
            nome_final = f"{nome_custom}{extensao}"
        elif match_id:
            extensao = os.path.splitext(arquivo.name)[1]
            nome_final = f"{match_id}_{arquivo.name}"
        else:
            nome_final = arquivo.name
        
        # Caminho completo
        caminho_completo = os.path.join(pasta_destino, nome_final)
        
        # Salva arquivo
        with open(caminho_completo, 'wb') as f:
            f.write(arquivo.read())
        
        # Salva metadados
        salvar_metadados_arquivo(
            caminho_completo,
            par_id,
            categoria,
            match_id,
            descricao
        )
        
        return True
        
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False


def salvar_metadados_arquivo(caminho_arquivo, par_id, categoria, match_id, descricao):
    """Salva metadados do arquivo em JSON"""
    try:
        metadados_file = os.path.join(PRINTS_DIR, 'metadados.json')
        
        # Carrega metadados existentes
        if os.path.exists(metadados_file):
            with open(metadados_file, 'r', encoding='utf-8') as f:
                metadados = json.load(f)
        else:
            metadados = {"arquivos": []}
        
        # Adiciona novo arquivo
        metadados["arquivos"].append({
            "caminho": caminho_arquivo,
            "par_id": par_id,
            "categoria": categoria,
            "match_id": match_id,
            "descricao": descricao,
            "data_upload": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": datetime.now().timestamp()
        })
        
        # Salva
        with open(metadados_file, 'w', encoding='utf-8') as f:
            json.dump(metadados, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        st.warning(f"Erro ao salvar metadados: {str(e)}")


def tab_upload_massa():
    """Tab de upload em massa"""
    st.subheader("📦 Upload em Massa")
    st.caption("Faça upload de múltiplos arquivos ao mesmo tempo")
    
    # Seleção de arquivos
    arquivos = st.file_uploader(
        "Selecione múltiplos arquivos",
        type=['png', 'jpg', 'jpeg', 'gif', 'pdf'],
        accept_multiple_files=True,
        help=f"Máximo {UPLOAD_CONFIG['max_files_por_upload']} arquivos por vez"
    )
    
    if arquivos:
        if len(arquivos) > UPLOAD_CONFIG['max_files_por_upload']:
            st.error(f"❌ Máximo de {UPLOAD_CONFIG['max_files_por_upload']} arquivos por upload!")
            return
        
        st.success(f"✅ {len(arquivos)} arquivos selecionados")
        
        st.divider()
        
        # Configurações globais
        st.markdown("#### ⚙️ Configurações Globais")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            par_global = st.text_input("Par ID Global (opcional)", placeholder="Aplicar a todos")
        
        with col2:
            cat_global = st.selectbox("Categoria Global (opcional)", [''] + UPLOAD_CONFIG['categorias'])
        
        with col3:
            aplicar_global = st.checkbox("Aplicar a todos", value=False)
        
        st.divider()
        
        # Preview em grid
        st.markdown("#### 🖼️ Preview e Configuração Individual")
        
        # Armazena configurações
        if 'configs_massa' not in st.session_state:
            st.session_state['configs_massa'] = {}
        
        cols_por_linha = 3
        
        for i in range(0, len(arquivos), cols_por_linha):
            cols = st.columns(cols_por_linha)
            
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(arquivos):
                    arquivo = arquivos[idx]
                    
                    with col:
                        # Preview da imagem
                        extensao = os.path.splitext(arquivo.name)[1].lower()
                        
                        if extensao in TIPOS_ARQUIVO_PERMITIDOS['imagens']:
                            try:
                                img = Image.open(arquivo)
                                st.image(img, caption=arquivo.name, use_container_width=True)
                                arquivo.seek(0)
                            except:
                                st.error(f"Erro: {arquivo.name}")
                        else:
                            st.info(f"📄 {arquivo.name}")
                        
                        # Configurações individuais
                        with st.expander("⚙️ Configurar"):
                            par_id = st.text_input(
                                "Par ID",
                                value=par_global if aplicar_global else "",
                                key=f"par_{idx}",
                                placeholder="Par ID"
                            )
                            
                            categoria = st.selectbox(
                                "Categoria",
                                UPLOAD_CONFIG['categorias'],
                                index=UPLOAD_CONFIG['categorias'].index(cat_global) if cat_global else 0,
                                key=f"cat_{idx}"
                            )
                            
                            match_id = st.text_input(
                                "Match ID",
                                key=f"match_{idx}",
                                placeholder="Opcional"
                            )
                            
                            # Salva config
                            st.session_state['configs_massa'][arquivo.name] = {
                                'par_id': par_id,
                                'categoria': categoria,
                                'match_id': match_id
                            }
        
        st.divider()
        
        # Botão de salvar todos
        if st.button("💾 Salvar Todos os Arquivos", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            sucessos = 0
            erros = 0
            
            for idx, arquivo in enumerate(arquivos):
                config = st.session_state['configs_massa'].get(arquivo.name, {})
                
                if config.get('par_id'):
                    status_text.text(f"Salvando {arquivo.name}...")
                    
                    sucesso = salvar_arquivo_individual(
                        arquivo,
                        config['par_id'],
                        config['categoria'],
                        config.get('match_id', ''),
                        '',
                        ''
                    )
                    
                    if sucesso:
                        sucessos += 1
                    else:
                        erros += 1
                    
                    # Reset file pointer
                    arquivo.seek(0)
                else:
                    erros += 1
                
                progress_bar.progress((idx + 1) / len(arquivos))
            
            status_text.empty()
            progress_bar.empty()
            
            # Resultado
            col1, col2 = st.columns(2)
            col1.success(f"✅ {sucessos} arquivos salvos com sucesso")
            if erros > 0:
                col2.error(f"❌ {erros} erros (verifique Par ID)")
            
            if sucessos > 0:
                st.balloons()
            
            # Limpa configs
            st.session_state['configs_massa'] = {}


def tab_upload_url():
    """Tab de upload via URL"""
    st.subheader("🔗 Upload via URL")
    st.caption("Faça upload de arquivos diretamente de URLs (Google Drive, Dropbox, etc)")
    
    with st.form("form_upload_url"):
        # URL
        url = st.text_input(
            "URL do Arquivo *",
            placeholder="https://drive.google.com/... ou https://dropbox.com/...",
            help="Cole a URL do arquivo"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            par_id = st.text_input("Par ID *")
            categoria = st.selectbox("Categoria *", UPLOAD_CONFIG['categorias'])
        
        with col2:
            match_id = st.text_input("Match ID (opcional)")
            nome_arquivo = st.text_input("Nome do Arquivo")
        
        submit = st.form_submit_button("⬇️ Download e Salvar", use_container_width=True)
        
        if submit:
            if not url or not par_id:
                st.error("❌ URL e Par ID são obrigatórios!")
            else:
                with st.spinner("Baixando arquivo..."):
                    sucesso = baixar_e_salvar_url(url, par_id, categoria, match_id, nome_arquivo)
                    
                    if sucesso:
                        st.success(MENSAGENS['sucesso_upload'])
                        st.balloons()
                    else:
                        st.error("❌ Erro ao baixar/salvar arquivo da URL")


def baixar_e_salvar_url(url, par_id, categoria, match_id, nome_arquivo):
    """
    Baixa arquivo de URL e salva
    
    Args:
        url: URL do arquivo
        par_id: ID do par
        categoria: Categoria
        match_id: Match ID
        nome_arquivo: Nome desejado
        
    Returns:
        True se sucesso
    """
    try:
        # Tenta baixar
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Define nome
        if not nome_arquivo:
            nome_arquivo = url.split('/')[-1].split('?')[0]
            if not nome_arquivo:
                nome_arquivo = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Pasta destino
        pasta_destino = os.path.join(PRINTS_DIR, categoria, str(par_id))
        os.makedirs(pasta_destino, exist_ok=True)
        
        # Salva
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        
        with open(caminho_completo, 'wb') as f:
            f.write(response.content)
        
        # Metadados
        salvar_metadados_arquivo(
            caminho_completo,
            par_id,
            categoria,
            match_id,
            f"Baixado de: {url}"
        )
        
        return True
        
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False


def tab_galeria():
    """Tab de galeria de prints"""
    st.subheader("🖼️ Galeria de Prints")
    st.caption("Visualize e gerencie todos os arquivos carregados")
    
    # Filtros
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            par_filtro = st.text_input("Filtrar por Par ID", placeholder="Digite o Par ID")
        
        with col2:
            cat_filtro = st.selectbox("Filtrar por Categoria", ['Todas'] + UPLOAD_CONFIG['categorias'])
        
        with col3:
            busca = st.text_input("Buscar por nome", placeholder="Digite para buscar")
    
    st.divider()
    
    # Carrega metadados
    metadados_file = os.path.join(PRINTS_DIR, 'metadados.json')
    
    if os.path.exists(metadados_file):
        with open(metadados_file, 'r', encoding='utf-8') as f:
            metadados = json.load(f)
        
        arquivos = metadados.get('arquivos', [])
        
        # Aplica filtros
        if par_filtro:
            arquivos = [a for a in arquivos if str(a.get('par_id')) == par_filtro]
        
        if cat_filtro != 'Todas':
            arquivos = [a for a in arquivos if a.get('categoria') == cat_filtro]
        
        if busca:
            arquivos = [a for a in arquivos if busca.lower() in a.get('caminho', '').lower()]
        
        # Ordena por data
        arquivos = sorted(arquivos, key=lambda x: x.get('timestamp', 0), reverse=True)
        
        if arquivos:
            st.caption(f"🖼️ {len(arquivos)} arquivos encontrados")
            
            # Galeria
            cols_por_linha = 4
            
            for i in range(0, len(arquivos), cols_por_linha):
                cols = st.columns(cols_por_linha)
                
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(arquivos):
                        arquivo_info = arquivos[idx]
                        caminho = arquivo_info.get('caminho')
                        
                        with col:
                            # Tenta exibir imagem
                            if os.path.exists(caminho):
                                extensao = os.path.splitext(caminho)[1].lower()
                                
                                if extensao in TIPOS_ARQUIVO_PERMITIDOS['imagens']:
                                    try:
                                        img = Image.open(caminho)
                                        st.image(img, use_container_width=True)
                                    except:
                                        st.error("Erro ao carregar")
                                else:
                                    st.info(f"📄 {os.path.basename(caminho)}")
                                
                                # Informações
                                st.caption(f"**Par:** {arquivo_info.get('par_id')}")
                                st.caption(f"**Cat:** {arquivo_info.get('categoria')}")
                                
                                if arquivo_info.get('match_id'):
                                    st.caption(f"**Match:** {arquivo_info.get('match_id')}")
                                
                                # Botões
                                col_btn1, col_btn2 = st.columns(2)
                                
                                with col_btn1:
                                    with open(caminho, 'rb') as f:
                                        st.download_button(
                                            "⬇️",
                                            f.read(),
                                            file_name=os.path.basename(caminho),
                                            key=f"download_gal_{idx}"
                                        )
                                
                                with col_btn2:
                                    if st.button("🗑️", key=f"delete_gal_{idx}"):
                                        if deletar_arquivo(caminho, metadados_file, idx):
                                            st.success("Deletado!")
                                            st.rerun()
                            else:
                                st.warning("Arquivo não encontrado")
        else:
            st.info("Nenhum arquivo encontrado com os filtros aplicados")
    else:
        st.info("📁 Nenhum arquivo carregado ainda")


def deletar_arquivo(caminho, metadados_file, idx):
    """Deleta arquivo e remove dos metadados"""
    try:
        # Deleta arquivo físico
        if os.path.exists(caminho):
            os.remove(caminho)
        
        # Remove dos metadados
        with open(metadados_file, 'r', encoding='utf-8') as f:
            metadados = json.load(f)
        
        if idx < len(metadados['arquivos']):
            metadados['arquivos'].pop(idx)
        
        with open(metadados_file, 'w', encoding='utf-8') as f:
            json.dump(metadados, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        st.error(f"Erro ao deletar: {str(e)}")
        return False


if __name__ == "__main__":
    pagina_admin()

