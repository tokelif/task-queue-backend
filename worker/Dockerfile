FROM python:3.12-slim
RUN apt-get update && \
    apt-get install -y wget unzip nmap iputils-ping libpq-dev gcc && \
    wget -O katana.zip https://github.com/projectdiscovery/katana/releases/download/v1.1.3/katana_1.1.3_linux_amd64.zip && \
    unzip katana.zip -d /tmp && \
    mv /tmp/katana /usr/local/bin/katana && \
    chmod +x /usr/local/bin/katana && \
    rm -f katana.zip && \
    apt-get remove -y wget unzip && apt-get autoremove -y && apt-get clean 

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "worker.py"]
