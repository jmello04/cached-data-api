# Guia de Contribuição

Obrigado por considerar contribuir com o **Cached Data API**! Este guia descreve o processo para reportar bugs, sugerir melhorias e submeter pull requests.

---

## Pré-requisitos

- Python 3.12+
- Docker e Docker Compose v2
- Git configurado localmente

---

## Configurando o Ambiente

```bash
# 1. Fork e clone o repositório
git clone https://github.com/jmello04/cached-data-api.git
cd cached-data-api

# 2. Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Copie as variáveis de ambiente
cp .env.example .env

# 5. Suba a infraestrutura e popule o banco
make up && make seed
```

---

## Fluxo de Trabalho

1. **Abra uma issue** descrevendo o que pretende mudar antes de começar
2. **Crie uma branch** com nome descritivo:
   ```bash
   git checkout -b fix/cache-decorator-headers
   git checkout -b feat/cache-warmup-endpoint
   ```
3. **Faça as alterações** seguindo os padrões do projeto
4. **Execute os testes** e confirme que todos passam:
   ```bash
   make test
   ```
5. **Faça commits** seguindo o padrão [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: adiciona endpoint de warm-up de cache
   fix: corrige cálculo de hit_rate quando total é zero
   docs: atualiza exemplos de benchmark no README
   refactor: extrai lógica de chave para módulo separado
   test: adiciona casos de borda para cache miss
   ```
6. **Abra o Pull Request** preenchendo o template

---

## Padrões de Código

- Tipagem estática em todas as funções (parâmetros e retorno)
- Nomes de variáveis e funções em `snake_case`
- Nomes de classes em `PascalCase`
- Sem comentários redundantes — o código deve ser autoexplicativo
- Sem prints em código de produção — use logs estruturados

---

## Executando os Testes

```bash
# Todos os testes
make test

# Com verbose e rastreamento de erros
pytest -v --tb=long

# Apenas um arquivo
pytest tests/test_cache.py -v
```

---

## Dúvidas

Abra uma [issue](https://github.com/jmello04/cached-data-api/issues) com a label `question`.
