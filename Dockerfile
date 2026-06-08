# Imagem base com Python 3.10.
# O Python 3.10 foi escolhido para maior compatibilidade com a biblioteca TenSEAL.
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container.
WORKDIR /app

# Instala ferramentas básicas necessárias para testes e validações.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências para dentro do container.
COPY requirements.txt /app/requirements.txt

# Instala as bibliotecas Python do projeto.
RUN pip install --no-cache-dir -r /app/requirements.txt

# Mantém o bash como comando padrão.
CMD ["bash"]
