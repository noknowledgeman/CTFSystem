CREATE DATABASE intranet_db;

\connect intranet_db;

CREATE USER intranet_bydhwzfp WITH PASSWORD 'w#Q8WxjX^pUX*UFbTxT!7afkGhLZ^K!W';

CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) NOT NULL,
    config_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO system_config (config_key, config_value) VALUES
    ('app_version', '2.1.0'),
    ('maintenance_mode', 'false'),
    ('secret_flag', 'EH2025{39aa9ec8a0380e8639656c891f3c3bb9411ce6744bdfad557dd342eac4cf3430}'),
    ('max_upload_size', '10485760');

GRANT ALL PRIVILEGES ON DATABASE intranet_db TO intranet_bydhwzfp;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO intranet_bydhwzfp;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO intranet_bydhwzfp;

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO employees (name, email, department) VALUES
    ('John Smith', 'john.smith@company.internal', 'IT'),
    ('Jane Doe', 'jane.doe@company.internal', 'HR'),
    ('Bob Johnson', 'bob.johnson@company.internal', 'Engineering'),
    ('Alice Williams', 'alice.williams@company.internal', 'Security');

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO intranet_bydhwzfp;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO intranet_bydhwzfp;
