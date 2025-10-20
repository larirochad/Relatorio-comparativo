import pandas as pd
from datetime import timedelta

# Função para identificar o tipo de dispositivo
def identificar_dispositivo(df):
    if 'Tipo Dispositivo' not in df.columns:
        return 'Desconhecido'
    tipo_dispositivo = df['Tipo Dispositivo'].dropna().astype(str).unique()
    if any('385349' in x for x in tipo_dispositivo):
        return 'TM08'
    elif any('802003' in x for x in tipo_dispositivo):
        return 'TM10'
    elif any('83' in x for x in tipo_dispositivo):
        return 'TM07'
    else:
        return 'Desconhecido'


def analise_estabilidade_satelite(df_teste, df_ref):
    def processar_dispositivo(df):
        debug_file = open('debug_processamento_detalhado.txt', 'w', encoding='utf-8')
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
            # print(f"Colunas disponíveis: {list(df.columns)}")
            raise ValueError("Coluna 'Tipo Mensagem' ou 'Event Code' não encontrada no DataFrame")
        
        # Procura robustamente a coluna de satélites (considera acentos/mojibake e alternativas como MS Satellite Number)
        satelite_col = None
        # Mapeia colunas para uma versão normalizada (sem acentos e minúsculas)
        colunas_norm = {col: (str(col)
                               .strip()
                               .encode('latin1', 'ignore')
                               .decode('latin1', 'ignore')
                               ) for col in df.columns}
        colunas_simpl = {orig: (val
                                 .encode('utf-8', 'ignore')
                                 .decode('utf-8', 'ignore')
                                 .lower()) for orig, val in colunas_norm.items()}

        candidatos = []
        palavras_chave = [
            'satelites', 'satélites', 'satellite number', 'satellite'
        ]
        for orig, simple in colunas_simpl.items():
            tem_chave = any(pc in simple for pc in palavras_chave)
            if tem_chave and 'status' not in simple:
                candidatos.append(orig)
        

        # Prioriza coluna sem prefixo "MS"; se não houver, usa a primeira disponível
        if candidatos:
            preferidos = [c for c in candidatos if 'ms ' not in c.lower()]
            satelite_col = preferidos[0] if preferidos else candidatos[0]

        if satelite_col is None:
            # print(f"Colunas disponíveis: {list(df.columns)}")
            raise ValueError("Coluna de satélites não encontrada (ex.: 'Satélites' ou 'MS Satellite Number')")
        
        
        # Mapeamento de códigos para tipos de mensagem
        codigo_para_tipo = {
            '20': 'GTIGF',
            '21': 'GTIGN',
            '30': 'GTERI',
            '27': 'GTERI'
        }
        
        def get_tipo(row):
            tipo = str(row.get(tipo_col, '') if tipo_col else '').strip().upper()
            codigo = row.get(event_code_col, '') if event_code_col else ''

            # Prioriza detecção explícita por texto
            if tipo:
                if 'MODO ECONÔMICO' in tipo:
                    return 'MODOECO'
                # Se já vier com as tags conhecidas, usa-as; caso contrário (ex.: '01','02' no TM07),
                # tenta mapear pelo Event Code abaixo
                if tipo in {'GTERI', 'GTIGN', 'GTIGF'}:
                    return tipo

            if not pd.isna(codigo):
                # Converte para string e remove .0 se for float
                codigo_str = str(codigo).replace('.0', '').strip()
                return codigo_para_tipo.get(codigo_str, '')
            return ''
        
        df = df.copy()
        # Exclui mensagens GTSTT e GTIGL do cálculo de satélites
        if tipo_col is not None:
            mascara_excluir = df[tipo_col].astype(str).str.upper().str.contains(r'\bGTSTT\b|\bGTIGL\b', na=False)
            df = df[~mascara_excluir]

        df['TipoFiltrado'] = df.apply(get_tipo, axis=1)
        df = df[df['TipoFiltrado'].isin(['MODOECO', 'GTERI', 'GTIGN', 'GTIGF'])].copy()
        
        if df.empty:
            return {}
        
        # Padroniza a data/hora aceitando YYYY-MM-DD HH:MM[:SS] e YY-MM-DD HH:MM[:SS]
        serie_data = df['Data/Hora Evento'].astype(str).str.strip()
        dt1 = pd.to_datetime(serie_data, format='%Y-%m-%d %H:%M:%S', errors='coerce')
        faltantes = dt1.isna()
        if faltantes.any():
            dt2 = pd.to_datetime(serie_data, format='%Y-%m-%d %H:%M', errors='coerce')
            dt1 = dt1.fillna(dt2)
        faltantes = dt1.isna()
        if faltantes.any():
            dt3 = pd.to_datetime(serie_data, format='%y-%m-%d %H:%M:%S', errors='coerce')
            dt1 = dt1.fillna(dt3)
        faltantes = dt1.isna()
        if faltantes.any():
            dt4 = pd.to_datetime(serie_data, format='%y-%m-%d %H:%M', errors='coerce')
            dt1 = dt1.fillna(dt4)
        df['Data'] = dt1.dt.date
        
        dispositivo = identificar_dispositivo(df)
        if dispositivo == 'TM10':

            # Para TM10, usar a coluna 'Precisão GNSS' para definir válido/inválido
            precisao_col = None
            for col in df.columns:
                if 'Precisão GNSS' in col:
                    precisao_col = col
                    break
            if precisao_col is None:
                # print(f"Colunas disponíveis: {list(df.columns)}")
                raise ValueError("Coluna 'Precisão GNSS' não encontrada para TM10")
            # Converte no DF base (evita SettingWithCopyWarning)
            df[precisao_col + '_num'] = pd.to_numeric(df[precisao_col].astype(str).str.strip(), errors='coerce')
            df[satelite_col + '_num'] = pd.to_numeric(df[satelite_col].astype(str).str.strip(), errors='coerce')

            # Filtra em cópias - usa a versão numérica para comparação
            df_validos = df[df[precisao_col + '_num'] > 0].copy()
            df_invalidos = df[df[precisao_col + '_num'] == 0].copy()

            # Conta mensagens por dia (contagem de eventos)
            resultado_validos = df_validos.groupby('Data').size().to_frame('validos')
            resultado_invalidos = df_invalidos.groupby('Data').size().to_frame('invalidos')
            # Soma diária dos valores de satélites para eventos válidos
            soma_sat_validos = df_validos.groupby('Data')[satelite_col + '_num'].sum().to_frame('soma_sat_validos')
            # Total diário (contar todas as mensagens)
            total_por_dia = df.groupby('Data').size().to_frame('total')
            resultado = (total_por_dia
                         .join(resultado_validos, how='outer')
                         .join(resultado_invalidos, how='outer')
                         .join(soma_sat_validos, how='outer')
                         .fillna(0))
            # Converte colunas de contagem para int, preservando soma como float (pode ser int naturalmente)
            for col_conv in ['total', 'validos', 'invalidos']:
                if col_conv in resultado.columns:
                    resultado[col_conv] = resultado[col_conv].astype(int)
            return resultado.to_dict('index')

        elif dispositivo == 'TM07':
            # Para TM07, usar a coluna 'Fix Status' para definir válido/inválido
            fix_status_col = None
            for col in df.columns:
                if 'Fix Status' in col:
                    fix_status_col = col
                    break

            if fix_status_col is None:
                # print(f"Colunas disponíveis: {list(df.columns)}")
                raise ValueError("Coluna 'Fix Status' não encontrada para TM07")
            # print(f"Coluna de Fix Status detectada: {fix_status_col}")
            # print(df[fix_status_col].head(50))

            df[satelite_col + '_num'] = pd.to_numeric(df[satelite_col].astype(str).str.strip(), errors='coerce')

            # Função para converter hex para binário e analisar o bit 4 (2D Fix)
            def analisar_fix_status(valor):
                if pd.isna(valor):
                    return False

                try:
                    # Garante que seja inteiro (mesmo que venha como float)
                    valor_int = int(float(valor))
                except Exception:
                    return False

                # Extrai o bit 3 (InvalidFix)
                bit3_invalid_fix = (valor_int >> 3) & 1

                # bit3 == 0 → fix válido
                return bit3_invalid_fix == 0



            # Aplica a análise do Fix Status
            df['fix_valido'] = df[fix_status_col].apply(analisar_fix_status)


            
            # Filtra em cópias baseado na validade do fix
            df_validos = df[df['fix_valido'] == True].copy()
            df_invalidos = df[df['fix_valido'] == False].copy()



            # Conta mensagens por dia (contagem de eventos)
            resultado_validos = df_validos.groupby('Data').size().to_frame('validos')
            resultado_invalidos = df_invalidos.groupby('Data').size().to_frame('invalidos')
            # Soma diária dos valores de satélites para eventos válidos
            soma_sat_validos = df_validos.groupby('Data')[satelite_col + '_num'].sum().to_frame('soma_sat_validos')
            # Total diário (contar todas as mensagens)
            total_por_dia = df.groupby('Data').size().to_frame('total')
            resultado = (total_por_dia
                         .join(resultado_validos, how='outer')
                         .join(resultado_invalidos, how='outer')
                         .join(soma_sat_validos, how='outer')
                         .fillna(0))
            for col_conv in ['total', 'validos', 'invalidos']:
                if col_conv in resultado.columns:
                    resultado[col_conv] = resultado[col_conv].astype(int)
            return resultado.to_dict('index')
      
        else:
            # Debug: verificar valores antes da conversão
            # print(f"Dispositivo: {dispositivo}")
            # print(f"Coluna satélites: {satelite_col}")
            # print(f"Valores únicos ANTES da conversão: {df[satelite_col].astype(str).unique()}")
            
            df[satelite_col + '_num'] = pd.to_numeric(df[satelite_col].astype(str).str.strip(), errors='coerce')
            
            # Debug: verificar valores após a conversão
            # print(f"Valores únicos APÓS conversão: {df[satelite_col + '_num'].unique()}")
            # print(f"Contagem de zeros: {(df[satelite_col + '_num'] == 0).sum()}")
            # print(f"Contagem de <= 0: {(df[satelite_col + '_num'] <= 0).sum()}")
            # print(f"Contagem de NaN: {pd.isna(df[satelite_col + '_num']).sum()}")
            # print(f"Contagem de inválidos (<=0 ou NaN): {((df[satelite_col + '_num'] <= 0) | pd.isna(df[satelite_col + '_num'])).sum()}")
            # print(f"Contagem de válidos (>0): {(df[satelite_col + '_num'] > 0).sum()}")
            
            # Debug: verificar alguns exemplos específicos
            zeros_mask = df[satelite_col + '_num'] == 0
            # if zeros_mask.any():
            #      print(f"Exemplos de linhas com zero: {df[zeros_mask][[satelite_col, satelite_col + '_num']].head()}")
            
            # Conta mensagens válidas (sat > 0) e inválidas (sat <= 0 ou NaN) - contando eventos
            df_validos = df[df[satelite_col + '_num'] > 0].copy()
            df_invalidos = df[( (df[satelite_col + '_num'] <= 0) | pd.isna(df[satelite_col + '_num']) )].copy()

            validos = df_validos.groupby('Data').size().to_frame('validos')
            invalidos = df_invalidos.groupby('Data').size().to_frame('invalidos')
            # Soma diária dos valores de satélites para eventos válidos
            soma_sat_validos = df_validos.groupby('Data')[satelite_col + '_num'].sum().to_frame('soma_sat_validos')
            # Total diário contando todas as mensagens
            total_por_dia = df.groupby('Data').size().to_frame('total')
            resultado = (total_por_dia
                         .join(validos, how='left')
                         .join(invalidos, how='left')
                         .join(soma_sat_validos, how='left')
                         .fillna(0))
            for col_conv in ['total', 'validos', 'invalidos']:
                if col_conv in resultado.columns:
                    resultado[col_conv] = resultado[col_conv].astype(int)
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
        # print("ref:", ref)
        # print("teste:",teste)
        registros.append({
            'Dia': data.strftime('%d/%m/%Y'),
            'Validos referencia': ref.get('validos', 0),
            'Validos teste': teste.get('validos', 0),
            'Inválidos referencia': ref.get('invalidos', 0),
            'Inválidos teste': teste.get('invalidos', 0),
            'Soma Satélites Válidos referencia': ref.get('soma_sat_validos', 0),
            'Soma Satélites Válidos teste': teste.get('soma_sat_validos', 0)
        })

    return pd.DataFrame(registros)

if __name__ == "__main__":
    df_teste = pd.read_csv('logs/ENG_048.csv', encoding='latin1')
    df_ref = pd.read_csv('logs/AYL2486.csv', encoding='latin1')
    resultado = analise_estabilidade_satelite(df_teste, df_ref)
    # print(resultado)