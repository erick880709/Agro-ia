// Ejecuta el scaffold con Playwright real, sin navegador ni aplicación externa.
// Uso: node native-ctrf.mjs --dependencies <proyecto-con-node_modules> [--keep]
// Las dependencias son las del proyecto generado; no instala paquetes globales.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { parseArgs } from 'node:util';
import { fileURLToPath, pathToFileURL } from 'node:url';

const {values} = parseArgs({options:{dependencies:{type:'string'},keep:{type:'boolean',default:false}}});
assert(values.dependencies, 'Declara --dependencies con un proyecto que tenga las dependencias de la plantilla instaladas.');
const modules = fs.realpathSync(path.join(path.resolve(values.dependencies), 'node_modules'));
const cli = path.join(modules, '@playwright/test/cli.js');
assert(fs.existsSync(cli), 'Falta @playwright/test en el proyecto indicado.');
assert(fs.existsSync(path.join(modules, 'playwright-ctrf-json-reporter')), 'Falta playwright-ctrf-json-reporter.');
const skill = fileURLToPath(new URL('../', import.meta.url));
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pw-native-ctrf-'));
try {
  const scaffold = spawnSync(process.env.PYTHON ?? (process.platform === 'win32' ? 'python' : 'python3'),
    [path.join(skill,'scripts/scaffold.py'),'--nombre','ctrf-native','--salida',root,'--default-env','local','--ci',''],
    {encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}});
  assert.equal(scaffold.status,0,scaffold.stdout+scaffold.stderr);
  const project = path.join(root,'ctrf-native');
  fs.symlinkSync(modules,path.join(project,'node_modules'),process.platform === 'win32' ? 'junction' : 'dir');
  const fixtures = path.join(project,'native-tests');fs.mkdirSync(fixtures);
  fs.writeFileSync(path.join(fixtures,'report.spec.ts'), `
import { test, expect } from '@playwright/test';
import fs from 'node:fs';
async function context(info) {
  // Playwright normaliza mayúsculas en outputDir; el fixture evita compartir el archivo fuente.
  const suffix = Buffer.from(info.project.name).toString('hex');
  const file = info.outputPath('contexto-' + suffix + '.json');
  fs.writeFileSync(file, JSON.stringify({project:info.project.name,retry:info.retry}));
  await info.attach('contexto', {path:file,contentType:'application/json'});
}
test('API-01 [critical] aprobado', {
  annotation: [{type:'case',description:'API-01'},{type:'priority',description:'critical'}],
}, async ({}, info) => {
  // El adjunto ausente va primero: no debe impedir organizar los siguientes.
  if (process.env.CTRF_SCENARIO === 'missing') {
    info.attachments.push({name:'ausente',path:info.outputPath('no-existe.txt'),contentType:'text/plain'});
  }
  await context(info);
  await info.attach('nota', {body:Buffer.from('adjunto en memoria'),contentType:'text/plain'});
  await info.attach('captura-jpg', {body:Buffer.from('jpg'),contentType:'image/jpeg'});
  await info.attach('captura-png', {body:Buffer.from('png'),contentType:'image/png'});
  expect(1).toBe(1);
});
if (process.env.CTRF_SCENARIO === 'mixed') {
  test('API-02 [high] fallido', async () => { expect(1).toBe(2); });
  test.skip('API-03 [medium] omitido', async () => {});
  test('API-04 [medium] reintento', async ({}, info) => { await context(info); expect(info.retry).toBe(1); });
}
if (process.env.CTRF_SCENARIO === 'duplicate') {
  test('API-01 [critical] segundo caso con el mismo ID', async () => {});
}
`);
  fs.writeFileSync(path.join(fixtures,'global-teardown.ts'), `export default async () => { throw new Error('CTRF_NATIVE_GLOBAL_ERROR'); };`);
  fs.writeFileSync(path.join(project,'native.config.ts'), `
import { defineConfig } from '@playwright/test';
import config from './playwright.config';
export default defineConfig({ ...config,
  testDir:'./native-tests', projects:process.env.CTRF_SCENARIO === 'projects'
    ? [{name:'chromium-desktop',use:{browserName:'chromium'}},{name:'chromium-mobile',use:{browserName:'chromium'}}]
    : [{name:'api'}], workers:2, retries:1, fullyParallel:false,
  globalTeardown:process.env.CTRF_SCENARIO === 'global' ? './native-tests/global-teardown.ts' : undefined,
});
`);
  for (const [mode,scenario] of [['local','clean'],['local','mixed'],['ci','mixed'],['local','global'],['local','projects'],['ci','projects'],['local','missing'],['local','duplicate']]) {
    const runId=`native-${mode}-${scenario}`;
    const run = spawnSync(process.execPath,[cli,'test','--config','native.config.ts'],{
      cwd:project,encoding:'utf8',timeout:60_000,
      env:{...process.env,CI:mode==='ci'?'1':'',QA_RUN_ID:runId,QA_SLOWMO_MS:'0',TEST_ENV:'local',CTRF_SCENARIO:scenario},
    });
    assert.equal(run.status,['clean','projects'].includes(scenario)?0:1,run.stdout+run.stderr+(run.error?.message??''));
    const file=path.join(project,'resources/qa/reports',runId,'ctrf.json');
    assert(fs.existsSync(file),'El reporter no generó CTRF para '+runId);
    const report=JSON.parse(fs.readFileSync(file,'utf8'));
    assert.equal(report.reportFormat,'CTRF');
    assert.equal(report.results.tool.name,'playwright');
    const {tests,summary}=report.results;
    assert.equal(summary.tests,tests.length);
    assert.equal(tests.length,scenario==='mixed'?4:['projects','duplicate'].includes(scenario)?2:1);
    for (const status of ['passed','failed','skipped','pending','other']) {
      assert.equal(summary[status],tests.filter(test=>test.status===status).length);
    }
    const passed=tests.find(test=>test.name==='API-01 [critical] aprobado');
    assert.equal(passed.status,'passed');
    assert(passed.extra.annotations.some(a=>a.type==='case'&&a.description==='API-01'));
    assert(Number.isFinite(passed.duration)&&passed.duration>=0);
    const attachment=passed.attachments.find(a=>a.name==='contexto');
    assert(attachment?.path,'El reporter debe conservar la ruta del adjunto');
    assert(fs.existsSync(path.resolve(project,attachment.path)));
    assert.equal(attachment.path,`resources/qa/API-01/${runId}/${passed.suite[0]}/attempt-0/contexto.json`);
    for (const item of tests) for (const attached of item.attachments ?? []) {
      if (['missing','duplicate'].includes(scenario)) continue; // Los errores conservan las referencias originales restantes.
      assert(!path.isAbsolute(attached.path),'La ruta de evidencia debe ser relativa al proyecto');
      assert(fs.existsSync(path.resolve(project,attached.path)));
    }
    // Las capturas en memoria conservan su extensión y comparten la numeración.
    assert.deepEqual(['captura-jpg','captura-png'].map(name=>path.basename(passed.attachments.find(a=>a.name===name).path)),
      ['screenshot-0.jpg','screenshot-1.png']);
    const body=passed.attachments.find(a=>a.name==='nota');
    assert.equal(fs.readFileSync(path.resolve(project,body.path),'utf8'),'adjunto en memoria');
    if (scenario==='projects') {
      assert.deepEqual(tests.map(t=>t.suite[0]).sort(),['chromium-desktop','chromium-mobile']);
      for (const item of tests) {
        const data=JSON.parse(fs.readFileSync(path.resolve(project,item.attachments.find(a=>a.name==='contexto').path),'utf8'));
        assert.equal(data.project,item.suite[0]);
      }
    }
    if (scenario==='mixed') {
      assert.equal(summary.passed,2);assert.equal(summary.failed,1);assert.equal(summary.skipped,1);
      const failure=tests.find(test=>test.name.startsWith('API-02'));
      assert(failure.message?.length,'El fallo debe conservar su mensaje');
      const retried=tests.find(test=>test.name.startsWith('API-04'));
      assert.equal(retried.status,'passed');assert.equal(retried.retries,1);assert.equal(retried.flaky,true);
      // Los enlaces a intentos previos son solo del CTRF: el reporte JSON de Playwright no los recibe.
      const native=JSON.parse(fs.readFileSync(path.join(project,'resources/qa/test-results',runId,'results.json'),'utf8'));
      const names=JSON.stringify(native).match(/"name":"attempt-\d+\//g);
      assert.equal(names,null,'results.json no debe incluir adjuntos attempt-<n>/');
      for (const [name,attempt] of [['contexto',1],['attempt-0/contexto',0]]) {
        const attached=retried.attachments.find(a=>a.name===name);
        assert(attached,'El CTRF debe enlazar la evidencia de cada intento');
        assert.equal(attached.path,`resources/qa/API-04/${runId}/api/attempt-${attempt}/contexto.json`);
        const data=JSON.parse(fs.readFileSync(path.resolve(project,attached.path),'utf8'));
        assert.equal(data.retry,attempt);
      }
    }
    if (scenario==='missing') {
      assert.equal(summary.passed,1);
      const missing=report.results.extra.errors.filter(error=>error.message.includes('No se pudo organizar'));
      assert.equal(missing.length,1,'El adjunto fallido se informa una sola vez');
      assert(missing[0].message.includes('ausente'));
      for (const name of ['contexto','nota']) {
        const attached=passed.attachments.find(a=>a.name===name);
        assert(attached.path.startsWith(`resources/qa/API-01/${runId}/api/attempt-0/`),'Los demás adjuntos se organizan igual');
        assert(fs.existsSync(path.resolve(project,attached.path)));
      }
    }
    if (scenario==='duplicate') {
      assert(report.results.extra.errors.some(error=>error.message.includes('Caso/proyecto duplicado')));
    }
    if (scenario==='global') {
      assert.equal(summary.passed,1);assert.equal(summary.failed,0);
      assert(report.results.extra.errors.some(error=>error.message.includes('CTRF_NATIVE_GLOBAL_ERROR')));
    }
    console.log(`${runId}: CTRF nativo verificado, ${tests.length} casos, exit ${run.status}`);
  }
  const preserved=path.join(project,'resources/qa/API-01/native-local-clean/api/attempt-0/contexto.json');
  const original=fs.readFileSync(preserved);
  const previousCtrf=fs.readFileSync(path.join(project,'resources/qa/reports/native-local-clean/ctrf.json'));
  const previousFiles=fs.readdirSync(path.dirname(preserved)).sort();
  const repeated=spawnSync(process.execPath,[cli,'test','--config','native.config.ts'],{
    cwd:project,encoding:'utf8',timeout:60_000,
    env:{...process.env,CI:'',QA_RUN_ID:'native-local-clean',QA_SLOWMO_MS:'0',TEST_ENV:'local',CTRF_SCENARIO:'clean'},
  });
  assert.equal(repeated.status,1,'Reutilizar runId no puede sobrescribir evidencia ni pasar inadvertido');
  assert.deepEqual(fs.readFileSync(preserved),original);
  assert.deepEqual(fs.readFileSync(path.join(project,'resources/qa/reports/native-local-clean/ctrf.json')),previousCtrf,'El CTRF anterior se conserva');
  assert.deepEqual(fs.readdirSync(path.dirname(preserved)).sort(),previousFiles,'La corrida repetida no agrega archivos a la anterior');
  assert(repeated.stdout.includes('ya tiene CTRF')||repeated.stderr.includes('ya tiene CTRF'),repeated.stdout+repeated.stderr);
  console.log('Las ocho ejecuciones y la protección contra sobrescritura usaron la plantilla, sin conversión ni Ranger.');

  const invoke = (args, runId, env = {}) => spawnSync(process.execPath, [cli,...args], {
    cwd:project,encoding:'utf8',timeout:60_000,
    env:{...process.env,CI:'',QA_RUN_ID:runId,QA_SLOWMO_MS:'0',TEST_ENV:'local',CTRF_SCENARIO:'clean',...env},
  });
  const load = runId => JSON.parse(fs.readFileSync(path.join(project,'resources/qa/reports',runId,'ctrf.json'),'utf8'));
  const reporter = path.join(project,'reporters/evidence-ctrf.ts');
  const config = (file, runId, projects = [{name:'api'}]) => {
    fs.mkdirSync(path.dirname(path.join(project,file)),{recursive:true});
    fs.writeFileSync(path.join(project,file), `
import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:${JSON.stringify(fixtures)},workers:2,retries:1,
 projects:${JSON.stringify(projects)},reporter:[[${JSON.stringify(reporter)},{runId:${JSON.stringify(runId)},
 projectRoot:${JSON.stringify(project)},outputDir:${JSON.stringify(path.join(project,'resources/qa/reports',runId))},outputFile:'ctrf.json',annotations:true}]]});`);
  };
  config('nested/check.config.ts','regression-nested');
  let execution = invoke(['test','--config','nested/check.config.ts'],'regression-nested');
  assert.equal(execution.status,0,execution.stdout+execution.stderr);
  assert(load('regression-nested').results.tests[0].attachments.every(a=>fs.existsSync(path.resolve(project,a.path))));
  assert(!fs.existsSync(path.join(project,'nested/resources')));

  config('check.config.ts','regression-case',[{name:'Chromium'},{name:'chromium'}]);
  execution = invoke(['test','--config','check.config.ts'],'regression-case');
  assert.equal(execution.status,0,execution.stdout+execution.stderr);
  const caseReport=load('regression-case');
  const casePaths=caseReport.results.tests.map(t=>t.attachments.find(a=>a.name==='contexto').path);
  assert.equal(new Set(casePaths.map(p=>p.toLowerCase())).size,2);
  for (const item of caseReport.results.tests) {
    const data=JSON.parse(fs.readFileSync(path.resolve(project,item.attachments.find(a=>a.name==='contexto').path),'utf8'));
    assert.equal(data.project,item.suite[0]);
  }

  // Un runId reservado en Windows no puede usarse como carpeta.
  config('check.config.ts','nul');
  execution = invoke(['test','--config','check.config.ts'],'nul');
  assert.notEqual(execution.status,0,'Un runId reservado debe fallar la corrida');
  assert.match(execution.stdout+execution.stderr,/runId inválido/);

  config('check.config.ts','regression-write');
  fs.mkdirSync(path.join(project,'resources/qa/reports/regression-write/ctrf.json'),{recursive:true});
  execution = invoke(['test','--config','check.config.ts'],'regression-write');
  assert.equal(execution.status,1,'Un fallo de escritura del CTRF debe fallar la corrida');

  const outside=path.join(root,'outside');fs.mkdirSync(outside);
  const link=path.join(project,'resources/qa/API-01/regression-link/api');
  fs.mkdirSync(path.dirname(link),{recursive:true});
  fs.symlinkSync(outside,link,process.platform==='win32'?'junction':'dir');
  config('check.config.ts','regression-link');
  execution = invoke(['test','--config','check.config.ts'],'regression-link');
  assert.equal(execution.status,1,'No se debe escribir a través de enlaces en el destino');
  assert.deepEqual(fs.readdirSync(outside),[]);
  assert(load('regression-link').results.extra.errors.some(e=>e.message.includes('Destino no permitido')));

  // Usa la misma unión que el workflow generado, con dos shards, fallos, bodies y retries.
  const blobs=path.join(project,'merge-inputs');fs.mkdirSync(blobs);
  for (const shard of [1,2]) {
    execution=invoke(['test','--config','native.config.ts',`--shard=${shard}/2`],`regression-shard-${shard}`,{CI:'1',CTRF_SCENARIO:'mixed'});
    assert([0,1].includes(execution.status),execution.stdout+execution.stderr);
    for (const zip of fs.readdirSync(path.join(project,'blob-report')).filter(f=>f.endsWith('.zip'))) {
      fs.copyFileSync(path.join(project,'blob-report',zip),path.join(blobs,`${shard}-${zip}`));
    }
  }
  execution=invoke(['merge-reports','--config','reporters/merge.config.ts',blobs],'regression-merged');
  assert.equal(execution.status,0,execution.stdout+execution.stderr);
  const merged=load('regression-merged');
  // El HTML y el JUnit unidos quedan junto al CTRF, dentro de lo que publica el workflow.
  for (const file of ['html/index.html','junit.xml']) {
    assert(fs.existsSync(path.join(project,'resources/qa/reports/regression-merged',file)),`Falta ${file} del merge`);
  }
  assert(!fs.existsSync(path.join(project,'reporters/resources')),'El merge no escribe reportes bajo reporters/');
  // El freno del workflow sobre el CTRF unido: un caso crítico acordado que no corrió da NO-GO.
  const expectedFile=path.join(project,'casos.json');
  fs.writeFileSync(expectedFile,JSON.stringify([
    ...merged.results.tests.map(t=>({id:t.name.match(/^[A-Z]+-\d+/)[0],project:'api',priority:t.name.match(/\[(\w+)\]/)[1]})),
    {id:'API-99',project:'api',priority:'critical'},
  ]));
  const gate=spawnSync(process.execPath,[path.join(skill,'../../contracts/output/generate-execution-report.mjs'),
    '--ctrf','resources/qa/reports/regression-merged/ctrf.json','--expected',expectedFile,
    '--out','resources/qa/reports/regression-merged/execution-report.md','--fail-on-no-go'],
    {cwd:project,encoding:'utf8'});
  assert.equal(gate.status,2,gate.stdout+gate.stderr);
  assert.match(fs.readFileSync(path.join(project,'resources/qa/reports/regression-merged/execution-report.md'),'utf8'),/Veredicto: NO-GO/);
  assert.equal(merged.results.summary.tests,4);
  assert.equal(merged.results.summary.failed,1);
  for (const item of merged.results.tests) for (const attached of item.attachments ?? []) {
    assert(!path.isAbsolute(attached.path));
    assert(attached.path.includes('/regression-merged/'));
    assert(fs.existsSync(path.resolve(project,attached.path)));
  }
  const mergedBody=merged.results.tests.find(t=>t.name==='API-01 [critical] aprobado').attachments.find(a=>a.name==='nota');
  assert.equal(fs.readFileSync(path.resolve(project,mergedBody.path),'utf8'),'adjunto en memoria');
  const mergedRetry=merged.results.tests.find(t=>t.name.startsWith('API-04'));
  assert(mergedRetry.attachments.some(a=>a.name==='attempt-0/contexto'));
  assert(mergedRetry.attachments.some(a=>a.name==='contexto'&&a.path.includes('/attempt-1/')));
  fs.mkdirSync(path.join(project,'resources/qa/reports/regression-merge-write/ctrf.json'),{recursive:true});
  execution=invoke(['merge-reports','--config','reporters/merge.config.ts',blobs],'regression-merge-write');
  assert.equal(execution.status,1,'Un fallo al escribir el CTRF consolidado también debe fallar el comando');

  // Reproduce onError con la metadata que proporciona Playwright.
  const ts=(await import(pathToFileURL(path.join(modules,'typescript/lib/typescript.js')))).default;
  const compiled=ts.transpileModule(fs.readFileSync(reporter,'utf8'),{compilerOptions:{
    module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true,
  }}).outputText;
  const compiledFile=path.join(project,'reporters/check.cjs');fs.writeFileSync(compiledFile,compiled);
  const loaded=(await import(pathToFileURL(compiledFile))).default;
  const instance=new loaded.default({runId:'regression-worker',projectRoot:project,outputDir:'resources/qa/reports/regression-worker',outputFile:'ctrf.json'});
  instance.onBegin({configFile:path.join(project,'native.config.ts')},{allTests:()=>[],suites:[],tests:[]});
  instance.onError({message:'Error con metadata de worker'},{workerIndex:7,parallelIndex:0});
  await instance.onEnd();
  assert.equal(load('regression-worker').results.extra.errors[0].workerIndex,7);
  console.log('Seis regresiones verificadas: raíz, mayúsculas, escritura, enlaces, unión de CI y metadata del worker.');
} finally {
  if (values.keep) console.log(`Fixtures y resultados conservados en ${root}`);
  else {
    assert.equal(path.dirname(root),path.resolve(os.tmpdir()),'Directorio temporal fuera de la ubicación prevista');
    fs.rmSync(root,{recursive:true,force:true});
  }
}
