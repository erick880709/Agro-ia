// La evidencia de Playwright llega en el CTRF de playwright-ctrf-json-reporter: un caso por proyecto,
// con sus reintentos y adjuntos del último intento. Estas pruebas usan esa forma, verificada con 1.63.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fromCtrf, render } from "../../../contracts/output/render-report.mjs";

function project(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "pw-ctrf-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}
function caseFor(root, name, browser, status, retries = 0) {
  const folder = `resources/qa/test-results/run-1/${name.slice(0, 5)}-${browser}${retries ? `-retry${retries}` : ""}`;
  const attachments = [["video", "video/webm", "video.webm"], ["trace", "application/zip", "trace.zip"], ["screenshot", "image/png", "test-finished-1.png"]]
    .map(([kind, contentType, file]) => {
      fs.mkdirSync(path.join(root, folder), { recursive: true });
      fs.writeFileSync(path.join(root, folder, file), `${kind} ${browser}`);
      return { name: kind, contentType, path: `${folder}/${file}` };
    });
  return { name, status, duration: 10, retries, flaky: status === "passed" && retries > 0, suite: [browser, "login.spec.ts"], attachments };
}
function report(tests) {
  const count = (s) => tests.filter((t) => t.status === s).length;
  return { reportFormat: "CTRF", specVersion: "0.1.0", results: { tool: { name: "playwright" }, summary: { tests: tests.length, passed: count("passed"), failed: count("failed"), pending: 0, skipped: count("skipped"), other: 0, start: 0, stop: 1 }, tests } };
}
const expected = ["chromium", "firefox"].map((project) => ({ id: "TC-01", project, priority: "critical" }));
const criteria = [{ id: "gate", status: "met", evidence: "Criterios del plan." }];

test("A failing browser is preserved when another passes, including in the Markdown report", (t) => {
  const root = project(t);
  const ctrf = report([caseFor(root, "TC-01 [critical] login", "chromium", "passed"), caseFor(root, "TC-01 [critical] login", "firefox", "failed")]);
  const [metrics, cases] = fromCtrf(ctrf, root, { expected, exitCriteria: criteria });
  assert.equal(metrics.recommendation, "NO-GO");
  assert.deepEqual(metrics.counts, { passed: 1, failed: 1, blocked: 0, "not-run": 0 });
  const markdown = render(metrics, cases);
  assert.match(markdown, /\| TC-01 \| firefox \| critical \| failed \|/);
  assert.match(markdown, /\| TC-01 \| chromium \| critical \| passed \|/);
});

test("Attachments and retries are preserved per project and critical omissions prevent GO", (t) => {
  const root = project(t);
  const flaky = report([caseFor(root, "TC-01 [critical] login", "chromium", "passed", 1), caseFor(root, "TC-01 [critical] login", "firefox", "passed")]);
  const [retried, cases] = fromCtrf(flaky, root, { expected, exitCriteria: criteria });
  assert.equal(retried.recommendation, "GO with known risks");
  assert.equal(retried.retriedCases, 1);
  assert.equal(retried.casesMissingEvidence, 0);
  assert.deepEqual(cases.find((c) => c.project === "chromium").evidence, ["video.webm", "trace.zip", "test-finished-1.png"]);
  const omitted = report([caseFor(root, "TC-01 [critical] login", "chromium", "passed")]);
  assert.equal(fromCtrf(omitted, root, { expected, exitCriteria: criteria })[0].recommendation, "NO-GO");
});

test("Duplicate case/project is rejected instead of overwritten", (t) => {
  const root = project(t);
  const duplicated = report([caseFor(root, "TC-01 [critical] login", "chromium", "passed"), caseFor(root, "TC-01 [critical] otro título", "chromium", "passed")]);
  assert.throws(() => fromCtrf(duplicated, root, { expected, exitCriteria: criteria }), /duplicado en el CTRF/);
});

test("Setup and teardown projects are not cases; a failed setup blocks GO", (t) => {
  const root = project(t);
  const setup = { name: "autenticar usuario de pruebas", status: "passed", duration: 5, suite: ["setup", "auth.setup.ts"], filePath: "tests/auth.setup.ts" };
  const passing = report([setup, caseFor(root, "TC-01 [critical] login", "chromium", "passed"), caseFor(root, "TC-01 [critical] login", "firefox", "passed")]);
  const [metrics, cases] = fromCtrf(passing, root, { expected, exitCriteria: criteria });
  assert.equal(metrics.recommendation, "GO");
  assert.equal(cases.length, 2);
  const failed = report([{ ...setup, status: "failed" }]);
  assert.equal(fromCtrf(failed, root, { expected, exitCriteria: criteria })[0].recommendation, "NO-GO");
});
