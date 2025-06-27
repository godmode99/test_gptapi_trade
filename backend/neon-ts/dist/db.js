"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.insertEvent = exports.insertTrade = exports.insertOrder = exports.insertSignal = void 0;
require("dotenv/config");
const serverless_1 = require("@neondatabase/serverless");
const sql = (0, serverless_1.neon)(process.env.DATABASE_URL);
async function insert(table, data) {
    const keys = Object.keys(data);
    const values = keys.map((k) => data[k]);
    const placeholders = keys.map((_, i) => `$${i + 1}`).join(",");
    const query = `INSERT INTO ${table} (${keys.join(",")}) VALUES (${placeholders}) RETURNING *`;
    const rows = await sql(query, values);
    return rows[0];
}
const insertSignal = (data) => insert("signals", data);
exports.insertSignal = insertSignal;
const insertOrder = (data) => insert("pending_orders", data);
exports.insertOrder = insertOrder;
const insertTrade = (data) => insert("trades", data);
exports.insertTrade = insertTrade;
const insertEvent = (data) => insert("trade_events", data);
exports.insertEvent = insertEvent;
