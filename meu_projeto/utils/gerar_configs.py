"""
Utilitário para gerar arquivos de configuração automaticamente
"""

import os
import json


def gerar_estrutura_pastas(base_dir):
    """
    Cria estrutura de pastas se não existir
    
    Args:
        base_dir: Diretório base do projeto
    """
    pastas = [
        'dados',
        'htmls',
        'prints',
        'prints/gps',
        'prints/velocidade',
        'prints/direcao',
        'prints/hodometro',
        'prints/eventos',
        'prints/satelites',
        'prints/conexao',
        'prints/outros'
    ]
    
    for pasta in pastas:
        caminho = os.path.join(base_dir, pasta)
        os.makedirs(caminho, exist_ok=True)
        
        # Cria .gitkeep se pasta vazia
        gitkeep = os.path.join(caminho, '.gitkeep')
        if not os.path.exists(gitkeep):
            with open(gitkeep, 'w') as f:
                f.write(f"# Pasta para {pasta}\n")
    
    print(f"✅ Estrutura de pastas criada em: {base_dir}")


def gerar_comentarios_inicial(caminho):
    """
    Gera arquivo de comentários inicial
    
    Args:
        caminho: Caminho do arquivo comentarios.json
    """
    if not os.path.exists(caminho):
        estrutura = {
            "comentarios": [],
            "metadata": {
                "versao": "1.0",
                "ultima_atualizacao": ""
            }
        }
        
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(estrutura, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Arquivo de comentários criado: {caminho}")


def gerar_gitignore(base_dir):
    """
    Gera arquivo .gitignore apropriado
    
    Args:
        base_dir: Diretório base
    """
    conteudo = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Streamlit
.streamlit/

# Dados sensíveis
*.csv
*.xlsx
*.json
!comentarios.json

# Imagens (muito pesadas)
*.png
*.jpg
*.jpeg
*.gif

# HTMLs gerados
htmls/*.html

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Sistema
.DS_Store
Thumbs.db
"""
    
    caminho = os.path.join(base_dir, '.gitignore')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"✅ .gitignore criado: {caminho}")


def verificar_dependencias():
    """
    Verifica se todas as dependências estão instaladas
    
    Returns:
        Lista de pacotes faltando
    """
    pacotes_necessarios = [
        'streamlit',
        'pandas',
        'plotly',
        'folium',
        'streamlit_folium',
        'PIL',
        'requests'
    ]
    
    faltando = []
    
    for pacote in pacotes_necessarios:
        try:
            __import__(pacote)
        except ImportError:
            faltando.append(pacote)
    
    return faltando


if __name__ == "__main__":
    # Executa setup inicial
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("🚀 Iniciando setup do projeto...")
    print()
    
    gerar_estrutura_pastas(base)
    gerar_comentarios_inicial(os.path.join(base, 'comentarios.json'))
    gerar_gitignore(base)
    
    print()
    print("🔍 Verificando dependências...")
    faltando = verificar_dependencias()
    
    if faltando:
        print(f"⚠️  Pacotes faltando: {', '.join(faltando)}")
        print("Execute: pip install -r requirements.txt")
    else:
        print("✅ Todas as dependências instaladas!")
    
    print()
    print("✨ Setup concluído! Execute: streamlit run app.py")

