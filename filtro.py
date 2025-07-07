import numpy as np
import pandas as pd
import os
import sys

from Categorizacao_Vel_direcao_Distancia.distancia import *
from Categorizacao_Vel_direcao_Distancia.diff_vel import *
from Categorizacao_Vel_direcao_Distancia.Direção import *
from Categorizacao_Vel_direcao_Distancia.match import *
from Categorizacao_Vel_direcao_Distancia.nv_html import *
from Conexão.conexao import conexao
from Conexão.conexoes_html import gerar_bloco_grafico_conexao
from Contagem_eventos.contagem_diaria import analise_diaria
from Contagem_eventos.nv_html import gerar_bloco_grafico
from Hodometro.gerarhtml import gerar_bloco_viagens
from Hodometro.contagem_de_viagens import viagens
from Satelites.Satelites_in_use import analise_estabilidade_satelite
from Satelites.html import gerar_bloco_satellite_estabilidade
from Unir_HTML import unir_blocos


def filtro(tipo, df1, df2, output_dir=None):
    if output_dir is None:
        output_dir = os.getcwd()

    resultados = []
    dataframes = []

    operacoes = ['velocidade', 'direção', 'distância'] if tipo.lower() == 'todas' else [tipo.lower()]

    df1 = df1[df1['Match_Type'] != 'NA']
    df2 = df2[df2['Match_Type'] != 'NA']

    for operacao in operacoes:
        if operacao == 'velocidade':
            df1_op, df2_op = calcular_diferenca_velocidade(df1, df2)
            dataframes.append((df1_op[['Match_Type', 'Match_ID', 'Diferença de Velocidade']], 'Diferença de Velocidade'))

        elif operacao == 'direção':
            df1_op, df2_op = direcao(df1, df2)
            dataframes.append((df1_op[['Match_Type', 'Match_ID', 'Diferença Angular']], 'Diferença Angular'))

        elif operacao == 'distância':
            df1_op, df2_op = calcular_distancia(df1, df2)
            df_dist = df1_op[['Match_Type', 'Match_ID', 'Distância', 'Discrepancia', 'Distancia esperada']]
            dataframes.extend([
                (df_dist[['Match_Type', 'Match_ID', 'Distância']], 'Distância'),
                (df_dist[['Match_Type', 'Match_ID', 'Discrepancia']], 'Discrepancia'),
                (df_dist[['Match_Type', 'Match_ID', 'Distancia esperada']], 'Distancia esperada')
            ])

    if not dataframes:
        raise ValueError("Nenhum DataFrame válido após filtragem.")

    df_merged = dataframes[0][0]
    for df, nome in dataframes[1:]:
        df = df.drop_duplicates(subset=['Match_Type', 'Match_ID'])
        df_merged = pd.merge(df_merged, df, on=['Match_Type', 'Match_ID'], how='inner')
    
    df_merged = df_merged.copy()
    df_merged.loc[:, 'Match_Complete'] = df_merged['Match_Type'].astype(str) + "_" + df_merged['Match_ID'].astype(str)
    df_merged = df_merged[
        ~df_merged['Match_Type'].astype(str).str.lower().eq('nan') &
        (df_merged['Match_ID'].astype(str).str.strip() != '0')
    ]

    output_path = os.path.join(output_dir, 'outputGeral.csv')
    df_merged.to_csv(output_path, index=False, encoding='utf-8')

    return output_path, dataframes


def gerar_estatisticas_de_medias(df, dataframes):
    medias_por_tipo = {}

    for _, coluna_resultado in dataframes:
        resultado = {}
        for grupo in sorted(df['Match_Type'].unique()):
            # Primeiro filtra os dados por grupo
            dados_grupo = df[df['Match_Type'] == grupo][coluna_resultado]
            # Converte para numérico e remove valores NaN
            valores = pd.to_numeric(dados_grupo, errors='coerce')
            # Garante que valores seja uma Series do pandas
            if isinstance(valores, pd.Series):
                valores = valores.dropna()
                if len(valores) > 0:
                    resultado[grupo] = valores.mean()
        if resultado:
            medias_por_tipo[coluna_resultado] = resultado

    # Função interna para ajustar as chaves de T1 para D1, etc
    def ajustar_chaves_medias(medias):
        medias_ajustadas = {}
        for tipo, grupos in medias.items():
            novo_grupo = {}
            for g, valor in grupos.items():
                if g.startswith('T'):
                    novo_g = 'D' + g[1:]  # Exemplo: T1 → D1
                    novo_grupo[novo_g] = valor
            medias_ajustadas[tipo] = novo_grupo
        return medias_ajustadas  # <-- Isso estava faltando

    medias_por_tipo = ajustar_chaves_medias(medias_por_tipo)

    return medias_por_tipo



def executar_analise_completa(tipo, input1, input2):
    match1, match2, _ = analisar_match(input1=input1, input2=input2)

    df1 = pd.read_csv(match1)
    df2 = pd.read_csv(match2)

    # Filtro
    output_geral, dataframes = filtro(tipo=tipo, df1=df1, df2=df2)

    df_output = pd.read_csv(output_geral)
    medias_por_tipo = gerar_estatisticas_de_medias(df_output, dataframes)
    # print(medias_por_tipo)
    # Gera HTML dos gráficos de distancia/vel/direcao
    out_html(
        input1=match1,
        input2=match2,
        match_path=output_geral,
        tipo=tipo,
        template_path=None,
        medias=medias_por_tipo,
        save_blocks=True
    )

    df_raw1 = pd.read_csv(input1, low_memory=False)
    df_raw1 = df_raw1.loc[:, ~df_raw1.columns.str.contains('^Unnamed')]

    df_raw2 = pd.read_csv(input2, low_memory=False)
    df_raw2 = df_raw2.loc[:, ~df_raw2.columns.str.contains('^Unnamed')]


    df_conexao = conexao(df_raw1, df_raw2)
    gerar_bloco_grafico_conexao(df_conexao)

    df_eventos = analise_diaria(df_raw1, df_raw2)
    gerar_bloco_grafico(df_eventos)

    df_viagens = viagens(df_raw1, df_raw2)
    gerar_bloco_viagens(df_viagens)


    df_satelites = analise_estabilidade_satelite(df_raw1, df_raw2)
    gerar_bloco_satellite_estabilidade(df_satelites)

    unir_blocos(df_raw1, df_raw2)

    print("✅ Dashboard final gerado!")



if __name__ == "__main__":
    executar_analise_completa(
        tipo='todas',
        input1='logs/analise_par09.csv',
        input2='logs/TM08-PAR09 - Copia.csv'
    )
