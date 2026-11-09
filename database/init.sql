CREATE TABLE if not EXISTS users(
        id BIGSERIAL PRIMARY KEY,
        username VARCHAR(30) NOT NULL UNIQUE
    );

CREATE TABLE if not EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    text VARCHAR(500) NOT NULL CHECK (length(trim(text)) > 0),
    client_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS messages_user_id_idx ON messages (user_id);