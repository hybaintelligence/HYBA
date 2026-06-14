import { useState, useCallback } from "react";

interface UseApiRequestOptions<T> {
  maxRetries?: number;
  baseDelayMs?: number;
  onSuccess?: (data: T) => void;
  onError?: (error: any) => void;
}

export function useApiRequest<T>(
  apiFn: (...args: any[]) => Promise<T>,
  options: UseApiRequestOptions<T> = {},
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(
    async (...args: any[]) => {
      setIsLoading(true);
      setError(null);

      let retries = 0;
      const maxRetries = options.maxRetries ?? 3;
      const baseDelayMs = options.baseDelayMs ?? 1000;
      let delay = baseDelayMs;

      while (true) {
        try {
          const response = await apiFn(...args);
          setData(response);
          if (options.onSuccess) options.onSuccess(response);
          setIsLoading(false);
          return response;
        } catch (err: any) {
          if (retries >= maxRetries) {
            setError(err);
            if (options.onError) options.onError(err);
            setIsLoading(false);
            throw err;
          }
          console.warn(
            `Request failed, retrying in ${delay}ms... (Attempt ${retries + 1}/${maxRetries})`,
          );
          await new Promise((resolve) => setTimeout(resolve, delay));
          delay *= 2;
          retries++;
        }
      }
    },
    [apiFn, options],
  );

  return { data, isLoading, error, execute };
}
