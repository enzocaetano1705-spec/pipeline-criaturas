"""Teste rápido do protótipo: python -m forja exemplo_spec.py --out saida --sem-gif"""
from forja import Model
from forja.templates import quadruped

exemplo = Model("exemplo_quadrupede", palette="jade")
quadruped(exemplo)
