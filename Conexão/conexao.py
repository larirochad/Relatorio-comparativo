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
        # print(tipo_dispositivo)
        if any('385349' in x for x in tipo_dispositivo):
            return 'TM08'
        elif any('802003' in x for x in tipo_dispositivo):
            return 'TM10'
        elif any('83' in x for x in tipo_dispositivo):
            return 'TM07'
        else:
            return 'Desconhecido'

    def contar_conexoes(df, dispositivo):
        mapa = None
        if dispositivo == 'TM07':
            mapa = {'00': 'Sem conexão', '01': '2G', '10': '4G' }
        elif dispositivo == 'TM08':
            mapa = {'0': 'Sem conexão', '1': '2G', '2': '4G', '3': '4G'}
        elif dispositivo == 'TM10':
            mapa = {'0': 'Sem conexão', '1': '2G', '4': '4G' }
        else:
            return {'Sem conexão': 0, '2G': 0, '4G': 0}

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

    # Identifica o tipo de dispositivo de cada DataFrame separadamente
    dispositivo1 = identificar_dispositivo(df1)
    dispositivo2 = identificar_dispositivo(df2)

    contagem1 = contar_conexoes(df1, dispositivo1)  # Para Teste
    contagem2 = contar_conexoes(df2, dispositivo2)  # Para Referencia

    # Monta o DataFrame final no formato esperado pelo HTML, mantendo as contagens separadas
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
    # print(resultado)
    return resultado


# if __name__ == "__main__":
#     df1 = pd.read_csv('logs/analise_par09.csv')
#     df2 = pd.read_csv('logs/TM08-PAR09.csv')
#     conexao(df1, df2)