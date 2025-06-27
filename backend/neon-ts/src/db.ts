import 'dotenv/config';
import { neon } from '@neondatabase/serverless';
const sql = neon(process.env.DATABASE_URL as string);

async function insert(table: string, data: Record<string, unknown>) {
  const keys = Object.keys(data);
  const values = keys.map((k) => (data as any)[k]);
  const placeholders = keys.map((_, i) => `$${i + 1}`).join(',');
  const query = `INSERT INTO ${table} (${keys.join(',')}) VALUES (${placeholders}) RETURNING *`;
  const { rows } = await sql(query, values);
  return rows[0];
}

export const insertSignal = (data: Record<string, unknown>) => insert('signals', data);
export const insertOrder = (data: Record<string, unknown>) => insert('pending_orders', data);
export const insertTrade = (data: Record<string, unknown>) => insert('trades', data);
export const insertEvent = (data: Record<string, unknown>) => insert('trade_events', data);
