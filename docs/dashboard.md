# Visualizing Supabase data in Grafana and Retool

This guide shows how to connect your Supabase PostgreSQL database to either Grafana or Retool in order to build dashboards for your trading records.

## Connecting Grafana

1. Open Grafana and go to **Configuration → Data sources**.
2. Click **Add data source** and choose **PostgreSQL**.
3. Fill in the connection details from your Supabase project:
   - **Host**: `db.<project-ref>.supabase.co`
   - **Database**: `postgres`
   - **User**: `postgres`
   - **Password**: your database password
   - **SSL mode**: `require`
4. Save the data source. Grafana can now query your Supabase tables.

## Connecting Retool

1. In Retool, navigate to **Resources** and create a new **PostgreSQL** resource.
2. Enter the same connection parameters as above. You can copy the full connection string from the Supabase dashboard under **Settings → Database**.
3. Test the connection and save. Retool queries will now run against Supabase.

## Example queries

These queries can be used in Grafana panels or Retool components to visualize your trading workflow.

### Signals
```sql
SELECT created_at, symbol, type, confidence
FROM signals
ORDER BY created_at DESC
LIMIT 100;
```

### Pending orders
```sql
SELECT sent_time, status, cancel_reason
FROM pending_orders
ORDER BY sent_time DESC
LIMIT 100;
```

### Trades
```sql
SELECT open_time, close_time, profit, lot_size, status
FROM trades
ORDER BY open_time DESC
LIMIT 100;
```

You can adapt these queries further to show daily counts, average profit or other metrics. Both Grafana and Retool support visualizing tables or charts based on the SQL output.
