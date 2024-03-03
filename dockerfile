# Use a imagem base do Python
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Copie o arquivo de requisitos para o diretório de trabalho
# COPY requirements.txt .

# Instale as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie todos os arquivos da aplicação para o diretório de trabalho
COPY . .

# Exponha a porta 5000 para fora do container
EXPOSE 5000

# Comando para iniciar a aplicação quando o container for executado
CMD ["python", "bduser.py"]
