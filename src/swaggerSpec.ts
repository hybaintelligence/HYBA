export const swaggerDocument = {
  openapi: "3.0.0",
  info: {
    title: "HYBA Quantum Intelligence API",
    version: "2.5.0",
    description:
      "Full-stack APIs for substrate-independent Quantum Intelligence, evidence-sealed execution, PULVINI φ-memory, Salamander regeneration, Quantum Finance Intelligence, session auth, and enterprise execution controls; HYBA rejects AGI/ASI positioning in favor of Quantum Intelligence.",
    contact: {
      email: "operator@quantum.hyba",
    },
  },
  servers: [
    {
      url: "{protocol}://{host}",
      description: "Dynamic Substrate Gateway",
      variables: {
        protocol: {
          default: "https",
          enum: ["http", "https"],
        },
        host: {
          default: "localhost:3000",
        },
      },
    },
  ],
  paths: {
    "/api/qiaas/query": {
      post: {
        tags: ["Quantum Intelligence API"],
        summary: "Execute evidence-sealed Quantum Intelligence query",
        description:
          "Runs predict, explain, optimize, heal, simulate, counterfactual, evidence, or quantum-finance workloads through enterprise-controlled QIaaS rails. Responses include claim boundary, evidence packet, trace ID, customer meter, substrate state, and audit seal.",
        security: [{ BearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["query", "query_type", "context"],
                properties: {
                  query: { type: "string", example: "Explain portfolio convexity." },
                  query_type: {
                    type: "string",
                    enum: ["predict", "explain", "optimize", "heal", "simulate", "counterfactual", "evidence", "quantum-finance"],
                  },
                  context: { type: "object" },
                },
              },
            },
          },
        },
        responses: {
          200: {
            description: "Quantum Intelligence execution artifact sealed and metered.",
            content: {
              "application/json": {
                schema: { $ref: "#/components/schemas/QuantumIntelligenceEnvelope" },
              },
            },
          },
        },
      },
    },
    "/api/qiaas/metrics": {
      get: {
        tags: ["Quantum Intelligence API"],
        summary: "Get QIaaS metering and substrate metrics",
        security: [{ BearerAuth: [] }],
        responses: { 200: { description: "Usage meter, phi coherence, and substrate metrics." } },
      },
    },
    "/api/qiaas/health": {
      get: {
        tags: ["Quantum Intelligence API"],
        summary: "Get Quantum Intelligence API health",
        responses: { 200: { description: "QIaaS health, claim boundary, and substrate state." } },
      },
    },
    "/api/auth/register": {
      post: {
        summary: "User Registration",
        description:
          "Creates a new user profile with a secure hashed password. Idempotently saved in localized JSON DB.",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["username", "password"],
                properties: {
                  username: { type: "string", example: "operator" },
                  password: { type: "string", example: "operator123" },
                },
              },
            },
          },
        },
        responses: {
          201: {
            description: "User profile successfully registered.",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean", example: true },
                    message: { type: "string", example: "User profile registered successfully" },
                    user: {
                      type: "object",
                      properties: {
                        id: { type: "string", example: "u3" },
                        username: { type: "string", example: "operator" },
                        role: { type: "string", example: "operator" },
                      },
                    },
                  },
                },
              },
            },
          },
          400: {
            description: "Bad Request - Missing fields, or username already taken.",
          },
        },
      },
    },
    "/api/auth/login": {
      post: {
        summary: "User Authentication / Login",
        description:
          "Verifies user credentials and yields a valid JSON Web Token (JWT) for session management.",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["username", "password"],
                properties: {
                  username: { type: "string", example: "admin" },
                  password: { type: "string", example: "admin123" },
                },
              },
            },
          },
        },
        responses: {
          200: {
            description: "Login successful. Returns JWT token.",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean", example: true },
                    token: { type: "string", example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." },
                    user: {
                      type: "object",
                      properties: {
                        username: { type: "string", example: "admin" },
                        role: { type: "string", example: "administrator" },
                      },
                    },
                  },
                },
              },
            },
          },
          401: {
            description: "Unauthorized - Invalid username or password.",
          },
        },
      },
    },
    "/api/auth/profile": {
      get: {
        summary: "Get Authenticated User Profile",
        description: "Decodes JWT and returns profile. Requires Bearer Token authorization header.",
        security: [
          {
            BearerAuth: [],
          },
        ],
        responses: {
          200: {
            description: "Valid profile resolved.",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean", example: true },
                    user: {
                      type: "object",
                      properties: {
                        id: { type: "string", example: "u1" },
                        username: { type: "string", example: "admin" },
                        role: { type: "string", example: "administrator" },
                        createdAt: { type: "string", example: "2026-06-09T09:38:40.000Z" },
                      },
                    },
                  },
                },
              },
            },
          },
          401: {
            description: "Unauthorized - Bearer token missing / expired / malformed.",
          },
        },
      },
    },
    "/api/health": {
      get: {
        summary: "Fetch Health & Physics Live Telemetry",
        description:
          "Extracts active atomic stats, quantum coherence coefficient, block height, and golden ratio invariants.",
        responses: {
          200: {
            description: "Telemetry payload retrieved successfully.",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    status: { type: "string", example: "healthy" },
                    timestamp: { type: "string", example: "2026-06-09T09:38:40.000Z" },
                    quantumCoherence: { type: "number", nullable: true, example: null },
                    quantumSpeedupFactor: { type: "number", nullable: true, example: null },
                    phiResonance: { type: "number", nullable: true, example: null },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/api/tests/run": {
      get: {
        summary: "Run Quantum Symmetries Proofs",
        description:
          "Executes mathematical checks testing unitary normalization, maximum Hadamard entropy, and quadratic speedup limits.",
        responses: {
          200: {
            description: "Mathematical tests ran completely.",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean", example: true },
                    tests: { type: "array", items: { type: "object" } },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/api/predict": {
      post: {
        summary: "Calibrate Wave Realignment Solutions",
        description:
          "Accepts high-dimensional core mining inputs to determine golden-ratio Grover iterations and resonance radius bounds.",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  state: { type: "object" },
                },
              },
            },
          },
        },
        responses: {
          200: {
            description: "Calibration parameters calculated.",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean", example: true },
                    params: { type: "object" },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/api/products": {
      get: {
        summary: "Get Seeded Quantum Hardware Products",
        description:
          "Retrieves complete catalog of seeded quantum accelerator chips and co-processors from JSON DB.",
        responses: {
          200: {
            description: "Seeded items resolved successfully.",
            content: {
              "application/json": {
                schema: {
                  type: "array",
                  items: {
                    type: "object",
                    properties: {
                      id: { type: "string", example: "prod-dodeca" },
                      name: {
                        type: "string",
                        example: "Dodecahedral Quantum State Accelerator v2",
                      },
                      description: { type: "string" },
                      category: { type: "string" },
                      qubitDimension: { type: "number" },
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/api/ai/chat": {
      post: {
        summary: "PYTHAGORAS-v2 Chat Coprocessor",
        description:
          "Initiates specialized conversation with the PYTHAGORAS AI reasoning engine (Gemini or Local fallback mode).",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["message"],
                properties: {
                  message: { type: "string", example: "Explain why Grover costs O(sqrt(I)) here." },
                  history: { type: "array", items: { type: "object" } },
                },
              },
            },
          },
        },
        responses: {
          200: {
            description: "Copressor markdown response.",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    reply: { type: "string" },
                    model: { type: "string" },
                    fallback: { type: "boolean" },
                  },
                },
              },
            },
          },
        },
      },
    },
  },
  components: {
    schemas: {
      QuantumIntelligenceEnvelope: {
        type: "object",
        required: ["qi_execution_id", "result", "confidence", "phi_coherence", "substrate_state", "evidence_packet", "usage_meter", "trace", "claim_boundary"],
        properties: {
          qi_execution_id: { type: "string" },
          result: { type: "object" },
          confidence: { type: "number" },
          phi_coherence: { type: "number" },
          substrate_state: { type: "object" },
          evidence_packet: {
            type: "object",
            properties: {
              evidence_id: { type: "string" },
              input_hash: { type: "string" },
              formula_hash: { type: "string" },
              substrate_hash: { type: "string" },
              audit_seal: { type: "string" },
            },
          },
          usage_meter: { type: "object" },
          trace: {
            type: "object",
            properties: { trace_id: { type: "string" }, customer_id: { type: "string" } },
          },
          claim_boundary: {
            type: "string",
            example: "substrate-independent Quantum Intelligence execution; evidence packet governs external claims",
          },
        },
      },
    },
    securitySchemes: {
      BearerAuth: {
        type: "http",
        scheme: "bearer",
        bearerFormat: "JWT",
        description: "Provide JSON Web Token (JWT) for session authentication.",
      },
    },
  },
};
