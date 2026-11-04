package qa;

import java.util.UUID;

/** Define la carpeta de evidencia de una corrida para todos los ejecutores de pruebas. */
public final class QaEvidence {
    private static final String RUN_ID = resolveRunId();

    private QaEvidence() { }

    private static String resolveRunId() {
        String runId = System.getenv("QA_RUN_ID");
        if (runId == null || runId.isBlank()) {
            return UUID.randomUUID().toString();
        }
        if (!runId.matches("[a-zA-Z0-9][a-zA-Z0-9._-]*")) {
            throw new IllegalArgumentException("QA_RUN_ID debe ser un ID sin separadores de ruta");
        }
        return runId;
    }

    public static String reportDirectory() {
        String directory = "resources/qa/reports/" + RUN_ID + "/karate-reports";
        System.out.println("Evidencia QA: " + directory);
        return directory;
    }
}
