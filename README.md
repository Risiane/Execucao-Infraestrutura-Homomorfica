# Instruções de Execução: Infraestrutura de Criptografia Homomórfica

Este projeto implementa uma prova de conceito de criptografia homomórfica em um ambiente de nuvem simulado. A arquitetura utiliza containers Docker, LocalStack para simular o serviço S3, um cliente responsável pela criptografia e descriptografia, e um servidor responsável por processar dados criptografados sem acessar os valores em texto claro.

## Objetivo

Demonstrar como dados sensíveis podem ser processados em um ambiente de nuvem sem que o servidor tenha acesso aos valores originais. O cliente criptografa os dados, envia os ciphertexts para um bucket S3 simulado, o servidor executa a soma homomórfica e retorna o resultado ainda criptografado. A descriptografia final ocorre somente no cliente.

## Arquitetura

A solução é composta por três serviços principais:

| Componente | Função |
|---|---|
| `he-client` | Gera o contexto criptográfico, mantém a chave secreta, criptografa os dados, envia os ciphertexts e descriptografa o resultado final |
| `he-server` | Baixa os ciphertexts, realiza a soma homomórfica e envia o resultado criptografado de volta ao bucket |
| `he-localstack` | Simula o serviço S3 localmente, armazenando contexto público, dados criptografados, manifestos e resultados |

O fluxo da aplicação é:

1. O cliente gera o contexto criptográfico BFV.
2. A chave secreta fica armazenada somente no cliente.
3. Os dados numéricos são criptografados.
4. Os ciphertexts são enviados para o bucket S3 simulado.
5. O servidor baixa apenas o contexto público e os dados criptografados.
6. O servidor realiza a soma homomórfica sem descriptografar os valores.
7. O resultado criptografado é enviado de volta ao bucket.
8. O cliente baixa o resultado e realiza a descriptografia final.

## Tecnologias utilizadas

| Tecnologia | Uso no projeto |
|---|---|
| Docker | Execução dos containers |
| Docker Compose | Orquestração dos serviços |
| LocalStack | Simulação local do serviço S3 |
| Python 3.10 | Execução dos scripts |
| TenSEAL | Biblioteca de criptografia homomórfica |
| Boto3 | Comunicação com o S3 simulado |
| NumPy | Dependência utilizada pelo TenSEAL |

## Estrutura do projeto

```text
proto-he-cloud/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── client/
│   ├── client_encrypt_upload.py
│   └── client_decrypt_result.py
├── server/
│   ├── server_process.py
│   └── server_security_check.py
├── output/
└── evidencias/
```

## Descrição dos principais arquivos

| Arquivo | Descrição |
|---|---|
| `Dockerfile` | Define a imagem Python usada pelos containers cliente e servidor |
| `docker-compose.yml` | Define os serviços LocalStack, cliente e servidor |
| `requirements.txt` | Lista as bibliotecas Python necessárias |
| `client/client_encrypt_upload.py` | Gera o contexto, criptografa os dados e envia os ciphertexts ao bucket |
| `server/server_process.py` | Processa os dados criptografados e gera o resultado criptografado |
| `client/client_decrypt_result.py` | Baixa o resultado criptografado e realiza a descriptografia final |
| `server/server_security_check.py` | Valida que o servidor não possui chave secreta e não consegue descriptografar os dados |

## Pré-requisitos

Antes de executar o projeto, é necessário ter instalado:

```bash
docker --version
docker compose version
python3 --version
```

Também é necessário que o serviço Docker esteja ativo.

## Execução

Entre na pasta do projeto:

```bash
cd ~/proto-he-cloud
```

Suba os containers:

```bash
docker compose build
docker compose up -d
docker ps
```

Containers esperados:

```text
he-localstack
he-client
he-server
```

Crie e valide o bucket S3 simulado:

```bash
docker compose exec localstack awslocal s3 mb s3://he-bucket 2>/dev/null || echo "Bucket já existe"
docker compose exec localstack awslocal s3 ls
```

Execute o cliente para criptografar os dados e enviar os ciphertexts ao bucket:

```bash
docker compose exec client python client/client_encrypt_upload.py
```

Liste os objetos criados no bucket:

```bash
docker compose exec localstack awslocal s3 ls s3://he-bucket --recursive
```

Execute o servidor para processar os dados criptografados:

```bash
docker compose exec server python server/server_process.py
```

Liste novamente o bucket após o processamento:

```bash
docker compose exec localstack awslocal s3 ls s3://he-bucket --recursive
```

Execute o cliente para descriptografar o resultado final:

```bash
docker compose exec client python client/client_decrypt_result.py
```

Resultado esperado:

```text
REGIAO | SOMA | QUANTIDADE | MEDIA
----------------------------------
Norte  | 90   | 2          | 45.00
Sul    | 135  | 3          | 45.00
Leste  | 105  | 3          | 35.00
```

## Validação de segurança

Verifique se a chave secreta ficou somente no cliente:

```bash
docker compose exec client sh -c 'ls -l /tmp/he_secret_context.tenseal'
docker compose exec server sh -c 'ls -l /tmp/he_secret_context.tenseal 2>/dev/null || echo "OK: chave secreta não existe no servidor"'
```

Execute a validação de segurança no servidor:

```bash
docker compose exec server python server/server_security_check.py
```

Resultado esperado:

```text
[OK] Chave secreta não existe no servidor.
[OK] O servidor não conseguiu descriptografar o resultado.
[MOTIVO] Contexto público não possui chave secreta.
```

## Geração de evidências

As evidências podem ser salvas com os comandos abaixo:

```bash
mkdir -p evidencias

docker ps > evidencias/01_containers_em_execucao.txt

docker compose exec localstack awslocal s3 ls s3://he-bucket --recursive > evidencias/02_listagem_bucket.txt

docker compose exec server python server/server_process.py > evidencias/03_execucao_servidor.txt

docker compose exec client python client/client_decrypt_result.py > evidencias/04_resultado_final_cliente.txt

docker compose exec server python server/server_security_check.py > evidencias/05_validacao_seguranca_servidor.txt
```

Conferência dos arquivos:

```bash
tree evidencias
cat output/resultados_finais.json
cat output/resultados_finais.csv
```

## Resultados obtidos

| Região | Soma obtida | Quantidade | Média |
|---|---:|---:|---:|
| Norte | 90 | 2 | 45.00 |
| Sul | 135 | 3 | 45.00 |
| Leste | 105 | 3 | 35.00 |

Os arquivos finais são gerados em:

```text
output/resultados_finais.json
output/resultados_finais.csv
```

## Observações de segurança

A chave secreta é criada e mantida somente no container cliente, no caminho temporário `/tmp/he_secret_context.tenseal`. O servidor recebe apenas o contexto público e os ciphertexts, permitindo a execução da soma homomórfica sem acesso aos valores originais.

O bucket armazena os dados criptografados, os manifestos e os resultados ainda criptografados. A descriptografia final ocorre somente no cliente.

## Limitações

Esta implementação é uma prova de conceito acadêmica. Em um ambiente de produção, seria necessário considerar:

- proteção do host Docker;
- controle de acesso ao bucket;
- uso de TLS;
- autenticação e autorização reais;
- rotação e proteção de chaves;
- logs centralizados;
- escolha formal de parâmetros criptográficos;
- avaliação de desempenho e custo computacional;
- diferença entre LocalStack e nuvem real.

## Encerramento do ambiente

Para parar os containers:

```bash
docker compose down
```

Para remover também os volumes temporários:

```bash
docker compose down -v
