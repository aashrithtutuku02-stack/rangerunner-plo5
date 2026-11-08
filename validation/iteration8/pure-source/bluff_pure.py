"""Fold-only bluff score: never credit showdown equity when selecting a bluff."""
import bluff_read

observe=bluff_read.observe
fold_bound=bluff_read.fold_bound
coin=bluff_read.coin


def choose(obs,memory,equity,passive_ev,action,frequency=.25):
    if equity>=.45:
        memory['bluff_override']=False
        return action
    return bluff_read.choose(obs,memory,0.,passive_ev,action,frequency)
