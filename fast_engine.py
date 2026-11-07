"""Load a portable Linux numeric kernel, with the Numba engine as fallback.

The shipped shared library uses the baseline x86-64 instruction set, no Python
extension ABI, and no writable state beyond a call's supplied output arrays.
Source and a build command are included under native/.
"""
import ctypes
from pathlib import Path
import platform
import os

import numpy as np

import equity_engine as reference

percentiles = reference.percentiles
_lib = None
if platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'):
    try:
        _lib = ctypes.CDLL(str(Path(__file__).with_name('native') / 'plo5_fast_linux_x86_64.so'))
    except OSError:
        pass
if len(reference.PREFLOP_KEYS) != 19998 or os.environ.get('RANGERUNNER_ENGINE') == 'numba':
    _lib = None

BACKEND = 'portable C' if _lib is not None else 'Numba'

if _lib is None:
    score = reference.score
    simulate = reference.simulate
    preflop_equity = reference.preflop_equity
    preflop_quality = reference.preflop_quality
    warm_engine = reference.warm_engine
else:
    _intp = ctypes.POINTER(ctypes.c_int32)
    _longp = ctypes.POINTER(ctypes.c_int64)
    _floatp = ctypes.POINTER(ctypes.c_float)
    _doublep = ctypes.POINTER(ctypes.c_double)
    _lib.fast_init.argtypes = [_intp, _longp, _floatp, ctypes.c_int]
    _lib.fast_init.restype = None
    _lib.fast_init(reference.RANK_TABLE.ctypes.data_as(_intp),
                   reference.PREFLOP_KEYS.ctypes.data_as(_longp),
                   reference.PREFLOP_EQUITIES.ctypes.data_as(_floatp),
                   len(reference.PREFLOP_KEYS))
    _lib.fast_score.argtypes = [_intp, _intp, ctypes.c_int]
    _lib.fast_score.restype = ctypes.c_int32
    _lib.fast_equity.argtypes = [_intp]
    _lib.fast_equity.restype = ctypes.c_double
    _lib.fast_simulate.argtypes = [_intp, _intp, ctypes.c_int, ctypes.c_int,
        ctypes.c_uint64, _intp, _doublep, _doublep, _doublep]
    _lib.fast_simulate.restype = ctypes.c_uint64

    def _cards(cards):
        return np.ascontiguousarray(cards, dtype=np.int32)

    def score(hole, board):
        h, b = _cards(hole), _cards(board)
        return _lib.fast_score(h.ctypes.data_as(_intp), b.ctypes.data_as(_intp), len(b))

    def preflop_equity(hole):
        h = _cards(hole)
        return _lib.fast_equity(h.ctypes.data_as(_intp))

    preflop_quality = preflop_equity

    def simulate(hole, board, count, state):
        h, b = _cards(hole), _cards(board)
        hands = np.empty((count, 5), dtype=np.int32)
        values = np.empty((count, 4), dtype=np.float64)
        outcomes = np.empty(count, dtype=np.float64)
        future = np.empty(count, dtype=np.float64)
        rng = _lib.fast_simulate(h.ctypes.data_as(_intp), b.ctypes.data_as(_intp),
            len(b), count, int(state), hands.ctypes.data_as(_intp),
            values.ctypes.data_as(_doublep), outcomes.ctypes.data_as(_doublep),
            future.ctypes.data_as(_doublep))
        return hands, values, outcomes, future, np.uint64(rng)

    def warm_engine():
        # Exercise every board length before serving requests.
        h = _cards([0, 5, 10, 15, 20])
        b = _cards([3, 8, 13, 18, 23])
        for n in (0, 3, 4, 5):
            simulate(h, b[:n], 2, np.uint64(777))


# Validate at the public boundary before passing pointers to native code.
# Invalid shapes or card IDs must raise Python errors, never read beyond C
# buffers. The same checks apply to the Numba fallback.
_backend_score=score
_backend_equity=preflop_equity
_backend_quality=preflop_quality
_backend_simulate=simulate


def _validated(hole,board,board_lengths):
    h=np.asarray(hole);b=np.asarray(board)
    if h.ndim!=1 or b.ndim!=1 or len(h)!=5 or len(b) not in board_lengths:
        raise ValueError('Expected five hole cards and a valid visible board length')
    if h.dtype.kind not in 'iu' or (len(b) and b.dtype.kind not in 'iu'):
        raise ValueError('Cards must be integers')
    cards=h.tolist()+b.tolist()
    if any(c<0 or c>=36 for c in cards) or len(set(cards))!=len(cards):
        raise ValueError('Cards must be distinct integers from 0 to 35')
    return np.ascontiguousarray(h,dtype=np.int32),np.ascontiguousarray(b,dtype=np.int32)


def score(hole,board):
    h,b=_validated(hole,board,(3,4,5))
    return _backend_score(h,b)


def preflop_equity(hole):
    h,b=_validated(hole,(),(0,))
    return _backend_equity(h)


def preflop_quality(hole):
    h,b=_validated(hole,(),(0,))
    return _backend_quality(h)


def simulate(hole,board,count,state):
    h,b=_validated(hole,board,(0,3,4,5))
    if not isinstance(count,(int,np.integer)) or not 1<=count<=65536:
        raise ValueError('Sample count must be an integer from 1 to 65536')
    if not isinstance(state,(int,np.integer)) or not 0<int(state)<2**64:
        raise ValueError('Random state must be a nonzero uint64')
    return _backend_simulate(h,b,int(count),np.uint64(state))
