"""
Funções de processamento e análise de dados
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calcular_estatisticas_basicas(df, coluna):
    """
    Calcula estatísticas básicas de uma coluna
    
    Args:
        df: DataFrame
        coluna: Nome da coluna
        
    Returns:
        Dicionário com estatísticas
    """
    if coluna not in df.columns:
        return {}
    
    serie = df[coluna].dropna()
    
    if len(serie) == 0:
        return {}
    
    return {
        'media': serie.mean(),
        'mediana': serie.median(),
        'minimo': serie.min(),
        'maximo': serie.max(),
        'desvio_padrao': serie.std(),
        'total': serie.sum() if pd.api.types.is_numeric_dtype(serie) else len(serie),
        'count': len(serie)
    }


def filtrar_por_data(df, coluna_data, data_inicio=None, data_fim=None):
    """
    Filtra DataFrame por intervalo de datas
    
    Args:
        df: DataFrame
        coluna_data: Nome da coluna de data
        data_inicio: Data inicial (datetime ou string)
        data_fim: Data final (datetime ou string)
        
    Returns:
        DataFrame filtrado
    """
    if coluna_data not in df.columns:
        return df
    
    df_copia = df.copy()
    
    # Converte coluna para datetime se necessário
    if not pd.api.types.is_datetime64_any_dtype(df_copia[coluna_data]):
        df_copia[coluna_data] = pd.to_datetime(df_copia[coluna_data], errors='coerce')
    
    # Aplica filtros
    if data_inicio:
        if isinstance(data_inicio, str):
            data_inicio = pd.to_datetime(data_inicio)
        df_copia = df_copia[df_copia[coluna_data] >= data_inicio]
    
    if data_fim:
        if isinstance(data_fim, str):
            data_fim = pd.to_datetime(data_fim)
        df_copia = df_copia[df_copia[coluna_data] <= data_fim]
    
    return df_copia


def identificar_problemas(df, tipo='gps'):
    """
    Identifica problemas nos dados baseado no tipo
    
    Args:
        df: DataFrame
        tipo: 'gps', 'velocidade' ou 'direcao'
        
    Returns:
        DataFrame com coluna 'problema' adicionada/atualizada
    """
    df_copia = df.copy()
    
    if tipo == 'gps':
        # Problema se discrepância > 50m
        if 'discrepancia' in df_copia.columns:
            df_copia['problema'] = df_copia['discrepancia'] > 50
    
    elif tipo == 'velocidade':
        # Problema se diferença > 20 km/h
        if 'diferenca' in df_copia.columns:
            df_copia['problema'] = df_copia['diferenca'].abs() > 20
    
    elif tipo == 'direcao':
        # Problema se diferença > 90 graus
        if 'diferenca' in df_copia.columns:
            df_copia['problema'] = df_copia['diferenca'].abs() > 90
    
    return df_copia


def agrupar_por_periodo(df, coluna_data, periodo='D'):
    """
    Agrupa dados por período
    
    Args:
        df: DataFrame
        coluna_data: Nome da coluna de data
        periodo: 'D' (dia), 'W' (semana), 'M' (mês)
        
    Returns:
        DataFrame agrupado
    """
    if coluna_data not in df.columns:
        return df
    
    df_copia = df.copy()
    
    # Converte para datetime
    if not pd.api.types.is_datetime64_any_dtype(df_copia[coluna_data]):
        df_copia[coluna_data] = pd.to_datetime(df_copia[coluna_data], errors='coerce')
    
    # Agrupa
    df_copia['periodo'] = df_copia[coluna_data].dt.to_period(periodo)
    
    return df_copia.groupby('periodo').size().reset_index(name='quantidade')


def calcular_metricas_par(dados_gps, dados_vel, dados_dir):
    """
    Calcula métricas consolidadas de um par
    
    Args:
        dados_gps: DataFrame de GPS
        dados_vel: DataFrame de velocidade
        dados_dir: DataFrame de direção
        
    Returns:
        Dicionário com métricas
    """
    metricas = {
        'total_registros': 0,
        'problemas_gps': 0,
        'problemas_velocidade': 0,
        'problemas_direcao': 0,
        'periodo_inicio': None,
        'periodo_fim': None
    }
    
    # GPS
    if dados_gps is not None and not dados_gps.empty:
        metricas['total_registros'] += len(dados_gps)
        if 'problema' in dados_gps.columns:
            metricas['problemas_gps'] = dados_gps['problema'].sum()
    
    # Velocidade
    if dados_vel is not None and not dados_vel.empty:
        metricas['total_registros'] += len(dados_vel)
        if 'problema' in dados_vel.columns:
            metricas['problemas_velocidade'] = dados_vel['problema'].sum()
    
    # Direção
    if dados_dir is not None and not dados_dir.empty:
        metricas['total_registros'] += len(dados_dir)
        if 'problema' in dados_dir.columns:
            metricas['problemas_direcao'] = dados_dir['problema'].sum()
    
    # Período
    todas_datas = []
    for df in [dados_gps, dados_vel, dados_dir]:
        if df is not None and not df.empty and 'datetime' in df.columns:
            todas_datas.extend(pd.to_datetime(df['datetime'], errors='coerce').dropna().tolist())
    
    if todas_datas:
        metricas['periodo_inicio'] = min(todas_datas)
        metricas['periodo_fim'] = max(todas_datas)
    
    return metricas


def exportar_relatorio_csv(df, caminho_saida, incluir_timestamp=True):
    """
    Exporta DataFrame para CSV com opções
    
    Args:
        df: DataFrame a exportar
        caminho_saida: Caminho do arquivo de saída
        incluir_timestamp: Se True, adiciona timestamp ao nome
        
    Returns:
        Caminho do arquivo gerado
    """
    if incluir_timestamp:
        base, ext = caminho_saida.rsplit('.', 1)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_saida = f"{base}_{timestamp}.{ext}"
    
    df.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
    
    return caminho_saida


def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula distância entre dois pontos GPS usando fórmula de Haversine
    
    Args:
        lat1, lon1: Coordenadas do ponto 1
        lat2, lon2: Coordenadas do ponto 2
        
    Returns:
        Distância em metros
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Raio da Terra em metros
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distancia = R * c
    
    return distancia


def validar_coordenadas(lat, lon):
    """
    Valida se coordenadas são válidas
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        True se válidas
    """
    try:
        lat = float(lat)
        lon = float(lon)
        
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return True
    except:
        pass
    
    return False


def processar_upload_arquivo(arquivo, tipo_arquivo):
    """
    Processa arquivo uploadado
    
    Args:
        arquivo: Arquivo do Streamlit uploader
        tipo_arquivo: Tipo esperado ('csv', 'imagem', etc)
        
    Returns:
        Dados processados ou None se erro
    """
    try:
        if tipo_arquivo == 'csv':
            return pd.read_csv(arquivo)
        elif tipo_arquivo == 'imagem':
            from PIL import Image
            return Image.open(arquivo)
        else:
            return arquivo.read()
    except Exception as e:
        return None

