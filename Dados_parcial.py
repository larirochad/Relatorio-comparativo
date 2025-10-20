import pandas as pd
import glob
import os
import json
from preprocessamento.pre_processo_tm10 import normalizar_TM10
from preprocessamento.pre_processo_TM08 import normalizar_TM08
from preprocessamento.pre_processo_TM07 import normalizar_TM07
from preprocessamento.pre_processo_LC03 import normalizar_LC03

def criar_mapeamento_cores_pareadas():
    """
    Cria um dicionário que mapeia cada veículo à sua cor específica.
    Veículos que formam pares terão a mesma cor.
    """
    # Definição dos pares de análise
    pares_analise = [
        {'csv1': 'ENG_146.csv', 'csv2': 'A474999.csv', 'problema': 'TM-08'},
        {'csv1': 'ENG_048.csv', 'csv2': 'AYL2486.csv', 'problema': 'TM-07'},
        {'csv1': 'ENG_046.csv', 'csv2': 'JAP8F64.csv', 'problema': 'TM-07'},
        {'csv1': 'ENG_042.csv', 'csv2': 'A474038.csv', 'problema': 'TM-08'},
        {'csv1': 'ENG_039.csv', 'csv2': 'RHH4B26.csv', 'problema': 'TM-07'},
        {'csv1': 'ENG_004.csv', 'csv2': 'BDB3D78.csv', 'problema': 'TM-07'},
        {'csv1': 'ENG_014.csv', 'csv2': 'TYA9C79.csv', 'problema': 'TM-08'},
        {'csv1': 'ENG_009.csv', 'csv2': 'BAA1364.csv', 'problema': 'TM-08'},
        {'csv1': 'ENG_111.csv', 'csv2': 'A475104.csv', 'problema': 'TM-08'},
    ]
    
    # Paleta de cores distintas para cada par (tons harmoniosos)
    cores_pares = [
        '#00FFFF',  # olive gray
        '#5F9EA0',  # sage
        '#483D8B',  # taupe light
        '#7B68EE',  # sand
        '#4B0082',  # pale sand
        '#483D8B',  # camel
        '#FFC0CB',  # slate
        '#FF00FF',  # grey muted
        '#1E90FF',  # mauve gray
        '#1E90FF'   # pale olive

    ]
    
    # Cria o mapeamento veículo -> cor
    mapeamento_cores = {}
    
    for idx, par in enumerate(pares_analise):
        # Remove extensão .csv dos nomes
        veiculo1 = par['csv1'].replace('.csv', '')
        veiculo2 = par['csv2'].replace('.csv', '')
        
        # Atribui a mesma cor para ambos os veículos do par
        cor_par = cores_pares[idx % len(cores_pares)]
        mapeamento_cores[veiculo1] = cor_par
        mapeamento_cores[veiculo2] = cor_par
    
    return mapeamento_cores


def gerar_cores_para_veiculos(labels, mapeamento_cores_pareadas, cores_padrao):
    """
    Gera a lista de cores para os veículos, usando cores pareadas quando disponível
    e cores padrão para os demais.
    
    Args:
        labels: Lista de nomes dos veículos
        mapeamento_cores_pareadas: Dicionário {nome_veiculo: cor}
        cores_padrao: Lista de cores padrão para veículos não pareados
    
    Returns:
        Lista de cores na mesma ordem dos labels
    """
    cores_finais = []
    indice_cor_padrao = 0
    
    for label in labels:
        if label in mapeamento_cores_pareadas:
            # Usa cor do par
            cores_finais.append(mapeamento_cores_pareadas[label])
        else:
            # Usa cor padrão
            cores_finais.append(cores_padrao[indice_cor_padrao % len(cores_padrao)])
            indice_cor_padrao += 1
    
    return cores_finais


