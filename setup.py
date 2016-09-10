#coding: utf-8

#返回上一层执行：python jackals/setup.py install(or develop)

from setuptools import setup, find_packages 

_packages = find_packages(where="..")

setup (name='jackals',
       version='0.1',
       author="djskl",
       packages=_packages 
)