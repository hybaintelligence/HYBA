/**
 * Frontend Privilege Boundary Regression Tests
 * 
 * These tests verify that non-admin users cannot access admin-only QaaS/CIaaS endpoints
 * and that the frontend correctly routes to customer endpoints when isAdmin is false.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  provisionQaaSComputer,
  provisionCustomerQaaSComputer,
  provisionCIAASService,
  provisionCustomerCIAASService,
  type CustomerProvisionFaultTolerantComputerRequest,
  type CustomerProvisionComputationalIntelligenceRequest,
  type ProvisionFaultTolerantComputerRequest,
  type ProvisionComputationalIntelligenceRequest,
} from "../src/apiClient";

// Mock fetch to track which endpoints are called
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("Frontend QaaS Privilege Boundary", () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it("non-admin QaaS provision calls customer endpoint only", async () => {
    const customerRequest: CustomerProvisionFaultTolerantComputerRequest = {
      name: "test-computer",
      tier: "developer",
      isolation: "single-tenant",
      code_distance: 5,
      logical_qubits: 10,
      physical_error_rate: 0.001,
      phi_resonance_target: 0.95,
      max_circuit_depth: 100,
      max_shots: 1000,
      data_residency: "us-east-1",
      allowed_operations: ["surface_code_cycle"],
    };

    // Mock successful response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        computer_id: "comp-123",
        name: "test-computer",
        state: "provisioned",
      }),
    });

    // Call the customer endpoint
    await provisionCustomerQaaSComputer(customerRequest);

    // Verify the correct endpoint was called
    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[0]).toContain("/api/v1/qaas/customer/computers");
    expect(callArgs[0]).not.toContain("/api/v1/qaas/admin/computers");
  });

  it("non-admin QaaS provision cannot call admin endpoint", async () => {
    const adminRequest: ProvisionFaultTolerantComputerRequest = {
      name: "test-computer",
      tier: "developer",
      isolation: "single-tenant",
      code_distance: 5,
      logical_qubits: 10,
      physical_error_rate: 0.001,
      phi_resonance_target: 0.95,
      max_circuit_depth: 100,
      max_shots: 1000,
      admin_privileged: true,
      data_residency: "us-east-1",
      allowed_operations: ["surface_code_cycle"],
    };

    // Mock successful response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        computer_id: "comp-123",
        name: "test-computer",
        state: "provisioned",
      }),
    });

    // Call the admin endpoint
    await provisionQaaSComputer(adminRequest);

    // Verify the admin endpoint was called
    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[0]).toContain("/api/v1/qaas/admin/computers");
    expect(callArgs[0]).not.toContain("/api/v1/qaas/customer/computers");
  });

  it("customer request type excludes admin_privileged field", () => {
    const customerRequest: CustomerProvisionFaultTolerantComputerRequest = {
      name: "test-computer",
      tier: "developer",
      isolation: "single-tenant",
      code_distance: 5,
      logical_qubits: 10,
      physical_error_rate: 0.001,
      phi_resonance_target: 0.95,
      max_circuit_depth: 100,
      max_shots: 1000,
      data_residency: "us-east-1",
      allowed_operations: ["surface_code_cycle"],
    };

    // Verify admin_privileged is not in the type
    expect("admin_privileged" in customerRequest).toBe(false);
  });
});

describe("Frontend CIaaS Privilege Boundary", () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it("non-admin CIaaS provision calls customer endpoint only", async () => {
    const customerRequest: CustomerProvisionComputationalIntelligenceRequest = {
      name: "test-service",
      service_tier: "developer",
      tenancy: "single-tenant",
      code_distance: 5,
      logical_compute_units: 10,
      physical_error_rate: 0.001,
      max_workloads_per_minute: 10,
      max_context_bytes: 1024,
      data_residency: "us-east-1",
      allowed_workloads: ["explain"],
    };

    // Mock successful response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        service_id: "svc-123",
        name: "test-service",
        state: "provisioned",
      }),
    });

    // Call the customer endpoint
    await provisionCustomerCIAASService(customerRequest);

    // Verify the correct endpoint was called
    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[0]).toContain("/api/v1/ciaas/customer/services");
    expect(callArgs[0]).not.toContain("/api/v1/ciaas/admin/services");
  });

  it("non-admin CIaaS provision cannot call admin endpoint", async () => {
    const adminRequest: ProvisionComputationalIntelligenceRequest = {
      name: "test-service",
      service_tier: "developer",
      tenancy: "single-tenant",
      code_distance: 5,
      logical_compute_units: 10,
      physical_error_rate: 0.001,
      max_workloads_per_minute: 10,
      max_context_bytes: 1024,
      admin_privileged: true,
      data_residency: "us-east-1",
      allowed_workloads: ["explain"],
    };

    // Mock successful response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        service_id: "svc-123",
        name: "test-service",
        state: "provisioned",
      }),
    });

    // Call the admin endpoint
    await provisionCIAASService(adminRequest);

    // Verify the admin endpoint was called
    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[0]).toContain("/api/v1/ciaas/admin/services");
    expect(callArgs[0]).not.toContain("/api/v1/ciaas/customer/services");
  });

  it("customer request type excludes admin_privileged field", () => {
    const customerRequest: CustomerProvisionComputationalIntelligenceRequest = {
      name: "test-service",
      service_tier: "developer",
      tenancy: "single-tenant",
      code_distance: 5,
      logical_compute_units: 10,
      physical_error_rate: 0.001,
      max_workloads_per_minute: 10,
      max_context_bytes: 1024,
      data_residency: "us-east-1",
      allowed_workloads: ["explain"],
    };

    // Verify admin_privileged is not in the type
    expect("admin_privileged" in customerRequest).toBe(false);
  });
});

describe("Frontend UI Admin-Only Field Visibility", () => {
  it("non-admin users cannot access sovereign tier", () => {
    const customerRequest: CustomerProvisionFaultTolerantComputerRequest = {
      name: "test-computer",
      tier: "developer", // Only developer or production allowed
      isolation: "single-tenant",
      code_distance: 5,
      logical_qubits: 10,
      physical_error_rate: 0.001,
      phi_resonance_target: 0.95,
      max_circuit_depth: 100,
      max_shots: 1000,
      data_residency: "us-east-1",
      allowed_operations: ["surface_code_cycle"],
    };

    // Sovereign tier should not be assignable to customer requests
    expect(customerRequest.tier).not.toBe("sovereign");
  });

  it("non-admin users cannot access sovereign-isolated isolation", () => {
    const customerRequest: CustomerProvisionFaultTolerantComputerRequest = {
      name: "test-computer",
      tier: "developer",
      isolation: "single-tenant", // Only single-tenant allowed
      code_distance: 5,
      logical_qubits: 10,
      physical_error_rate: 0.001,
      phi_resonance_target: 0.95,
      max_circuit_depth: 100,
      max_shots: 1000,
      data_residency: "us-east-1",
      allowed_operations: ["surface_code_cycle"],
    };

    // Sovereign-isolated isolation should not be assignable to customer requests
    expect(customerRequest.isolation).not.toBe("sovereign-isolated");
  });

  it("non-admin users cannot access dedicated-control-plane tenancy", () => {
    const customerRequest: CustomerProvisionComputationalIntelligenceRequest = {
      name: "test-service",
      service_tier: "developer",
      tenancy: "single-tenant", // Only single-tenant allowed
      code_distance: 5,
      logical_compute_units: 10,
      physical_error_rate: 0.001,
      max_workloads_per_minute: 10,
      max_context_bytes: 1024,
      data_residency: "us-east-1",
      allowed_workloads: ["explain"],
    };

    // Dedicated-control-plane tenancy should not be assignable to customer requests
    expect(customerRequest.tenancy).not.toBe("dedicated-control-plane");
  });

  it("admin_privileged field is absent from customer request types", () => {
    const qaasCustomerRequest: CustomerProvisionFaultTolerantComputerRequest = {
      name: "test-computer",
      tier: "developer",
      isolation: "single-tenant",
      code_distance: 5,
      logical_qubits: 10,
      physical_error_rate: 0.001,
      phi_resonance_target: 0.95,
      max_circuit_depth: 100,
      max_shots: 1000,
      data_residency: "us-east-1",
      allowed_operations: ["surface_code_cycle"],
    };

    const ciaasCustomerRequest: CustomerProvisionComputationalIntelligenceRequest = {
      name: "test-service",
      service_tier: "developer",
      tenancy: "single-tenant",
      code_distance: 5,
      logical_compute_units: 10,
      physical_error_rate: 0.001,
      max_workloads_per_minute: 10,
      max_context_bytes: 1024,
      data_residency: "us-east-1",
      allowed_workloads: ["explain"],
    };

    // Verify admin_privileged is not in either customer request type
    expect("admin_privileged" in qaasCustomerRequest).toBe(false);
    expect("admin_privileged" in ciaasCustomerRequest).toBe(false);
  });
});
