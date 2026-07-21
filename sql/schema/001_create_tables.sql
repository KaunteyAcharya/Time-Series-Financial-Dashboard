CREATE TABLE IF NOT EXISTS symbols (
    symbol      VARCHAR(20) PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    asset_type  VARCHAR(20) NOT NULL DEFAULT 'equity',
    exchange    VARCHAR(50),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prices (
    symbol      VARCHAR(20) NOT NULL REFERENCES symbols(symbol),
    trade_date  DATE        NOT NULL,
    open        NUMERIC(18,6) NOT NULL,
    high        NUMERIC(18,6) NOT NULL,
    low         NUMERIC(18,6) NOT NULL,
    close       NUMERIC(18,6) NOT NULL,
    adj_close   NUMERIC(18,6) NOT NULL,
    volume      BIGINT      NOT NULL DEFAULT 0,

    PRIMARY KEY (symbol, trade_date),

    CONSTRAINT chk_high_gte_low CHECK (high >= low),
    CONSTRAINT chk_prices_positive CHECK (
        open > 0 AND high > 0 AND low > 0 AND close > 0 AND adj_close > 0
    )
);

CREATE INDEX idx_prices_symbol_date_desc
    ON prices (symbol, trade_date DESC);

CREATE INDEX idx_prices_date
    ON prices (trade_date);