def identificar_tipo_dispositivo(df):
    """
    Identifica o tipo de dispositivo.
    1) Tenta ler a coluna 'Tipo Dispositivo' (variações de nome suportadas)
    2) Caso ausente/vazia, infere pelo conteúdo:
       - Se existir coluna 'Event code' com valores 21/20 ou 'Tipo Mensagem' com
         'Ignição ligada/desligada' → TM-07 ('83')
       - Se existir coluna 'Motion Status' → TM-10 ('802003')
       - Se existirem eventos GTIGN/GTIGF (em texto) → TM-10/TM-08; assumimos TM-08 ('385349')
    Retorna: código do tipo (ex: '802003', '385349', '83', '77') ou None
    """
    tipo_mapping = {
        '802003': 'TM-10',
        '385349': 'TM-08',
        '83': 'TM-07',
        '77': 'LC03',
        'REF': 'Dispositivos referência TM-07 e TM08'
    }

    # 1) Tenta pela coluna explicitamente informada
    try:
        possiveis_colunas = ['Tipo Dispositivo', 'Tipo dispositivo', 'TipoDispositivo', 'Device Type', 'Device type']
        col_disp = encontrar_coluna(df, possiveis_colunas)
        if col_disp is not None:
            tipo_disp_series = df[col_disp].dropna().astype(str)
            if not tipo_disp_series.empty:
                tipo_disp = tipo_disp_series.iloc[0].strip()
                for codigo in tipo_mapping.keys():
                    if codigo in tipo_disp:
                        return codigo
    except Exception:
        pass

    # 2) Inferência pelo conteúdo
    try:
        # Coluna que pode conter códigos ou descrições de eventos
        col_tm = encontrar_coluna(df, ['Event code', 'Tipo Mensagem', 'Tipo mensagem'])
        amostra = []
        if col_tm is not None:
            amostra = df[col_tm].dropna().astype(str).head(100).tolist()

        # Preferência 1: TM-10 costuma ter 'Motion Status'
        if encontrar_coluna(df, ['Motion Status']):
            return '802003'

        # Preferência 2: Se aparecem GTIGN/GTIGF, classifica como TM-08
        if col_tm is not None and any(v.strip().upper() in ('GTIGN', 'GTIGF') for v in amostra):
            return '385349'

        # Preferência 3: TM-07 quando há 'Event code' 21/20 ou strings "Ignição ..."
        if col_tm is not None and (
            any(v.strip() in ('21', '20') for v in amostra) or any('Ignição' in v for v in amostra)
        ):
            return '83'  # TM-07+

        if col_tm is not None and any(v.strip().upper() in ('IGN', 'IGF') for v in amostra):
            return '77'  # LC03
    except Exception:
        pass

    return None

def obter_nome_dispositivo(codigo_tipo):
    """
    Retorna o nome amigável do dispositivo baseado no código.
    """
    tipo_mapping = {
        '802003': 'Analise dispositivo teste TM-10',
        '385349': 'TM-08',
        '83': 'TM-07', 
        '77': 'LC03',
        'REF': 'Dispositivos referência'
    }
    return tipo_mapping.get(codigo_tipo, f"Tipo {codigo_tipo}")

def encontrar_coluna(df, possiveis_nomes):
    """
    Procura uma coluna no DataFrame considerando variações de nome.
    Retorna o nome exato da coluna encontrada ou None.
    """
    colunas_lower = {col.lower().strip(): col for col in df.columns}
    
    for nome in possiveis_nomes:
        nome_lower = nome.lower().strip()
        if nome_lower in colunas_lower:
            return colunas_lower[nome_lower]
    
    return None

