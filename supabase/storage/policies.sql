-- Storage setup for private deal documents.
-- Run after creating/confirming the `deal-documents` bucket.

insert into storage.buckets (id, name, public)
values ('deal-documents', 'deal-documents', false)
on conflict (id) do update set public = false;

create policy "deal_documents_upload_own_folder"
on storage.objects for insert to authenticated
with check (
    bucket_id = 'deal-documents'
    and (storage.foldername(name))[1] = auth.uid()::text
);

create policy "deal_documents_read_own_folder"
on storage.objects for select to authenticated
using (
    bucket_id = 'deal-documents'
    and (storage.foldername(name))[1] = auth.uid()::text
);

create policy "deal_documents_update_own_folder"
on storage.objects for update to authenticated
using (
    bucket_id = 'deal-documents'
    and (storage.foldername(name))[1] = auth.uid()::text
)
with check (
    bucket_id = 'deal-documents'
    and (storage.foldername(name))[1] = auth.uid()::text
);

create policy "deal_documents_delete_own_folder"
on storage.objects for delete to authenticated
using (
    bucket_id = 'deal-documents'
    and (storage.foldername(name))[1] = auth.uid()::text
);
