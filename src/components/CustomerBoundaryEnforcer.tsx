import { useEffect } from "react";

import FEATURES from "../config/features";

/**
 * CustomerBoundaryEnforcer is a defence-in-depth visibility guard for legacy
 * dashboard panels that still render from the shared operating console.
 *
 * The primary product boundary should live in component conditionals. This guard
 * protects customer-mode deployments by removing any internal treasury/mining
 * surfaces that remain in the DOM while the dashboard continues to be refactored.
 */
export const CUSTOMER_BOUNDARY_DENYLIST = [
  "stratum mining pools",
  "mining telemetry",
  "network operations",
  "hashrate",
  "eh/s cap",
  "active pool",
  "pools configured",
  "active pools",
  "pool telemetry",
  "shares submitted",
  "operator command routes",
  "/api/mining/",
] as const;

function isCustomerBoundaryEnabled(): boolean {
  return (
    !FEATURES.SHOW_MINING_UI && !FEATURES.SHOW_POOL_MANAGEMENT && !FEATURES.SHOW_HASHRATE_METRICS
  );
}

function nearestHideableSurface(element: Element): HTMLElement | null {
  return (
    element.closest<HTMLElement>("[data-hyba-internal-surface]") ||
    element.closest<HTMLElement>(".kpi-card") ||
    element.closest<HTMLElement>(".overflow-hidden") ||
    element.closest<HTMLElement>("section")
  );
}

function scrubInternalSurfaces(root: ParentNode = document): void {
  if (!isCustomerBoundaryEnabled()) return;

  const candidates = root.querySelectorAll<HTMLElement>("h1,h2,h3,h4,h5,p,span,strong,button,div");

  candidates.forEach((candidate) => {
    const text = candidate.textContent?.toLowerCase() || "";
    if (!text) return;

    const denied = CUSTOMER_BOUNDARY_DENYLIST.some((phrase) => text.includes(phrase));
    if (!denied) return;

    const surface = nearestHideableSurface(candidate);
    if (!surface) return;

    surface.dataset.hybaCustomerBoundaryHidden = "true";
    surface.setAttribute("aria-hidden", "true");
    surface.setAttribute("hidden", "");
  });
}

export function CustomerBoundaryEnforcer() {
  useEffect(() => {
    if (!isCustomerBoundaryEnabled()) return undefined;

    scrubInternalSurfaces();

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            scrubInternalSurfaces(node as Element);
          }
        });
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, []);

  return null;
}