def limpar_e_organizar_dados(df, nome_veiculo=""):
    """
    Limpa e organiza os dados do DataFrame:
    1. Organiza por 'Data/Hora Evento' 
    2. Remove duplicatas baseadas na coluna 'Sequência'
    3. Remove linhas com dados inválidos
    
    Args:
        df: DataFrame original
        nome_veiculo: Nome do veículo para debug
    
    Returns:
        DataFrame limpo e organizado
    """
    print(f"\n🧹 LIMPEZA DE DADOS - {nome_veiculo}")
    print(f"{'='*50}")
    
    df_limpo = df.copy()
    registros_originais = len(df_limpo)
    
    # 1. Verifica se existe coluna 'Data/Hora Evento'
    col_data_hora = encontrar_coluna(df_limpo, ['Data/Hora Evento', 'Data/Hora evento', 'data/hora evento'])
    if col_data_hora is None:
        print(f"⚠️ Coluna 'Data/Hora Evento' não encontrada. Pulando limpeza temporal.")
        return df_limpo
    
    print(f"✓ Coluna de data/hora encontrada: '{col_data_hora}'")
    
    # 2. Converte 'Data/Hora Evento' para datetime
    try:
        df_limpo[col_data_hora] = pd.to_datetime(df_limpo[col_data_hora], errors='coerce')
        registros_antes_conv = len(df_limpo)
        df_limpo = df_limpo.dropna(subset=[col_data_hora])
        registros_apos_conv = len(df_limpo)
        print(f"✓ Conversão de data: {registros_antes_conv} → {registros_apos_conv} registros")
    except Exception as e:
        print(f"❌ Erro ao converter data: {e}")
        return df_limpo
    
    # 3. Verifica se existe coluna 'Sequência'
    col_sequencia = encontrar_coluna(df_limpo, ['Sequência', 'Sequencia', 'sequencia', 'Sequence', 'sequence'])
    if col_sequencia is None:
        print(f"⚠️ Coluna 'Sequência' não encontrada. Pulando remoção de duplicatas.")
        # Apenas organiza por data
        df_limpo = df_limpo.sort_values(by=col_data_hora)
        print(f"✓ Dados organizados por data: {len(df_limpo)} registros")
        return df_limpo
    
    print(f"✓ Coluna de sequência encontrada: '{col_sequencia}'")
    
    # 4. Remove duplicatas baseadas na sequência (mantém o primeiro)
    registros_antes_dedup = len(df_limpo)
    df_limpo = df_limpo.drop_duplicates(subset=[col_sequencia], keep='first')
    registros_apos_dedup = len(df_limpo)
    duplicatas_removidas = registros_antes_dedup - registros_apos_dedup
    print(f"✓ Remoção de duplicatas: {duplicatas_removidas} duplicatas removidas ({registros_antes_dedup} → {registros_apos_dedup})")
    
    # 5. Organiza por 'Data/Hora Evento'
    df_limpo = df_limpo.sort_values(by=col_data_hora)
    print(f"✓ Dados organizados por data/hora")
    
    # 6. Remove linhas com hodômetro inválido (se existir) - APENAS NULLs, não zeros!
    col_hodometro = encontrar_coluna(df_limpo, ['Hodômetro total', 'Hodometro total', 'hodometro total', 
                                               'Odômetro total', 'Odometro total', 'odometro total',
                                               'Hodômetro', 'Hodometro', 'Odômetro', 'Odometro'])
    if col_hodometro is not None:
        registros_antes_hod = len(df_limpo)
        # Remove APENAS linhas onde hodômetro é NaN (zero é válido!)
        df_limpo = df_limpo[df_limpo[col_hodometro].notna()]
        registros_apos_hod = len(df_limpo)
        hodometro_invalido_removido = registros_antes_hod - registros_apos_hod
        if hodometro_invalido_removido > 0:
            print(f"✓ Remoção de hodômetros NULL: {hodometro_invalido_removido} registros removidos")
    
    # 7. Resumo final
    registros_finais = len(df_limpo)
    registros_removidos = registros_originais - registros_finais
    print(f"\n📊 RESUMO DA LIMPEZA:")
    print(f"   • Registros originais: {registros_originais}")
    print(f"   • Registros finais: {registros_finais}")
    print(f"   • Registros removidos: {registros_removidos} ({registros_removidos/registros_originais*100:.1f}%)")
    
    return df_limpo

def analisar_distancia(df, nome_veiculo=""):
    """
    Análise SIMPLES de distância: pega o maior e menor valor de hodômetro e calcula a diferença.
    Não depende de ignições ou normalizações - apenas matemática básica.
    """
    print(f"\n📏 ANÁLISE SIMPLES DE DISTÂNCIA - {nome_veiculo}")
    print(f"{'='*50}")
    
    # Possíveis nomes para a coluna de hodômetro
    possiveis_nomes = ['Hodômetro total', 'Hodometro total', 'hodometro total', 
                       'Odômetro total', 'Odometro total', 'odometro total',
                       'Hodômetro', 'Hodometro', 'Odômetro', 'Odometro']
    
    col_hodometro = encontrar_coluna(df, possiveis_nomes)
    
    if col_hodometro is None:
        print(f"❌ Coluna de hodômetro não encontrada!")
        print(f"   Colunas disponíveis: {list(df.columns)[:10]}...")
        return 0
    
    print(f"✓ Coluna de hodômetro encontrada: '{col_hodometro}'")
    
    try:
        # Converte para numérico, removendo valores inválidos
        hodometro_numerico = pd.to_numeric(df[col_hodometro], errors='coerce')
        hodometro_valido = hodometro_numerico.dropna()
        
        if len(hodometro_valido) == 0:
            print(f"❌ Nenhum valor válido de hodômetro encontrado!")
            return 0
        
        # Remove apenas valores negativos (zero é válido!)
        hodometro_valido_final = hodometro_valido[hodometro_valido >= 0]
        
        if len(hodometro_valido_final) == 0:
            print(f"❌ Nenhum valor válido de hodômetro encontrado!")
            return 0
        
        # CÁLCULO SIMPLES: maior - menor (incluindo zero se for o menor)
        hodometro_min = hodometro_valido_final.min()
        hodometro_max = hodometro_valido_final.max()
        distancia = hodometro_max - hodometro_min
        
        print(f"✓ Cálculo simples de distância:")
        print(f"   • Menor valor: {hodometro_min:.2f} km")
        print(f"   • Maior valor: {hodometro_max:.2f} km")
        print(f"   • Distância total: {distancia:.2f} km")
        print(f"   • Registros processados: {len(hodometro_valido_final)}")
        
        return distancia
        
    except Exception as e:
        print(f"❌ Erro ao processar hodômetro: {e}")
        import traceback
        traceback.print_exc()
    
    return 0

