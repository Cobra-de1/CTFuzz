from setuptools import setup
from distutils.command.build import build as DistutilsBuild


class Build(DistutilsBuild):
    def run(self):
        DistutilsBuild.run(self)


setup(
    name='ctfuzz',
    version='1.0.0',
    platforms='Posix',
    install_requires=[
        'gym>=0.10.3',
        'posix-ipc>=1.1.1',
        'xxhash>=3.2.0',
    ],
    author='cobra',
    packages=[
        'ctfuzz',
        'ctfuzz.coverage',
        'ctfuzz.envs',
    ],
    cmdclass={'build': Build}
)
