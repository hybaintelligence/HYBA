import { useState, useCallback, useRef } from "react";
import {
  classifyError,
  logError,
  isRetryable,
  HybaError,
} from "../utils/errorHandler";

interface UseApiRequestOptions<T> {
  maxRetries?: number;
  baseDelayMs?: number;
  onSuccess?: (data: T) => void;
  onError?: (error: HybaError) => void;
  context?: Record<string, unknown>;
}

export function useApiRequest<T>(
  apiFn: (...args: unknown[]) => Promise<T>,
  options: UseApiRequestOptions<T> = {},
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<HybaError | null>(null);
  // Keep a stable ref to options so the callback identity doesn't change on
  // every render while still reading the latest values.
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const execute = useCallback(
    async (...args: unknown[]) => {
      setIsLoading(true);
      setError(null);

      const { maxRetries = 3, baseDelayMs = 1000 } = optionsRef.current;

      for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
          const response = await apiFn(...args);
          setData(response);
          optionsRef.current.onSuccess?.(response);
          setIsLoading(false);
          return response;
        } catch (err: unknown) {
          const classifiedError = classifyError(err);
          logError(classifiedError, optionsRef.current.context);

          const isLastAttempt = attempt >= maxRetries;
          if (isLastAttempt || !isRetryable(classifiedError)) {
            setError(classifiedError);
            optionsRef.current.onError?.(classifiedError);
            setIsLoading(false);
            throw classifiedError;
          }

          // Exponential backoff with full jitter: delay = rand(0, base * 2^attempt)
          const cap = Math.min(baseDelayMs * Math.pow(2, attempt), 30_000);
          const jitteredDelay = Math.floor(Math.random() * cap);
          console.warn(
            `[useApiRequest] Attempt ${attempt + 1}/${maxRetries} failed, retrying in ${jitteredDelay}ms`,
          );
          await new Promise((resolve) => setTimeout(resolve, jitteredDelay));
        }
      }
    },
    [apiFn],
  );

  return { data, isLoading, error, execute };
}
