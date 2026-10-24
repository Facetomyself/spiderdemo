const _0x2aa469 = (function () {
    let _0x54dcaf = !![];
    return function (_0x54adae, _0x228058) {
        const _0x4a0679 = _0x54dcaf ? function () {
            if (_0x228058) {
                const _0x290877 = _0x228058['apply'](_0x54adae, arguments);
                _0x228058 = null;
                return _0x290877;
            }
        } : function () {
        };
        _0x54dcaf = ![];
        return _0x4a0679;
    };
}());
(function () {
    _0x2aa469(this, function () {
        const _0x3c4603 = new RegExp('function\x20*\x5c(\x20*\x5c)');
        const _0x8e9b8c = new RegExp('\x5c+\x5c+\x20*(?:[a-zA-Z_$][0-9a-zA-Z_$]*)', 'i');
        const _0x3ca56 = _0x49f727('init');
        if (!_0x3c4603['test'](_0x3ca56 + 'chain') || !_0x8e9b8c['test'](_0x3ca56 + 'input')) {
            _0x3ca56('0');
        } else {
            _0x49f727();
        }
    })();
}());
function simpleMD5(_0x5ee141) {
    function _0x26ee06(_0x4852b0, _0x54f635) {
        return _0x4852b0 << _0x54f635 | _0x4852b0 >>> 0x20 - _0x54f635;
    }
    function _0x59635c(_0x2e239a, _0xb582b8) {
        return _0x2e239a + _0xb582b8 >>> 0x0;
    }
    function _0x78d2b4(_0x501607, _0x3add9c) {
        let _0x3a7bf0 = _0x501607[0x0], _0x5b7afd = _0x501607[0x1], _0x3f8cea = _0x501607[0x2], _0x356b1b = _0x501607[0x3];
        _0x3a7bf0 = _0x2f5fe3(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x0], 0x7, -0x28955b88);
        _0x356b1b = _0x2f5fe3(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x1], 0xc, -0x173848aa);
        _0x3f8cea = _0x2f5fe3(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0x2], 0x11, 0x242070db);
        _0x5b7afd = _0x2f5fe3(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x3], 0x16, -0x3e423112);
        _0x3a7bf0 = _0x2f5fe3(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x4], 0x7, -0xa83f051);
        _0x356b1b = _0x2f5fe3(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x5], 0xc, 0x4787c62a);
        _0x3f8cea = _0x2f5fe3(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0x6], 0x11, -0x57cfb9ed);
        _0x5b7afd = _0x2f5fe3(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x7], 0x16, -0x2b96aff);
        _0x3a7bf0 = _0x2f5fe3(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x8], 0x7, 0x698098d8);
        _0x356b1b = _0x2f5fe3(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x9], 0xc, -0x74bb0851);
        _0x3f8cea = _0x2f5fe3(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0xa], 0x11, -0xa44f);
        _0x5b7afd = _0x2f5fe3(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0xb], 0x16, -0x76a32842);
        _0x3a7bf0 = _0x2f5fe3(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0xc], 0x7, 0x6b901122);
        _0x356b1b = _0x2f5fe3(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0xd], 0xc, -0x2678e6d);
        _0x3f8cea = _0x2f5fe3(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0xe], 0x11, -0x5986bc72);
        _0x5b7afd = _0x2f5fe3(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0xf], 0x16, 0x49b40821);
        _0x3a7bf0 = _0x1a02c4(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x1], 0x5, -0x9e1da9e);
        _0x356b1b = _0x1a02c4(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x6], 0x9, -0x3fbf4cc0);
        _0x3f8cea = _0x1a02c4(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0xb], 0xe, 0x265e5a51);
        _0x5b7afd = _0x1a02c4(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x0], 0x14, -0x16493856);
        _0x3a7bf0 = _0x1a02c4(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x5], 0x5, -0x29d0efa3);
        _0x356b1b = _0x1a02c4(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0xa], 0x9, 0x2441453);
        _0x3f8cea = _0x1a02c4(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0xf], 0xe, -0x275e197f);
        _0x5b7afd = _0x1a02c4(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x4], 0x14, -0x182c0438);
        _0x3a7bf0 = _0x1a02c4(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x9], 0x5, 0x21e1cde6);
        _0x356b1b = _0x1a02c4(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0xe], 0x9, -0x3cc8f82a);
        _0x3f8cea = _0x1a02c4(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0x3], 0xe, -0xb2af279);
        _0x5b7afd = _0x1a02c4(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x8], 0x14, 0x455a14ed);
        _0x3a7bf0 = _0x1a02c4(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0xd], 0x5, -0x561c16fb);
        _0x356b1b = _0x1a02c4(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x2], 0x9, -0x3105c08);
        _0x3f8cea = _0x1a02c4(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0x7], 0xe, 0x676f02d9);
        _0x5b7afd = _0x1a02c4(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0xc], 0x14, -0x72d5b376);
        _0x3a7bf0 = _0x3381e6(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x5], 0x4, -0x5c6be);
        _0x356b1b = _0x3381e6(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x8], 0xb, -0x788e097f);
        _0x3f8cea = _0x3381e6(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0xb], 0x10, 0x6d9d6122);
        _0x5b7afd = _0x3381e6(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0xe], 0x17, -0x21ac7f4);
        _0x3a7bf0 = _0x3381e6(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x1], 0x4, -0x5b4115bc);
        _0x356b1b = _0x3381e6(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x4], 0xb, 0x4bdecfa9);
        _0x3f8cea = _0x3381e6(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0x7], 0x10, -0x944b4a0);
        _0x5b7afd = _0x3381e6(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0xa], 0x17, -0x41404390);
        _0x3a7bf0 = _0x3381e6(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0xd], 0x4, 0x289b7ec6);
        _0x356b1b = _0x3381e6(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x0], 0xb, -0x155ed806);
        _0x3f8cea = _0x3381e6(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0x3], 0x10, -0x2b10cf7b);
        _0x5b7afd = _0x3381e6(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x6], 0x17, 0x4881d05);
        _0x3a7bf0 = _0x3381e6(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x9], 0x4, -0x262b2fc7);
        _0x356b1b = _0x3381e6(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0xc], 0xb, -0x1924661b);
        _0x3f8cea = _0x3381e6(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0xf], 0x10, 0x1fa27cf8);
        _0x5b7afd = _0x3381e6(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x2], 0x17, -0x3b53a99b);
        _0x3a7bf0 = _0x1ff0ed(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x0], 0x6, -0xbd6ddbc);
        _0x356b1b = _0x1ff0ed(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x7], 0xa, 0x432aff97);
        _0x3f8cea = _0x1ff0ed(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0xe], 0xf, -0x546bdc59);
        _0x5b7afd = _0x1ff0ed(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x5], 0x15, -0x36c5fc7);
        _0x3a7bf0 = _0x1ff0ed(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0xc], 0x6, 0x655b59c3);
        _0x356b1b = _0x1ff0ed(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0x3], 0xa, -0x70f3336e);
        _0x3f8cea = _0x1ff0ed(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0xa], 0xf, -0x100b83);
        _0x5b7afd = _0x1ff0ed(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x1], 0x15, -0x7a7ba22f);
        _0x3a7bf0 = _0x1ff0ed(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x8], 0x6, 0x6fa87e4f);
        _0x356b1b = _0x1ff0ed(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0xf], 0xa, -0x1d31920);
        _0x3f8cea = _0x1ff0ed(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0x6], 0xf, -0x5cfebcec);
        _0x5b7afd = _0x1ff0ed(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0xd], 0x15, 0x4e0811a1);
        _0x3a7bf0 = _0x1ff0ed(_0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x356b1b, _0x3add9c[0x4], 0x6, -0x8ac817e);
        _0x356b1b = _0x1ff0ed(_0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3f8cea, _0x3add9c[0xb], 0xa, -0x42c50dcb);
        _0x3f8cea = _0x1ff0ed(_0x3f8cea, _0x356b1b, _0x3a7bf0, _0x5b7afd, _0x3add9c[0x2], 0xf, 0x2ad7d2bb);
        _0x5b7afd = _0x1ff0ed(_0x5b7afd, _0x3f8cea, _0x356b1b, _0x3a7bf0, _0x3add9c[0x9], 0x15, -0x14792c6f);
        _0x501607[0x0] = _0x59635c(_0x3a7bf0, _0x501607[0x0]);
        _0x501607[0x1] = _0x59635c(_0x5b7afd, _0x501607[0x1]);
        _0x501607[0x2] = _0x59635c(_0x3f8cea, _0x501607[0x2]);
        _0x501607[0x3] = _0x59635c(_0x356b1b, _0x501607[0x3]);
    }
    function _0x4518cd(_0x21f28a, _0x1ca482, _0xf413b2, _0x240974, _0x15fdf6, _0x38c8a7) {
        _0x1ca482 = _0x59635c(_0x59635c(_0x1ca482, _0x21f28a), _0x59635c(_0x240974, _0x38c8a7));
        return _0x59635c(_0x26ee06(_0x1ca482, _0x15fdf6), _0xf413b2);
    }
    function _0x2f5fe3(_0x4dff25, _0xe9f1c0, _0x2709f8, _0x17ef1b, _0xb5323e, _0x4f2b33, _0x70d9fe) {
        return _0x4518cd(_0xe9f1c0 & _0x2709f8 | ~_0xe9f1c0 & _0x17ef1b, _0x4dff25, _0xe9f1c0, _0xb5323e, _0x4f2b33, _0x70d9fe);
    }
    function _0x1a02c4(_0x506709, _0x524f5d, _0x11773b, _0x2bd18f, _0x2c565d, _0x21d36c, _0x5909a6) {
        return _0x4518cd(_0x524f5d & _0x2bd18f | _0x11773b & ~_0x2bd18f, _0x506709, _0x524f5d, _0x2c565d, _0x21d36c, _0x5909a6);
    }
    function _0x3381e6(_0x45dd4a, _0x1ca23b, _0x28f4ce, _0x59751c, _0x3fb5f5, _0x288496, _0x401e7c) {
        return _0x4518cd(_0x1ca23b ^ _0x28f4ce ^ _0x59751c, _0x45dd4a, _0x1ca23b, _0x3fb5f5, _0x288496, _0x401e7c);
    }
    function _0x1ff0ed(_0x5f5508, _0x2f57e8, _0x54910f, _0x3c6da0, _0x2a295d, _0x393bf7, _0x3d87be) {
        return _0x4518cd(_0x54910f ^ (_0x2f57e8 | ~_0x3c6da0), _0x5f5508, _0x2f57e8, _0x2a295d, _0x393bf7, _0x3d87be);
    }
    function _0x37cec5(_0x1116b0) {
        let _0x34746d = _0x1116b0['length'];
        let _0x4bc04c = [
            0x67452301,
            -0x10325477,
            -0x67452302,
            0x10325476
        ];
        let _0x43d35c;
        for (_0x43d35c = 0x40; _0x43d35c <= _0x34746d; _0x43d35c += 0x40) {
            _0x78d2b4(_0x4bc04c, _0x2777d9(_0x1116b0['substring'](_0x43d35c - 0x40, _0x43d35c)));
        }
        _0x1116b0 = _0x1116b0['substring'](_0x43d35c - 0x40);
        let _0x4caa4d = [
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0
        ];
        for (_0x43d35c = 0x0; _0x43d35c < _0x1116b0['length']; _0x43d35c++) {
            _0x4caa4d[_0x43d35c >> 0x2] |= _0x1116b0['charCodeAt'](_0x43d35c) << (_0x43d35c % 0x4 << 0x3);
        }
        _0x4caa4d[_0x43d35c >> 0x2] |= 0x80 << (_0x43d35c % 0x4 << 0x3);
        if (_0x43d35c > 0x37) {
            _0x78d2b4(_0x4bc04c, _0x4caa4d);
            for (_0x43d35c = 0x0; _0x43d35c < 0x10; _0x43d35c++)
                _0x4caa4d[_0x43d35c] = 0x0;
        }
        _0x4caa4d[0xe] = _0x34746d * 0x8;
        _0x78d2b4(_0x4bc04c, _0x4caa4d);
        return _0x4bc04c;
    }
    function _0x2777d9(_0x7035c8) {
        let _0x3426b5 = [];
        for (let _0x39f32b = 0x0; _0x39f32b < 0x40; _0x39f32b += 0x4) {
            _0x3426b5[_0x39f32b >> 0x2] = _0x7035c8['charCodeAt'](_0x39f32b) + (_0x7035c8['charCodeAt'](_0x39f32b + 0x1) << 0x8) + (_0x7035c8['charCodeAt'](_0x39f32b + 0x2) << 0x10) + (_0x7035c8['charCodeAt'](_0x39f32b + 0x3) << 0x18);
        }
        return _0x3426b5;
    }
    let _0x4b0bf9 = '0123456789abcdef'['split']('');
    function _0x5c8655(_0x4223b9) {
        let _0x3ef6c0 = '', _0x180fa9 = 0x0;
        for (; _0x180fa9 < 0x4; _0x180fa9++) {
            _0x3ef6c0 += _0x4b0bf9[_0x4223b9 >> _0x180fa9 * 0x8 + 0x4 & 0xf] + _0x4b0bf9[_0x4223b9 >> _0x180fa9 * 0x8 & 0xf];
        }
        return _0x3ef6c0;
    }
    function _0x6d3bf0(_0x420e37) {
        for (let _0x284daa = 0x0; _0x284daa < _0x420e37['length']; _0x284daa++) {
            _0x420e37[_0x284daa] = _0x5c8655(_0x420e37[_0x284daa]);
        }
        return _0x420e37['join']('');
    }
    return _0x6d3bf0(_0x37cec5(_0x5ee141));
}
function generateMagicSign(_0x1c6569, _0x2bb0d2, _0x20be11 = 'wlz_shield_magic_2024') {
    let _0x15f926 = _0x1c6569 + '|' + _0x2bb0d2 + '|' + _0x20be11;
    let _0x731749 = simpleMD5(_0x15f926);
    let _0xff3bad = _0x731749['split']('')['reverse']()['join']('');
    let _0x158112 = simpleMD5(_0xff3bad);
    let _0x81dbf2 = _0x158112['substring'](0x0, 0x8);
    let _0x65301c = _0x158112['substring'](0x8, 0x10);
    let _0x4b8958 = _0x158112['substring'](0x10, 0x18);
    let _0x55da4b = _0x158112['substring'](0x18, 0x20);
    let _0x6b33a3 = _0x65301c + _0x55da4b + _0x81dbf2 + _0x4b8958;
    let _0x2bcb32 = simpleMD5(_0x6b33a3 + _0x20be11);
    return _0x2bcb32;
}
let currentPage = 0x1;
let totalPages = 0x64;
let numbersPerPage = 0xa;
let pageData = {};
let visitedPages = new Set();
let challengeType = 'wlzshield_captcha_challenge';
let pendingPageNum = null;
let wlzshieldCaptcha = null;
async function apiInitChallenge(_0x4430e8 = challengeType) {
    const _0x26af42 = '/captcha/api/wlzshield_captcha_challenge/init/?challenge_type=' + encodeURIComponent(_0x4430e8);
    const _0x29cfc7 = await fetch(_0x26af42);
    const _0x42cbdb = await _0x29cfc7['json']();
    if (!_0x29cfc7['ok']) {
        const _0x291a16 = _0x42cbdb['error'] || 'HTTP\x20' + _0x29cfc7['status'] + ':\x20' + _0x29cfc7['statusText'];
        throw new Error(_0x291a16);
    }
    return _0x42cbdb;
}
async function apiSubmitAnswer(_0x5d7f34, _0xa577d0 = challengeType) {
    const _0x241a03 = await fetch('/captcha/api/wlzshield_captcha_challenge/submit/', {
        'method': 'POST',
        'headers': { 'Content-Type': 'application/json' },
        'body': JSON['stringify']({
            'challenge_type': _0xa577d0,
            'answer': _0x5d7f34
        })
    });
    const _0x3c651d = await _0x241a03['json']();
    if (!_0x241a03['ok']) {
        const _0x42cb32 = _0x3c651d['error'] || 'HTTP\x20' + _0x241a03['status'] + ':\x20' + _0x241a03['statusText'];
        throw new Error(_0x42cb32);
    }
    return _0x3c651d;
}
function getChallengeTypeFromUrl() {
    const _0x5756e1 = new URLSearchParams(window['location']['search']);
    return _0x5756e1['get']('challenge_type') || _0x5756e1['get']('type') || 'cap1_challenge';
}
function getChallengeDisplayName(_0x4895f9) {
    const _0x37025c = {
        'header_check': '请求头检测挑战',
        'number_challenge': '动态数字求和挑战',
        'js_challenge': 'JS混淆解析挑战',
        'slide_puzzle_challenge': '滑动拼图',
        'slide_scratch_challenge': '滑动刮刮乐',
        'cap1_challenge': '第一代验证码1',
        'wlzshield_captcha_challenge': 'WlzShield无感验证码'
    };
    return _0x37025c[_0x4895f9] || _0x4895f9;
}
function updatePageTitle() {
    const _0x44dd86 = document['querySelector']('.challenge-title');
    if (_0x44dd86) {
        const _0x34be1e = getChallengeDisplayName(challengeType);
        _0x44dd86['innerHTML'] = '🎯\x20任务:\x20采集这100页的全部数字，计算加和并提交结果<br/><small>(' + _0x34be1e + ')</small>';
    }
    const _0x22190f = document['querySelector']('.page-title');
    if (_0x22190f) {
        _0x22190f['innerHTML'] = '🔢\x20' + getChallengeDisplayName(challengeType);
    }
}
async function generateNumbers(_0x395588) {
    try {
        if (_0x395588 === 0x1 && visitedPages['size'] === 0x0) {
            const _0x7799f9 = await apiInitChallenge(challengeType);
            if (_0x7799f9['success']) {
                if (_0x7799f9['has_passed_before']) {
                    showResult('提示:\x20' + _0x7799f9['message'], 'info');
                }
                return _0x7799f9['page_data'];
            } else {
                throw new Error(_0x7799f9['error'] || '初始化失败');
            }
        } else {
            const _0x409c27 = await apiGetPageData(_0x395588, challengeType);
            if (_0x409c27['success']) {
                return _0x409c27['page_data'];
            } else {
                throw new Error(_0x409c27['error'] || '获取数据失败');
            }
        }
    } catch (_0x281ebd) {
        console['error']('获取数据失败:', _0x281ebd);
        if (_0x281ebd['message']['includes']('请先登录')) {
            showLoginAlert();
        } else if (_0x281ebd['message']['includes']('need_init')) {
            showResult('挑战未初始化，正在重新初始化...', 'info');
            visitedPages['clear']();
            return await generateNumbers(0x1);
        } else {
            showResult('获取数据失败:\x20' + _0x281ebd['message'], 'error');
        }
        return [];
    }
}
function renderNumbers(_0x3aea3b) {
    const _0x1e50a4 = document['getElementById']('numbersGrid');
    _0x1e50a4['innerHTML'] = _0x3aea3b['map']((_0x242042, _0x657655) => '<div\x20class=\x22number-box\x22\x20style=\x22animation-delay:\x20' + _0x657655 * 0.1 + 's\x22>' + _0x242042 + '</div>')['join']('');
}
async function loadPageData(_0x38691c) {
    showLoading();
    try {
        const _0x2cd272 = await generateNumbers(_0x38691c);
        if (_0x2cd272['length'] > 0x0) {
            pageData[_0x38691c] = _0x2cd272;
            visitedPages['add'](_0x38691c);
            renderNumbers(_0x2cd272);
            updateStats();
            updatePagination();
            recordBehavior('page_view', {
                'page': _0x38691c,
                'numbers': _0x2cd272['length'],
                'challengeType': challengeType
            });
        }
    } catch (_0x264b2e) {
        console['error']('加载页面数据失败:', _0x264b2e);
        showResult('加载页面数据失败', 'error');
    }
    hideLoading();
}
let isPageChanging = ![];
function changePage(_0x2ccc9b) {
    if (isPageChanging) {
        console['log']('页面切换中，请稍候...');
        return;
    }
    if (_0x2ccc9b === 'prev') {
        _0x2ccc9b = Math['max'](0x1, currentPage - 0x1);
    } else if (_0x2ccc9b === 'next') {
        _0x2ccc9b = Math['min'](totalPages, currentPage + 0x1);
    }
    if (_0x2ccc9b !== currentPage && _0x2ccc9b >= 0x1 && _0x2ccc9b <= totalPages) {
        if (!validatePageNavigation(challengeType, _0x2ccc9b)) {
            return;
        }
        isPageChanging = !![];
        disableAllPageButtons(!![]);
        if (_0x2ccc9b === 0x1) {
            currentPage = _0x2ccc9b;
            loadPageData(_0x2ccc9b)['finally'](() => {
                isPageChanging = ![];
                disableAllPageButtons(![]);
            });
            return;
        }
        showCaptchaForPage(_0x2ccc9b)['finally'](() => {
            isPageChanging = ![];
        });
    }
}
function updateStats() {
    document['getElementById']('currentPageNum')['textContent'] = currentPage;
    document['getElementById']('totalPages')['textContent'] = totalPages;
    document['getElementById']('collectedPages')['textContent'] = visitedPages['size'];
}
function updatePagination() {
    document['getElementById']('paginationInfo')['textContent'] = '第\x20' + currentPage + '\x20页，共\x20' + totalPages + '\x20页\x20|\x20当前页面包含\x20' + numbersPerPage + '\x20个数字';
    const _0x12b093 = document['getElementById']('paginationControls');
    let _0x143aa6 = '\x0a\x20\x20\x20\x20\x20\x20\x20\x20<button\x20class=\x22page-btn\x22\x20onclick=\x22changePage(\x27prev\x27)\x22\x20' + (currentPage <= 0x1 ? 'disabled' : '') + '>←\x20上一页</button>\x0a\x20\x20\x20\x20';
    if (totalPages <= 0x7) {
        for (let _0x55d698 = 0x1; _0x55d698 <= totalPages; _0x55d698++) {
            _0x143aa6 += '<button\x20class=\x22page-btn\x20' + (_0x55d698 === currentPage ? 'active' : '') + '\x22\x20onclick=\x22changePage(' + _0x55d698 + ')\x22>' + _0x55d698 + '</button>';
        }
    } else {
        if (currentPage <= 0x4) {
            for (let _0x325bf8 = 0x1; _0x325bf8 <= 0x5; _0x325bf8++) {
                _0x143aa6 += '<button\x20class=\x22page-btn\x20' + (_0x325bf8 === currentPage ? 'active' : '') + '\x22\x20onclick=\x22changePage(' + _0x325bf8 + ')\x22>' + _0x325bf8 + '</button>';
            }
            _0x143aa6 += '<span\x20class=\x22page-dots\x22>...</span>';
            _0x143aa6 += '<button\x20class=\x22page-btn\x22\x20onclick=\x22changePage(' + totalPages + ')\x22>' + totalPages + '</button>';
        } else if (currentPage >= totalPages - 0x3) {
            _0x143aa6 += '<button\x20class=\x22page-btn\x22\x20onclick=\x22changePage(1)\x22>1</button>';
            _0x143aa6 += '<span\x20class=\x22page-dots\x22>...</span>';
            for (let _0xdb1b5 = totalPages - 0x4; _0xdb1b5 <= totalPages; _0xdb1b5++) {
                _0x143aa6 += '<button\x20class=\x22page-btn\x20' + (_0xdb1b5 === currentPage ? 'active' : '') + '\x22\x20onclick=\x22changePage(' + _0xdb1b5 + ')\x22>' + _0xdb1b5 + '</button>';
            }
        } else {
            _0x143aa6 += '<button\x20class=\x22page-btn\x22\x20onclick=\x22changePage(1)\x22>1</button>';
            _0x143aa6 += '<span\x20class=\x22page-dots\x22>...</span>';
            for (let _0x9d87e2 = currentPage - 0x1; _0x9d87e2 <= currentPage + 0x1; _0x9d87e2++) {
                _0x143aa6 += '<button\x20class=\x22page-btn\x20' + (_0x9d87e2 === currentPage ? 'active' : '') + '\x22\x20onclick=\x22changePage(' + _0x9d87e2 + ')\x22>' + _0x9d87e2 + '</button>';
            }
            _0x143aa6 += '<span\x20class=\x22page-dots\x22>...</span>';
            _0x143aa6 += '<button\x20class=\x22page-btn\x22\x20onclick=\x22changePage(' + totalPages + ')\x22>' + totalPages + '</button>';
        }
    }
    _0x143aa6 += '\x0a\x20\x20\x20\x20\x20\x20\x20\x20<button\x20class=\x22page-btn\x22\x20onclick=\x22changePage(\x27next\x27)\x22\x20' + (currentPage >= totalPages ? 'disabled' : '') + '>下一页\x20→</button>\x0a\x20\x20\x20\x20';
    _0x12b093['innerHTML'] = _0x143aa6;
}
async function submitAnswer() {
    const _0x441ff2 = document['getElementById']('answerInput')['value']['trim']();
    if (!_0x441ff2) {
        showResult('请输入答案！', 'error');
        return;
    }
    if (!/^\d+$/['test'](_0x441ff2)) {
        showResult('答案格式错误，请输入纯数字！', 'error');
        return;
    }
    try {
        const _0x139b0f = await apiSubmitAnswer(parseInt(_0x441ff2), challengeType);
        if (_0x139b0f['success']) {
            const _0x2df0b7 = _0x139b0f['is_correct'] ? '🎉' : '❌';
            const _0x4d1cfd = _0x139b0f['is_correct'] ? '正确' : '错误';
            let _0x41adf4 = '\x0a\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20<strong>' + _0x2df0b7 + '\x20答案' + _0x4d1cfd + '！</strong><br/>\x0a\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20提交答案:\x20' + _0x139b0f['submitted_answer'] + '<br/>\x0a\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20已访问页面:\x20' + visitedPages['size'] + '/' + totalPages + '<br/>\x0a\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20挑战类型:\x20' + getChallengeDisplayName(_0x139b0f['challenge_type']) + '<br/>\x0a\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20提交时间:\x20' + new Date(_0x139b0f['submitted_at'])['toLocaleString']() + '<br/>\x0a\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20';
            if (_0x139b0f['is_repeat_success']) {
                _0x41adf4 += '<br/>💡\x20' + _0x139b0f['message'];
            } else if (_0x139b0f['is_correct']) {
                _0x41adf4 += '<br/>🎊\x20' + _0x139b0f['message'];
            } else {
                _0x41adf4 += '<br/>📝\x20建议:\x20仔细检查计算过程，可以重新提交答案！';
            }
            showResult(_0x41adf4, _0x139b0f['is_correct'] ? 'success' : 'error');
            document['getElementById']('answerInput')['value'] = '';
            document['getElementById']('answerInput')['focus']();
            recordBehavior('submit_answer', {
                'challengeType': challengeType,
                'answer': _0x139b0f['submitted_answer'],
                'visitedPages': Array['from'](visitedPages),
                'isCorrect': _0x139b0f['is_correct'],
                'isRepeatSuccess': _0x139b0f['is_repeat_success']
            });
        } else {
            showResult(_0x139b0f['message'] || _0x139b0f['error'], 'error');
        }
    } catch (_0x163a56) {
        console['error']('提交答案失败:', _0x163a56);
        if (_0x163a56['message']['includes']('请先登录')) {
            showLoginAlert();
        } else {
            showResult('提交答案失败:\x20' + _0x163a56['message'], 'error');
        }
    }
}
function showResult(_0x609d48, _0x183aa7) {
    const _0x288d5e = document['getElementById']('resultMessage');
    _0x288d5e['innerHTML'] = _0x609d48;
    _0x288d5e['style']['display'] = 'block';
    const _0x47e53b = {
        'success': '#d4edda',
        'error': '#f8d7da',
        'info': '#d1ecf1'
    };
    const _0x2473e8 = {
        'success': '#c3e6cb',
        'error': '#f5c6cb',
        'info': '#bee5eb'
    };
    _0x288d5e['style']['backgroundColor'] = _0x47e53b[_0x183aa7] || _0x47e53b['info'];
    _0x288d5e['style']['border'] = '1px\x20solid\x20' + (_0x2473e8[_0x183aa7] || _0x2473e8['info']);
    _0x288d5e['style']['color'] = _0x183aa7 === 'error' ? '#721c24' : _0x183aa7 === 'success' ? '#155724' : '#0c5460';
}
function recordBehavior(_0x21ed9a, _0x4af5a5) {
    console['log']('行为记录:', {
        'action': _0x21ed9a,
        'data': _0x4af5a5,
        'timestamp': Date['now']()
    });
}
function showLoading() {
    const _0x32b5f4 = document['getElementById']('loadingOverlay');
    if (_0x32b5f4) {
        _0x32b5f4['style']['display'] = 'flex';
    }
}
function hideLoading() {
    const _0x4d2a71 = document['getElementById']('loadingOverlay');
    if (_0x4d2a71) {
        _0x4d2a71['style']['display'] = 'none';
    }
}
function initEventListeners() {
    document['addEventListener']('keypress', function (_0x1d919f) {
        if (_0x1d919f['key'] === 'Enter' && _0x1d919f['target']['id'] === 'answerInput') {
            submitAnswer();
        }
        if (_0x1d919f['key'] === 'Enter' && _0x1d919f['target']['id'] === 'captcha-input') {
            verifyCaptchaAndGetData();
        }
    });
    const _0x322d5 = document['getElementById']('captcha-input');
    if (_0x322d5) {
        _0x322d5['addEventListener']('input', function () {
            this['value'] = this['value']['toUpperCase']();
        });
    }
}
function initializePage() {
    challengeType = getChallengeTypeFromUrl();
    console['log']('当前挑战类型:', challengeType);
    updatePageTitle();
    loadPageData(0x1);
    initEventListeners();
}
document['addEventListener']('DOMContentLoaded', function () {
    initializePage();
});
function initWlzShieldCaptcha(_0x31d4ad = 'checkbox') {
    return new Promise(async (_0x19e814, _0x140cec) => {
        let _0x947367 = document['getElementById']('login-captcha');
        if (!_0x947367) {
            console['error']('验证码容器不存在！');
            _0x140cec(new Error('验证码容器不存在'));
            return;
        }
        while (_0x947367['firstChild']) {
            _0x947367['removeChild'](_0x947367['firstChild']);
        }
        Array['from'](_0x947367['attributes'])['forEach'](_0x4da3f0 => {
            if (_0x4da3f0['name'] !== 'id' && _0x4da3f0['name'] !== 'style') {
                _0x947367['removeAttribute'](_0x4da3f0['name']);
            }
        });
        if (typeof WlzShield === 'undefined') {
            console['error']('WlzShield\x20SDK未加载！');
            _0x140cec(new Error('WlzShield\x20SDK未加载'));
            return;
        }
        const _0x4afcd6 = _0x31d4ad === 'scratch' ? WlzShield['ScratchCaptcha'] : WlzShield['CheckboxCaptcha'];
        try {
            const _0x5eeed5 = new _0x4afcd6({
                'siteKey': '9d4295076aaef0b4c16e18e4f53b5120',
                'containerId': '#login-captcha',
                'width': 0x12c,
                'height': 0x3c,
                'onSuccess': async function (_0x815c84) {
                    console['log']('🎉\x20WlzShield验证成功，收到响应:', _0x815c84);
                    try {
                        const _0x580009 = _0x815c84['wsToken'];
                        if (!_0x580009) {
                            throw new Error('未收到验证token');
                        }
                        console['log']('✅\x20收到token，向业务接口请求页面数据...');
                        const _0x19ec1e = Date['now']();
                        const _0x1b1144 = generateMagicSign(_0x19ec1e, pendingPageNum);
                        const _0x5bd516 = await fetch('/captcha/api/wlzshield_captcha_challenge/verify/?page_num=' + pendingPageNum + '&timestamp=' + _0x19ec1e + '&sign=' + _0x1b1144, {
                            'method': 'POST',
                            'headers': { 'Content-Type': 'application/json' },
                            'body': JSON['stringify']({
                                'wlz_token': _0x580009,
                                'page_num': pendingPageNum,
                                'challenge_type': challengeType
                            })
                        });
                        const _0x10325f = await _0x5bd516['json']();
                        if (_0x10325f['success'] && _0x10325f['page_data'] && _0x10325f['page_data']['length'] > 0x0) {
                            const _0x5657ad = _0x10325f['page_num'] || pendingPageNum;
                            console['log']('✅\x20获取页面', _0x5657ad, '数据成功');
                            pageData[_0x5657ad] = _0x10325f['page_data'];
                            visitedPages['add'](_0x5657ad);
                            currentPage = _0x5657ad;
                            renderNumbers(_0x10325f['page_data']);
                            updateStats();
                            updatePagination();
                            setTimeout(() => {
                                hideLoading();
                                hideCaptchaSection();
                                disableAllPageButtons(![]);
                            }, 0x64);
                            recordBehavior('page_view_with_captcha', {
                                'page': currentPage,
                                'numbers': _0x10325f['page_data']['length'],
                                'challengeType': challengeType
                            });
                        } else {
                            throw new Error(_0x10325f['error'] || '获取数据失败');
                        }
                    } catch (_0xddfdac) {
                        console['error']('❌\x20处理token失败:', _0xddfdac);
                        hideLoading();
                        showCaptchaMessage('获取数据失败:\x20' + _0xddfdac['message'], 'error');
                        disableAllPageButtons(![]);
                        setTimeout(() => showCaptchaForPage(pendingPageNum), 0x7d0);
                    }
                },
                'onFailure': function (_0x34a412) {
                    console['error']('❌\x20WlzShield验证失败:', _0x34a412);
                    hideLoading();
                    showCaptchaMessage('验证失败，请重试', 'error');
                    disableAllPageButtons(![]);
                    setTimeout(() => showCaptchaForPage(pendingPageNum), 0x7d0);
                },
                'onError': function (_0x5734fa) {
                    console['error']('❌\x20WlzShield系统错误:', _0x5734fa);
                    hideLoading();
                    showCaptchaMessage('系统错误:\x20' + _0x5734fa['message'], 'error');
                    disableAllPageButtons(![]);
                    setTimeout(() => showCaptchaForPage(pendingPageNum), 0xbb8);
                }
            });
            _0x19e814(_0x5eeed5);
        } catch (_0x31754f) {
            console['error']('创建验证码失败:', _0x31754f);
            _0x140cec(_0x31754f);
        }
    });
}
function disableAllPageButtons(_0x1191f9) {
    const _0x450d54 = document['querySelectorAll']('.page-btn:not([disabled])');
    _0x450d54['forEach'](_0x47c614 => {
        if (_0x1191f9) {
            _0x47c614['classList']['add']('verifying');
            _0x47c614['style']['pointerEvents'] = 'none';
        } else {
            _0x47c614['classList']['remove']('verifying');
            _0x47c614['style']['pointerEvents'] = '';
        }
    });
}
async function showCaptchaForPage(_0x5e9547) {
    console['log']('准备显示第' + _0x5e9547 + '页的验证码');
    pendingPageNum = _0x5e9547;
    showLoading();
    disableAllPageButtons(!![]);
    const _0x54ca58 = document['getElementById']('captchaSection');
    const _0x161b55 = document['getElementById']('numbersGrid');
    try {
        if (wlzshieldCaptcha) {
            try {
                if (typeof wlzshieldCaptcha['destroy'] === 'function') {
                    wlzshieldCaptcha['destroy']();
                }
            } catch (_0x1e8374) {
                console['warn']('销毁旧验证码失败:', _0x1e8374);
            }
            wlzshieldCaptcha = null;
        }
        let _0x47d71c = document['getElementById']('login-captcha');
        if (_0x47d71c) {
            const _0x421b87 = _0x47d71c['parentNode'];
            const _0xc96043 = _0x47d71c['style']['cssText'];
            _0x421b87['removeChild'](_0x47d71c);
            await new Promise(_0x1dbe11 => setTimeout(_0x1dbe11, 0x32));
            const _0xc71185 = document['createElement']('div');
            _0xc71185['id'] = 'login-captcha';
            _0xc71185['style']['cssText'] = _0xc96043;
            _0x421b87['appendChild'](_0xc71185);
        }
        _0x161b55['style']['display'] = 'none';
        _0x54ca58['style']['display'] = 'block';
        const _0x9ab65d = document['querySelector']('.captcha-title');
        if (_0x9ab65d) {
            _0x9ab65d['textContent'] = '请完成安全验证以获取第' + _0x5e9547 + '页数据';
        }
        await new Promise(_0x53d7aa => setTimeout(_0x53d7aa, 0x96));
        wlzshieldCaptcha = await initWlzShieldCaptcha('checkbox');
        hideLoading();
        hideCaptchaMessage();
        disableAllPageButtons(![]);
        console['log']('✅\x20验证码已就绪，等待用户操作');
    } catch (_0x1aaabb) {
        console['error']('验证码初始化失败:', _0x1aaabb);
        hideLoading();
        showCaptchaMessage('验证码初始化失败，请刷新页面', 'error');
        disableAllPageButtons(![]);
        setTimeout(() => {
            hideCaptchaSection();
        }, 0xbb8);
    }
}
function hideCaptchaSection() {
    console['log']('🔄\x20hideCaptchaSection\x20被调用');
    const _0x5e4f8e = document['getElementById']('captchaSection');
    const _0x2485c9 = document['getElementById']('numbersGrid');
    if (_0x2485c9) {
        _0x2485c9['style']['cssText'] = 'display:\x20grid\x20!important;';
        console['log']('✅\x20数字网格强制设置为\x20grid');
    }
    if (_0x5e4f8e) {
        _0x5e4f8e['style']['cssText'] = 'display:\x20none\x20!important;';
        console['log']('✅\x20验证码界面强制设置为\x20none');
    }
    if (wlzshieldCaptcha) {
        try {
            if (typeof wlzshieldCaptcha['destroy'] === 'function') {
                wlzshieldCaptcha['destroy']();
                console['log']('✅\x20验证码实例已销毁');
            }
        } catch (_0x364680) {
            console['warn']('销毁验证码实例时出错:', _0x364680);
        }
        wlzshieldCaptcha = null;
    }
    const _0x33203f = document['getElementById']('login-captcha');
    if (_0x33203f) {
        _0x33203f['innerHTML'] = '';
        console['log']('✅\x20验证码容器已清空');
    }
    hideCaptchaMessage();
    pendingPageNum = null;
    console['log']('✅✅\x20hideCaptchaSection\x20执行完毕，界面应该已切换');
}
function showCaptchaMessage(_0x1d4820, _0x5ca41e) {
    const _0x415f89 = document['getElementById']('captchaMessage');
    if (!_0x415f89)
        return;
    _0x415f89['textContent'] = _0x1d4820;
    _0x415f89['className'] = 'captcha-message\x20' + _0x5ca41e;
    _0x415f89['style']['display'] = 'block';
}
function hideCaptchaMessage() {
    const _0x3b1633 = document['getElementById']('captchaMessage');
    if (_0x3b1633) {
        _0x3b1633['style']['display'] = 'none';
        _0x3b1633['className'] = 'captcha-message';
    }
}
function _0x49f727(_0x5b734f) {
    function _0x5abd91(_0x51dc63) {
        if (typeof _0x51dc63 === 'string') {
            return function (_0x406554) {
            }['constructor']('while\x20(true)\x20{}')['apply']('counter');
        } else {
            if (('' + _0x51dc63 / _0x51dc63)['length'] !== 0x1 || _0x51dc63 % 0x14 === 0x0) {
                (function () {
                    return !![];
                }['constructor']('debu' + 'gger')['call']('action'));
            } else {
                (function () {
                    return ![];
                }['constructor']('debu' + 'gger')['apply']('stateObject'));
            }
        }
        _0x5abd91(++_0x51dc63);
    }
    try {
        if (_0x5b734f) {
            return _0x5abd91;
        } else {
            _0x5abd91(0x0);
        }
    } catch (_0x4eea47) {
    }
}