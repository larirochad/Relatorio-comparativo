import pandas as pd
from datetime import timedelta

def analise_estabilidade_satelite(df_teste, df_ref):
    def processar_dispositivo(df):
        # Verifica e padroniza os nomes das colunas
        tipo_col = None
        for col in df.columns:
            if 'Tipo Mensagem' in col:
                tipo_col = col
                break
        
        # Procura por colunas que contenham "Event Code"
        event_code_col = None
        for col in df.columns:
            if 'Event Code' in col:
                event_code_col = col
                break
        
        if tipo_col is None and event_code_col is None:
            print(f"Colunas disponíveis: {list(df.columns)}")
            raise ValueError("Coluna 'Tipo Mensagem' ou 'Event Code' não encontrada no DataFrame")
        
        # Procura por colunas que contenham "Satélites" ou "Satélite"
        satelite_col = None
        for col in df.columns:
            if 'Satélites' in col or 'Satélite' in col:
                satelite_col = col
                break
        
        if satelite_col is None:
            print(f"Colunas disponíveis: {list(df.columns)}")
            raise ValueError("Coluna 'Satélites' não encontrada no DataFrame")
        
        # Mapeamento de códigos para tipos de mensagem
        codigo_para_tipo = {
            '20': 'GTIGF',
            '21': 'GTIGN',
            '30': 'GTERI',
            '27': 'GTERI'
        }
        
        def get_tipo(row):
            tipo = str(row.get(tipo_col, '') if tipo_col else '').strip().upper()
            codigo = str(row.get(event_code_col, '') if event_code_col else '').strip()
            if tipo:
                if 'MODO ECONÔMICO' in tipo:
                    return 'MODOECO'
                return tipo
            elif codigo:
                return codigo_para_tipo.get(codigo, '')
            return ''
        
        df = df.copy()
        df['TipoFiltrado'] = df.apply(get_tipo, axis=1)
        df = df[df['TipoFiltrado'].isin(['MODOECO', 'GTERI', 'GTIGN', 'GTIGF'])].copy()
        
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