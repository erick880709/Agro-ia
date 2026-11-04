// Define las URLs por ambiente en este archivo. Selecciona uno con TEST_ENV=dev|qa|stg.
// BASE_URL permite sobrescribir la URL del ambiente seleccionado.
const ENVS = {
  local: { baseURL: '{{BASE_URL_LOCAL}}' },
  dev: { baseURL: '{{BASE_URL_DEV}}' },
  qa: { baseURL: '{{BASE_URL_QA}}' },
  stg: { baseURL: '{{BASE_URL_STG}}' },
} as const;

export type EnvName = keyof typeof ENVS;

const name = (process.env.TEST_ENV ?? '{{DEFAULT_ENV}}') as EnvName;
if (!(name in ENVS)) {
  throw new Error(`TEST_ENV no soportado: "${name}". Usar: ${Object.keys(ENVS).join(', ')}`);
}

export const env = {
  name,
  baseURL: process.env.BASE_URL ?? ENVS[name].baseURL,
};

/** Lee una variable obligatoria y lanza un error con su nombre si falta. */
export function requerida(variable: string): string {
  const valor = process.env[variable];
  if (!valor) throw new Error(`Falta la variable de entorno ${variable} (ver .env.example)`);
  return valor;
}
