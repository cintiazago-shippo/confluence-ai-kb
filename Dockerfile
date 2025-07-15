FROM postgres:16

RUN apt-get update && \
    apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-all && \
    rm -rf /var/lib/apt/lists/*

RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && \
    make install && \
    rm -rf /tmp/pgvector

COPY init.sql /docker-entrypoint-initdb.d/