//backend\api\services\db.js
import "dotenv/config";
// หรือ (ใน CommonJS: require('dotenv').config())
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

console.log("SUPABASE_URL:", process.env.SUPABASE_URL);
console.log("SUPABASE_KEY:", process.env.SUPABASE_KEY);

export const supabase = createClient(supabaseUrl, supabaseKey);

export async function insertSignal(data) {
  const { data: result, error } = await supabase
    .from("signals")
    .insert(data)
    .select()
    .single();
  if (error) throw error;
  return result;
}

export async function insertOrder(data) {
  const { data: result, error } = await supabase
    .from("pending_orders")
    .insert(data)
    .select()
    .single();
  if (error) throw error;
  return result;
}

export async function insertTrade(data) {
  const { data: result, error } = await supabase
    .from("trades")
    .insert(data)
    .select()
    .single();
  if (error) throw error;
  return result;
}

export async function insertEvent(data) {
  const { data: result, error } = await supabase
    .from("trade_events")
    .insert(data)
    .select()
    .single();
  if (error) throw error;
  return result;
}
