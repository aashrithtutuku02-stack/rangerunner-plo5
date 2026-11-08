"""Benchmark a reviewed local checkout without copying its strategy into ours.

The original callbacks and game types run in a separate interpreter. Additional
diagnostics expose counters and source hashes, never cards or learned state.
"""
import functools
import hashlib
import importlib
import os
from pathlib import Path
import sys


def main():
    root=Path(os.environ['EXTERNAL_BOT_DIR']).resolve()
    os.chdir(root);sys.path.insert(0,str(root))
    bot=importlib.import_module('agent')
    counters={'fallback_calls':0,'caught_model_errors':0}
    original_half=bot.new_half
    def new_half(config,memory):
        counters.update(fallback_calls=0,caught_model_errors=0)
        return original_half(config,memory)
    bot.new_half=new_half
    if hasattr(bot,'_fallback'):
        original_fallback=bot._fallback
        def fallback(*args,**kwargs):
            counters['fallback_calls']+=1
            return original_fallback(*args,**kwargs)
        bot._fallback=fallback
    model=getattr(bot,'_OpponentModel',None)
    def instrument(fn):
        @functools.wraps(fn)
        def measured(*args,**kwargs):
            try:return fn(*args,**kwargs)
            except Exception:
                counters['caught_model_errors']+=1
                raise
        return measured
    if model is not None:
        for name in ('update_from_obs','on_hand_end','profile'):
            if hasattr(model,name):setattr(model,name,instrument(getattr(model,name)))
    sources=set()
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            path=Path(path).resolve()
            if path.is_relative_to(root) and path.is_file():sources.add(path)
    sources.update(root.glob('data/*.npy'))
    if (root/'params.json').exists():sources.add(root/'params.json')
    fingerprints={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)}
    harness_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    from fastapi import Request
    from fastapi.responses import JSONResponse
    @bot.app.get('/_benchmark_status')
    async def status(request:Request):
        if getattr(bot,'TOKEN',None) and request.headers.get('x-agent-token')!=bot.TOKEN:
            return JSONResponse({'error':'unauthorized'},status_code=401)
        error=getattr(bot,'_IMPORT_ERROR',None)
        eq=getattr(bot,'_E',None)
        diagnostic=getattr(bot,'diagnostics',None)
        return dict(counters,core_import_error=type(error).__name__ if error else None,
            core_available=getattr(bot,'_S',True) is not None,
            opponent_model_available=model is not None if hasattr(bot,'_OpponentModel') else None,
            range_module_available=getattr(getattr(bot,'_S',None),'RE',None) is not None if hasattr(bot,'_S') else None,
            preflop_table_loaded=getattr(eq,'PREFLOP_TABLE_LOADED',None),
            callback_errors=bot.MEMORY.get('errors',0),
            native_diagnostics=diagnostic(bot.MEMORY) if callable(diagnostic) else None,
            source_sha256=fingerprints,harness_sha256=harness_digest)
    import uvicorn
    uvicorn.run(bot.app,host='127.0.0.1',port=int(os.environ.get('PORT','5031')),access_log=False)


if __name__=='__main__':main()
