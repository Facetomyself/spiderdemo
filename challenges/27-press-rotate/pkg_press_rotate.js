let wasm;
let cachedUint8ArrayMemory0 = null;
function getUint8ArrayMemory0() {
    if (cachedUint8ArrayMemory0 === null || cachedUint8ArrayMemory0['byteLength'] === 0x0) {
        cachedUint8ArrayMemory0 = new Uint8Array(wasm['memory']['buffer']);
    }
    return cachedUint8ArrayMemory0;
}
let cachedTextDecoder = new TextDecoder('utf-8', {
    'ignoreBOM': !![],
    'fatal': !![]
});
cachedTextDecoder['decode']();
const MAX_SAFARI_DECODE_BYTES = 0x7ff00000;
let numBytesDecoded = 0x0;
function decodeText(_0xb2eb3a, _0x5c7449) {
    numBytesDecoded += _0x5c7449;
    if (numBytesDecoded >= MAX_SAFARI_DECODE_BYTES) {
        cachedTextDecoder = new TextDecoder('utf-8', {
            'ignoreBOM': !![],
            'fatal': !![]
        });
        cachedTextDecoder['decode']();
        numBytesDecoded = _0x5c7449;
    }
    return cachedTextDecoder['decode'](getUint8ArrayMemory0()['subarray'](_0xb2eb3a, _0xb2eb3a + _0x5c7449));
}
function getStringFromWasm0(_0x170166, _0x36b21c) {
    _0x170166 = _0x170166 >>> 0x0;
    return decodeText(_0x170166, _0x36b21c);
}
let WASM_VECTOR_LEN = 0x0;
const cachedTextEncoder = new TextEncoder();
if (!('encodeInto' in cachedTextEncoder)) {
    cachedTextEncoder['encodeInto'] = function (_0x80b1b8, _0x45d6b4) {
        const _0x2bbe92 = cachedTextEncoder['encode'](_0x80b1b8);
        _0x45d6b4['set'](_0x2bbe92);
        return {
            'read': _0x80b1b8['length'],
            'written': _0x2bbe92['length']
        };
    };
}
function passStringToWasm0(_0x1a1663, _0x2b6ac8, _0x318552) {
    if (_0x318552 === undefined) {
        const _0x2b8966 = cachedTextEncoder['encode'](_0x1a1663);
        const _0x510434 = _0x2b6ac8(_0x2b8966['length'], 0x1) >>> 0x0;
        getUint8ArrayMemory0()['subarray'](_0x510434, _0x510434 + _0x2b8966['length'])['set'](_0x2b8966);
        WASM_VECTOR_LEN = _0x2b8966['length'];
        return _0x510434;
    }
    let _0x102682 = _0x1a1663['length'];
    let _0x445764 = _0x2b6ac8(_0x102682, 0x1) >>> 0x0;
    const _0x18cd03 = getUint8ArrayMemory0();
    let _0x3c885c = 0x0;
    for (; _0x3c885c < _0x102682; _0x3c885c++) {
        const _0x58f327 = _0x1a1663['charCodeAt'](_0x3c885c);
        if (_0x58f327 > 0x7f)
            break;
        _0x18cd03[_0x445764 + _0x3c885c] = _0x58f327;
    }
    if (_0x3c885c !== _0x102682) {
        if (_0x3c885c !== 0x0) {
            _0x1a1663 = _0x1a1663['slice'](_0x3c885c);
        }
        _0x445764 = _0x318552(_0x445764, _0x102682, _0x102682 = _0x3c885c + _0x1a1663['length'] * 0x3, 0x1) >>> 0x0;
        const _0x552136 = getUint8ArrayMemory0()['subarray'](_0x445764 + _0x3c885c, _0x445764 + _0x102682);
        const _0x296dc7 = cachedTextEncoder['encodeInto'](_0x1a1663, _0x552136);
        _0x3c885c += _0x296dc7['written'];
        _0x445764 = _0x318552(_0x445764, _0x102682, _0x3c885c, 0x1) >>> 0x0;
    }
    WASM_VECTOR_LEN = _0x3c885c;
    return _0x445764;
}
const StateFinalization = typeof FinalizationRegistry === 'undefined' ? {
    'register': () => {
    },
    'unregister': () => {
    }
} : new FinalizationRegistry(_0x4cc4c4 => wasm['__wbg_state_free'](_0x4cc4c4 >>> 0x0, 0x1));
export class State {
    ['__destroy_into_raw']() {
        const _0x476b8b = this['__wbg_ptr'];
        this['__wbg_ptr'] = 0x0;
        StateFinalization['unregister'](this);
        return _0x476b8b;
    }
    ['free']() {
        const _0x23b64e = this['__destroy_into_raw']();
        wasm['__wbg_state_free'](_0x23b64e, 0x0);
    }
    constructor() {
        const _0x25158b = wasm['state_new']();
        this['__wbg_ptr'] = _0x25158b >>> 0x0;
        StateFinalization['register'](this, this['__wbg_ptr'], this);
        return this;
    }
    ['pressStart']() {
        wasm['state_pressStart'](this['__wbg_ptr']);
    }
    ['pressEnd']() {
        wasm['state_pressEnd'](this['__wbg_ptr']);
    }
    ['tick'](_0x6757ed) {
        const _0x185605 = wasm['state_tick'](this['__wbg_ptr'], _0x6757ed);
        return _0x185605;
    }
    ['reset']() {
        wasm['state_reset'](this['__wbg_ptr']);
    }
    ['init_inst']() {
        wasm['state_init_inst'](this['__wbg_ptr']);
    }
    ['calculate'](_0x3e3606, _0x8b95b8) {
        const _0x56a707 = wasm['state_calculate'](this['__wbg_ptr'], _0x3e3606, _0x8b95b8);
        return _0x56a707;
    }
    ['check_data'](_0x21b410) {
        const _0x13dbcb = passStringToWasm0(_0x21b410, wasm['__wbindgen_malloc'], wasm['__wbindgen_realloc']);
        const _0x3cf24b = WASM_VECTOR_LEN;
        wasm['state_check_data'](this['__wbg_ptr'], _0x13dbcb, _0x3cf24b);
    }
    ['set_t'](_0x5d35c6) {
        wasm['state_set_t'](this['__wbg_ptr'], _0x5d35c6);
    }
    get ['angle']() {
        const _0xa41a8 = wasm['state_angle'](this['__wbg_ptr']);
        return _0xa41a8;
    }
    get ['duration']() {
        const _0x69730a = wasm['state_duration'](this['__wbg_ptr']);
        return _0x69730a;
    }
    ['getResult'](_0xb6f05d) {
        let _0x519a03;
        let _0x122b73;
        try {
            const _0x11d860 = passStringToWasm0(_0xb6f05d, wasm['__wbindgen_malloc'], wasm['__wbindgen_realloc']);
            const _0x1d64a3 = WASM_VECTOR_LEN;
            const _0x223ab6 = wasm['state_getResult'](this['__wbg_ptr'], _0x11d860, _0x1d64a3);
            _0x519a03 = _0x223ab6[0x0];
            _0x122b73 = _0x223ab6[0x1];
            return getStringFromWasm0(_0x223ab6[0x0], _0x223ab6[0x1]);
        } finally {
            wasm['__wbindgen_free'](_0x519a03, _0x122b73, 0x1);
        }
    }
}
if (Symbol['dispose'])
    State['prototype'][Symbol['dispose']] = State['prototype']['free'];
