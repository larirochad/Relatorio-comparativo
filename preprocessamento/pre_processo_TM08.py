from tkinter import EventType
import pandas as pd
import os
from datetime import datetime


def normalizar_TM08(df: pd.DataFrame) -> dict:
    try:
        #print("[normalizar_TM08] Iniciando normalização TM-08...")
        df = df.copy()
        
        if 'Tipo Mensagem' not in df.columns and 'Tipo mensagem' not in df.columns:
            #print("❌ A coluna 'Tipo Mensagem' não foi encontrada no arquivo.")
            return None

        coluna_tipo = 'Tipo Mensagem' if 'Tipo Mensagem' in df.columns else 'Tipo mensagem'
        tipos_antes = df[coluna_tipo].dropna().astype(str).str.upper().unique().tolist()
        #print(f"[normalizar_TM08] Tipos antes do mapeamento (amostra): {tipos_antes[:12]}")

        # Aplica mapeamento específico para TM-08 (principalmente GTIGN/GTIGF e variações em português)
        df_mapeado = mapear_eventos_tipo_mensagem(df)

        tipos_depois = df_mapeado[coluna_tipo].dropna().astype(str).unique().tolist()
        #print(f"[normalizar_TM08] Tipos após mapeamento (amostra): {tipos_depois[:12]}")

        # Estatísticas de interesse para TM-08 (foco em ignição)
        cont_667 = (df_mapeado[coluna_tipo] == 667).sum() if 667 in set(df_mapeado[coluna_tipo].unique()) else 0
        cont_668 = (df_mapeado[coluna_tipo] == 668).sum() if 668 in set(df_mapeado[coluna_tipo].unique()) else 0
        #print(f"[normalizar_TM08] Contagens -> 667 (Ignição ligada): {cont_667}, 668 (Ignição desligada): {cont_668}")

        # Cria coluna legível opcional
        mapa_legenda = {667: 'Ignição ligada', 668: 'Ignição desligada'}
        df_mapeado['Tipo Mensagem Legenda'] = df_mapeado[coluna_tipo].apply(lambda v: mapa_legenda.get(v, str(v)))
        #print("[normalizar_TM08] Exemplo de legendas:")
       #print(df_mapeado[['Tipo Mensagem Legenda']].head(5).to_string(index=False))

        #print("[normalizar_TM08] Normalização TM-08 concluída.")
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


    # Função de mapeamento por linha
    def mapear_linha(idx: int, tipo_raw):
        tipo_original = str(tipo_raw)
        tipo_stripped = tipo_original.strip()
        tipo_upper = tipo_stripped.upper()

        # Mapeia textos GTI* e equivalentes em PT-BR
        if tipo_upper == 'GTIGN' or 'IGINI' in tipo_upper or 'IGNIÇÃO LIGADA' in tipo_upper:
            return 667
        if tipo_upper == 'GTIGF' or 'DESLIGADA' in tipo_upper or 'IGNIÇÃO DESLIGADA' in tipo_upper:
            return 668

        # Mantém numéricos 667/668, caso já venham normalizados
        if tipo_stripped in ('667', '668'):
            return int(tipo_stripped)

        # Sem mapeamento: mantém valor original
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
        print("✅ Arquivo com mapeamento salvo em 'logs/teste_mapeado.csv'")
    except Exception as e:
        print(f"⚠️ Não foi possível salvar o arquivo de saída: {e}")


 