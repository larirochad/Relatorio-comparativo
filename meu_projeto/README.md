# 🚗 Sistema de Análise de Pares - TM10 vs TM-07/TM-08

Sistema completo de dashboard com Streamlit para análise comparativa de dispositivos de rastreamento.

## 📋 Características

- **Dashboard Macro**: Visão geral de todos os pares analisados
- **Análise Detalhada**: Análise específica por tipo (GPS, Velocidade, Direção)
- **Detalhes de Par**: Visão completa de um par específico com todas as análises
- **Sistema de Comentários**: Adicione observações e anotações
- **Upload de Arquivos**: Sistema completo de upload e gerenciamento
- **Galeria de Prints**: Visualize e gerencie todas as imagens
- **Exportação de Dados**: Exporte relatórios e dados filtrados

## 🚀 Instalação

### 1. Clone o Repositório (ou baixe os arquivos)

```bash
cd meu_projeto
```

### 2. Instale as Dependências

```bash
pip install -r requirements.txt
```

**Dependências principais:**
- streamlit >= 1.28.0
- pandas >= 2.0.0
- plotly >= 5.17.0
- folium >= 0.14.0
- streamlit-folium >= 0.15.0
- pillow >= 10.0.0

### 3. (Opcional) Configure o Ambiente

Execute o script de setup para criar estrutura de pastas:

```bash
python utils/gerar_configs.py
```

## ▶️ Executar o Sistema

```bash
streamlit run app.py
```

O sistema abrirá automaticamente no navegador em `http://localhost:8501`

## 📁 Estrutura do Projeto

```
meu_projeto/
├── app.py                      # Arquivo principal
├── config.py                   # Configurações centralizadas
├── componentes.py              # Componentes reutilizáveis
├── requirements.txt            # Dependências Python
├── comentarios.json            # Armazenamento de comentários
├── README.md                   # Este arquivo
│
├── paginas/                    # Módulos de páginas
│   ├── __init__.py
│   ├── dashboard_macro.py      # Dashboard geral
│   ├── detalhes_par.py         # Detalhes de pares
│   └── admin_uploads.py        # Administração de uploads
│
├── utils/                      # Utilitários
│   ├── __init__.py
│   ├── gerar_configs.py        # Setup inicial
│   └── processamento.py        # Processamento de dados
│
├── dados/                      # Dados CSV
│   ├── analises_pares.csv      # Dados principais dos pares
│   ├── matches_gps.csv         # Matches GPS
│   ├── matches_velocidade.csv  # Matches velocidade
│   └── matches_direcao.csv     # Matches direção
│
├── htmls/                      # HTMLs gerados externamente
├── prints/                     # Imagens e prints organizados
│   ├── gps/
│   ├── velocidade/
│   ├── direcao/
│   └── metadados.json
```

## 🎯 Como Usar

### Dashboard Macro

1. Selecione "📊 Dashboard Macro" no menu lateral
2. Visualize KPIs e gráficos gerais
3. Use filtros para refinar a busca
4. Clique em "📋 Detalhes" em qualquer par para análise completa

### Análise Detalhada

1. Selecione "🔍 Análise Detalhada" no menu lateral
2. Escolha o tipo: GPS, Velocidade ou Direção
3. Navegue pela tabela de matches
4. Clique em "📋 Ver Detalhes" para informações completas
5. Visualize prints, mapas e adicione comentários

### Detalhes do Par

Ao clicar em um par no Dashboard Macro, você acessa:

**Tabs disponíveis:**
- **🗺️ GPS**: Análise de dispersão GPS, prints e mapa
- **🚗 Velocidade**: Gráficos comparativos e discrepâncias
- **🧭 Direção**: Análise de orientação e manobras
- **📊 Dados Brutos**: CSV completo filtrado
- **📄 Dashboard HTML**: HTML completo gerado externamente
- **💬 Observações Gerais**: Comentários e anotações

### Admin - Uploads

1. Selecione "🔧 Admin - Uploads" no menu lateral
2. Escolha entre:
   - **Upload Individual**: Um arquivo por vez com controle total
   - **Upload em Massa**: Múltiplos arquivos simultaneamente
   - **Upload via URL**: Baixe de Google Drive, Dropbox, etc
   - **Galeria**: Visualize e gerencie todos os arquivos

## 📊 Formato dos Dados

### analises_pares.csv

```csv
par_id,placa,imei_tm10,imei_ref,tipo_ref,problema_gps,problema_vel,problema_dir,observacoes_gerais,qt_viagens,distancia_km,inicio_analise
1,ENG_004,867488068383602,4675644778,TM-07,False,True,False,Observação aqui,49,2.4,2025-09-29 14:20:00
```

### matches_gps.csv

```csv
match_id,par_id,datetime,lat,lon,discrepancia,teste_valor,ref_valor,diferenca,velocidade,direcao,observacao,problema
T1_37,1,2025-10-06 19:55:53,-9.546707,-35.729989,6.51,0,0,0,0.0,329.0,Observação,True
```

### matches_velocidade.csv

```csv
match_id,par_id,datetime,teste,referencia,diferenca,lat,lon,observacao,problema
V1_12,1,2025-10-06 08:22:15,45.5,23.2,22.3,-9.546707,-35.729989,Observação,True
```

### matches_direcao.csv

```csv
match_id,par_id,datetime,teste,referencia,diferenca,lat,lon,velocidade,observacao,problema
D2_08,2,2025-10-05 09:20:18,185.5,92.3,93.2,-9.546707,-35.729989,15.5,Observação,True
```

