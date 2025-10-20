from tkinter import EventType
import pandas as pd
import os
from datetime import datetime


def normalizar_TM07(df: pd.DataFrame) -> dict:
    try:
        print("\n🔍 [DEBUG TM07] Iniciando normalização TM-07...")
        df = df.copy()
        
        # Para TM-07, procura por 'Event Code' (preferencial), 'Event code', 'Tipo Mensagem' ou 'Tipo mensagem'
        coluna_tipo = None
        if 'Event Code' in df.columns:
            coluna_tipo = 'Event Code'
            print("✅ [DEBUG TM07] Usando coluna 'Event Code'")
        elif 'Event code' in df.columns:
            coluna_tipo = 'Event code'
            print("✅ [DEBUG TM07] Usando coluna 'Event code'")
        
        if coluna_tipo is None:
            print("❌ [DEBUG TM07] Nenhuma coluna de tipo de mensagem encontrada!")
            print(f"   Colunas disponíveis: {list(df.columns)}")
            return None

        print(f"📊 [DEBUG TM07] Amostra dos dados antes da conversão:")
        print(f"   Primeiros 10 valores únicos: {df[coluna_tipo].dropna().unique()[:10]}")
        print(f"   Tipos de dados: {df[coluna_tipo].dtype}")

        # Aplica mapeamento específico para TM-07 (códigos 21/20 e variações em português)
        df_mapeado = mapear_eventos_tipo_mensagem(df)
        
        # Se usou 'Event Code' ou 'Event code', renomeia para 'Tipo Mensagem' para padronizar
        if coluna_tipo in ['Event Code', 'Event code']:
            df_mapeado = df_mapeado.rename(columns={coluna_tipo: 'Tipo Mensagem'})
            coluna_tipo = 'Tipo Mensagem'
            

        # 🔧 CORREÇÃO PRINCIPAL: Converte explicitamente para int onde foi mapeado
        def converter_para_int(valor):
            if pd.isna(valor):
                return valor
            try:
                # Se for 667.0 ou 668.0, converte para int
                if float(valor) in [667.0, 668.0]:
                    return int(float(valor))
            except (ValueError, TypeError):
                pass
            return valor
        
        df_mapeado[coluna_tipo] = df_mapeado[coluna_tipo].apply(converter_para_int)

        tipos_depois = df_mapeado[coluna_tipo].dropna().astype(str).unique().tolist()
        print(f"📊 [DEBUG TM07] Tipos após mapeamento: {tipos_depois}")
        print(f"🔢 [DEBUG TM07] Contagem de valores após mapeamento:")
        contagem_depois = df_mapeado[coluna_tipo].value_counts()
        for valor, count in contagem_depois.head(15).items():
            print(f"   {valor}: {count} ocorrências")

        # Estatísticas de interesse para TM-07 (foco em ignição)
        cont_667 = (df_mapeado[coluna_tipo] == 667).sum()
        cont_668 = (df_mapeado[coluna_tipo] == 668).sum()
        
        print(f"🎯 [DEBUG TM07] Contagens de eventos de ignição:")
        print(f"   • 667 (Ignição ligada): {cont_667}")
        print(f"   • 668 (Ignição desligada): {cont_668}")

        # Cria coluna legível opcional
        mapa_legenda = {667: 'Ignição ligada', 668: 'Ignição desligada'}
        df_mapeado['Tipo Mensagem Legenda'] = df_mapeado[coluna_tipo].apply(lambda v: mapa_legenda.get(v, str(v)))
        
        print("📋 [DEBUG TM07] Amostra das primeiras linhas com legenda:")
        amostra_legenda = df_mapeado[['Tipo Mensagem', 'Tipo Mensagem Legenda']].head(10)
        for idx, row in amostra_legenda.iterrows():
            print(f"   Linha {idx}: {row['Tipo Mensagem']} (tipo: {type(row['Tipo Mensagem']).__name__}) -> '{row['Tipo Mensagem Legenda']}'")

        print("✅ [DEBUG TM07] Normalização TM-07 concluída.")
        return df_mapeado
    except Exception as e:
        print(f"❌ [DEBUG TM07] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return None


def mapear_eventos_tipo_mensagem(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna um novo DataFrame com a mesma estrutura do de entrada, porém com a
    coluna `Tipo Mensagem` sobrescrita pelos seguintes identificadores numéricos
    quando aplicável (demais valores permanecem inalterados):

    - GTIGN ou 21 -> 667 (INT, não float)
    - GTIGF ou 20 -> 668 (INT, não float)
    """
    if df is None or not isinstance(df, pd.DataFrame):
        return df

    if 'Tipo Mensagem' not in df.columns and 'Tipo mensagem' not in df.columns and 'Event code' not in df.columns and 'Event Code' not in df.columns:
        print("❌ [DEBUG MAPEAMENTO] A coluna 'Tipo Mensagem' não foi encontrada no arquivo.")
        return df

    df_out = df.copy()

    # Detecta qual variação de coluna existe (prioriza 'Event Code' para TM-07)
    coluna_tipo = None
    if 'Event Code' in df_out.columns:
        coluna_tipo = 'Event Code'
    elif 'Event code' in df_out.columns:
        coluna_tipo = 'Event code'
    elif 'Tipo Mensagem' in df_out.columns:
        coluna_tipo = 'Tipo Mensagem'
    elif 'Tipo mensagem' in df_out.columns:
        coluna_tipo = 'Tipo mensagem'
    else:
        print("❌ [DEBUG MAPEAMENTO] Nenhuma coluna de tipo de mensagem encontrada.")
        return df_out
    
    print(f"🔍 [DEBUG MAPEAMENTO] Mapeando coluna: '{coluna_tipo}'")

    # Função de mapeamento por linha - RETORNA INT quando mapear 667/668
    def mapear_linha(tipo_raw):
        if pd.isna(tipo_raw):
            return tipo_raw
        
        # CONVERTE PARA STRING PRIMEIRO
        tipo_str = str(tipo_raw).strip()
        
        # Normaliza códigos numéricos que possam vir como float (ex.: '21.0', '20.0')
        try:
            if tipo_str.endswith('.0'):
                tipo_str = tipo_str[:-2]
            
            if tipo_str.replace('.', '').isdigit():
                tipo_str = str(int(float(tipo_str)))
        except (ValueError, TypeError):
            pass
        
        # MAPEAMENTO - retorna INT diretamente
        if tipo_str == '21':
            return 667  # 🔧 INT, não float
        elif tipo_str == '20':
            return 668  # 🔧 INT, não float
        elif tipo_str.lower() == 'ignição ligada' or tipo_str.upper() == 'GTIGN':
            return 667
        elif tipo_str.lower() == 'ignição desligada' or tipo_str.upper() == 'GTIGF':
            return 668
        
        return tipo_raw  # Mantém valor original

    print("🔄 [DEBUG MAPEAMENTO] Aplicando mapeamento linha por linha...")
    
    # Aplica o mapeamento com debug nas primeiras 50 linhas
    resultados_mapeamento = []
    for i, v in enumerate(df_out[coluna_tipo]):
        if i < 50:
            resultado = mapear_linha(v)
            resultados_mapeamento.append(resultado)
            if i < 5:  # Debug mais verboso nas primeiras 5
                print(f"🔍 [DEBUG MAPEAMENTO] Linha {i}: {v} -> {resultado} (tipo: {type(resultado).__name__})")
        else:
            # Aplicação rápida sem debug
            if pd.isna(v):
                resultados_mapeamento.append(v)
            else:
                tipo_str = str(v).strip()
                try:
                    if tipo_str.endswith('.0'):
                        tipo_str = tipo_str[:-2]
                    if tipo_str.replace('.', '').isdigit():
                        tipo_str = str(int(float(tipo_str)))
                except (ValueError, TypeError):
                    pass
                
                # Mapeamento rápido
                if tipo_str == '21':
                    resultados_mapeamento.append(667)
                elif tipo_str == '20':
                    resultados_mapeamento.append(668)
                elif tipo_str.lower() == 'ignição ligada' or tipo_str.upper() == 'GTIGN':
                    resultados_mapeamento.append(667)
                elif tipo_str.lower() == 'ignição desligada' or tipo_str.upper() == 'GTIGF':
                    resultados_mapeamento.append(668)
                else:
                    resultados_mapeamento.append(v)
    
    df_out[coluna_tipo] = resultados_mapeamento
    
    print("✅ [DEBUG MAPEAMENTO] Mapeamento concluído")
    return df_out


if __name__ == "__main__":
    df_exemplo = pd.read_csv('logs/BDB3D78.csv', encoding='latin-1', low_memory=False)

    # Exemplo de uso do mapeamento
    df_mapeado = mapear_eventos_tipo_mensagem(df_exemplo)
    
    # Salva um arquivo exemplo mantendo tudo e adicionando a coluna com IDs
    try:
        os.makedirs('logs', exist_ok=True)
        df_mapeado.to_csv('logs/teste_mapeado.csv', index=False, encoding='utf-8')
        print("✅ Arquivo com mapeamento salvo em 'logs/teste_mapeado.csv'")
    except Exception as e:
        print(f"⚠️ Não foi possível salvar o arquivo de saída: {e}")