"""
Configuração centralizada do sistema de análise de pares
"""

import os

# Diretórios base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados")
PRINTS_DIR = os.path.join(BASE_DIR, "prints")
HTMLS_DIR = os.path.join(BASE_DIR, "htmls")
COMENTARIOS_FILE = os.path.join(BASE_DIR, "comentarios.json")

# Paleta de cores
CORES = {
    "sucesso": "#28a745",
    "erro": "#dc3545",
    "aviso": "#ffc107",
    "info": "#17a2b8",
    "primaria": "#007bff",
    "secundaria": "#6c757d",
    "destaque": "#ff6b6b",
    "fundo_claro": "#f8f9fa",
    "fundo_escuro": "#343a40"
}

# Configuração dos dashboards
DASHBOARDS = {
    "gps": {
        "nome": "Análise GPS",
        "icone": "🗺️",
        "csv": os.path.join(DADOS_DIR, "matches_gps.csv"),
        "colunas_principais": ["match_id", "datetime", "discrepancia", "observacao"],
        "colunas_exibir": ["match_id", "par_id", "datetime", "discrepancia", "problema"],
        "coluna_id": "match_id",
        "pasta_prints": os.path.join(PRINTS_DIR, "gps"),
        "html_template": "gps_{par_id}.html",
        "tem_mapa": True,
        "cor_problema": CORES["erro"],
        "descricao": "Análise de dispersão GPS e precisão de localização",
        "metricas": ["discrepancia", "velocidade", "direcao"],
        "filtros": ["par_id", "problema", "datetime"]
    },
    "velocidade": {
        "nome": "Análise Velocidade",
        "icone": "🚗",
        "csv": os.path.join(DADOS_DIR, "matches_velocidade.csv"),
        "colunas_principais": ["match_id", "datetime", "teste", "referencia", "diferenca"],
        "colunas_exibir": ["match_id", "par_id", "datetime", "teste", "referencia", "diferenca", "problema"],
        "coluna_id": "match_id",
        "pasta_prints": os.path.join(PRINTS_DIR, "velocidade"),
        "html_template": "velocidade_{par_id}.html",
        "tem_mapa": False,
        "cor_problema": CORES["aviso"],
        "descricao": "Análise comparativa de velocidades entre TM10 e TM-07/TM-08",
        "metricas": ["diferenca", "teste", "referencia"],
        "filtros": ["par_id", "problema", "datetime"]
    },
    "direcao": {
        "nome": "Análise Direção",
        "icone": "🧭",
        "csv": os.path.join(DADOS_DIR, "matches_direcao.csv"),
        "colunas_principais": ["match_id", "datetime", "teste", "referencia", "diferenca"],
        "colunas_exibir": ["match_id", "par_id", "datetime", "teste", "referencia", "diferenca", "problema"],
        "coluna_id": "match_id",
        "pasta_prints": os.path.join(PRINTS_DIR, "direcao"),
        "html_template": "direcao_{par_id}.html",
        "tem_mapa": False,
        "cor_problema": CORES["info"],
        "descricao": "Análise de direção e orientação do veículo",
        "metricas": ["diferenca", "teste", "referencia"],
        "filtros": ["par_id", "problema", "datetime"]
    }
}

# Configuração da análise de pares
ANALISE_PARES_CONFIG = {
    "csv": os.path.join(DADOS_DIR, "analises_pares.csv"),
    "colunas_principais": ["par_id", "placa", "imei_tm10", "imei_ref", "tipo_ref"],
    "colunas_metricas": ["qt_viagens", "distancia_km", "problema_gps", "problema_vel", "problema_dir"],
    "coluna_id": "par_id"
}

# Configurações de visualização
VISUALIZACAO = {
    "itens_por_pagina": 20,
    "largura_mapa": 800,
    "altura_mapa": 600,
    "zoom_padrao_mapa": 15,
    "colunas_galeria": 2,
    "tamanho_imagem": 400,
    "formato_data": "%Y-%m-%d %H:%M:%S",
    "formato_data_curto": "%Y-%m-%d"
}

# Limites e thresholds
THRESHOLDS = {
    "gps_discrepancia_max": 50,  # metros
    "velocidade_diferenca_max": 20,  # km/h
    "direcao_diferenca_max": 90,  # graus
    "arquivo_max_size": 10 * 1024 * 1024,  # 10MB
}

# Tipos de arquivo permitidos
TIPOS_ARQUIVO_PERMITIDOS = {
    "imagens": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"],
    "documentos": [".pdf", ".doc", ".docx", ".txt"],
    "dados": [".csv", ".xlsx", ".json"]
}

# Configuração de uploads
UPLOAD_CONFIG = {
    "categorias": ["gps", "velocidade", "direcao", "hodometro", "eventos", "satelites", "conexao", "outros"],
    "max_files_por_upload": 20,
    "pasta_base": PRINTS_DIR
}

# Mensagens do sistema
MENSAGENS = {
    "sem_dados": "⚠️ Nenhum dado encontrado",
    "carregando": "🔄 Carregando dados...",
    "sucesso_upload": "✅ Upload realizado com sucesso!",
    "erro_upload": "❌ Erro ao realizar upload",
    "sucesso_comentario": "✅ Comentário salvo com sucesso!",
    "erro_comentario": "❌ Erro ao salvar comentário",
    "confirmacao_delete": "⚠️ Tem certeza que deseja deletar?",
    "sem_prints": "📷 Nenhuma imagem encontrada",
    "sem_html": "📄 HTML não encontrado"
}

# Configuração de cache
CACHE_CONFIG = {
    "ttl": 3600,  # 1 hora
    "max_entries": 1000
}

