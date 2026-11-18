# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos estudantes visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Professores autenticados podem inscrever e remover estudantes
- Estudantes podem consultar as atividades e inscrições sem fazer login

## Configuração da autenticação de professores

Configure `TEACHER_CREDENTIALS` com um objeto JSON de nomes de usuário e senhas atribuídas, por exemplo, `{"teacher1":"senha-forte"}`, e `SESSION_SECRET` com um valor aleatório de pelo menos 32 caracteres. Configure ambos como secrets do ambiente de execução; não os salve no repositório nem em um arquivo JSON versionado.

Para gerar um segredo de sessão, execute:

```
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

As sessões expiram após oito horas. O cookie é `HttpOnly` e `SameSite=Strict`, e recebe a flag `Secure` quando a aplicação é acessada por HTTPS. Use HTTPS fora do desenvolvimento local.

## Primeiros Passos

1. Instale as dependências:

   ```
   pip install fastapi uvicorn
   ```

2. Execute a aplicação:

   ```
   python app.py
   ```

3. Abra seu navegador e vá para:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint                                                          | Descrição                                                           |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Obter todas as atividades com seus detalhes e contagem atual de participantes |
| POST   | `/auth/login`                                                     | Iniciar uma sessão de professor                                     |
| GET    | `/auth/session`                                                   | Verificar se há uma sessão de professor ativa                       |
| POST   | `/auth/logout`                                                    | Encerrar a sessão de professor                                      |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Inscrever um estudante (somente professores)                        |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Remover uma inscrição (somente professores)                      |

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:

   - Descrição
   - Cronograma
   - Número máximo de participantes permitidos
   - Lista de emails de estudantes que estão inscritos

2. **Estudantes** - Usa email como identificador:
   - Nome
   - Nível da série

Todos os dados são armazenados na memória, o que significa que os dados serão resetados quando o servidor reiniciar.
