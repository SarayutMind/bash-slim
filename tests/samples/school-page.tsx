"use client";
/**
 * School list page.
 * Shows schools with a search box and paging.
 * Data comes from the API through React Query.
 */
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Box, Button, TextField } from "@mui/material";
import { api } from "@/lib/api";
import type { School } from "./types";

export default function SchoolPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();
  const { data = [], isLoading } = useQuery({ queryKey: ["schools", page], queryFn: () => api.schools(page) });

  const total = useMemo(() => data.length, [data]);

  useEffect(() => {
    setPage(1);
  }, [search]);

  const handleSubmit = async (form: School) => {
    if (total < 0) return setError("ห้ามติดลบ");
    await api.save(form);
    router.refresh();
  };

  if (isLoading) return <p>Loading...</p>;
  return (
    <Box>
      <TextField value={search} onChange={(e) => setSearch(e.target.value)} />
      <Button onClick={() => setPage(page + 1)}>Next</Button>
      {error && <p>{error}</p>}
      <p>Total: {total}</p>
    </Box>
  );
}
