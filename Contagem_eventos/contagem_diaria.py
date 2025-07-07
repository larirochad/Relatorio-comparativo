import pandas as pd

def analise_diaria(df1, df2):
    def get_evento(row):
        tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
        codigo = str(row.get('Event Code', '')).strip()

        if tipo:
            if 'MODO ECONÔMICO' in tipo:
                return 'MODOECO'
            return tipo
        elif codigo:
            mapa = {
                '20': 'GTIGF',
                '21': 'GTIGN',
                '30': 'GTERI',
                '27': 'GTERI'
            }
            return mapa.get(codigo, '')
        return ''
    
    def tipo_dispositivo(df):
        tipo_dispositivo = ''
        if 'Tipo Dispositivo' in df.columns and not df['Tipo Dispositivo'].empty:
            valor = df['Tipo Dispositivo'].iloc[0]
            if pd.notna(valor):
                try:
                    tipo_dispositivo = str(int(float(valor)))
                except ValueError:
                    tipo_dispositivo = str(valor).strip()
        return tipo_dispositivo


    def processar_dispositivo(df, nome_dispositivo):
        df = df.copy()
        df.columns = [col.strip() for col in df.columns]


        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df = df.dropna(subset=['Data/Hora Evento'])
        df = df.sort_values('Data/Hora Evento')
        df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')
        resultados = []
        dispositivo = tipo_dispositivo(df)
        # print(dispositivo)

        for dia, grupo in df.groupby('Dia'):
            grupo = grupo.sort_values('Sequência', ascending=True)
            grupo = grupo.drop_duplicates(subset='Sequência', keep='first')

            peri = 0
            eco = 0
            ign_on = 0
            ign_off = 0
            modo_eco_ativo = False
            periodicas = False

            for _, row in grupo.iterrows():
                evento = get_evento(row)
                motion = row.get('Motion Status', '')
                motion_str = str(motion) if pd.notna(motion) else ''
                motion_prefix = motion_str[0] if len(motion_str) > 0 else None
                codigo = str(row.get('Event Code', '')).strip()

                report_type_raw = row.get('Position Report Type', '')
                if pd.notna(report_type_raw) and str(report_type_raw).strip() != '':
                    try:
                        report_type = str(int(float(report_type_raw)))
                    except ValueError:
                        report_type = ''
                else:
                    report_type = ''

                if dispositivo in ['802003', '385349']:
                    if evento == 'GTIGN':
                        ign_on += 1
                        # modo_eco_ativo = False

                    elif evento == 'GTIGF':
                        ign_off += 1
                        # modo_eco_ativo = True

                    elif evento == 'GTERI':
                        if motion_prefix == '1':
                            eco += 1
                            continue
                        elif (motion_prefix == '2' and report_type == '10') or  codigo == '30':
                            peri += 1
                        elif pd.isna(motion) or motion_str == '':
                            peri += 1
                    elif evento == 'MODOECO':
                        eco += 1

                else:
                    if evento == 'GTIGN':
                        ign_on += 1
                        # modo_eco_ativo = False
                        # periodicas = True

                    elif evento == 'GTIGF':
                        ign_off += 1
                        # modo_eco_ativo = True
                        # periodicas = False

                    elif evento == 'GTERI':
                        if motion_prefix == '1':
                            eco += 1
                            continue
                        if motion_prefix == '1'  or codigo == '27':
                            eco += 1
                        else:
                            if motion_prefix == '2'  or codigo == '30':
                                peri += 1
                            elif pd.isna(motion) or motion_str == '':
                                peri += 1
                    elif evento == 'MODOECO':
                        eco += 1

            resultados.append({
                'Dias': dia,
                f'Periódicas do {nome_dispositivo}': peri,
                f'Modo econômico {nome_dispositivo}': eco,
                f'Ignição ligada {nome_dispositivo}': ign_on,
                f'Ignição desligada {nome_dispositivo}': ign_off
            })

        return pd.DataFrame(resultados)

    df_teste = processar_dispositivo(df1, "teste")
    df_referencia = processar_dispositivo(df2, "referencia")

    df_final = pd.merge(df_referencia, df_teste, on='Dias', how='outer').fillna(0)
    df_final['Dias'] = pd.to_datetime(df_final['Dias'], format='%d/%m/%Y')
    df_final = df_final.sort_values(by='Dias')
    df_final['Dias'] = df_final['Dias'].dt.strftime('%d/%m/%Y')

    colunas = [
        'Dias',
        'Periódicas do referencia', 'Periódicas do teste',
        'Modo econômico referencia', 'Modo econômico teste',
        'Ignição ligada referencia', 'Ignição ligada teste',
        'Ignição desligada referencia', 'Ignição desligada teste'
    ]
    # print(df_final)
    df_final = df_final.reindex(columns=colunas)
    # print(df_final.head())

    return df_final

# if __name__ == "__main__":
#     df1 = pd.read_csv('logs/analise_par09.csv')
#     df2 = pd.read_csv('logs/TM08-PAR09 - Copia.csv')
#     analise_diaria(df1, df2)    