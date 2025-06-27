import 'dotenv/config';
import pkg from 'pg';

const { Pool } = pkg;
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

type RowData = Record<string, unknown>;

async function insert(table: string, data: RowData) {
  const keys = Object.keys(data);
  const placeholders = keys.map((_, i) => `$${i + 1}`).join(',');
  const values = keys.map((k) => (data as any)[k]);
  const query = `INSERT INTO ${table} (${keys.join(',')}) VALUES (${placeholders}) RETURNING *`;
  const result = await pool.query(query, values);
  return result.rows[0];
}

export const insertSignal = (data: RowData) => insert('signals', data);
export const insertOrder = (data: RowData) => insert('pending_orders', data);
export const insertTrade = (data: RowData) => insert('trades', data);
export const insertEvent = (data: RowData) => insert('trade_events', data);
