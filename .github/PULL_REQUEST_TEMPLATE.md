# Pull Request

## Tipo de Mudança

- [ ] Bug fix (correção sem quebra de compatibilidade)
- [ ] Nova funcionalidade (adição sem quebra de compatibilidade)
- [ ] Breaking change (correção ou funcionalidade que altera comportamento existente)
- [ ] Refatoração (sem mudança de comportamento)
- [ ] Documentação

## Descrição

Descreva de forma objetiva o que foi alterado e por quê.

## Issue Relacionada

Fixes #(número da issue)

## Como Testar

Descreva os passos para validar as mudanças:

1. Suba o ambiente: `make up && make seed`
2. Execute: `curl http://localhost:8000/...`
3. Verifique: ...

## Checklist

- [ ] O código segue os padrões do projeto
- [ ] Os testes existentes continuam passando (`make test`)
- [ ] Novos testes foram adicionados para cobrir as mudanças
- [ ] A documentação foi atualizada (README, docstrings, etc.)
- [ ] Não há secrets, credenciais ou dados sensíveis no código
