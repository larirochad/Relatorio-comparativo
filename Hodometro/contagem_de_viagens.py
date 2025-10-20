import pandas as pd
import numpy as np

def viagens(df_teste, df_ref, salvar_detalhes=True):
    def get_evento(row):
        tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
        codigo = str(row.get('Event Code', '')).strip().upper()
        if tipo:
            if tipo in ['GTIGN', 'GTIGF']:
                return tipo
            if 'MODO ECONÔMICO' in tipo:
                return 'MODOECO'
        if codigo:
            if codigo in ['GTIGN', 'GTIGF']:
                return codigo
            mapa = {'20': 'GTIGF', '21': 'GTIGN'}
            return mapa.get(codigo, '')
        return ''

    def extrair_viagens(df, nome_dispositivo):
        df = df.copy()
        df.columns = [col.strip() for col in df.columns]
        
        # print(f'\n🔍 ORGANIZANDO DADOS - {nome_dispositivo}')
        # print(f"{'='*60}")
        
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
        
        # print(f'📊 Registros originais: {len(df)}')
        
        # # PASSO 1: Organizar por Data/Hora Evento
        # print(f'\n🕒 PASSO 1: Organizando dados por Data/Hora Evento...')
        
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
        
        df['Data/Hora Evento'] = dt1
        df = df.dropna(subset=['Data/Hora Evento'])
        df = df.sort_values('Data/Hora Evento')
        # print(f'✓ Dados organizados cronologicamente: {len(df)} registros')
        # print(f'   Período: {df["Data/Hora Evento"].min()} até {df["Data/Hora Evento"].max()}')

        # Remove duplicatas
        col_sequencia = None
        for col in df.columns:
            if 'sequência' in col.lower() or 'sequencia' in col.lower() or 'sequence' in col.lower():
                col_sequencia = col
                break
        
        if col_sequencia is not None:
            antes = len(df)
            df = df.drop_duplicates(subset=[col_sequencia], keep='first')
            #print(f'✓ Duplicatas removidas: {antes - len(df)}')
        
        df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')

        # PASSO 2: Identificar eventos de ignição
       #print(f'\n🔍 PASSO 2: Identificando eventos de ignição (GTIGN/21 e GTIGF/20)...')
        
        ignicoes = df[df.apply(lambda row: get_evento_row(row) == 'GTIGN', axis=1)].reset_index(drop=True)
        desligamentos = df[df.apply(lambda row: get_evento_row(row) == 'GTIGF', axis=1)].reset_index(drop=True)
        
        #print(f'✓ GTIGN (ignição ligada): {len(ignicoes)} eventos')
        #print(f'✓ GTIGF (ignição desligada): {len(desligamentos)} eventos')
        
        if len(ignicoes) == 0 or len(desligamentos) == 0:
            #print(f'⚠️ Não há pares IGN/IGF suficientes para análise')
            return pd.DataFrame(columns=['Dispositivo', 'Dia', 'Hora_Ignicao', 'Hora_Desligamento', 
                                       'Data_Hora_IGN', 'Data_Hora_IGF', 'Hodometro_IGN', 
                                       'Hodometro_IGF', 'Distancia_km'])

        # PASSO 3: Calcular distâncias IGF - IGN
        #print(f'\n📏 PASSO 3: Calculando distâncias (IGF - IGN)...')
        
        viagens = []
        inconsistencias = []

        for i, ign in ignicoes.iterrows():
            ign_time = ign['Data/Hora Evento']
            ign_odometro = pd.to_numeric(ign.get('Hodômetro Total', 0), errors='coerce')
            dia_formatado = ign_time.strftime('%d/%m/%Y')

            # Próxima ignição
            next_ign_time = ignicoes.iloc[i + 1]['Data/Hora Evento'] if i + 1 < len(ignicoes) else pd.Timestamp.max

            # IGFs entre esta ignição e a próxima
            igfs_possiveis = desligamentos[
                (desligamentos['Data/Hora Evento'] > ign_time) &
                (desligamentos['Data/Hora Evento'] < next_ign_time)
            ]

            if not igfs_possiveis.empty:
                igf = igfs_possiveis.iloc[0]
                igf_time = igf['Data/Hora Evento']
                igf_odometro = pd.to_numeric(igf.get('Hodômetro Total', 0), errors='coerce')

                if pd.notna(ign_odometro) and pd.notna(igf_odometro):
                    # CÁLCULO SIMPLES: IGF - IGN
                    km = igf_odometro - ign_odometro
                    
                    # Registra inconsistências (valores negativos ou muito estranhos)
                    if km < 0:
                        inconsistencias.append({
                            'viagem_num': len(viagens) + 1,
                            'data_hora': ign_time,
                            'hodometro_ign': ign_odometro,
                            'hodometro_igf': igf_odometro,
                            'distancia': km,
                            'tipo': 'negativa'
                        })
                    
                    viagens.append({
                        'Dispositivo': nome_dispositivo,
                        'Dia': dia_formatado,
                        'Hora_Ignicao': ign_time.strftime('%H:%M:%S'),
                        'Hora_Desligamento': igf_time.strftime('%H:%M:%S'),
                        'Data_Hora_IGN': ign_time,
                        'Data_Hora_IGF': igf_time,
                        'Hodometro_IGN': ign_odometro,
                        'Hodometro_IGF': igf_odometro,
                        'Distancia_km': km
                    })
        
        #print(f'✓ Total de viagens processadas: {len(viagens)}')
        
        # Reporta inconsistências encontradas
        if inconsistencias:
            #print(f'\n⚠️  INCONSISTÊNCIAS ENCONTRADAS: {len(inconsistencias)}')
            #print(f"{'─'*60}")
            for inc in inconsistencias:
                print(f"   Viagem #{inc['viagem_num']} em {inc['data_hora']}")
                print(f"   Hodômetro: {inc['hodometro_ign']:.1f} → {inc['hodometro_igf']:.1f} km")
                print(f"   Distância: {inc['distancia']:.4f} km (NEGATIVA!)")
                print()

        df_out = pd.DataFrame(viagens, columns=['Dispositivo', 'Dia', 'Hora_Ignicao', 'Hora_Desligamento', 
                                                 'Data_Hora_IGN', 'Data_Hora_IGF', 'Hodometro_IGN', 
                                                 'Hodometro_IGF', 'Distancia_km'])
        
        # PASSO 4: Validação final
        if len(df_out) > 0:
            #print(f'\n📊 VALIDAÇÃO FINAL - {nome_dispositivo}')
            #print(f"{'='*60}")
            
            hod_inicial = df_out.iloc[0]['Hodometro_IGN']
            hod_final = df_out.iloc[-1]['Hodometro_IGF']
            distancia_real_hodometro = hod_final - hod_inicial
            
            # Soma TODAS as distâncias (incluindo negativas)
            soma_total = df_out['Distancia_km'].sum()
            
            # Soma apenas positivas
            soma_positivas = df_out[df_out['Distancia_km'] >= 0]['Distancia_km'].sum()
            
            # Soma apenas negativas
            soma_negativas = df_out[df_out['Distancia_km'] < 0]['Distancia_km'].sum()
            
            # print(f"📍 Hodômetro inicial (primeira IGN): {hod_inicial:.1f} km")
            # print(f"📍 Hodômetro final (última IGF): {hod_final:.1f} km")
            # print(f"📏 Distância real (hodômetro): {distancia_real_hodometro:.1f} km")
            # print()
            # print(f"➕ Soma distâncias positivas: {soma_positivas:.1f} km")
            # print(f"➖ Soma distâncias negativas: {soma_negativas:.1f} km")
            # print(f"🔢 Soma TOTAL (todas viagens): {soma_total:.1f} km")
            # print()
            
            diferenca = soma_total - distancia_real_hodometro
            
            # if abs(diferenca) < 0.1:
            #     print(f"✅ VALIDAÇÃO OK: Diferença desprezível ({diferenca:.2f} km)")
            # elif diferenca > 0:
            #     print(f"❌ ERRO: Soma das viagens ({soma_total:.1f} km) é MAIOR que hodômetro real ({distancia_real_hodometro:.1f} km)")
            #     print(f"   Diferença: +{diferenca:.1f} km")
            #     print(f"   ⚠️  Isso não deveria acontecer! Verifique os dados de origem.")
            # else:
            #     print(f"⚠️  Soma das viagens ({soma_total:.1f} km) é menor que hodômetro real ({distancia_real_hodometro:.1f} km)")
            #     print(f"   Diferença: {diferenca:.1f} km")
            #     print(f"   ℹ️  Isso pode ocorrer por incrementos entre viagens ou efeitos naturais.")
        
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
    
    if salvar_detalhes:
        todas_viagens = pd.concat([viagens_teste, viagens_ref], ignore_index=True)
        todas_viagens.to_csv('viagens_detalhes.csv', index=False, encoding='utf-8')
        #print(f"\n✅ Arquivo 'viagens_detalhes.csv' salvo com {len(todas_viagens)} viagens")
    
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
            # Filtra apenas valores positivos (exclui 'Ignorar')
            soma_teste = viagens_teste[
                (viagens_teste['Dia'] == dia) & 
                (viagens_teste['Categoria'] == categoria) &
                (viagens_teste['Distancia_km'] >= 0)
            ]['Distancia_km'].sum()

            soma_ref = viagens_ref[
                (viagens_ref['Dia'] == dia) & 
                (viagens_ref['Categoria'] == categoria) &
                (viagens_ref['Distancia_km'] >= 0)
            ]['Distancia_km'].sum()

            linha[f'{categoria} para teste'] = round(soma_teste, 2)
            linha[f'{categoria} para referência'] = round(soma_ref, 2)
        resultados.append(linha)

    resultado_df = pd.DataFrame(resultados)
    resultado_df['Dia'] = pd.to_datetime(resultado_df['Dia'], format='%d/%m/%Y')
    resultado_df = resultado_df.sort_values(by='Dia')
    resultado_df['Dia'] = resultado_df['Dia'].dt.strftime('%d/%m/%Y')

    #print(f"\n{'='*60}")
    #print(f"✅ Processamento finalizado")
    #print(f"   Total de dias processados: {len(resultado_df)}")
    #print(f"{'='*60}\n")
    
    return resultado_df

if __name__ == '__main__':
    df_teste = pd.read_csv('logs/ENG_042.csv', encoding='latin1')
    df_ref = pd.read_csv('logs/A474038.csv', encoding='latin1')
    viagens(df_teste, df_ref, salvar_detalhes=True)