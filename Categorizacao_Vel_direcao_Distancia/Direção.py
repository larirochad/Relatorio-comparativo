import pandas as pd

def direcao(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    Calcula a diferença angular entre os valores de direção (Azimuth ou Heading)
    de dois DataFrames com base no Match_Type e Match_ID.
    Retorna os dois DataFrames com a coluna 'Diferença Angular' adicionada.
    """

    df1 = df1.copy()
    df2 = df2.copy()

    # Identifica a coluna de direção
    dir_col1 = next((col for col in ['Azimuth', 'Heading'] if col in df1.columns), None)
    dir_col2 = next((col for col in ['Azimuth', 'Heading'] if col in df2.columns), None)

    if dir_col1 is None or dir_col2 is None:
        raise ValueError("Coluna de direção (Azimuth ou Heading) não encontrada.")

    # Cria chave de correspondência
    df1['chave'] = df1['Match_Type'].astype(str) + '_' + df1['Match_ID'].astype(str)
    df2['chave'] = df2['Match_Type'].astype(str) + '_' + df2['Match_ID'].astype(str)

    # Conjunto de chaves em comum
    common_chaves = set(df1['chave']).intersection(set(df2['chave']))

    # Inicializa coluna
    df1['Diferença Angular'] = None
    df2['Diferença Angular'] = None

    for chave in common_chaves:
        if chave == '0_0':
            continue
        try:
            ponto1 = df1[df1['chave'] == chave].iloc[0]
            ponto2 = df2[df2['chave'] == chave].iloc[0]

            ang1 = float(ponto1[dir_col1])
            ang2 = float(ponto2[dir_col2])
            
            if ang1 > ang2:
                diff_ang = (ang1 - ang2) % 360
            elif ang1 < ang2:
                diff_ang = (ang2 - ang1) % 360
            else:
                diff_ang = 0

            diff_ang = float(diff_ang)

            if diff_ang > 180:
                diff_ang = 360 - diff_ang

            df1.loc[df1['chave'] == chave, 'Diferença Angular'] = diff_ang
            df2.loc[df2['chave'] == chave, 'Diferença Angular'] = diff_ang

        except Exception as e:
            print(f"Erro ao processar chave {chave}: {e}")
            continue

    # Remove chave temporária
    df1 = df1.drop(columns=['chave'])
    df2 = df2.drop(columns=['chave'])

    return df1, df2
