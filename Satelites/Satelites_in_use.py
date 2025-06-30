import pandas as pd
from datetime import timedelta

def analise_estabilidade_satelite(df_teste, df_ref):
    def processar_dispositivo(df):
        # Verifica e padroniza os nomes das colunas
        tipo_col = 'Tipo Mensagem' if 'Tipo Mensagem' in df.columns else 'Event Code'
        satelite_col = 'Satélites' if 'Satélites' in df.columns else 'Satélite'
        
        df = df[df[tipo_col].isin(['Modo Econômico', 'GTERI', 'GTIGN', 'GTIGF'])].copy()
        
        if df.empty:
            return {}
        
        df['Data'] = pd.to_datetime(df['Data/Hora Evento']).dt.date
        
        df['Valido'] = df[satelite_col] > 0
        
        resultado = df.groupby('Data')['Valido'].value_counts().unstack(fill_value=0)
        resultado = resultado.rename(columns={True: 'validos', False: 'invalidos'})
        
        return resultado.to_dict('index')
    
    # Processa ambos dispositivos
    dados_teste = processar_dispositivo(df_teste)
    dados_referencia = processar_dispositivo(df_ref)
    
    # Cria lista de todas as datas presentes em ambos
    todas_datas = set(dados_teste.keys()).union(set(dados_referencia.keys()))
    datas_ordenadas = sorted(todas_datas)
    
    # Prepara o DataFrame final
    registros = []
    for data in datas_ordenadas:
        ref = dados_referencia.get(data, {'validos': 0, 'invalidos': 0})
        teste = dados_teste.get(data, {'validos': 0, 'invalidos': 0})
        
        registros.append({
            'Dia': data.strftime('%d/%m/%Y'),
            'Validos referencia': ref.get('validos', 0),
            'Validos teste': teste.get('validos', 0),
            'Inválidos referencia': ref.get('invalidos', 0),
            'Inválidos teste': teste.get('invalidos', 0)
        })

    return pd.DataFrame(registros)

# Exemplo de uso:
# df_teste = pd.read_csv('analise_par09.csv')
# df_ref = pd.read_csv('analise_referencia.csv')
# resultado = analise_estabilidade_satelite(df_teste, df_ref)
# print(resultado)