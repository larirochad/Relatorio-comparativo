"""
Script de Teste - Verifica se o sistema está configurado corretamente
Execute este script antes de rodar o Streamlit
"""

import sys
import os
from pathlib import Path

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_header(msg):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{msg:^60}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")


def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    print_header("VERIFICANDO DEPENDÊNCIAS")
    
    dependencias = {
        'streamlit': 'Streamlit',
        'pandas': 'Pandas',
        'plotly': 'Plotly',
        'folium': 'Folium',
        'streamlit_folium': 'Streamlit-Folium',
        'PIL': 'Pillow',
        'requests': 'Requests'
    }
    
    faltando = []
    
    for modulo, nome in dependencias.items():
        try:
            __import__(modulo)
            print_success(f"{nome} instalado")
        except ImportError:
            print_error(f"{nome} NÃO instalado")
            faltando.append(nome)
    
    if faltando:
        print_warning(f"\nFaltam {len(faltando)} dependências!")
        print_info("Execute: pip install -r requirements.txt")
        return False
    else:
        print_success("\n✨ Todas as dependências instaladas!")
        return True


def verificar_estrutura_pastas():
    """Verifica se a estrutura de pastas está correta"""
    print_header("VERIFICANDO ESTRUTURA DE PASTAS")
    
    base_dir = Path(__file__).parent
    
    pastas_necessarias = [
        'paginas',
        'utils',
        'dados',
        'htmls',
        'prints'
    ]
    
    todas_ok = True
    
    for pasta in pastas_necessarias:
        caminho = base_dir / pasta
        if caminho.exists() and caminho.is_dir():
            print_success(f"Pasta '{pasta}/' existe")
        else:
            print_error(f"Pasta '{pasta}/' NÃO existe")
            todas_ok = False
    
    return todas_ok


def verificar_arquivos_principais():
    """Verifica se os arquivos principais existem"""
    print_header("VERIFICANDO ARQUIVOS PRINCIPAIS")
    
    base_dir = Path(__file__).parent
    
    arquivos = {
        'app.py': 'Arquivo principal',
        'config.py': 'Configurações',
        'componentes.py': 'Componentes',
        'requirements.txt': 'Dependências',
        'comentarios.json': 'Comentários',
        'paginas/__init__.py': 'Init páginas',
        'paginas/dashboard_macro.py': 'Dashboard Macro',
        'paginas/detalhes_par.py': 'Detalhes Par',
        'paginas/admin_uploads.py': 'Admin Uploads',
        'utils/__init__.py': 'Init utils',
        'utils/gerar_configs.py': 'Gerar Configs',
        'utils/processamento.py': 'Processamento'
    }
    
    todos_ok = True
    
    for arquivo, descricao in arquivos.items():
        caminho = base_dir / arquivo
        if caminho.exists() and caminho.is_file():
            print_success(f"{descricao}: {arquivo}")
        else:
            print_error(f"{descricao}: {arquivo} NÃO existe")
            todos_ok = False
    
    return todos_ok


def verificar_dados():
    """Verifica se os dados CSV existem"""
    print_header("VERIFICANDO DADOS CSV")
    
    base_dir = Path(__file__).parent
    dados_dir = base_dir / 'dados'
    
    csvs_necessarios = [
        'analises_pares.csv',
        'matches_gps.csv',
        'matches_velocidade.csv',
        'matches_direcao.csv'
    ]
    
    todos_ok = True
    
    for csv in csvs_necessarios:
        caminho = dados_dir / csv
        if caminho.exists() and caminho.is_file():
            # Verifica tamanho
            tamanho = caminho.stat().st_size
            print_success(f"{csv} existe ({tamanho} bytes)")
            
            # Tenta carregar
            try:
                import pandas as pd
                df = pd.read_csv(caminho)
                print_info(f"  └─ {len(df)} registros, {len(df.columns)} colunas")
            except Exception as e:
                print_warning(f"  └─ Erro ao carregar: {str(e)}")
        else:
            print_error(f"{csv} NÃO existe")
            todos_ok = False
    
    return todos_ok


