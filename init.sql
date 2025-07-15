-- init.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS test_vectors (
    id SERIAL PRIMARY KEY,
    embedding vector(3)
);

INSERT INTO test_vectors (embedding) VALUES
('[1,2,3]'),
('[4,5,6]');

SELECT 'CREATE DATABASE confluence_kb'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'confluence_kb')\gexec