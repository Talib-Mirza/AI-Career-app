-- Reading-level onboarding removed from product; column no longer used.
alter table public.profiles
  drop column if exists reading_level;
