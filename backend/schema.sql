-- SQL schema for trading signals database
-- This file creates the "signals" table used by the backend API.

CREATE TABLE IF NOT EXISTS signals (
    signal_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    entry REAL NOT NULL,
    sl REAL NOT NULL,
    tp REAL NOT NULL,
    pending_order_type TEXT NOT NULL,
    confidence INTEGER,
    regime_type TEXT,
    short_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
