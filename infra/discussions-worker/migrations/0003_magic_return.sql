-- Bind the destination to the issued challenge rather than an editable URL.
-- Outstanding legacy links intentionally require requesting a fresh link.
ALTER TABLE magic_tokens ADD COLUMN return_to TEXT;
