/**
 * Comprehensive Error Handling Utilities
 * Provides centralized error handling, classification, and recovery mechanisms
 */

// ── Error Types ─────────────────────────────────────────────────────────────

export enum ErrorCategory {
  NETWORK = 'network',
  API = 'api',
  VALIDATION = 'validation',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  DATABASE = 'database',
  TIMEOUT = 'timeout',
  RATE_LIMIT = 'rate_limit',
  INTERNAL = 'internal',
  EXTERNAL_SERVICE = 'external_service',
  UNKNOWN = 'unknown'
}

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface AppError {
  name: string;
  message: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  code?: string;
  statusCode?: number;
  requestId?: string;
  timestamp: Date;
  stack?: string;
  context?: Record<string, unknown>;
  recoverable: boolean;
  retryable: boolean;
}

// ── Error Classes ────────────────────────────────────────────────────────────

export class HybaError extends Error implements AppError {
  public readonly category: ErrorCategory;
  public readonly severity: ErrorSeverity;
  public readonly code?: string;
  public readonly statusCode?: number;
  public readonly requestId?: string;
  public readonly timestamp: Date;
  public readonly context?: Record<string, unknown>;
  public readonly recoverable: boolean;
  public readonly retryable: boolean;

  constructor(
    message: string,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    options?: {
      code?: string;
      statusCode?: number;
      requestId?: string;
      context?: Record<string, unknown>;
      recoverable?: boolean;
      retryable?: boolean;
      cause?: Error;
    }
  ) {
    super(message, { cause: options?.cause });
    this.name = this.constructor.name;
    this.category = category;
    this.severity = severity;
    this.code = options?.code;
    this.statusCode = options?.statusCode;
    this.requestId = options?.requestId;
    this.timestamp = new Date();
    this.context = options?.context;
    this.recoverable = options?.recoverable ?? true;
    this.retryable = options?.retryable ?? this.isRetryableByDefault(category);
  }

  private isRetryableByDefault(category: ErrorCategory): boolean {
    return [
      ErrorCategory.NETWORK,
      ErrorCategory.TIMEOUT,
      ErrorCategory.RATE_LIMIT,
      ErrorCategory.EXTERNAL_SERVICE
    ].includes(category);
  }

  toJSON(): AppError {
    return {
      name: this.name,
      message: this.message,
      category: this.category,
      severity: this.severity,
      code: this.code,
      statusCode: this.statusCode,
      requestId: this.requestId,
      timestamp: this.timestamp,
      stack: this.stack,
      context: this.context,
      recoverable: this.recoverable,
      retryable: this.retryable
    };
  }
}

export class NetworkError extends HybaError {
  constructor(message: string, options?: {
    code?: string;
    statusCode?: number;
    requestId?: string;
    context?: Record<string, unknown>;
    recoverable?: boolean;
    retryable?: boolean;
    cause?: Error;
  }) {
    super(message, ErrorCategory.NETWORK, ErrorSeverity.HIGH, options || {});
  }
}

export class ApiError extends HybaError {
  constructor(message: string, statusCode: number, options?: {
    code?: string;
    requestId?: string;
    context?: Record<string, unknown>;
    recoverable?: boolean;
    retryable?: boolean;
    cause?: Error;
  }) {
    super(message, ErrorCategory.API, ErrorSeverity.MEDIUM, { ...(options || {}), statusCode });
  }
}

export class ValidationError extends HybaError {
  constructor(message: string, options?: {
    code?: string;
    statusCode?: number;
    requestId?: string;
    context?: Record<string, unknown>;
    cause?: Error;
  }) {
    super(message, ErrorCategory.VALIDATION, ErrorSeverity.LOW, { ...(options || {}), recoverable: false, retryable: false });
  }
}

export class AuthenticationError extends HybaError {
  constructor(message: string, options?: {
    code?: string;
    statusCode?: number;
    requestId?: string;
    context?: Record<string, unknown>;
    cause?: Error;
  }) {
    super(message, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH, { ...(options || {}), recoverable: false, retryable: false });
  }
}