def contar_viagens(df, nome_veiculo=""):
    """
    Conta o número de viagens válidas (pares 667 -> 668).
    Uma viagem é contabilizada apenas quando há um 667 (ignição ligada) seguido de um 668 (ignição desligada).
    Para TM-10, os códigos são normalizados: GTIGN -> 667, GTIGF -> 668
    Agora usa dados já limpos e organizados por Data/Hora Evento.
    """
    print(f"\n{'='*60}")
    print(f"🔍 CONTAGEM DE VIAGENS - {nome_veiculo}")
    print(f"{'='*60}")
    
    # Possíveis nomes para a coluna de tipo de mensagem
    possiveis_nomes = ['Tipo mensagem', 'Tipo Mensagem', 'tipo mensagem',
                       'Message Type', 'message type', 'Mensagem', 'Type']
    
    col_tipo_msg = encontrar_coluna(df, possiveis_nomes)
    
    if col_tipo_msg is None:
        print(f"❌ Coluna de tipo mensagem não encontrada!")
        return 0
    
    print(f"✓ Coluna encontrada: '{col_tipo_msg}'")
    
    # Verifica se existe coluna de data para ordenação
    col_data_hora = encontrar_coluna(df, ['Data/Hora Evento', 'Data/Hora evento', 'data/hora evento'])
    if col_data_hora is not None:
        print(f"✓ Dados organizados por: '{col_data_hora}'")
    
    try:
        # 🔧 CORREÇÃO: Normaliza para comparação numérica (compatível com preprocessadores)
        def normalizar_valor(v):
            """Converte valor para int se for 667/668, independente do tipo original"""
            if pd.isna(v):
                return None
            
            # Tenta converter para número primeiro
            try:
                num = float(v)
                # Se for 667.0 ou 668.0, retorna como int
                if num == 667.0 or num == 668.0:
                    return int(num)
                # Se for 667 ou 668 já como int, retorna
                if num == 667 or num == 668:
                    return int(num)
            except (ValueError, TypeError):
                pass
            
            # Para strings, tenta converter
            v_str = str(v).strip()
            if v_str in ('667', '668'):
                return int(v_str)
            
            # Para outros valores, retorna como string (não é evento de ignição)
            return v_str
        
        # Cria DataFrame com mensagens e índices para análise
        df_viagens = df.copy()
        df_viagens['mensagem_normalizada'] = df_viagens[col_tipo_msg].apply(normalizar_valor)
        
        # Filtra apenas eventos de ignição (667 e 668)
        eventos_ignicao = df_viagens[df_viagens['mensagem_normalizada'].isin([667, 668])].copy()
        
        if len(eventos_ignicao) == 0:
            print(f"❌ Nenhum evento de ignição (667/668) encontrado!")
            return 0
        
        # Ordena por data se disponível
        if col_data_hora is not None:
            eventos_ignicao = eventos_ignicao.sort_values(by=col_data_hora)
            print(f"✓ Eventos ordenados por data/hora")
        
        mensagens = eventos_ignicao['mensagem_normalizada'].tolist()
        
        print(f"📊 Total de eventos de ignição: {len(mensagens)}")
        
        # Conta eventos de ignição
        total_667 = sum(1 for v in mensagens if v == 667)
        total_668 = sum(1 for v in mensagens if v == 668)
        
        print(f"   • Eventos 667 (ignição ligada): {total_667}")
        print(f"   • Eventos 668 (ignição desligada): {total_668}")
        
        # Mostra os primeiros eventos de ignição
        print(f"\n📋 Primeiros 10 eventos de ignição na sequência:")
        print(f"   {mensagens[:10]}")
        
        if mensagens:
            print(f"\n   Primeiro evento: {mensagens[0]}")
            print(f"   Último evento: {mensagens[-1]}")

        # Máquina de estados: aguarda 667; quando vê 668 após um 667, conta uma viagem
        aguardando_desligar = False
        count = 0
        pares_encontrados = []

        print(f"\n🔄 Processando sequência de eventos...")
        for idx, valor in enumerate(mensagens):
            if valor == 667:
                if aguardando_desligar:
                    print(f"   ⚠️ Posição {idx}: Encontrado 667 sem fechar o anterior (duplo ligar)")
                aguardando_desligar = True
                continue
            if valor == 668 and aguardando_desligar:
                count += 1
                pares_encontrados.append(f"Par {count} finalizado na posição {idx}")
                aguardando_desligar = False

        # Heurística de correção para casos especiais
        if mensagens:
            primeiro = mensagens[0]
            if primeiro == 668 and total_667 == total_668 and count + 1 == total_667:
                count_corrigido = min(total_667, total_668)
                print(f"✓ Aplicada correção heurística: {count} → {count_corrigido}")
                return count_corrigido

        print(f"✓ Total de viagens encontradas: {count}")
        return count
        
    except Exception as e:
        print(f"❌ Erro ao contar viagens: {e}")
        import traceback
        traceback.print_exc()
    
    return 0

