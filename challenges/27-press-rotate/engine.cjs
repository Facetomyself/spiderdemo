const fs = require("fs");

const jobPath = process.argv[2];
const outPath = process.argv[3];
const job = JSON.parse(fs.readFileSync(jobPath, "utf8"));
const path = require("path");
const bytes = fs.readFileSync(path.join(__dirname, "press_rotate_bg.wasm"));
let wasm;
const decoder = new TextDecoder();
const encoder = new TextEncoder();

function readString(ptr, len) {
  return decoder.decode(new Uint8Array(wasm.memory.buffer, ptr, len));
}

const wasmModule = new WebAssembly.Module(bytes);

function boot() {
  const instance = new WebAssembly.Instance(wasmModule, {
    wbg: {
      __wbg_wbindgenthrow_451ec1a8469d7eb6(ptr, len) {
        throw new Error(readString(ptr, len));
      },
      __wbindgen_init_externref_table() {
        const table = wasm.__wbindgen_export_0;
        const offset = table.grow(4);
        table.set(0, undefined);
        table.set(offset + 0, undefined);
        table.set(offset + 1, null);
        table.set(offset + 2, true);
        table.set(offset + 3, false);
      },
    },
  });
  wasm = instance.exports;
  wasm.__wbindgen_start();
}

function passString(value) {
  const encoded = encoder.encode(value);
  const ptr = wasm.__wbindgen_malloc(encoded.length, 1);
  new Uint8Array(wasm.memory.buffer, ptr, encoded.length).set(encoded);
  return [ptr, encoded.length];
}

function freshState(blob) {
  const state = wasm.state_new();
  wasm.state_init_inst(state);
  const [ptr, len] = passString(blob);
  wasm.state_check_data(state, ptr, len);
  return state;
}

function pressUntil(state, startMs, targetAngle) {
  wasm.state_set_t(state, BigInt(startMs));
  wasm.state_pressStart(state);
  let angle = 0;
  let elapsed = 0;
  while (angle < targetAngle - 1e-6 && elapsed < 12) {
    const remain = targetAngle - angle;
    const step = remain > 8 ? 0.004 : remain > 1 ? 0.0005 : 0.00005;
    angle = wasm.state_tick(state, step);
    elapsed += step;
  }
  wasm.state_pressEnd(state);
  return angle;
}

function prove(startMs) {
  boot();
  const state = freshState(job.blob);
  const angle = pressUntil(state, startMs, Number(job.target_angle));
  const [uaPtr, uaLen] = passString(job.ua);
  const result = wasm.state_getResult(state, uaPtr, uaLen);
  return {
    angle,
    duration: wasm.state_duration(state),
    proof: readString(result[0], result[1]),
  };
}

function alignProof() {
  let payload = null;
  let skew = 0;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const started = Date.now();
    const rough = prove(0);
    const cost = Math.max(40, Date.now() - started);
    const durationMs = Math.round(rough.duration * 1000);
    const margin = cost + 120 + attempt * 40;
    const startMs = Date.now() + margin - durationMs;
    const finalProof = prove(startMs);
    const timestamp = startMs + Math.round(finalProof.duration * 1000);
    const fireAt = timestamp + 30;
    const wait = fireAt - Date.now();
    if (wait > 0) {
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, wait);
    }
    skew = Date.now() - timestamp;
    payload = {
      timestamp,
      angle: finalProof.angle,
      proof: finalProof.proof,
    };
    if (skew >= 20 && skew <= 75) {
      break;
    }
  }
  return { payload, skew };
}

const aligned = alignProof();
fs.writeFileSync(outPath, JSON.stringify(aligned.payload));
console.log("ready", aligned.skew);
