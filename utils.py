#!/usr/bin/env python3
# utils.py
def fprint(x):
    print("rv => ", x)


def repr_recom(recoms):
    return ", ".join([m + "(" + str(r) + ")" for m, r in recoms]) if recoms is not None else str(None)
