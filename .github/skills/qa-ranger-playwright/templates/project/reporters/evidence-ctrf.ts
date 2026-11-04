// Organiza adjuntos; el paquete oficial sigue generando el CTRF.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import CtrfReporter from 'playwright-ctrf-json-reporter';
import type { FullConfig, FullResult, Reporter, Suite, TestCase, TestError, TestResult, WorkerInfo } from '@playwright/test/reporter';

const CASE_ID = /\b(?:TC|SEC|FRAUD|API|A11Y|UT|PERF)-[A-Za-z0-9-]+\b/i;
function segment(value: string): string {
  if (/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(value) && !value.endsWith('.') &&
      !/^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(value)) return value;
  const slug = value.replace(/[^a-zA-Z0-9-]/g, '-').slice(0, 40) || 'sin-nombre';
  return `${slug}-${createHash('sha256').update(value).digest('hex').slice(0, 10)}`;
}

function within(root: string, target: string): boolean {
  const relative = path.relative(root, target);
  return relative === '' || (!path.isAbsolute(relative) && relative !== '..' && !relative.startsWith(`..${path.sep}`));
}

// Comprueba cada componente antes de crear el siguiente: no sigue enlaces ni junctions.
function directory(root: string, target: string): void {
  if (!within(root, target)) throw new Error('Destino fuera del proyecto');
  let current = root;
  for (const part of path.relative(root, target).split(path.sep).filter(Boolean)) {
    current = path.join(current, part);
    if (!fs.existsSync(current)) {
      // lstat también detecta enlaces rotos, que existsSync considera ausentes.
      const entry = fs.lstatSync(current, { throwIfNoEntry: false });
      if (entry) throw new Error(`Enlace no permitido en destino: ${current}`);
      fs.mkdirSync(current);
    }
    const entry = fs.lstatSync(current);
    if (entry.isSymbolicLink() || !entry.isDirectory() || !within(root, fs.realpathSync(current))) {
      throw new Error(`Destino no permitido: ${current}`);
    }
  }
}

function folders(values: string[]): Map<string, string> {
  const distinct = [...new Set(values)];
  const groups = new Map<string, string[]>();
  for (const value of distinct) {
    const key = segment(value).toLowerCase();
    groups.set(key, [...(groups.get(key) ?? []), value]);
  }
  return new Map(distinct.map(value => [value, groups.get(segment(value).toLowerCase())!.length > 1
    ? `${segment(value)}-${createHash('sha256').update(value).digest('hex').slice(0, 10)}` : segment(value)]));
}

// Normaliza solo la salida CTRF; los otros reporters reciben rutas absolutas válidas.
class ProjectCtrfReporter extends CtrfReporter {
  constructor(options: ConstructorParameters<typeof CtrfReporter>[0], private readonly root: string) { super(options); }
  override writeReportToFile(data: Parameters<CtrfReporter['writeReportToFile']>[0]): void {
    for (const test of data.results.tests) for (const attachment of test.attachments ?? []) {
      if (!attachment.path) continue;
      const absolute = path.resolve(this.root, attachment.path);
      if (!within(this.root, absolute)) throw new Error('Adjunto CTRF fuera del proyecto');
      attachment.path = path.relative(this.root, absolute).split(path.sep).join('/');
    }
    super.writeReportToFile(data);
  }
}

type Options = ConstructorParameters<typeof CtrfReporter>[0] & { runId: string; projectRoot?: string };

export default class EvidenceCtrfReporter implements Reporter {
  private readonly ctrf: ProjectCtrfReporter;
  private readonly runId: string;
  private readonly root: string;
  private readonly reportFile: string;
  private canWrite = false;
  private reused = false;
  private suite?: Suite;
  private failed = false;
  private readonly owners = new Map<string, string>();
  private readonly copied = new WeakSet<object>();
  private readonly names = new Map<string, Set<string>>();
  private projectFolders = new Map<string, string>();
  private caseFolders = new Map<string, string>();

