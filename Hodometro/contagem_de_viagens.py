import pandas as pd

def viagens(df_teste, df_ref):
    def get_evento(row):
        tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
        codigo = str(row.get('Event Code', '')).strip()
        if tipo:
            return tipo
        elif codigo:
            mapa = {'20': 'GTIGF', '21': 'GTIGN'}
            return mapa.get(codigo, '')
        return ''

    def extrair_viagens(df, nome_dispositivo):
        df = df.copy()
        df.columns = [col.strip() for col in df.columns]
        # print(f'começou a contagem de viagens do {nome_dispositivo}')
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df = df.dropna(subset=['Data/Hora Evento'])
        df = df.sort_values('Data/Hora Evento')
        df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')

        ignicoes = df[df.apply(lambda row: get_evento(row) == 'GTIGN', axis=1)].reset_index(drop=True)
        desligamentos = df[df.apply(lambda row: get_evento(row) == 'GTIGF', axis=1)].reset_index(drop=True)

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
                    # print(f"➡️ IGN: {ign_time} | Odom IGN: {ign_odometro} | Próximo IGF: {igf_time} | Odom IGF: {igf_odometro} = {km}")

                    viagens.append({
                        'Dia': dia_formatado,
                        'IGN': ign_time,
                        'IGF': igf_time,
                        'Distancia_km': km
                    })

        return pd.DataFrame(viagens)


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
