import pandas as pd
from datetime import datetime
import os
from typing import Dict, Tuple

def match(path: str) -> pd.DataFrame:
    encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(
                path,
                encoding=encoding,
                on_bad_lines='warn',
                engine='python',
                dtype=str
            )
            df.columns = df.columns.str.strip()  # <- REMOVE espaços extras
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            if 'Data/Hora Evento' not in df.columns:
                continue

            if 'Event Code' in df.columns and 'Tipo Mensagem' not in df.columns:
                df['Tipo Mensagem'] = df['Event Code'].map({
                    '30': 'GTERI',
                    '27': 'GTERI'
                }).fillna('X')

            if 'Tipo Mensagem' not in df.columns:
                continue

            # Parser robusto: tenta YYYY-MM-DD HH:MM[:SS] e depois YY-MM-DD HH:MM[:SS]
            serie_evento = df['Data/Hora Evento'].astype(str).str.strip()
            dt_evento = pd.to_datetime(serie_evento, format='%Y-%m-%d %H:%M:%S', errors='coerce')
            falt = dt_evento.isna()
            if falt.any():
                dt_aux = pd.to_datetime(serie_evento, format='%Y-%m-%d %H:%M', errors='coerce')
                dt_evento = dt_evento.fillna(dt_aux)
            falt = dt_evento.isna()
            if falt.any():
                dt_aux = pd.to_datetime(serie_evento, format='%y-%m-%d %H:%M:%S', errors='coerce')
                dt_evento = dt_evento.fillna(dt_aux)
            falt = dt_evento.isna()
            if falt.any():
                dt_aux = pd.to_datetime(serie_evento, format='%y-%m-%d %H:%M', errors='coerce')
                dt_evento = dt_evento.fillna(dt_aux)
            df['Data/Hora Evento'] = dt_evento

            if 'GNSS UTC Time' in df.columns:
                serie_gnss = df['GNSS UTC Time'].astype(str).str.strip()
                dt_gnss = pd.to_datetime(serie_gnss, format='%Y-%m-%d %H:%M:%S', errors='coerce')
                falt = dt_gnss.isna()
                if falt.any():
                    dt_aux = pd.to_datetime(serie_gnss, format='%Y-%m-%d %H:%M', errors='coerce')
                    dt_gnss = dt_gnss.fillna(dt_aux)
                falt = dt_gnss.isna()
                if falt.any():
                    dt_aux = pd.to_datetime(serie_gnss, format='%y-%m-%d %H:%M:%S', errors='coerce')
                    dt_gnss = dt_gnss.fillna(dt_aux)
                falt = dt_gnss.isna()
                if falt.any():
                    dt_aux = pd.to_datetime(serie_gnss, format='%y-%m-%d %H:%M', errors='coerce')
                    dt_gnss = dt_gnss.fillna(dt_aux)
                df['GNSS UTC Time'] = dt_gnss

            df = df.dropna(subset=['Latitude', 'Longitude', 'Data/Hora Evento'])
            df = df.sort_values('Data/Hora Evento')

            if len(df.columns) > len(set(df.columns)):
                df = df.loc[:, ~df.columns.duplicated()]

            return df.reset_index(drop=True)
        except:
            continue

    raise ValueError(f"Não foi possível ler o arquivo {path} corretamente")


def classify_message(message: str) -> str:
    message = str(message).strip().upper()
    if message == "GTERI":
        return "T"
    return "X"

# Classificação que considera regras específicas do TM07 (Tipo Dispositivo '83')
def classify_row(row) -> str:
    tipo_mensagem = str(row.get('Tipo Mensagem', '')).strip().upper()
    if tipo_mensagem == 'GTERI':
        return 'T'

    tipo_dispositivo = str(row.get('Tipo Dispositivo', '')).strip()
    event_code = str(row.get('Event Code', '')).strip().upper()

    # TM07 (tipo 83) utiliza Event Code 30 e 27 para mensagens temporizadas (equivalente a GTERI)
    if tipo_dispositivo == '83' and event_code in {'30', '27'}:
        return 'T'

    return 'X'

def time_difference_category(delta: float) -> str:
    try:
        delta = float(delta)
        if delta <= 1:
            return "1"
        elif delta <= 5:
            return "5"
        elif delta <= 10:
            return "10"
    except:
        pass
    return None