  constructor(options: Options) {
    this.runId = options.runId;
    // Escenario: un runId como con o nul es un nombre reservado en Windows y no sirve como carpeta.
    if (typeof this.runId !== 'string' || !/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(this.runId) || this.runId.endsWith('.') ||
        /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(this.runId)) {
      throw new Error('runId inválido para organizar evidencias');
    }
    this.root = fs.realpathSync(path.resolve(options.projectRoot ?? process.cwd()));
    const outputDir = path.resolve(this.root, options.outputDir ?? 'ctrf');
    const file = options.outputFile ?? 'ctrf-report.json';
    this.reportFile = path.resolve(outputDir, file.endsWith('.json') ? file : `${file}.json`);
    this.ctrf = new ProjectCtrfReporter({ ...options, outputDir }, this.root);
  }

  onBegin(config: FullConfig, suite: Suite): void {
    this.suite = suite;
    this.projectFolders = folders(suite.allTests().map(test => test.parent.project()?.name || 'sin-proyecto'));
    this.caseFolders = folders(suite.allTests().map(test => this.caseId(test)));
    try {
      directory(this.root, path.dirname(this.reportFile));
      const entry = fs.lstatSync(this.reportFile, { throwIfNoEntry: false });
      if (entry?.isSymbolicLink()) throw new Error('Enlace no permitido como archivo CTRF');
      // Escenario: se repite un runId que ya tiene CTRF.
      // No se escribe nada para conservar el CTRF y la evidencia de la corrida anterior.
      if (entry?.isFile()) {
        this.reused = true;
        throw new Error(`El runId ${this.runId} ya tiene CTRF; usa un runId nuevo`);
      }
      this.canWrite = true;
      this.ctrf.onBegin(config, suite);
    } catch (error) { this.error('No se pudo preparar CTRF', error); }
  }

  onError(error: TestError, workerInfo?: WorkerInfo): void { this.ctrf.onError(error, workerInfo); }
  printsToStdio(): boolean { return false; }

  private caseId(test: TestCase): string {
    return test.annotations.find(a => a.type === 'case')?.description || test.title.match(CASE_ID)?.[0] ||
      `SIN-ID-${createHash('sha256').update(test.id).digest('hex').slice(0, 10)}`;
  }

  private error(context: string, error: unknown): void {
    this.failed = true;
    const message = `${context}: ${String(error)}`;
    console.error(message);
    this.ctrf.onError({ message });
  }

  // Los adjuntos en memoria deben existir como archivos antes de que blob los serialice.
  onStepEnd(test: TestCase, result: TestResult): void { this.organize(test, result); }
  onTestEnd(test: TestCase, result: TestResult): void { this.organize(test, result); }