const EXPECTED_RESPONSE_TYPES = new Set([
    'basic',
    'cors',
    'default'
]);
async function __wbg_load(_0x34e767, _0x179bef) {
    if (typeof Response === 'function' && _0x34e767 instanceof Response) {
        if (typeof WebAssembly['instantiateStreaming'] === 'function') {
            try {
                return await WebAssembly['instantiateStreaming'](_0x34e767, _0x179bef);
            } catch (_0xa2f426) {
                const _0x1bdbff = _0x34e767['ok'] && EXPECTED_RESPONSE_TYPES['has'](_0x34e767['type']);
                if (_0x1bdbff && _0x34e767['headers']['get']('Content-Type') !== 'application/wasm') {
                    console['warn']('`WebAssembly.instantiateStreaming`\x20failed\x20because\x20your\x20server\x20does\x20not\x20serve\x20Wasm\x20with\x20`application/wasm`\x20MIME\x20type.\x20Falling\x20back\x20to\x20`WebAssembly.instantiate`\x20which\x20is\x20slower.\x20Original\x20error:\x0a', _0xa2f426);
                } else {
                    throw _0xa2f426;
                }
            }
        }
        const _0x4b9f08 = await _0x34e767['arrayBuffer']();
        return await WebAssembly['instantiate'](_0x4b9f08, _0x179bef);
    } else {
        const _0x573363 = await WebAssembly['instantiate'](_0x34e767, _0x179bef);
        if (_0x573363 instanceof WebAssembly['Instance']) {
            return {
                'instance': _0x573363,
                'module': _0x34e767
            };
        } else {
            return _0x573363;
        }
    }
}
function __wbg_get_imports() {
    const _0xb20bb2 = {};
    _0xb20bb2['wbg'] = {};
    _0xb20bb2['wbg']['__wbg_wbindgenthrow_451ec1a8469d7eb6'] = function (_0x44e068, _0x22811c) {
        throw new Error(getStringFromWasm0(_0x44e068, _0x22811c));
    };
    _0xb20bb2['wbg']['__wbindgen_init_externref_table'] = function () {
        const _0x32a6e0 = wasm['__wbindgen_export_0'];
        const _0x3d109f = _0x32a6e0['grow'](0x4);
        _0x32a6e0['set'](0x0, undefined);
        _0x32a6e0['set'](_0x3d109f + 0x0, undefined);
        _0x32a6e0['set'](_0x3d109f + 0x1, null);
        _0x32a6e0['set'](_0x3d109f + 0x2, !![]);
        _0x32a6e0['set'](_0x3d109f + 0x3, ![]);
        ;
    };
    return _0xb20bb2;
}
function __wbg_init_memory(_0x163be6, _0x175601) {
}
function __wbg_finalize_init(_0x1a41b0, _0x55b9b1) {
    wasm = _0x1a41b0['exports'];
    __wbg_init['__wbindgen_wasm_module'] = _0x55b9b1;
    cachedUint8ArrayMemory0 = null;
    wasm['__wbindgen_start']();
    return wasm;
}
function initSync(_0x3cc0dc) {
    if (wasm !== undefined)
        return wasm;
    if (typeof _0x3cc0dc !== 'undefined') {
        if (Object['getPrototypeOf'](_0x3cc0dc) === Object['prototype']) {
            ({module: _0x3cc0dc} = _0x3cc0dc);
        } else {
            console['warn']('using\x20deprecated\x20parameters\x20for\x20`initSync()`;\x20pass\x20a\x20single\x20object\x20instead');
        }
    }
    const _0x250134 = __wbg_get_imports();
    __wbg_init_memory(_0x250134);
    if (!(_0x3cc0dc instanceof WebAssembly['Module'])) {
        _0x3cc0dc = new WebAssembly['Module'](_0x3cc0dc);
    }
    const _0x240d7a = new WebAssembly['Instance'](_0x3cc0dc, _0x250134);
    return __wbg_finalize_init(_0x240d7a, _0x3cc0dc);
}
async function __wbg_init(_0x1340be) {
    if (wasm !== undefined)
        return wasm;
    if (typeof _0x1340be !== 'undefined') {
        if (Object['getPrototypeOf'](_0x1340be) === Object['prototype']) {
            ({module_or_path: _0x1340be} = _0x1340be);
        } else {
            console['warn']('using\x20deprecated\x20parameters\x20for\x20the\x20initialization\x20function;\x20pass\x20a\x20single\x20object\x20instead');
        }
    }
    if (typeof _0x1340be === 'undefined') {
        _0x1340be = new URL('press_rotate_bg.wasm', import.meta['url']);
    }
    const _0x366016 = __wbg_get_imports();
    if (typeof _0x1340be === 'string' || typeof Request === 'function' && _0x1340be instanceof Request || typeof URL === 'function' && _0x1340be instanceof URL) {
        _0x1340be = fetch(_0x1340be);
    }
    __wbg_init_memory(_0x366016);
    const {
        instance: _0x2d40a1,
        module: _0x16df5f
    } = await __wbg_load(await _0x1340be, _0x366016);
    return __wbg_finalize_init(_0x2d40a1, _0x16df5f);
}
export {
    initSync
};
export default __wbg_init;