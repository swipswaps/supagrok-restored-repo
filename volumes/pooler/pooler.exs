# Default pooler configuration
Supavisor.start_tenant(%{
  "id" => System.get_env("POOLER_TENANT_ID", "default"),
  "db_host" => "db",
  "db_port" => String.to_integer(System.get_env("POSTGRES_PORT", "5432")),
  "db_name" => System.get_env("POSTGRES_DB", "postgres"),
  "db_user" => "supabase_admin",
  "db_password" => System.get_env("POSTGRES_PASSWORD"),
  "port" => 5432,
  "pool_size" => String.to_integer(System.get_env("POOLER_DEFAULT_POOL_SIZE", "10")),
  "max_client_conn" => String.to_integer(System.get_env("POOLER_MAX_CLIENT_CONN", "100")),
  "pool_mode" => "transaction",
  "cmd_timeout" => 3000,
  "server_lifetime" => 3600,
  "idle_timeout" => 1800,
  "autorestart" => true
})
