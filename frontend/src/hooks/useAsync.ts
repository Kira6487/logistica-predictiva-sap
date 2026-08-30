import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";

export function useAsync<T>(loader: () => Promise<T>, dependencies: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    setErrorStatus(null);
    try {
      setData(await loader());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error inesperado.");
      setErrorStatus(cause instanceof ApiError ? cause.status : null);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    void run();
  }, [run]);

  return { data, loading, error, errorStatus, retry: run };
}