export class AuthorizationError extends HybaError {
  constructor(message: string, options?: {
    code?: string;
    statusCode?: number;
    requestId?: string;
    context?: Record<string, unknown>;
    cause?: Error;
  }) {
    super(message, ErrorCategory.AUTHORIZATION, ErrorSeverity.HIGH, { ...(options || {}), recoverable: false, retryable: false });
  }
}

export class DatabaseError extends HybaError {
  constructor(message: string, options?: {
    code?: string;
    statusCode?: number;
    requestId?: string;
    context?: Record<string, unknown>;
    recoverable?: boolean;
    retryable?: boolean;
    cause?: Error;
  }) {
    super(message, ErrorCategory.DATABASE, ErrorSeverity.HIGH, options || {});
  }
}

export class TimeoutError extends HybaError {
  constructor(message: string, options?: {
    code?: string;
    statusCode?: number;
    requestId?: string;
    context?: Record<string, unknown>;
    recoverable?: boolean;
    cause?: Error;
  }) {
    super(message, ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM, { ...(options || {}), retryable: true });
  }
}

export class RateLimitError extends HybaError {
  constructor(message: string, options?: {
    code?: string;
    statusCode?: number;
    requestId?: string;
    context?: Record<string, unknown>;
    recoverable?: boolean;
    cause?: Error;
  }) {
    super(message, ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM, { ...(options || {}), retryable: true });
  }
}

export class ExternalServiceError extends HybaError {
  constructor(message: string, options?: {
    code?: string;
    statusCode?: number;
    requestId?: string;
    context?: Record<string, unknown>;
    recoverable?: boolean;
    retryable?: boolean;
    cause?: Error;
  }) {
    super(message, ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH, options || {});
  }
}

// ── Error Classification ────────────────────────────────────────────────────

export function classifyError(error: unknown): HybaError {
  if (error instanceof HybaError) {
    return error;
  }

  if (error instanceof Error) {
    // Check error message patterns for classification
    const message = error.message.toLowerCase();
    
    if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
      return new NetworkError(error.message, { cause: error });
    }
    
    if (message.includes('timeout') || message.includes('timed out')) {
      return new TimeoutError(error.message, { cause: error });
    }
    
    if (message.includes('validation') || message.includes('invalid') || message.includes('required')) {
      return new ValidationError(error.message, { cause: error });
    }
    
    if (message.includes('auth') || message.includes('unauthorized') || message.includes('forbidden')) {
      return new AuthenticationError(error.message, { cause: error });
    }
    
    if (message.includes('permission') || message.includes('access denied')) {
      return new AuthorizationError(error.message, { cause: error });
    }
    
    if (message.includes('rate limit') || message.includes('too many requests')) {
      return new RateLimitError(error.message, { cause: error });
    }
    
    if (message.includes('database') || message.includes('db') || message.includes('sql')) {
      return new DatabaseError(error.message, { cause: error });
    }
    
    // Default classification
    return new HybaError(error.message, ErrorCategory.INTERNAL, ErrorSeverity.MEDIUM, { cause: error });
  }

  if (typeof error === 'string') {
    return new HybaError(error, ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM, {});
  }

  return new HybaError('An unknown error occurred', ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM, {
    context: { originalError: error }
  });
}

// ── Error Logging ───────────────────────────────────────────────────────────

export interface ErrorLogEntry {
  error: AppError;
  userAgent?: string;
  url?: string;
  userId?: string;
}

let errorLogCallback: ((entry: ErrorLogEntry) => void) | null = null;

export function setErrorLogCallback(callback: (entry: ErrorLogEntry) => void): void {
  errorLogCallback = callback;
}