  private organize(test: TestCase, result: TestResult): void {
    if (this.reused) return;
    try {
      const caseId = this.caseId(test);
      const project = test.parent.project()?.name || 'sin-proyecto';
      const relative = path.join('resources', 'qa', this.caseFolders.get(caseId) ?? segment(caseId), this.runId,
        this.projectFolders.get(project) ?? segment(project), `attempt-${result.retry}`);
      const destinationDir = path.join(this.root, relative);
      // Un ID repetido en el mismo proyecto no puede sobrescribir otra prueba.
      const owner = this.owners.get(destinationDir);
      if (owner && owner !== test.id) throw new Error(`Caso/proyecto duplicado: ${caseId} / ${project}`);
      this.owners.set(destinationDir, test.id);
      const names = this.names.get(destinationDir) ?? new Set<string>();
      this.names.set(destinationDir, names);
      for (const attachment of result.attachments) {
        if (this.copied.has(attachment)) continue;
        if (attachment.contentType === 'application/vnd.ctrf.message+json') continue;
        if (!attachment.path && attachment.body === undefined) continue;
        // Escenario: un adjunto no se puede copiar (no existe, destino inválido).
        // Se registra una sola vez y no impide organizar los demás adjuntos del intento.
        this.copied.add(attachment);
        try {
          const extension = attachment.path ? path.extname(attachment.path) :
            attachment.contentType === 'image/png' ? '.png' :
            attachment.contentType === 'image/jpeg' ? '.jpg' :
            attachment.contentType === 'application/json' ? '.json' :
            attachment.contentType.startsWith('text/') ? '.txt' : '.bin';
          let name = attachment.name === 'video' ? `video${extension}` :
            attachment.name === 'trace' ? `trace${extension}` :
            attachment.contentType.startsWith('image/') ? `screenshot-0${extension}` :
            `${segment(attachment.name)}${path.extname(attachment.name) ? '' : extension}`;
          // Las capturas se numeran desde 0 sin importar su extensión; los demás duplicados reciben un sufijo desde 2.
          const base = name, screenshot = base === `screenshot-0${extension}` && attachment.contentType.startsWith('image/');
          const taken = (candidate: string) => screenshot
            ? [...names].some(used => path.parse(used).name === path.parse(candidate).name.toLowerCase())
            : names.has(candidate.toLowerCase());
          for (let index = screenshot ? 1 : 2; taken(name); index++) {
            name = screenshot ? `screenshot-${index}${extension}` : `${path.parse(base).name}-${index}${path.extname(base)}`;
          }
          directory(this.root, destinationDir);
          const destination = path.join(destinationDir, name);
          // No se sobrescriben evidencias de una corrida previa con el mismo runId.
          if (attachment.path) fs.copyFileSync(path.resolve(this.root, attachment.path), destination, fs.constants.COPYFILE_EXCL);
          else fs.writeFileSync(destination, attachment.body!, { flag: 'wx' });
          // El nombre se reserva solo cuando la copia existe.
          names.add(name.toLowerCase());
          attachment.path = destination;
        } catch (error) {
          this.error(`No se pudo organizar la evidencia de ${test.title} (${attachment.name})`, error);
        }
      }
    } catch (error) {
      this.error(`No se pudo organizar la evidencia de ${test.title}`, error);
    }
  }

  async onEnd(result?: FullResult): Promise<void> {
    // CTRF conserva un resultado final por prueba; enlaza también la evidencia de retries anteriores.
    // Escenario: los demás reporters reciben el mismo TestResult después de este.
    // Los enlaces se agregan solo mientras se escribe el CTRF y luego se retiran.
    const linked: Array<[TestResult, number]> = [];
    for (const test of this.suite?.allTests() ?? []) {
      const last = test.results.at(-1);
      if (!last) continue;
      const before = last.attachments.length;
      for (const attempt of test.results.slice(0, -1)) {
        last.attachments.push(...attempt.attachments.filter(a => a.path).map(a => ({
          ...a, name: `attempt-${attempt.retry}/${a.name}`,
        })));
      }
      if (last.attachments.length > before) linked.push([last, before]);
    }
    if (this.canWrite) try {
      directory(this.root, path.dirname(this.reportFile));
      if (fs.lstatSync(this.reportFile, { throwIfNoEntry: false })?.isSymbolicLink()) throw new Error('Enlace no permitido como archivo CTRF');
      this.ctrf.onEnd();
      // El paquete imprime errores de escritura sin lanzarlos. Un reporte viejo tampoco acredita esta corrida.
      const written = JSON.parse(fs.readFileSync(this.reportFile, 'utf8'));
      if (written.reportFormat !== 'CTRF' || written.reportId !== this.ctrf.ctrfReport.reportId) {
        throw new Error('No se escribió el CTRF de esta corrida');
      }
    } catch (error) { this.error('No se pudo escribir CTRF', error); }
    for (const [last, before] of linked) last.attachments.splice(before);
    if (this.failed) {
      // merge-reports comprueba errores del reporter, no el estado devuelto por onEnd.
      if (result) result.status = 'failed';
      throw new Error('No se completó la entrega de evidencias y CTRF');
    }
  }
}
