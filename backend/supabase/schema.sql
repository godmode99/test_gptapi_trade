-- Supabase schema for automated trading system
-- Run this script inside a Supabase SQL editor or through psql

CREATE TABLE signals (
    signal_id TEXT PRIMARY KEY,
    symbol TEXT,
    entry REAL,
    sl REAL,
    tp REAL,
    type TEXT,
    confidence INTEGER,
    regime_type TEXT,
    created_at TIMESTAMPTZ
);

CREATE TABLE pending_orders (
    id UUID PRIMARY KEY,
    signal_id TEXT REFERENCES signals(signal_id),
    status TEXT,
    sent_time TIMESTAMPTZ,
    filled_time TIMESTAMPTZ,
    cancel_reason TEXT
);

CREATE TABLE trades (
    id UUID PRIMARY KEY,
    signal_id TEXT REFERENCES signals(signal_id),
    pending_order_id UUID REFERENCES pending_orders(id),
    open_time TIMESTAMPTZ,
    close_time TIMESTAMPTZ,
    entry REAL,
    exit REAL,
    profit REAL,
    lot_size REAL,
    status TEXT,
    strategy TEXT
);

CREATE TABLE trade_events (
    id UUID PRIMARY KEY,
    trade_id UUID REFERENCES trades(id),
    event_type TEXT,
    event_time TIMESTAMPTZ,
    details TEXT
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    signal_id TEXT REFERENCES signals(signal_id),
    channel TEXT,
    message TEXT,
    status TEXT,
    sent_time TIMESTAMPTZ
);