def processar_dados(pasta_csv):
    """
    Processa todos os CSVs da pasta e retorna dados organizados por tipo de dispositivo.
    Retorna: dados_por_tipo (dict com os códigos dos tipos como chaves)
    """
    arquivos = glob.glob(os.path.join(pasta_csv, "*.csv"))
    
    if not arquivos:
        print(f"❌ Nenhum arquivo CSV encontrado em: {pasta_csv}")
        return None
    
    # Inicializa estrutura para cada tipo de dispositivo
    dados_por_tipo = {}
    
    for arquivo in arquivos:
        try:
            # Tenta ler o CSV com diferentes codificações
            df = None
            for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16', 'utf-16le', 'utf-16be']:
                try:
                    df = pd.read_csv(arquivo, encoding=enc, low_memory=False)
                    break
                except Exception:
                    continue
            
            if df is None:
                print(f"❌ Não foi possível ler o arquivo {arquivo} (problema de codificação)")
                continue
            
            # Normaliza nomes de colunas (remove BOM e espaços nas extremidades)
            try:
                df.columns = [str(c).encode('utf-8', 'ignore').decode('utf-8').strip() for c in df.columns]
            except Exception:
                pass

            # Extrai o nome do arquivo
            nome_arquivo = os.path.basename(arquivo)
            nome_veiculo = nome_arquivo.replace('.csv', '')
            
            # Identifica o tipo de dispositivo pela coluna 'Tipo Dispositivo'
            codigo_tipo = identificar_tipo_dispositivo(df)
            
            if codigo_tipo is None:
                print(f"⚠ Tipo não identificado (ignorado)")
                continue
            
            # Aplica normalização baseada no tipo de dispositivo
            if codigo_tipo == '802003':  # TM-10
                print(f"🔄 Aplicando normalização TM-10...")
                df_normalizado = normalizar_TM10(df)
                if df_normalizado is not None:
                    df = df_normalizado
                    print(f"✅ Normalização TM-10 concluída")
                else:
                    print(f"❌ Falha na normalização TM-10")
                    continue
            elif codigo_tipo == '385349':  # TM-08
                df_normalizado = normalizar_TM08(df)
                if df_normalizado is not None:
                    df = df_normalizado
                else:
                    continue
            elif codigo_tipo == '83':  # TM-07
                df_normalizado = normalizar_TM07(df)
                if df_normalizado is not None:
                    df = df_normalizado
                else:
                    continue
            elif codigo_tipo == '77':  # LC03
                print(f"🔄 Aplicando normalização LC03...")
                df_normalizado = normalizar_LC03(df)
                if df_normalizado is not None:
                    df = df_normalizado
                else:
                    print(f"❌ Falha na normalização LC03") 
                    continue
            
            # Inicializa o tipo se não existir
            if codigo_tipo not in dados_por_tipo:
                dados_por_tipo[codigo_tipo] = {'distancias': {}, 'viagens': {}}
            
            # 🧹 NOVA ETAPA: Limpa e organiza os dados
            df_limpo = limpar_e_organizar_dados(df, nome_veiculo)
            
            # Analisa distância usando dados limpos
            dist = analisar_distancia(df_limpo, nome_veiculo)
            
            # Analisa viagens usando dados limpos
            qtd_viagens = contar_viagens(df_limpo, nome_veiculo)
            
            # Armazena os dados
            dados_por_tipo[codigo_tipo]['distancias'][nome_veiculo] = dist
            dados_por_tipo[codigo_tipo]['viagens'][nome_veiculo] = qtd_viagens
            
            nome_dispositivo = obter_nome_dispositivo(codigo_tipo)
            print(f"\n✓ RESUMO [{nome_dispositivo}] {nome_veiculo}:")
            print(f"  • Distância: {dist:.2f} km")
            print(f"  • Viagens: {qtd_viagens}")
            
        except Exception as e:
            print(f"❌ Erro ao processar {arquivo}: {e}")
            import traceback
            traceback.print_exc()
    
    return dados_por_tipo