def testar_imports():
    """Testa se os imports do sistema funcionam"""
    print_header("TESTANDO IMPORTS DO SISTEMA")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        from config import DASHBOARDS, CORES
        print_success("config.py importado com sucesso")
        print_info(f"  └─ {len(DASHBOARDS)} dashboards configurados")
        
        from componentes import carregar_csv, tabela_clicavel_universal
        print_success("componentes.py importado com sucesso")
        
        from paginas.dashboard_macro import pagina_macro
        print_success("dashboard_macro.py importado com sucesso")
        
        from paginas.detalhes_par import pagina_detalhes
        print_success("detalhes_par.py importado com sucesso")
        
        from paginas.admin_uploads import pagina_admin
        print_success("admin_uploads.py importado com sucesso")
        
        from utils.processamento import calcular_estatisticas_basicas
        print_success("processamento.py importado com sucesso")
        
        from utils.gerar_configs import gerar_estrutura_pastas
        print_success("gerar_configs.py importado com sucesso")
        
        return True
        
    except Exception as e:
        print_error(f"Erro ao importar: {str(e)}")
        return False


def verificar_streamlit():
    """Verifica versão do Streamlit"""
    print_header("VERIFICANDO STREAMLIT")
    
    try:
        import streamlit as st
        versao = st.__version__
        print_success(f"Streamlit versão {versao}")
        
        # Verifica se é versão compatível
        versao_parts = versao.split('.')
        versao_major = int(versao_parts[0])
        versao_minor = int(versao_parts[1])
        
        if versao_major >= 1 and versao_minor >= 28:
            print_success("Versão compatível (>= 1.28.0)")
            return True
        else:
            print_warning("Versão pode ser incompatível. Recomendado: >= 1.28.0")
            return True
            
    except Exception as e:
        print_error(f"Erro ao verificar Streamlit: {str(e)}")
        return False


def main():
    """Função principal"""
    print(f"\n{Colors.BLUE}{'*'*60}{Colors.END}")
    print(f"{Colors.BLUE}*{' '*58}*{Colors.END}")
    print(f"{Colors.BLUE}*{'TESTE DE INSTALAÇÃO - SISTEMA DE ANÁLISE DE PARES':^58}*{Colors.END}")
    print(f"{Colors.BLUE}*{' '*58}*{Colors.END}")
    print(f"{Colors.BLUE}{'*'*60}{Colors.END}\n")
    
    resultados = {
        'Dependências': verificar_dependencias(),
        'Estrutura de Pastas': verificar_estrutura_pastas(),
        'Arquivos Principais': verificar_arquivos_principais(),
        'Dados CSV': verificar_dados(),
        'Imports do Sistema': testar_imports(),
        'Streamlit': verificar_streamlit()
    }
    
    # Resumo final
    print_header("RESUMO FINAL")
    
    total = len(resultados)
    passou = sum(1 for v in resultados.values() if v)
    
    for teste, resultado in resultados.items():
        if resultado:
            print_success(f"{teste}: OK")
        else:
            print_error(f"{teste}: FALHOU")
    
    print(f"\n{Colors.BLUE}{'─'*60}{Colors.END}\n")
    
    if passou == total:
        print(f"{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}{'🎉 TODOS OS TESTES PASSARAM! 🎉':^60}{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
        print_info("Sistema pronto para uso!")
        print_info("Execute: streamlit run app.py")
        return 0
    else:
        print(f"{Colors.RED}{'='*60}{Colors.END}")
        print(f"{Colors.RED}{f'❌ {total - passou} TESTE(S) FALHARAM ❌':^60}{Colors.END}")
        print(f"{Colors.RED}{'='*60}{Colors.END}\n")
        print_warning("Corrija os problemas antes de executar o sistema")
        print_info("Consulte o README.md para mais informações")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

