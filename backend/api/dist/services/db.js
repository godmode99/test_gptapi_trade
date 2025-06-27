"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.insertEvent = exports.insertTrade = exports.insertOrder = exports.insertSignal = void 0;
require("dotenv/config");
const pg_1 = __importDefault(require("pg"));
const { Pool } = pg_1.default;
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
async function insert(table, data) {
    const keys = Object.keys(data);
    const placeholders = keys.map((_, i) => `$${i + 1}`).join(',');
    const values = keys.map((k) => data[k]);
    const query = `INSERT INTO ${table} (${keys.join(',')}) VALUES (${placeholders}) RETURNING *`;
    const result = await pool.query(query, values);
    return result.rows[0];
}
const insertSignal = (data) => insert('signals', data);
exports.insertSignal = insertSignal;
const insertOrder = (data) => insert('pending_orders', data);
exports.insertOrder = insertOrder;
const insertTrade = (data) => insert('trades', data);
exports.insertTrade = insertTrade;
const insertEvent = (data) => insert('trade_events', data);
exports.insertEvent = insertEvent;
