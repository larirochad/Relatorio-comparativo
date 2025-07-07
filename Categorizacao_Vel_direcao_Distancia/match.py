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

            df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], format='mixed', dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Latitude', 'Longitude', 'Data/Hora Evento'])

            if 'GNSS UTC Time' in df.columns:
                df['GNSS UTC Time'] = pd.to_datetime(df['GNSS UTC Time'], errors='coerce')

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

    df1['Message_Category'] = df1['Tipo Mensagem'].apply(classify_message)
    df2['Message_Category'] = df2['Tipo Mensagem'].apply(classify_message)
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
        df['GNSS UTC Time'] = pd.to_datetime(df['GNSS UTC Time'], errors='coerce')
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
#     analisar_match(
#         input1='logs/test_1nv.csv',
#         input2='logs/test_2NV.csv'
#     )
