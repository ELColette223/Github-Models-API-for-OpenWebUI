# Usar uma imagem base do Python
FROM python:3.9-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar o arquivo requirements.txt para o diretório de trabalho
COPY requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante dos arquivos da aplicação para o diretório de trabalho
COPY . .

# Definir variáveis de ambiente para o Uvicorn e a aplicação
ENV PORT=80
ENV GITHUB_API_URL=https://models.inference.ai.azure.com

# True or False for Debug
ENV DEBUG=True 

# True or False for cache
ENV CACHE_STATUS=False

# Expor a porta
EXPOSE $PORT

# Comando para rodar o Uvicorn, utilizando as variáveis de ambiente
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
