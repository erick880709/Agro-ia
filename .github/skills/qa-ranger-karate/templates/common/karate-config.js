function fn() {
  // Selecciona el ambiente con -Dkarate.env=qa, KARATE_ENV o karate run -e qa.
  // El ambiente predeterminado es dev.
  var env = karate.env || 'dev';
  karate.log('karate.env =', env);

  // Lee los secretos desde propiedades -D o variables de entorno. No los guardes en el repositorio.
  function secreto(prop, envVar) {
    return karate.properties[prop] || java.lang.System.getenv(envVar) || null;
  }

  var ambientes = {
    dev: { baseUrl: '{{BASE_URL_DEV}}', tokenUrl: '{{TOKEN_URL_DEV}}' },
    qa:  { baseUrl: '{{BASE_URL_QA}}',  tokenUrl: '{{TOKEN_URL_QA}}' },
    stg: { baseUrl: '{{BASE_URL_STG}}', tokenUrl: '{{TOKEN_URL_STG}}' }
  };
  var amb = ambientes[env];
  if (!amb) {
    karate.fail('ambiente no soportado: ' + env + ' (usar dev, qa o stg)');
  }

  var config = {
    env: env,
    baseUrl: karate.properties['baseUrl'] || amb.baseUrl,
    authConfig: {
      tokenUrl: amb.tokenUrl,
      clientId: secreto('client.id', 'CLIENT_ID'),
      clientSecret: secreto('client.secret', 'CLIENT_SECRET'),
      scope: secreto('auth.scope', 'AUTH_SCOPE')
    }
  };

  // Obtiene un token OAuth2 por suite y lo comparte entre los hilos de ejecución.
  // Usa -Dauth=false para ejecutar archivos .feature que no requieren autenticación.
  if (karate.properties['auth'] != 'false' && config.authConfig.clientId) {
    var auth = karate.callSingle('classpath:common/auth.feature', config.authConfig);
    config.authHeader = { Authorization: 'Bearer ' + auth.token };
  } else {
    config.authHeader = {};
  }

  karate.configure('connectTimeout', 10000);
  karate.configure('readTimeout', 30000);
  if (env == 'dev' || env == 'qa') {
    // Acepta certificados autofirmados en dev y qa.
    // Para stg o una futura configuración prod, configura un almacén de certificados de confianza (truststore).
    karate.configure('ssl', true);
  }
  return config;
}
