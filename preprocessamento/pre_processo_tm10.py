from tkinter import EventType
import pandas as pd
import os
from datetime import datetime


def normalizar_TM10(df: pd.DataFrame) -> dict:
    try:
        #print("[normalizar_TM10] Iniciando normalização TM-10...")
        df = df.copy()
        # print(df.columns)
        if 'Tipo Mensagem' not in df.columns and 'Tipo mensagem' not in df.columns:
            #print("❌ A coluna 'Tipo Mensagem' não foi encontrada no arquivo.")
            return None

        coluna_tipo = 'Tipo Mensagem' if 'Tipo Mensagem' in df.columns else 'Tipo mensagem'
        tipos_antes = df[coluna_tipo].dropna().astype(str).str.upper().unique().tolist()
        #print(f"[normalizar_TM10] Tipos antes do mapeamento (amostra): {tipos_antes[:12]}")

        if 'Motion Status' in df.columns:
            motion_unique = df['Motion Status'].dropna().astype(str).str[:1].unique().tolist()
            #print(f"[normalizar_TM10] Motion Status prefixos únicos (amostra): {motion_unique[:12]}")
        else:
            #print("[normalizar_TM10] Coluna 'Motion Status' ausente. Mapeamento 760/761 pode manter 'GTERI'.")
            pass

        # Aplica mapeamento que sobrescreve 'Tipo Mensagem' com IDs (667, 668, 775, 776, 760, 761...)
        df_mapeado = mapear_eventos_tipo_mensagem(df)

        tipos_depois = df_mapeado[coluna_tipo].dropna().astype(str).unique().tolist()
        #print(f"[normalizar_TM10] Tipos após mapeamento (amostra): {tipos_depois[:12]}")

        # Estatísticas de interesse
        cont_667 = (df_mapeado[coluna_tipo] == 667).sum() if 667 in set(df_mapeado[coluna_tipo].unique()) else 0
        cont_668 = (df_mapeado[coluna_tipo] == 668).sum() if 668 in set(df_mapeado[coluna_tipo].unique()) else 0
        cont_760 = (df_mapeado[coluna_tipo] == 760).sum() if 760 in set(df_mapeado[coluna_tipo].unique()) else 0
        cont_761 = (df_mapeado[coluna_tipo] == 761).sum() if 761 in set(df_mapeado[coluna_tipo].unique()) else 0
        #print(f"[normalizar_TM10] Contagens -> 667: {cont_667}, 668: {cont_668}, 760: {cont_760}, 761: {cont_761}")

        # Também cria uma coluna legível opcional (não quebra nada existente)
        mapa_legenda = {667: 'Ignição ligada', 668: 'Ignição desligada', 775: 'Pin on', 776: 'Pin off', 760: 'ERI motion 1', 761: 'ERI motion 2'}
        df_mapeado['Tipo Mensagem Legenda'] = df_mapeado[coluna_tipo].apply(lambda v: mapa_legenda.get(v, str(v)))
        #print("[normalizar_TM10] Exemplo de legendas:")
        #print(df_mapeado[['Tipo Mensagem Legenda']].head(5).to_string(index=False))

       # print("[normalizar_TM10] Normalização TM-10 concluída.")
        return df_mapeado
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return None


# ==========================
# Mapeamento de Tipo Mensagem
# ==========================
def _normalizar_motion_prefix(motion_value) -> str:
    try:
        if isinstance(motion_value, (float, int)):
            if pd.notna(motion_value):
                motion_str = str(int(motion_value))
            else:
                motion_str = ''
        elif isinstance(motion_value, (str, bytes)):
            motion_str = str(motion_value)
        else:
            motion_str = ''
        return motion_str[0] if len(motion_str) > 0 else ''
    except Exception:
        return ''


def mapear_eventos_tipo_mensagem(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna um novo DataFrame com a mesma estrutura do de entrada, porém com a
    coluna `Tipo Mensagem` sobrescrita pelos seguintes identificadores numéricos
    quando aplicável (demais valores permanecem inalterados):

    - GTIGN -> 667
    - GTIGF -> 668
    - GTERI e motion_prefix '1' -> 760
    - GTERI e motion_prefix '2' -> 761
    - GTMPN -> 775
    - GTMPF -> 776

    Observações:
    - A coluna utilizada é `Tipo Mensagem` (case-insensitive). Se não existir, retorna o df original.
    - Para os casos de GTERI, utiliza-se a primeira posição de `Motion Status`.
    - Se não for possível determinar 760 vs 761 (ex.: ausência de `Motion Status`), mantém-se o valor original `GTERI`.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        return df

    if 'Tipo Mensagem' not in df.columns and 'Tipo mensagem' not in df.columns:
        #print("❌ A coluna 'Tipo Mensagem' não foi encontrada no arquivo.")
        return df

    df_out = df.copy()

    # Detecta qual variação de coluna existe
    coluna_tipo = 'Tipo Mensagem' if 'Tipo Mensagem' in df_out.columns else 'Tipo mensagem'
    tipo_series = df_out[coluna_tipo]

    # Pré-calcula motion prefix quando disponível
    motion_prefix_series = None
    if 'Motion Status' in df_out.columns:
        motion_prefix_series = df_out['Motion Status'].apply(_normalizar_motion_prefix)

    # Função de mapeamento por linha
    def mapear_linha(idx: int, tipo_raw):
        tipo_original = str(tipo_raw)
        tipo = tipo_original.strip().upper()
        if tipo == 'GTIGN':
            return 667
        if tipo == 'GTIGF':
            return 668
        if tipo == 'GTMPN':
            return 775
        if tipo == 'GTMPF':
            return 776
        if tipo == 'GTERI':
            motion_prefix = ''
            if motion_prefix_series is not None:
                try:
                    motion_prefix = str(motion_prefix_series.iloc[idx]) if pd.notna(motion_prefix_series.iloc[idx]) else ''
                except Exception:
                    motion_prefix = ''
            if motion_prefix == '1':
                return 760
            if motion_prefix == '2':
                return 761
            return tipo_original  # mantém 'GTERI' quando não dá para decidir
        return tipo_original

    # Aplica o mapeamento sobrescrevendo a coluna de entrada
    df_out[coluna_tipo] = [mapear_linha(i, v) for i, v in enumerate(tipo_series)]

    return df_out

# def salvar_resultados_csv(resultados: dict, nome_arquivo: str = None):
#  

if __name__ == "__main__":
    df_exemplo = pd.read_csv('logs/867488068342780_decoded.csv', encoding='latin-1', low_memory=False)

    # print("📊 Iniciando análise...")
    # Exemplo de uso do mapeamento
    df_mapeado = mapear_eventos_tipo_mensagem(df_exemplo)
    # Salva um arquivo exemplo mantendo tudo e adicionando a coluna com IDs
    try:
        os.makedirs('logs', exist_ok=True)
        df_mapeado.to_csv('logs/teste_mapeado.csv', index=False, encoding='utf-8')
        #print("✅ Arquivo com mapeamento salvo em 'logs/teste_mapeado.csv'")
    except Exception as e:
        print(f"⚠️ Não foi possível salvar o arquivo de saída: {e}")


 