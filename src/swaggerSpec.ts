export const swaggerDocument = {
  openapi: "3.0.0",
  info: {
    title: "Quantum ASIC Annihilation Console API",
    version: "2.5.0",
    description:
      "Full-stack APIs supporting Dodecahedral Hilbert Space Grover search optimizations, mathematical proofs, session JWT auth, and live physical telemetry.",
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
