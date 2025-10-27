# 🚀 Início Rápido

Guia rápido para executar o sistema em 5 minutos!

## ✅ Checklist Pré-Execução

### 1. Verifique os Arquivos

```bash
# No diretório meu_projeto/
ls
```

Você deve ver:
- ✅ `app.py` (arquivo principal)
- ✅ `config.py` (configurações)
- ✅ `componentes.py` (componentes)
- ✅ `requirements.txt` (dependências)
- ✅ `comentarios.json` (comentários)
- ✅ Pastas: `paginas/`, `utils/`, `dados/`, `htmls/`, `prints/`

### 2. Verifique os Dados

```bash
ls dados/
```

Deve conter:
- ✅ `analises_pares.csv`
- ✅ `matches_gps.csv`
- ✅ `matches_velocidade.csv`
- ✅ `matches_direcao.csv`

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

**Dependências instaladas:**
- Streamlit
- Pandas
- Plotly
- Folium
- Pillow
- Requests

## ▶️ Executar

```bash
streamlit run app.py
```

O navegador abrirá automaticamente em: `http://localhost:8501`

## 🎯 Primeira Navegação

### Dashboard Macro (Página Inicial)

1. O dashboard macro abre automaticamente
2. Você verá:
   - 📊 KPIs no topo (Total de Pares, Problemas, etc)
   - 📈 Gráficos de análise
   - 📋 Lista de pares

3. **Experimente:**
   - Use os filtros para buscar pares
   - Clique em "📋 Detalhes" em qualquer par
   - Exporte dados em CSV

### Análise Detalhada de um Par

1. Ao clicar em um par, você verá 6 tabs:
   - **🗺️ GPS**: Análise de localização
   - **🚗 Velocidade**: Comparativo de velocidades
   - **🧭 Direção**: Análise de direções
   - **📊 Dados Brutos**: Tabelas completas
   - **📄 Dashboard HTML**: HTMLs externos
   - **💬 Observações**: Comentários

2. **Em cada tab você pode:**
   - Ver prints relacionados
   - Visualizar mapas (GPS)
   - Adicionar comentários
   - Baixar dados

### Análise por Tipo (GPS/Velocidade/Direção)

1. No menu lateral, selecione "🔍 Análise Detalhada"
2. Escolha o tipo: GPS, Velocidade ou Direção
3. Navegue pelos matches problemáticos
4. Clique para ver detalhes completos

### Upload de Arquivos

1. No menu lateral, selecione "🔧 Admin - Uploads"
2. Escolha uma das 4 tabs:
   - **Upload Individual**: Um arquivo por vez
   - **Upload em Massa**: Vários arquivos
   - **Upload via URL**: De links externos
   - **Galeria**: Visualize tudo

## 🎨 Personalizar

### Mudar Cores

Edite `config.py`:

```python
CORES = {
    "sucesso": "#28a745",    # Verde
    "erro": "#dc3545",       # Vermelho
    "aviso": "#ffc107",      # Amarelo
    "info": "#17a2b8",       # Azul
    # Personalize aqui!
}
```

### Adicionar Seus Dados

Substitua os CSVs em `dados/` pelos seus dados reais.

**Importante:** Mantenha os nomes das colunas!

### Adicionar Prints

Coloque suas imagens em:
```
prints/
├── gps/
│   └── {par_id}/
├── velocidade/
│   └── {par_id}/
└── direcao/
    └── {par_id}/
```

## 💡 Dicas

### Performance

- O sistema usa cache automático
- Dados são carregados apenas uma vez
- Use o botão "R" para recarregar se necessário

### Navegação

- Use a sidebar para mudar de modo
- O botão "◀️ Voltar" retorna à lista
- Session state mantém suas seleções

### Comentários

- Comentários são salvos em `comentarios.json`
- Faça backup regularmente!
- Use categorias para organizar

### Filtros

- Todos os dashboards têm filtros
- Use busca por texto para encontrar rapidamente
- Combine múltiplos filtros

## 🐛 Problemas Comuns

### "Module not found"

```bash
pip install -r requirements.txt
```

### "File not found"

Verifique se está no diretório correto:
```bash
cd meu_projeto
```

### Dados não aparecem

1. Verifique se os CSVs existem em `dados/`
2. Clique no "R" no canto superior direito
3. Limpe o cache: Configurações > Clear Cache

### Imagens não carregam

1. Verifique se as imagens estão em `prints/categoria/par_id/`
2. Extensões suportadas: png, jpg, jpeg, gif, bmp, webp
3. Verifique permissões de arquivo

## 📚 Recursos

### Atalhos do Streamlit

- **R**: Recarregar aplicação
- **Ctrl+K**: Abrir command palette
- **Ctrl+Shift+R**: Limpar cache e recarregar

### Menu Hamburger (☰)

No canto superior direito:
- Settings: Configurações
- Print: Imprimir página
- Record screencast: Gravar tela
- About: Sobre o sistema

## 🎓 Próximos Passos

1. **Explore todos os modos** no menu lateral
2. **Adicione seus dados** reais
3. **Faça upload de prints** das suas análises
4. **Use o sistema de comentários** para documentar
5. **Exporte relatórios** para compartilhar

## 📞 Ajuda

- 📖 Leia o `README.md` completo
- ℹ️ Use o menu "About" no dashboard
- 🔍 Consulte os expandables "Como Usar" na sidebar

## ✨ Dicas Avançadas

### Executar em Rede

```bash
streamlit run app.py --server.address 0.0.0.0
```

Acesse de outros computadores: `http://SEU_IP:8501`

### Mudar Porta

```bash
streamlit run app.py --server.port 8502
```

### Modo de Desenvolvimento

```bash
streamlit run app.py --server.runOnSave true
```

Auto-reload ao salvar arquivos.

### Desabilitar Telemetria

Crie `.streamlit/config.toml`:

```toml
[browser]
gatherUsageStats = false
```

## 🎉 Pronto!

Seu sistema está 100% funcional!

Explore, customize e aproveite! 🚀

---

**Dúvidas?** Consulte o README.md ou a documentação no menu About.

