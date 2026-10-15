RETURN QUERY SELECT h.installed_rank,h.version::pg_catalog.text,h.type::pg_catalog.text,h.script::pg_catalog.text,h.checksum,h.success
      FROM public.flyway_schema_history h ORDER BY h.installed_rank;
