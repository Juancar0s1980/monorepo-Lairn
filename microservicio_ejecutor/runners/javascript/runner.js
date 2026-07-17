// Runner que corre DENTRO del contenedor efimero de JavaScript (Node.js).
// Mismo contrato que runners/python/runner.py: payload en base64 por env,
// siempre imprime un JSON de resultado, incluso si el codigo del
// estudiante truena. spawnSync con `timeout` hace de limite interno,
// ademas del timeout externo del microservicio ejecutor.

const fs = require('fs')
const { spawnSync } = require('child_process')

const MAX_SALIDA = 65536
const TIMEOUT_MAXIMO = 10

function main() {
  let payload
  try {
    payload = JSON.parse(Buffer.from(process.env.PAYLOAD_B64 || '', 'base64').toString('utf8'))
  } catch (error) {
    console.log(JSON.stringify({ stdout: '', stderr: `Payload invalido: ${error}`, exit_code: -1, timeout: false }))
    return
  }

  const codigo = payload.codigo || ''
  const entrada = payload.entrada || ''
  const timeoutSeg = Math.min(parseFloat(payload.timeout_seg || 5), TIMEOUT_MAXIMO)

  fs.writeFileSync('/tmp/solucion.js', codigo)

  const proceso = spawnSync('node', ['/tmp/solucion.js'], {
    input: entrada,
    timeout: timeoutSeg * 1000,
    encoding: 'utf8',
    killSignal: 'SIGKILL',
  })

  const huboTimeout = !!proceso.error && proceso.error.code === 'ETIMEDOUT'
  const resultado = {
    stdout: (proceso.stdout || '').slice(0, MAX_SALIDA),
    stderr: huboTimeout
      ? `Tiempo de ejecucion excedido (${timeoutSeg}s).`
      : (proceso.stderr || '').slice(0, MAX_SALIDA),
    exit_code: proceso.status === null ? -1 : proceso.status,
    timeout: huboTimeout,
  }

  console.log(JSON.stringify(resultado))
}

main()