def find_matches(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, int]]:
    counters = {'T1': 0, 'T5': 0, 'T10': 0, 'NA': 0}

    df1 = df1.copy()
    df2 = df2.copy()

    # Considera tanto 'Tipo Mensagem' (GTERI) quanto regras TM07 (tipo '83')
    df1['Message_Category'] = df1.apply(classify_row, axis=1)
    df2['Message_Category'] = df2.apply(classify_row, axis=1)
    df1['Match_Type'] = 'NA'
    df2['Match_Type'] = 'NA'
    df1['Match_ID'] = 0
    df2['Match_ID'] = 0
    df1['delta'] = None
    df2['delta'] = None

    msgs1 = df1[df1['Message_Category'] == 'T'].dropna(subset=['GNSS UTC Time']).copy()
    msgs2 = df2[df2['Message_Category'] == 'T'].dropna(subset=['GNSS UTC Time']).copy()

    used_indices_2 = set()

    for idx1, msg1 in msgs1.iterrows():
        msg1_time = msg1['GNSS UTC Time'].timestamp()
        best_match = None
        min_diff = float('inf')

        for idx2, msg2 in msgs2.iterrows():
            if idx2 in used_indices_2:
                continue

            try:
                time_diff = abs(msg2['GNSS UTC Time'].timestamp() - msg1_time)
                if time_diff <= 10 and time_diff < min_diff:
                    min_diff = time_diff
                    best_match = (idx2, time_diff)
            except:
                continue

        if best_match:
            idx2, diff = best_match
            category = time_difference_category(diff)

            if category:
                match_type = f"T{category}"
                counters[match_type] += 1
                match_id = counters[match_type]

                df1.at[idx1, 'Match_Type'] = match_type
                df2.at[idx2, 'Match_Type'] = match_type
                df1.at[idx1, 'Match_ID'] = match_id
                df2.at[idx2, 'Match_ID'] = match_id

                df1.at[idx1, 'Delta'] = diff
                df2.at[idx2, 'Delta'] = diff

                used_indices_2.add(idx2)

    counters['NA'] = len(df1[df1['Match_Type'] == 'NA']) + len(df2[df2['Match_Type'] == 'NA'])

    return df1, df2, counters


def analisar_match(input1: str, input2: str, output_dir: str = None) -> Dict[str, int]:
    df1 = match(input1)
    df2 = match(input2)

    required = ['Tipo Mensagem', 'Data/Hora Evento', 'Latitude', 'Longitude', 'GNSS UTC Time']
    for df, path in [(df1, input1), (df2, input2)]:
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Arquivo {path} está faltando colunas: {missing}")

    df1, df2, counts = find_matches(df1, df2)

    for df in [df1, df2]:
        serie_gnss = df['GNSS UTC Time'].astype(str).str.strip()
        dt_gnss = pd.to_datetime(serie_gnss, format='%Y-%m-%d %H:%M:%S', errors='coerce')
        falt = dt_gnss.isna()
        if falt.any():
            dt_aux = pd.to_datetime(serie_gnss, format='%Y-%m-%d %H:%M', errors='coerce')
            dt_gnss = dt_gnss.fillna(dt_aux)
        falt = dt_gnss.isna()
        if falt.any():
            dt_aux = pd.to_datetime(serie_gnss, format='%y-%m-%d %H:%M:%S', errors='coerce')
            dt_gnss = dt_gnss.fillna(dt_aux)
        falt = dt_gnss.isna()
        if falt.any():
            dt_aux = pd.to_datetime(serie_gnss, format='%y-%m-%d %H:%M', errors='coerce')
            dt_gnss = dt_gnss.fillna(dt_aux)
        df['GNSS UTC Time'] = dt_gnss
        df['Tempo de fix'] = (df['Data/Hora Evento'] - df['GNSS UTC Time']).dt.total_seconds()
        df['Match_Complete'] = df['Match_Type'].astype(str) + '_' + df['Match_ID'].astype(str)

    if output_dir is None:
        output_dir = os.path.dirname(input1)

    output1 = os.path.join(output_dir, 'match1.csv')
    output2 = os.path.join(output_dir, 'match2.csv')


    df1.to_csv(output1, index=False, encoding='utf-8', errors='replace')
    df2.to_csv(output2, index=False, encoding='utf-8', errors='replace')

    print(f"✅ Arquivos salvos")
    return output1, output2, counts

# if __name__ == "__main__":
#     df =
#     analisar_match(
#         input1='logs/test_1nv.csv',
#         input2='logs/test_2NV.csv'
#     )
