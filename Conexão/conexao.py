import pandas as pd
import unicodedata

def conexao(df1, df2):
    def limpar_colunas(df):
        df = df.copy()
        df.columns = df.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
        df.columns = df.columns.str.strip()
        return df

    def identificar_dispositivo(df):
        tipo_dispositivo = df['Tipo Dispositivo'].dropna().astype(str).unique()
        if any('346911' in x for x in tipo_dispositivo):
            return 'TM08'
        elif any('802003' in x for x in tipo_dispositivo):
            return 'TM10'
        else:
            return 'Desconhecido'

    def contar_conexoes(df, dispositivo):
        mapa_tm08 = {'0': 'Sem conexão', '1': '2G', '2': '4G', '3': '4G'}
        mapa_tm10 = {'0': 'Sem conexão', '1': '2G', '4': '4G'}
        mapa = mapa_tm08 if dispositivo == 'TM08' else mapa_tm10 if dispositivo == 'TM10' else None
        contagem = {'Sem conexão': 0, '2G': 0, '4G': 0}

        if mapa and 'RAT' in df.columns:
            df_filtrado = df[df['RAT'].notna() & (df['RAT'].astype(str).str.strip() != '')]
            for valor in df_filtrado['RAT']:
                try:
                    valor_int = int(float(valor))
                    tipo_rede = mapa.get(str(valor_int), None)
                    if tipo_rede:
                        contagem[tipo_rede] += 1
                except:
                    continue
        return contagem

    # Limpa os DataFrames
    df1 = limpar_colunas(df1)
    df2 = limpar_colunas(df2)

    dispositivo1 = identificar_dispositivo(df1)
    dispositivo2 = identificar_dispositivo(df2)

    contagem1 = contar_conexoes(df1, dispositivo1)
    contagem2 = contar_conexoes(df2, dispositivo2)

    resultado = pd.DataFrame({
        'Tipo de Rede': ['Sem conexão', '2G', '4G'],
        'Teste': [
            contagem1['Sem conexão'],
            contagem1['2G'],
            contagem1['4G']
        ],
        'Referencia': [
            contagem2['Sem conexão'],
            contagem2['2G'],
            contagem2['4G']
        ]
    })

    return resultado