def gerar_dashboard_completo(pasta_csv, arquivo_saida="dashboard_frotas.html", modo_relatorio='pares_de_teste', codigo_teste='802003', codigos_referencia=None):
    """
    Gera o dashboard completo com análises por tipo de dispositivo usando Chart.js.
    """
    print("="*60)
    print("🚗 DASHBOARD DE ANÁLISE DE FROTAS")
    print("="*60)
    
    # ===== Configuração de agrupamento =====
    MODO_RELATORIO = (modo_relatorio or 'pares_de_teste').strip()
    CODIGO_TESTE = (codigo_teste or '802003').strip()
    CODIGOS_REFERENCIA = codigos_referencia if codigos_referencia is not None else ['83', '385349']
    
    # Cria mapeamento de cores para pares
    mapeamento_cores_pareadas = criar_mapeamento_cores_pareadas()
    
    # Processa os dados
    dados_por_tipo = processar_dados(pasta_csv)
    
    if dados_por_tipo is None or len(dados_por_tipo) == 0:
        print("❌ Nenhum dado válido encontrado.")
        return
    
    # Combina TM-07 + TM-08 em um grupo de referência (REF)
    def somar_distancias(a, b):
        out = dict(a)
        for k, v in b.items():
            out[k] = float(out.get(k, 0)) + float(v)
        return out

    def somar_viagens(a, b):
        out = dict(a)
        for k, v in b.items():
            out[k] = int(out.get(k, 0)) + int(v)
        return out

    dados_ref = None
    if any(c in dados_por_tipo for c in CODIGOS_REFERENCIA):
        dist = {}
        viagens = {}
        for codigo in CODIGOS_REFERENCIA:
            if codigo in dados_por_tipo:
                dist = somar_distancias(dist, dados_por_tipo[codigo]['distancias'])
                viagens = somar_viagens(viagens, dados_por_tipo[codigo]['viagens'])
        dados_ref = {'distancias': dist, 'viagens': viagens}

    # Seleciona apenas TM-10 e REF para o dashboard
    dados_para_dashboard = {}
    if MODO_RELATORIO == 'single':
        if CODIGO_TESTE in dados_por_tipo:
            dados_para_dashboard[CODIGO_TESTE] = dados_por_tipo[CODIGO_TESTE]
        else:
            for codigo, dados in dados_por_tipo.items():
                dados_para_dashboard[codigo] = dados
    else:
        if dados_ref is not None:
            dados_para_dashboard['REF'] = dados_ref
        if CODIGO_TESTE in dados_por_tipo:
            dados_para_dashboard[CODIGO_TESTE] = dados_por_tipo[CODIGO_TESTE]
        excluidos = set(CODIGOS_REFERENCIA + [CODIGO_TESTE])
        for codigo, dados in dados_por_tipo.items():
            if codigo not in excluidos:
                dados_para_dashboard[codigo] = dados

    # Verifica se há dados para processar e calcula resumo
    print(f"\n📊 Resumo:")
    nomes_dinamicos = {}
    codigos_ref_presentes = [c for c in CODIGOS_REFERENCIA if c in dados_por_tipo]
    if 'REF' in dados_para_dashboard:
        if len(codigos_ref_presentes) > 0:
            nomes_ref = [obter_nome_dispositivo(c) for c in codigos_ref_presentes]
            nomes_dinamicos['REF'] = "Dispositivos referência " + " e ".join(nomes_ref)
        else:
            nomes_dinamicos['REF'] = "Dispositivos referência"
    if CODIGO_TESTE in dados_para_dashboard:
        nomes_dinamicos[CODIGO_TESTE] = f"Analise dispositivo teste ({obter_nome_dispositivo(CODIGO_TESTE)})"

    for codigo_tipo, dados in dados_para_dashboard.items():
        nome_dispositivo = nomes_dinamicos.get(codigo_tipo, obter_nome_dispositivo(codigo_tipo))
        total_km = sum(dados['distancias'].values())
        total_viagens = int(sum(dados['viagens'].values()))
        print(f"   {nome_dispositivo}: {len(dados['distancias'])} veículos ({total_km:.2f} km, {total_viagens} viagens)")
    
    # Cores padrão para veículos não pareados
    cores_padrao = [
        '#00FFFF',  # cyan
        '#5F9EA0',  # cadet blue
        '#483D8B',  # dark slate blue
        '#7B68EE',  # medium slate blue
        '#4B0082',  # indigo
        '#FFC0CB',  # pink
        '#FF00FF',  # magenta
        '#1E90FF',  # dodger blue
    ]
    
    # Prepara dados para Chart.js COM CORES PERSONALIZADAS
    def preparar_dados_chart(dados):
        labels_dist = list(dados['distancias'].keys())
        values_dist = [float(v) for v in dados['distancias'].values()]
        labels_viagens = list(dados['viagens'].keys())
        values_viagens = [int(v) for v in dados['viagens'].values()]
        
        # Gera cores específicas para cada dataset
        cores_dist = gerar_cores_para_veiculos(labels_dist, mapeamento_cores_pareadas, cores_padrao)
        cores_viagens = gerar_cores_para_veiculos(labels_viagens, mapeamento_cores_pareadas, cores_padrao)
        
        return {
            'distancias': {
                'labels': labels_dist, 
                'values': values_dist,
                'cores': cores_dist
            },
            'viagens': {
                'labels': labels_viagens, 
                'values': values_viagens,
                'cores': cores_viagens
            }
        }
    
    # Prepara dados de gráficos para todos os tipos
    chart_data_por_tipo = {}
    for codigo_tipo, dados in dados_para_dashboard.items():
        chart_data_por_tipo[codigo_tipo] = preparar_dados_chart(dados)

    if len(chart_data_por_tipo) == 0:
        chart_data_por_tipo['REF'] = {
            'distancias': {'labels': [], 'values': [], 'cores': []}, 
            'viagens': {'labels': [], 'values': [], 'cores': []}
        }
    
    # Cores específicas para cada tipo de dispositivo (tons neutros/terrosos)
    cores_dispositivos = {
        '802003': '#836FFF',
        'REF':    '#6C757D',
        '77':     '#2F855A'
    }

    # Gera HTML dinâmico baseado nos tipos encontrados
    analises_html = ""
    for codigo_tipo, dados in dados_para_dashboard.items():
        nome_dispositivo = nomes_dinamicos.get(codigo_tipo, obter_nome_dispositivo(codigo_tipo))
        total_km = sum(dados['distancias'].values())
        total_viagens = int(sum(dados['viagens'].values()))
        cor_dispositivo = cores_dispositivos.get(codigo_tipo, '#6C757D')
        dispositivos_usados = set()
        for veiculo in dados['distancias'].keys():
            dispositivos_usados.add(obter_nome_dispositivo(codigo_tipo))
        nome_dispositivo = " / ".join(sorted(dispositivos_usados))
        
        analises_html += f"""
                <div class="analise-bloco">
                    <h2 class="analise-titulo" style="color: {cor_dispositivo};">{nome_dispositivo}</h2>
                    
                    <!-- Análise de KM -->
                    <div class="secao">
                        <div class="secao-header">Análise de km</div>
                        <div class="conteudo-secao">
                            <div class="indicador">
                                <div class="indicador-titulo">Distância Percorrida (km)</div>
                                <div class="indicador-valor">{total_km:.2f}</div>
                            </div>
                            <div class="grafico-container">
                                <canvas id="chart{codigo_tipo}Km"></canvas>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Análise de Viagens -->
                    <div class="secao">
                        <div class="secao-header">Análise de contagem de viagens</div>
                        <div class="conteudo-secao">
                            <div class="indicador">
                                <div class="indicador-titulo">Total de viagens nesse período</div>
                                <div class="indicador-valor">{total_viagens}</div>
                            </div>
                            <div class="grafico-container">
                                <canvas id="chart{codigo_tipo}Viagens"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
        """
    
    # Gera legendas dinâmicas
    legendas_html = ""
    for codigo_tipo in dados_para_dashboard.keys():
        nome_dispositivo = obter_nome_dispositivo(codigo_tipo)
        cor_dispositivo = cores_dispositivos.get(codigo_tipo, '#6C757D')
        legendas_html += f"""
        
        """
    
    # Cria HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard de Análise de Frotas</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Saira:wght@600;700;800&display=swap" rel="stylesheet">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                min-height: 100vh;
                padding: 20px;
            }}
            
            .dashboard-container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            h1 {{
                text-align: center;
                color: #9B51E0;
                margin-bottom: 30px;
                font-size: 2.5em;
                font-family: 'Saira', sans-serif;
            }}
            
            .legenda {{
                padding: 15px;
                margin: 10px auto;
                border-radius: 8px;
                max-width: 1200px;
                border-left: 4px solid;
            }}
            
            .analises-container {{
                display: flex;
                gap: 30px;
                margin-bottom: 20px;
                flex-wrap: wrap;
                justify-content: center;
            }}
            
            .analise-bloco {{
                flex: 1;
                min-width: 500px;
                max-width: 650px;
                background: white;
                padding: 30px;
                border-radius: 20px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                border: 1px solid #e9ecef;
            }}
            
            .analise-titulo {{
                text-align: center;
                font-size: 1.8em;
                margin-bottom: 30px;
                font-family: 'Saira', sans-serif;
                font-weight: 700;
            }}
            
            .secao {{
                margin-bottom: 40px;
            }}
            
            .secao-header {{
                background: #9B51E0;
                color: white;
                padding: 15px 25px;
                border-radius: 10px;
                text-align: center;
                font-size: 1.3em;
                font-weight: 600;
                margin-bottom: 20px;
            }}
            
            .conteudo-secao {{
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            
            .indicador {{
                flex: 0 0 250px;
                text-align: center;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 15px;
            }}
            
            .indicador-titulo {{
                font-size: 0.9em;
                color: #666;
                margin-bottom: 10px;
            }}
            
            .indicador-valor {{
                font-size: 3em;
                font-weight: bold;
                color: #333;
            }}
            
            .grafico-container {{
                flex: 1;
                position: relative;
                height: 300px;
            }}
            
            @media (max-width: 900px) {{
                .conteudo-secao {{
                    flex-direction: column;
                }}
                
                .indicador {{
                    flex: 1;
                    width: 100%;
                }}
                
                .grafico-container {{
                    width: 100%;
                    height: 350px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <h1>📊 Parcial de Rodagem</h1>
            
            {legendas_html}
            
            <div class="analises-container">
                {analises_html}
            </div>
        </div>
        
        <script>
            // Configuração comum dos gráficos de donut
            const defaultOptions = {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            boxWidth: 15,
                            padding: 10,
                            font: {{
                                size: 11
                            }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(2);
                                
                                // Detecta se é gráfico de viagens pelo ID do canvas
                                const canvasId = context.chart.canvas.id;
                                const isViagemChart = canvasId.includes('Viagens');
                                
                                // Formata valor como inteiro para viagens, decimal para km
                                const formattedValue = isViagemChart ? Math.round(value).toString() : value.toFixed(2);
                                
                                return label + ': ' + formattedValue + ' (' + percentage + '%)';
                            }}
                        }}
                    }}
                }},
                cutout: '60%'
            }};
            
            // Dados dos gráficos por tipo (AGORA COM CORES PERSONALIZADAS)
            const chartDataPorTipo = {json.dumps(chart_data_por_tipo)};

            // Para o grupo de referência, garante valores inteiros nas viagens
            if (chartDataPorTipo['REF']) {{
                chartDataPorTipo['REF'].viagens.values = chartDataPorTipo['REF'].viagens.values.map(v => Math.trunc(v));
            }}
            
            // Cria gráficos dinamicamente para cada tipo
            Object.keys(chartDataPorTipo).forEach(codigoTipo => {{
                const dados = chartDataPorTipo[codigoTipo];
                
                // Gráfico de KM (USANDO CORES PERSONALIZADAS)
                if (dados.distancias.values.length > 0) {{
                    new Chart(document.getElementById('chart' + codigoTipo + 'Km'), {{
                        type: 'doughnut',
                        data: {{
                            labels: dados.distancias.labels,
                            datasets: [{{
                                data: dados.distancias.values,
                                backgroundColor: dados.distancias.cores,
                                borderWidth: 2,
                                borderColor: '#fff'
                            }}]
                        }},
                        options: defaultOptions
                    }});
                }}
                
                // Gráfico de Viagens (USANDO CORES PERSONALIZADAS)
                if (dados.viagens.values.length > 0) {{
                    new Chart(document.getElementById('chart' + codigoTipo + 'Viagens'), {{
                        type: 'doughnut',
                        data: {{
                            labels: dados.viagens.labels,
                            datasets: [{{
                                data: dados.viagens.values,
                                backgroundColor: dados.viagens.cores,
                                borderWidth: 2,
                                borderColor: '#fff'
                            }}]
                        }},
                        options: defaultOptions
                    }});
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Salva o arquivo
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Dashboard gerado com sucesso: {arquivo_saida}")
    print("="*60)

# ============================================
# EXECUÇÃO PRINCIPAL
# ============================================

if __name__ == "__main__":
    # Defina aqui o caminho da pasta com os CSVs
    PASTA_CSV = "C:\\Users\\Larissa Rocha\\Desktop\\coisas TM10\\Relatorio-comparativo\\logs"  # Altere para o caminho correto
    
    # Exemplos de uso:
    # 1) Modo pares de teste (default), teste TM-10 e referências TM-07 + TM-08
    gerar_dashboard_completo(PASTA_CSV, "dashboard_frotas.html", modo_relatorio='pares_de_teste', codigo_teste='802003', codigos_referencia=['83','385349'])
    
    # 2) Para executar em modo single para TM-08, use:
    # gerar_dashboard_completo(PASTA_CSV, "dashboard_tm08.html", modo_relatorio='single', codigo_teste='385349')