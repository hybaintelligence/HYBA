import { http, HttpResponse } from "msw";
import { poolConfigFixture, poolsFixture } from "../fixtures/pools";
import { telemetryHealthFixture, telemetrySecurityFixture } from "../fixtures/telemetry";
import { usersFixture } from "../fixtures/users";

const api = (path: string) => `/api${path}`;

export const handlers = [
  http.get(api("/health"), () => HttpResponse.json(telemetryHealthFixture)),
  http.get(api("/security/status"), () => HttpResponse.json(telemetrySecurityFixture)),
  http.get(api("/mining/pools"), () => HttpResponse.json(poolsFixture)),
  http.get(api("/mining/pool-config"), () => HttpResponse.json(poolConfigFixture)),
  http.get(api("/admin/users"), () => HttpResponse.json(usersFixture)),
  http.post(api("/admin/users"), async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ id: 99, role: "operator", ...body }, { status: 201 });
  }),
];
