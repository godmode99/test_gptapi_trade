import 'dotenv/config';
import pkg from 'pg';

const { Pool } = pkg;
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

async function insert(table, data) {
  const keys = Object.keys(data);
  const placeholders = keys.map((_, i) => `$${i + 1}`).join(',');
  const values = keys.map((k) => data[k]);
  const query = `INSERT INTO ${table} (${keys.join(',')}) VALUES (${placeholders}) RETURNING *`;
  const result = await pool.query(query, values);
  return result.rows[0];
}

export const insertSignal = (data) => insert('signals', data);
export const insertOrder = (data) => insert('pending_orders', data);
export const insertTrade = (data) => insert('trades', data);
export const insertEvent = (data) => insert('trade_events', data);

