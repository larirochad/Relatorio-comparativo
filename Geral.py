import os
import sys
import shutil
from datetime import datetime
import pandas as pd

# Importa suas funções principais de análise
from filtro import executar_analise_completa
from Dados_parcial import gerar_dashboard_completo

class Analises_geral:
    
    def __init__(self, pasta_logs='logs', pasta_relatorios='relatorios'):
        self.pasta_logs = pasta_logs
        self.pasta_relatorios = pasta_relatorios
        self.data_execucao = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Define os pares fixos de análise conforme planilha
        self.pares_analise = [
            # Par 1
            {'nome': 'Par_01_ENG_146_vs_A474999', 'csv1': 'ENG_146.csv', 'csv2': 'A474999.csv', 'problema': 'TM-08'},
            
            # Par 4
            {'nome': 'Par_04_ENG_048_vs_AYL2486', 'csv1': 'ENG_048.csv', 'csv2': 'AYL2486.csv', 'problema': 'TM-07'},
            
            # Par 5
            {'nome': 'Par_05_ENG_046_vs_JAP8F64', 'csv1': 'ENG_046.csv', 'csv2': 'JAP8F64.csv', 'problema': 'TM-07'},
            
            # Par 6
            {'nome': 'Par_06_ENG_042_vs_A474038', 'csv1': 'ENG_042.csv', 'csv2': 'A474038.csv', 'problema': 'TM-08'},
            
            # Par 7
            {'nome': 'Par_07_ENG_039_vs_RHH4B26', 'csv1': 'ENG_039.csv', 'csv2': 'RHH4B26.csv', 'problema': 'TM-07'},
            
            # Par 8
            {'nome': 'Par_08_ENG_004_vs_BDB3D78', 'csv1': 'ENG_004.csv', 'csv2': 'BDB3D78.csv', 'problema': 'TM-07'},
            
            # Par 10
            {'nome': 'Par_10_ENG_014_vs_TYA9C79', 'csv1': 'ENG_014.csv', 'csv2': 'TYA9C79.csv', 'problema': 'TM-08'},
            
            # Par Alexandre (separado)
            {'nome': 'Par_Alexandre_ENG_009_vs_BAA1364', 'csv1': 'ENG_009.csv', 'csv2': 'BAA1364.csv', 'problema': 'TM-08'},
        ]
        
        self.log_execucao = []
        
    def criar_estrutura_pastas(self):
        """Cria estrutura de pastas para organizar os relatórios"""
        pasta_data = os.path.join(self.pasta_relatorios, self.data_execucao)
        os.makedirs(pasta_data, exist_ok=True)
        return pasta_data
    
    def verificar_csvs_existem(self, csv1, csv2):
        """Verifica se os CSVs do par existem na pasta logs"""
        path1 = os.path.join(self.pasta_logs, csv1)
        path2 = os.path.join(self.pasta_logs, csv2)
        
        existe1 = os.path.exists(path1)
        existe2 = os.path.exists(path2)
        
        if not existe1:
            self.log_execucao.append(f"⚠️  Arquivo não encontrado: {csv1}")
        if not existe2:
            self.log_execucao.append(f"⚠️  Arquivo não encontrado: {csv2}")
            
        return existe1 and existe2
    
    def processar_par(self, par, pasta_destino):
        """Processa um par de CSVs e salva o HTML comparativo gerado"""
        nome_par = par['nome']
        csv1 = par['csv1']
        csv2 = par['csv2']
        problema = par.get('problema', 'N/A')
        
        print(f"\n{'='*60}")
        print(f"🔄 Processando: {nome_par}")
        print(f"   Problema: {problema}")
        print(f"{'='*60}")
        
        # Verifica se os arquivos existem
        if not self.verificar_csvs_existem(csv1, csv2):
            self.log_execucao.append(f"❌ Falha: {nome_par} - Arquivos não encontrados")
            return False
        
        # Caminhos completos
        path1 = os.path.join(self.pasta_logs, csv1)
        path2 = os.path.join(self.pasta_logs, csv2)
        
        try:
            # Executa a análise comparativa completa
            print(f"📊 Analisando comparativo: {csv1} vs {csv2}...")
            executar_analise_completa(
                tipo='todas',
                input1=path1,
                input2=path2
            )
            
            # Move o dashboard comparativo para a pasta organizada
            html_origem = 'dashboard_final.html'
            if os.path.exists(html_origem):
                html_destino = os.path.join(pasta_destino, f'{nome_par}.html')
                shutil.move(html_origem, html_destino)
                print(f"📁 HTML salvo em: {html_destino}")
            else:
                print(f"⚠️  HTML não encontrado: {html_origem}")
            
            self.log_execucao.append(f"✅ Sucesso: {nome_par}")
            print(f"✅ Análise comparativa concluída: {nome_par}")
            return True
            
        except Exception as e:
            self.log_execucao.append(f"❌ Erro em {nome_par}: {str(e)}")
            print(f"❌ Erro ao processar {nome_par}: {str(e)}")
            return False
    
    def gerar_dashboard_frotas_geral(self, pasta_destino):
        """Gera um único dashboard de frotas com TODOS os CSVs da pasta logs"""
        print(f"\n{'='*60}")
        print(f"🚗 Gerando Dashboard de Frotas Geral")
        print(f"{'='*60}")
        
        try:
            # Define o arquivo de saída na pasta de relatórios
            html_frotas_geral = os.path.join(pasta_destino, 'dashboard_frotas_geral.html')
            
            # Gera o dashboard de frotas com TODOS os CSVs da pasta logs
            print(f"📊 Processando todos os CSVs da pasta: {self.pasta_logs}")
            
            gerar_dashboard_completo(
                pasta_csv=self.pasta_logs,
                arquivo_saida=html_frotas_geral,
                modo_relatorio='pares_de_teste',
                codigo_teste='802003',  # TM-10
                codigos_referencia=['83', '385349']  # TM-07 e TM-08
            )
            
            print(f"✅ Dashboard de frotas geral salvo: {html_frotas_geral}")
            self.log_execucao.append(f"✅ Dashboard de frotas geral gerado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao gerar dashboard de frotas geral: {str(e)}")
            self.log_execucao.append(f"❌ Erro no dashboard de frotas geral: {str(e)}")
            return False
        """Move e renomeia o HTML gerado para a pasta de destino"""
        # Assumindo que o HTML comparativo é gerado como 'dashboard_final.html' na raiz
        html_origem = 'dashboard_final.html'
        
        if os.path.exists(html_origem):
            # Renomeia com o nome do par, sufixo opcional
            if sufixo:
                html_destino = os.path.join(pasta_destino, f'{nome_par}{sufixo}.html')
            else:
                html_destino = os.path.join(pasta_destino, f'{nome_par}.html')
            shutil.move(html_origem, html_destino)
            print(f"📁 HTML salvo em: {html_destino}")
        else:
            print(f"⚠️  HTML não encontrado: {html_origem}")
    
    def gerar_dashboard_frotas_geral(self, pasta_destino):
        """Gera um único dashboard de frotas com TODOS os CSVs da pasta logs"""
        print(f"\n{'='*60}")
        print(f"🚗 Gerando Dashboard de Frotas Geral")
        print(f"{'='*60}")
        
        try:
            # Define o arquivo de saída na pasta de relatórios
            html_frotas_geral = os.path.join(pasta_destino, 'dashboard_frotas_geral.html')
            
            # Gera o dashboard de frotas com TODOS os CSVs da pasta logs
            print(f"📊 Processando todos os CSVs da pasta: {self.pasta_logs}")
            
            # Chama a função importada (não é método da classe!)
            gerar_dashboard_completo(
                pasta_csv=self.pasta_logs,
                arquivo_saida=html_frotas_geral,
                modo_relatorio='pares_de_teste',
                codigo_teste='802003',  # TM-10
                codigos_referencia=['83', '385349']  # TM-07 e TM-08
            )
            
            print(f"✅ Dashboard de frotas geral salvo: {html_frotas_geral}")
            self.log_execucao.append(f"✅ Dashboard de frotas geral gerado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao gerar dashboard de frotas geral: {str(e)}")
            self.log_execucao.append(f"❌ Erro no dashboard de frotas geral: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def gerar_relatorio_execucao(self, pasta_destino):
        """Gera um relatório de execução com os resultados"""
        relatorio_path = os.path.join(pasta_destino, '_log_execucao.txt')
        
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            f.write(f"RELATÓRIO DE EXECUÇÃO\n")
            f.write(f"Data: {self.data_execucao}\n")
            f.write(f"{'='*60}\n\n")
            
            for log in self.log_execucao:
                f.write(f"{log}\n")
            
            f.write(f"\n{'='*60}\n")
            f.write(f"Total de pares processados: {len(self.pares_analise)}\n")
            
            sucessos = sum(1 for log in self.log_execucao if '✅' in log)
            falhas = sum(1 for log in self.log_execucao if '❌' in log)
            
            f.write(f"Sucessos: {sucessos}\n")
            f.write(f"Falhas: {falhas}\n")
        
        print(f"\n📋 Log de execução salvo em: {relatorio_path}")
    
    def executar_todas_analises(self):
        """Executa todas as análises dos pares definidos"""
        print(f"\n🚀 Iniciando processamento em lote")
        print(f"📅 Data/Hora: {self.data_execucao}")
        print(f"📂 Pasta de logs: {self.pasta_logs}")
        print(f"📊 Total de pares: {len(self.pares_analise)}\n")
        
        # Cria estrutura de pastas
        pasta_destino = self.criar_estrutura_pastas()
        
        # Processa cada par (análises comparativas)
        for i, par in enumerate(self.pares_analise, 1):
            print(f"\n[{i}/{len(self.pares_analise)}]")
            self.processar_par(par, pasta_destino)
        
        # Gera dashboard de frotas GERAL (uma única vez com todos os CSVs)
        print(f"\n{'='*60}")
        print(f"📊 Gerando análise geral de frotas...")
        print(f"{'='*60}")
        self.gerar_dashboard_frotas_geral(pasta_destino)
        
        # Gera relatório final
        self.gerar_relatorio_execucao(pasta_destino)
        
        print(f"\n{'='*60}")
        print(f"🎉 Processamento concluído!")
        print(f"📁 Relatórios salvos em: {pasta_destino}")
        print(f"{'='*60}\n")


def main():
    """Função principal para execução"""

    Gerar_analises_geral = Analises_geral(
        pasta_logs='logs',
        pasta_relatorios='relatorios'
    )
    
    # Executa todas as análises
    Gerar_analises_geral.executar_todas_analises()


if __name__ == "__main__":
    main()