export function logError(error: unknown, context?: Record<string, unknown>): void {
  const classifiedError = classifyError(error);
  
  const logEntry: ErrorLogEntry = {
    error: classifiedError.toJSON(),
    userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : undefined,
    url: typeof window !== 'undefined' ? window.location.href : undefined,
    userId: context?.userId as string | undefined
  };

  // Console logging with appropriate severity
  const consoleMethod = classifiedError.severity === ErrorSeverity.CRITICAL || classifiedError.severity === ErrorSeverity.HIGH
    ? console.error
    : classifiedError.severity === ErrorSeverity.MEDIUM
    ? console.warn
    : console.log;

  consoleMethod(`[${classifiedError.category.toUpperCase()}]`, classifiedError.message, logEntry);

  // Call custom error log callback if set
  if (errorLogCallback) {
    try {
      errorLogCallback(logEntry);
    } catch (loggingError) {
      console.error('Error in error log callback:', loggingError);
    }
  }
}

// ── Error Recovery Strategies ───────────────────────────────────────────────

export interface RecoveryStrategy {
  canRecover(error: HybaError): boolean;
  recover(error: HybaError): Promise<boolean> | boolean;
}

export class RetryStrategy implements RecoveryStrategy {
  constructor(
    private maxRetries: number = 3,
    private baseDelayMs: number = 1000,
    private maxDelayMs: number = 10000
  ) {}

  canRecover(error: HybaError): boolean {
    return error.retryable && this.maxRetries > 0;
  }

  async recover(error: HybaError): Promise<boolean> {
    if (!this.canRecover(error)) {
      return false;
    }
    
    // Calculate exponential backoff with jitter
    const delay = Math.min(
      this.baseDelayMs * Math.pow(2, error.context?.retryCount as number || 0),
      this.maxDelayMs
    );
    const jitter = delay * 0.1 * Math.random();
    
    await new Promise(resolve => setTimeout(resolve, delay + jitter));
    return true;
  }
}

export class RefreshAuthStrategy implements RecoveryStrategy {
  canRecover(error: HybaError): boolean {
    return error.category === ErrorCategory.AUTHENTICATION && error.statusCode === 401;
  }

  async recover(error: HybaError): Promise<boolean> {
    try {
      // Trigger token refresh logic
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth:refresh'));
      }
      return true;
    } catch {
      return false;
    }
  }
}

export class FallbackStrategy implements RecoveryStrategy {
  constructor(private fallbackValue: unknown) {}

  canRecover(error: HybaError): boolean {
    return error.recoverable;
  }

  recover(): boolean {
    return true;
  }

  getFallback(): unknown {
    return this.fallbackValue;
  }
}

// ── Error Handler Composition ───────────────────────────────────────────────

export class ErrorHandler {
  private strategies: RecoveryStrategy[] = [];

  constructor(strategies: RecoveryStrategy[] = []) {
    this.strategies = strategies;
  }

  addStrategy(strategy: RecoveryStrategy): void {
    this.strategies.push(strategy);
  }

  async handle(error: unknown, context?: Record<string, unknown>): Promise<unknown> {
    const classifiedError = classifyError(error);
    logError(classifiedError, context);

    for (const strategy of this.strategies) {
      if (strategy.canRecover(classifiedError)) {
        const recovered = await strategy.recover(classifiedError);
        if (recovered) {
          if (strategy instanceof FallbackStrategy) {
            return strategy.getFallback();
          }
          return true;
        }
      }
    }

    throw classifiedError;
  }
}

// ── Utility Functions ───────────────────────────────────────────────────────

export function isRecoverable(error: unknown): boolean {
  const classified = classifyError(error);
  return classified.recoverable;
}

export function isRetryable(error: unknown): boolean {
  const classified = classifyError(error);
  return classified.retryable;
}

export function getErrorSeverity(error: unknown): ErrorSeverity {
  const classified = classifyError(error);
  return classified.severity;
}

export function withErrorHandling<T>(
  fn: () => T,
  fallback?: T,
  context?: Record<string, unknown>
): T {
  try {
    return fn();
  } catch (error) {
    logError(error, context);
    if (fallback !== undefined) {
      return fallback;
    }
    throw error;
  }
}

export async function withAsyncErrorHandling<T>(
  fn: () => Promise<T>,
  fallback?: T,
  context?: Record<string, unknown>
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    logError(error, context);
    if (fallback !== undefined) {
      return fallback;
    }
    throw error;
  }
}
