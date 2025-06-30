import pandas as pd
from haversine import haversine

def calcular_distancia(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    Calcula a distância real entre pares de coordenadas GNSS com base na chave Match_Type + Match_ID
    e calcula a discrepância em relação à distância esperada (pela velocidade e tempo).
    Retorna os dois DataFrames com as colunas 'Distância' e 'Discrepancia' adicionadas.
    """

    df1 = df1.copy()
    df2 = df2.copy()

    # Criar chave de match
    df1['chave'] = df1['Match_Type'].astype(str) + '_' + df1['Match_ID'].astype(str)
    df2['chave'] = df2['Match_Type'].astype(str) + '_' + df2['Match_ID'].astype(str)

    # Garantir que as datas estejam em formato datetime
    df1['GNSS UTC Time'] = pd.to_datetime(df1['GNSS UTC Time'])
    df2['GNSS UTC Time'] = pd.to_datetime(df2['GNSS UTC Time'])

    # Inicializa colunas
    df1['Distância'] = None
    df2['Distância'] = None
    df1['Discrepancia'] = None
    df2['Discrepancia'] = None

    common_chaves = set(df1['chave']).intersection(set(df2['chave']))

    for chave in common_chaves:
        try:
            ponto1 = df1[df1['chave'] == chave].iloc[0]
            ponto2 = df2[df2['chave'] == chave].iloc[0]

            lat1, lon1 = float(ponto1['Latitude']), float(ponto1['Longitude'])
            lat2, lon2 = float(ponto2['Latitude']), float(ponto2['Longitude'])

            distancia_real = round(haversine((lat1, lon1), (lat2, lon2)) * 1000, 2)

            vel1 = float(ponto1['Velocidade'])
            vel2 = float(ponto2['Velocidade'])
            vel_med = ((vel1 + vel2) / 2) / 3.6  # m/s

            delta_t = abs((ponto1['GNSS UTC Time'] - ponto2['GNSS UTC Time']).total_seconds())

            distancia_esperada = round(vel_med * delta_t, 2)

            discrepancia_calc = round(abs(distancia_real - distancia_esperada), 2)
            valor_final = str(discrepancia_calc) if discrepancia_calc < distancia_real else f"{distancia_real}*"

            df1.loc[df1['chave'] == chave, 'Distância'] = distancia_real
            df2.loc[df2['chave'] == chave, 'Distância'] = distancia_real
            df1.loc[df1['chave'] == chave, 'Discrepancia'] = valor_final
            df2.loc[df2['chave'] == chave, 'Discrepancia'] = valor_final
            df1.loc[df1['chave'] == chave, 'Distancia esperada'] = distancia_esperada
            df2.loc[df2['chave'] == chave, 'Distancia esperada'] = distancia_esperada



        except Exception as e:
            print(f"Erro ao processar chave {chave}: {e}")
            continue

    df1 = df1.drop(columns=['chave'])
    df2 = df2.drop(columns=['chave'])

    return df1, df2


# if __name__ == "__main__":
#     calcular_distancia(
#         input1='logs/test_1nv_match1.csv',
#         input2='logs/test_2NV_match2.csv'
#     )
