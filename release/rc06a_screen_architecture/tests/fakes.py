"""Offline fakes and loaders for the RC06a tests. No Odoo, no network, no writes. Loads the addon modules by path."""
import hashlib, importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.abspath(os.path.join(HERE, "..", "addon", "synapsys"))
FIXTURE = os.environ.get("SYN_REG_FIXTURE") or os.path.abspath(os.path.join(HERE, "..", "..", "rc05_scaffold_lens", "fixtures", "mesh_registry_v0_3.json"))
REG_SHA = "7c31aa1de4c97e8e062c5ae9e2f907b4c67ea0949bf143235499c32b1a30f423"


def load(name):
    if ADDON not in sys.path:
        sys.path.insert(0, ADDON)
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(ADDON, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


sl = load("scaffold_lens")
sd = load("screen_decl")
sr = load("screen_render")
sw = load("scaffold_wire")
sv = load("scaffold_view")

from fakes_core import *  # noqa: F401,F403  (fake env, registry fixture, constants)
from fakes_core import RAW, REG, SHA, Env, STEW, COLL, Row, RecModel, CatModel, Rec, SP01, AccessError  # noqa: F401
