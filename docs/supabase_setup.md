# Setting up Supabase

This project stores trading records in a Supabase PostgreSQL database. The SQL schema can be found in `backend/supabase/schema.sql`.

## Applying the schema

1. Install the [Supabase CLI](https://supabase.com/docs/guides/cli) and login.
2. Create a new project from the Supabase dashboard.
3. Run the SQL file in the project database:

   ```bash
   supabase db remote set <database-url>
   supabase db push backend/supabase/schema.sql
   ```

   Alternatively, you can paste the contents of `schema.sql` into the SQL editor on the Supabase dashboard and execute it.

After the tables are created, update your environment variables `SUPABASE_URL` and `SUPABASE_KEY` so the application can connect to your project.
