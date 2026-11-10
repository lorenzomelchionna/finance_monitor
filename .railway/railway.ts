import { defineRailway, project, service, volume } from "railway/iac";

export const partial = "finance-monitor";

export default defineRailway(() => {
  // Existing volume holding the SQLite DB (/data/finance_monitor.db).
  // Must stay declared and mounted, or `config apply` detaches it.
  const data = volume("finance-monitor-volume", { region: "sfo", sizeMB: 5000 });

  const financeMonitor = service("finance-monitor", {
    build: { buildEnvironment: "V3", builder: "DOCKERFILE", dockerfilePath: "Dockerfile" },
    healthcheck: "/health",
    healthcheckTimeout: 120,
    replicas: { "sfo": 1 },
    deploy: {
      sleepApplication: true,
      // restartPolicyType omitted: ON_FAILURE is Railway's default and is
      // stored as null, so declaring it produces a perpetual plan diff.
      restartPolicyMaxRetries: 3,
    },
    volumeMounts: { "/data": data },
  });

  return project("finance-monitor", {
    // Variables (incl. FM_PASSWORD) stay managed on Railway, never in the repo.
    variables: { managed: false },
    resources: [data, financeMonitor],
  });
});
