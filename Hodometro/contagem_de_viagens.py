import pandas as pd

def viagens(df_teste, df_ref):
    def get_evento(row):
        tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
        codigo = str(row.get('Event Code', '')).strip().upper()
        if tipo:
            # Se já for GTIGN ou GTIGF, retorna direto
            if tipo in ['GTIGN', 'GTIGF']:
                return tipo
            # Se for modo econômico, retorna padronizado
            if 'MODO ECONÔMICO' in tipo:
                return 'MODOECO'
        if codigo:
            # Se já for GTIGN ou GTIGF, retorna direto
            if codigo in ['GTIGN', 'GTIGF']:
                return codigo
            # Se for numérico, faz o mapeamento
            mapa = {'20': 'GTIGF', '21': 'GTIGN'}
            return mapa.get(codigo, '')
        return ''

    def extrair_viagens(df, nome_dispositivo):
        df = df.copy()
        df.columns = [col.strip() for col in df.columns]
        # Tenta detectar colunas equivalentes a 'Tipo Mensagem' e 'Event Code'
        tipo_col = None
        event_code_col = None
        for col in df.columns:
            norm = col.lower().strip()
            if tipo_col is None and ('tipo mensagem' in norm or 'tipo_mensagem' in norm):
                tipo_col = col
            if event_code_col is None and ('event code' in norm or 'event_code' in norm or 'codigo de evento' in norm):
                event_code_col = col

        def get_evento_row(row):
            t = str(row.get(tipo_col, '') if tipo_col else row.get('Tipo Mensagem', '')).strip().upper()
            c_raw = row.get(event_code_col, '') if event_code_col else row.get('Event Code', '')
            c = str(c_raw).strip()
            # Normaliza códigos numéricos que possam vir como float (ex.: '21.0')
            try:
                if c != '' and all(ch.isdigit() or ch in '.-' for ch in c):
                    c = str(int(float(c)))
            except Exception:
                pass
            if t:
                if t in ['GTIGN', 'GTIGF']:
                    return t
                if 'MODO ECONÔMICO' in t:
                    return 'MODOECO'
            if c:
                if c in ['GTIGN', 'GTIGF']:
                    return c
                mapa = {'20': 'GTIGF', '21': 'GTIGN'}
                return mapa.get(c, '')
            return ''
        # print(f'começou a contagem de viagens do {nome_dispositivo}')
        # Parse robusto: tenta YYYY-MM-DD HH:MM[:SS]; se falhar, aceita YY-MM-DD e expande para 20YY
        serie_data = df['Data/Hora Evento'].astype(str).str.strip()
        dt1 = pd.to_datetime(serie_data, format='%Y-%m-%d %H:%M:%S', errors='coerce')
        faltantes = dt1.isna()
        if faltantes.any():
            dt2 = pd.to_datetime(serie_data, format='%Y-%m-%d %H:%M', errors='coerce')
            dt1 = dt1.fillna(dt2)
        faltantes = dt1.isna()
        if faltantes.any():
            # Tenta ano com 2 dígitos
            dt3 = pd.to_datetime(serie_data, format='%y-%m-%d %H:%M:%S', errors='coerce')
            dt1 = dt1.fillna(dt3)
        faltantes = dt1.isna()
        if faltantes.any():
            dt4 = pd.to_datetime(serie_data, format='%y-%m-%d %H:%M', errors='coerce')
            dt1 = dt1.fillna(dt4)
        df['Data/Hora Evento'] = dt1
        df = df.dropna(subset=['Data/Hora Evento'])
        df = df.sort_values('Data/Hora Evento')
        df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')

        ignicoes = df[df.apply(lambda row: get_evento_row(row) == 'GTIGN', axis=1)].reset_index(drop=True)
        desligamentos = df[df.apply(lambda row: get_evento_row(row) == 'GTIGF', axis=1)].reset_index(drop=True)
       # print(f"[viagens] {nome_dispositivo}: IGN={len(ignicoes)} IGF={len(desligamentos)} linhas_total={len(df)})")

        viagens = []

        for i, ign in ignicoes.iterrows():
            ign_time = ign['Data/Hora Evento']
            ign_odometro = pd.to_numeric(ign.get('Hodômetro Total', 0), errors='coerce')
            dia_formatado = ign_time.strftime('%d/%m/%Y')

            # Próxima ignição (se houver)
            next_ign_time = ignicoes.iloc[i + 1]['Data/Hora Evento'] if i + 1 < len(ignicoes) else pd.Timestamp.max

            # Filtra IGFs entre a ignição atual e a próxima ignição
            igfs_possiveis = desligamentos[
                (desligamentos['Data/Hora Evento'] > ign_time) &
                (desligamentos['Data/Hora Evento'] < next_ign_time)
            ]

            if not igfs_possiveis.empty:
                igf = igfs_possiveis.iloc[0]
                igf_time = igf['Data/Hora Evento']
                igf_odometro = pd.to_numeric(igf.get('Hodômetro Total', 0), errors='coerce')

                if pd.notna(ign_odometro) and pd.notna(igf_odometro):
                    km = igf_odometro - ign_odometro
                    #print(f'nome do dispositivo: {nome_dispositivo}')
                    # print(f"➡️ IGN: {ign_time} | Odom IGN: {ign_odometro} | Próximo IGF: {igf_time} | Odom IGF: {igf_odometro} = {km}")

                    viagens.append({
                        'Dia': dia_formatado,
                        'IGN': ign_time,
                        'IGF': igf_time,
                        'Distancia_km': km
                    })

        # Garante schema mesmo quando não houver viagens
        df_out = pd.DataFrame(viagens, columns=['Dia', 'IGN', 'IGF', 'Distancia_km'])
       # print(f"[viagens] {nome_dispositivo}: viagens_encontradas={len(df_out)}")
        return df_out


    def classificar(dist):
        if dist < 0:
            return 'Ignorar'
        elif dist <= 2:
            return 'Curta'
        elif dist <= 50:
            return 'Media'
        else:
            return 'Longa'

    viagens_teste = extrair_viagens(df_teste, 'Teste')
    viagens_ref = extrair_viagens(df_ref, 'Referencia')
    #print(f"[viagens] TESTE linhas={len(viagens_teste)} | REF linhas={len(viagens_ref)}")
    
    # Evita KeyError quando não houver viagens (ex.: ausência de pares IGN/IGF válidos)
    if 'Distancia_km' not in viagens_teste.columns:
        viagens_teste['Distancia_km'] = pd.Series(dtype='float')
    if 'Distancia_km' not in viagens_ref.columns:
        viagens_ref['Distancia_km'] = pd.Series(dtype='float')

    viagens_teste['Categoria'] = viagens_teste['Distancia_km'].apply(classificar)
    viagens_ref['Categoria'] = viagens_ref['Distancia_km'].apply(classificar)



    dias_todos = sorted(
        set(viagens_teste['Dia'].unique()).union(set(viagens_ref['Dia'].unique())),
        key=lambda x: pd.to_datetime(x, dayfirst=True)
    )

    resultados = []
    for dia in dias_todos:
        linha = {'Dia': dia}
        for categoria in ['Curta', 'Media', 'Longa']:
            soma_teste = viagens_teste[
                (viagens_teste['Dia'] == dia) & (viagens_teste['Categoria'] == categoria)
            ]['Distancia_km'].sum()

            soma_ref = viagens_ref[
                (viagens_ref['Dia'] == dia) & (viagens_ref['Categoria'] == categoria)
            ]['Distancia_km'].sum()

            linha[f'{categoria} para teste'] = round(soma_teste, 2)
            linha[f'{categoria} para referência'] = round(soma_ref, 2)
        resultados.append(linha)

    resultado_df = pd.DataFrame(resultados)
    resultado_df['Dia'] = pd.to_datetime(resultado_df['Dia'], format='%d/%m/%Y')
    resultado_df = resultado_df.sort_values(by='Dia')
    resultado_df['Dia'] = resultado_df['Dia'].dt.strftime('%d/%m/%Y')

    # print("\n✅ Viagens finalizadas. Total de dias processados:", len(resultado_df))
    return resultado_df

if __name__ == '__main__':
    df_teste = pd.read_csv('logs/867488061438387_decoded_par2.csv', encoding='latin1')
    df_ref = pd.read_csv('logs/Par2.csv', encoding='utf-8')
    viagens(df_teste, df_ref)   