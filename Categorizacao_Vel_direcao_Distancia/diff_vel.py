import pandas as pd

def calcular_diferenca_velocidade(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    Calcula a diferença de velocidade entre dois DataFrames com base no Match_Type e Match_ID.
    Retorna os dois DataFrames com a coluna 'Diferença de Velocidade' adicionada.
    """

    # Cria chave de correspondência
    df1 = df1.copy()
    df2 = df2.copy()

    df1['chave'] = df1['Match_Type'].astype(str) + '_' + df1['Match_ID'].astype(str)
    df2['chave'] = df2['Match_Type'].astype(str) + '_' + df2['Match_ID'].astype(str)

    # Cria dicionário com as velocidades de referência
    ref_dict = df2.set_index('chave')['Velocidade'].to_dict()

    # Inicializa nova coluna
    df1['Diferença de Velocidade'] = None
    df2['Diferença de Velocidade'] = None

    # Calcula as diferenças
    for idx, row in df1.iterrows():
        chave = row['chave']
        vel_teste = row['Velocidade']

        if chave in ref_dict:
            vel_ref = ref_dict[chave]
            diferenca = vel_ref - vel_teste
            df1.at[idx, 'Diferença de Velocidade'] = round(diferenca, 2)

            # Atualiza no df2 também
            idx2 = df2.index[df2['chave'] == chave]
            df2.loc[idx2, 'Diferença de Velocidade'] = round(diferenca, 2)

    # Remove chave temporária
    df1 = df1.drop(columns=['chave'])
    df2 = df2.drop(columns=['chave'])

    return df1, df2


# if __name__ == "__main__":
#     calcular_diferenca_velocidade(
#         input1='logs/test_1nv_match1.csv',
#         input2='logs/test_2NV_match2.csv'
#     )
