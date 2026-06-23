/**
 * InternalOnly HOC - Treasury Segregation Component
 *
 * Wraps components that should only be accessible to internal treasury operations.
 * Enforces both role-based access control and feature flag gating.
 *
 * Security Model:
 * - Requires treasury role (admin, cto, chairman, or specific treasury role)
 * - Requires FEATURE_INTERNAL_TOOLS environment variable to be enabled
 * - Prevents commercial product surfaces from exposing internal mining operations
 */

import React, { ReactNode } from "react";
import { useAuth } from "./AuthProvider";

interface InternalOnlyProps {
  children: ReactNode;
  fallback?: ReactNode;
  requiredRole?: string;
}

const TREASURY_ROLES = new Set([
  "admin",
  "cto",
  "chairman",
  "ceo_heir_apparent",
  "chief_of_staff",
  "treasury_operator",
]);

const FEATURE_FLAG = import.meta.env.VITE_FEATURE_INTERNAL_TOOLS === "true";

export function InternalOnly({ children, fallback, requiredRole }: InternalOnlyProps) {
  const { backendUser, isAdmin, isExecutive, hasRole } = useAuth();

  // Check feature flag first
  if (!FEATURE_FLAG) {
    return (
      fallback || (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-semibold">Internal tools are currently disabled.</p>
          <p className="mt-1 text-xs">
            This feature requires the FEATURE_INTERNAL_TOOLS flag to be enabled.
          </p>
        </div>
      )
    );
  }

  // Check if user has any treasury role
  const hasTreasuryRole = backendUser?.role && TREASURY_ROLES.has(backendUser.role);
  const hasRequiredRole = requiredRole ? hasRole(requiredRole) : true;
  const isAuthorized = isAdmin || isExecutive || (hasTreasuryRole && hasRequiredRole);

  if (!isAuthorized) {
    return (
      fallback || (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          <p className="font-semibold">Access Denied: Treasury Operations</p>
          <p className="mt-1 text-xs">
            This component is restricted to internal treasury personnel only.
          </p>
        </div>
      )
    );
  }

  return <>{children}</>;
}

/**
 * Higher-Order Component version for wrapping components
 */
export function withInternalOnly<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options?: { requiredRole?: string; fallback?: ReactNode },
) {
  return function InternalOnlyWrapper(props: P) {
    return (
      <InternalOnly requiredRole={options?.requiredRole} fallback={options?.fallback}>
        <WrappedComponent {...props} />
      </InternalOnly>
    );
  };
}

/**
 * Hook for checking internal access programmatically
 */
export function useInternalAccess(requiredRole?: string): {
  hasAccess: boolean;
  featureEnabled: boolean;
  hasTreasuryRole: boolean;
} {
  const { backendUser, isAdmin, isExecutive, hasRole } = useAuth();
  const hasTreasuryRole = backendUser?.role && TREASURY_ROLES.has(backendUser.role);
  const hasRequiredRole = requiredRole ? hasRole(requiredRole) : true;
  const isAuthorized = isAdmin || isExecutive || (hasTreasuryRole && hasRequiredRole);

  return {
    hasAccess: FEATURE_FLAG && isAuthorized,
    featureEnabled: FEATURE_FLAG,
    hasTreasuryRole: Boolean(hasTreasuryRole),
  };
}