## ⚙️ Configuração

Edite `config.py` para personalizar:

- **Cores**: Paleta de cores do dashboard
- **Dashboards**: Adicione novos tipos de análise
- **Thresholds**: Limites para identificação de problemas
- **Visualização**: Configurações de display
- **Caminhos**: Diretórios de dados e arquivos

### Exemplo: Adicionar Novo Dashboard

```python
DASHBOARDS = {
    "novo_tipo": {
        "nome": "Minha Análise",
        "icone": "🎯",
        "csv": os.path.join(DADOS_DIR, "meus_dados.csv"),
        "colunas_principais": ["id", "valor"],
        "coluna_id": "id",
        "pasta_prints": os.path.join(PRINTS_DIR, "novo_tipo"),
        "tem_mapa": False,
        "cor_problema": CORES["aviso"],
        "descricao": "Descrição da análise",
        "metricas": ["metrica1", "metrica2"],
        "filtros": ["filtro1", "filtro2"]
    }
}
```

## 🎨 Personalização

### Cores

Modifique as cores em `config.py`:

```python
CORES = {
    "sucesso": "#28a745",
    "erro": "#dc3545",
    "aviso": "#ffc107",
    "info": "#17a2b8",
    # ...
}
```

### Estilos CSS

Edite a seção de CSS em `app.py` para personalizar o visual.

## 📝 Sistema de Comentários

Os comentários são salvos em `comentarios.json` com a estrutura:

```json
{
  "comentarios": [
    {
      "tipo": "match_id",
      "id": "T1_37",
      "texto": "Observação importante",
      "autor": "Nome",
      "categoria": "Problema",
      "data": "2025-10-24 10:00:00",
      "timestamp": 1729767600.0
    }
  ],
  "metadata": {
    "versao": "1.0",
    "ultima_atualizacao": "2025-10-24 10:00:00"
  }
}
```

## 🖼️ Organização de Prints

Os prints são organizados automaticamente em:

```
prints/
├── gps/
│   ├── 1/              # Par ID 1
│   │   ├── T1_37.png
│   │   └── T1_63.png
│   └── 2/              # Par ID 2
├── velocidade/
│   └── 1/
└── direcao/
    └── 2/
```

Metadados são salvos em `prints/metadados.json`.

## 🔒 Segurança e Backup

### Backup Automático

Os comentários são salvos automaticamente. Faça backup regular de:
- `comentarios.json`
- `prints/metadados.json`
- Pastas de dados e prints

### .gitignore

O sistema inclui `.gitignore` apropriado que:
- Ignora dados CSV sensíveis
- Ignora imagens (podem ser grandes)
- Mantém estrutura de pastas
- Preserva arquivos de configuração

## 🐛 Solução de Problemas

### Erro ao carregar dados

```bash
# Verifique se os CSVs existem
ls dados/

# Verifique o formato dos CSVs
head dados/analises_pares.csv
```

### Erro de dependências

```bash
# Reinstale as dependências
pip install -r requirements.txt --force-reinstall
```

### Streamlit não inicia

```bash
# Verifique a instalação do Streamlit
streamlit --version

# Limpe o cache
streamlit cache clear
```

### Imagens não aparecem

- Verifique se os caminhos em `config.py` estão corretos
- Confirme que as imagens estão nas pastas corretas
- Verifique as extensões dos arquivos

## 📚 Documentação Técnica

### Componentes Principais

**carregar_csv(caminho)**: Carrega CSV com cache
**tabela_clicavel_universal(config)**: Cria tabela interativa
**mostrar_detalhes_universais(config, registro)**: Mostra detalhes
**mostrar_prints_automatico(config, id)**: Busca e exibe prints
**mostrar_mapa_automatico(lat, lon, titulo)**: Cria mapa interativo
**criar_grafico_comparativo(dados1, dados2, titulo)**: Gráfico comparativo
**mostrar_sistema_comentarios(tipo, id)**: Sistema de comentários

### Session State

O sistema usa `st.session_state` para navegação:
- `modo_visualizacao`: Modo atual ('macro', 'detalhes', etc)
- `par_selecionado`: Par atualmente selecionado
- `registro_selecionado`: Registro em detalhes
- `config_selecionada`: Configuração do dashboard atual

## 🤝 Contribuindo

Para adicionar funcionalidades:

1. Crie novos componentes em `componentes.py`
2. Adicione novas páginas em `paginas/`
3. Configure em `config.py`
4. Importe e use em `app.py`

## 📄 Licença

Este projeto é proprietário. Todos os direitos reservados.

## 📧 Suporte

Para suporte e dúvidas:
- Email: sistema@analise.com
- Documentação: Disponível no menu "About" da aplicação

## 🎉 Recursos Extras

- ✅ Cache automático de dados para performance
- ✅ Responsivo (funciona em diferentes tamanhos de tela)
- ✅ Exportação de relatórios
- ✅ Sistema de busca global
- ✅ Filtros avançados
- ✅ Validação de dados
- ✅ Mensagens de feedback
- ✅ Loading states
- ✅ Design moderno e intuitivo

## 🔄 Atualizações

**v1.0 (2025-10-24)**
- Versão inicial
- Dashboard macro
- Análise detalhada (GPS, Velocidade, Direção)
- Sistema de comentários
- Upload de arquivos
- Galeria de prints

---

**Desenvolvido com ❤️ usando Streamlit**

