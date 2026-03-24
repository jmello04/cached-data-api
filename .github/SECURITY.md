# Política de Segurança

## Versões Suportadas

| Versão | Suportada |
|--------|-----------|
| 1.x    | ✅        |

## Reportando uma Vulnerabilidade

Se você descobrir uma vulnerabilidade de segurança, **não abra uma issue pública**.

Entre em contato diretamente pelo e-mail informado no perfil do repositório. Inclua:

- Descrição clara da vulnerabilidade
- Passos para reprodução
- Impacto potencial
- Sugestão de correção (se houver)

Você receberá uma resposta em até **72 horas**. Se a vulnerabilidade for confirmada, publicaremos um patch e daremos crédito ao reporter (a menos que prefira anonimato).

---

## Boas Práticas Adotadas no Projeto

- Credenciais nunca commitadas — use `.env` (ignorado pelo `.gitignore`)
- Inputs de usuário sempre validados via Pydantic antes de chegarem à camada de serviço
- Parâmetros de query com limites explícitos (`ge`, `le`) para prevenir abusos
- Sem exposição de stack traces em respostas de produção
