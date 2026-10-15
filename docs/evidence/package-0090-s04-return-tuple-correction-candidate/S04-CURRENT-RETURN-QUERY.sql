RETURN QUERY SELECT h.installed_rank,h.version,h.type,h.script,h.checksum,h.success
      FROM public.flyway_schema_history h ORDER BY h.installed_rank;
