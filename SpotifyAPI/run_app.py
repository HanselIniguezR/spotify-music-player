"""Small launcher that runs the `PRUEBA.app` module with proper package context.

Usage:
    python run_app.py [--tk]

This avoids import issues when executing the script directly and preserves
command-line args (like --tk to force the tkinter fallback).
"""
import runpy
import sys

if __name__ == "__main__":
    # run PRUEBA.app as a module so package imports resolve reliably
    runpy.run_module('PRUEBA.app', run_name='__main__')
