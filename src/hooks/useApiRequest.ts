import { useState, useCallback } from "react";
import {
  classifyError,
  logError,
  isRetryable,
  HybaError,
  ErrorSeverity
} from "../utils/errorHandler";

interface UseApiRequestOptions<T> {
  maxRetries?: number;
  baseDelayMs?: number;
  onSuccess?: (data: T) => void;
  onError?: (error: HybaError) => void;
  context?: Record<string, unknown>;
}

export function useApiRequest<T>(
  apiFn: (...args: any[]) => Promise<T>,
  options: UseApiRequestOptions<T> = {},
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<HybaError | null>(null);

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
        } catch (err: unknown) {
          const classifiedError = classifyError(err);
          logError(classifiedError, options.context);
          
          if (retries >= maxRetries || !isRetryable(classifiedError)) {
            setError(classifiedError);
            if (options.onError) options.onError(classifiedError);
            setIsLoading(false);
            throw classifiedError;
          }
          
          console.warn(
            `[useApiRequest] Request failed, retrying in ${delay}ms... (Attempt ${retries + 1}/${maxRetries})`,
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
