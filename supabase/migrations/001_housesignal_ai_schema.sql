-- HouseSignal AI Supabase schema.
-- Apply from the Supabase SQL editor or CLI after reviewing for your project.

create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists public.user_profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text,
    full_name text,
    role text not null default 'analyst' check (role in ('analyst', 'admin')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.cre_properties (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    address text,
    city text,
    state text default 'CA',
    zip_code text,
    asset_type text,
    units integer check (units is null or units >= 0),
    purchase_price numeric check (purchase_price is null or purchase_price >= 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.deal_documents (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    property_id uuid references public.cre_properties(id) on delete cascade,
    document_type text not null check (document_type in ('lease_agreement', 'rent_roll', 'offering_memorandum', 't12_financial_statement', 'property_condition_report')),
    file_name text not null,
    storage_path text not null,
    content_sha256 text,
    status text not null default 'uploaded' check (status in ('uploaded', 'processing', 'processed', 'failed')),
    extracted_summary jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.document_chunks (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    document_id uuid not null references public.deal_documents(id) on delete cascade,
    chunk_index integer not null check (chunk_index >= 0),
    content text not null,
    token_count integer,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector(1536),
    created_at timestamptz not null default now(),
    unique (document_id, chunk_index)
);

create table if not exists public.agent_runs (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    property_id uuid references public.cre_properties(id) on delete cascade,
    agent_name text not null,
    input_summary jsonb not null default '{}'::jsonb,
    output_summary jsonb not null default '{}'::jsonb,
    model_name text,
    status text not null default 'completed' check (status in ('completed', 'failed')),
    created_at timestamptz not null default now()
);

create table if not exists public.cre_recommendations (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    property_id uuid references public.cre_properties(id) on delete cascade,
    recommendation_label text not null,
    investment_score numeric not null check (investment_score >= 0 and investment_score <= 100),
    risk_score numeric check (risk_score is null or (risk_score >= 0 and risk_score <= 100)),
    financial_metrics jsonb not null default '{}'::jsonb,
    assumptions jsonb not null default '{}'::jsonb,
    evidence jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.api_usage_logs (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid references auth.users(id) on delete set null,
    provider text not null,
    endpoint text not null,
    cache_key text,
    cache_status text not null check (cache_status in ('hit', 'miss', 'blocked', 'error')),
    request_date date not null default current_date,
    created_at timestamptz not null default now()
);

create table if not exists public.external_api_cache (
    cache_key text primary key,
    provider text not null,
    endpoint text not null,
    response_body jsonb not null,
    expires_at timestamptz not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_document_chunks_document_id on public.document_chunks(document_id);
create index if not exists idx_document_chunks_embedding on public.document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index if not exists idx_api_usage_provider_date on public.api_usage_logs(provider, request_date);
create index if not exists idx_external_api_cache_provider on public.external_api_cache(provider, expires_at);

alter table public.user_profiles enable row level security;
alter table public.cre_properties enable row level security;
alter table public.deal_documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.agent_runs enable row level security;
alter table public.cre_recommendations enable row level security;
alter table public.api_usage_logs enable row level security;
alter table public.external_api_cache enable row level security;

create policy "profiles_select_own" on public.user_profiles for select using (id = auth.uid());
create policy "profiles_update_own" on public.user_profiles for update using (id = auth.uid()) with check (id = auth.uid());

create policy "properties_owner_all" on public.cre_properties for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "documents_owner_all" on public.deal_documents for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "chunks_owner_all" on public.document_chunks for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "agent_runs_owner_select" on public.agent_runs for select using (owner_id = auth.uid());
create policy "recommendations_owner_all" on public.cre_recommendations for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "api_usage_owner_select" on public.api_usage_logs for select using (owner_id = auth.uid());

-- Cache rows should be written by backend service-role only. Authenticated users may not read raw cached payloads by default.
create policy "external_cache_service_only" on public.external_api_cache for all using (false) with check (false);
