from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='spirecomm',
    version='0.6.0',
    packages=['spirecomm', 'spirecomm.ai', 'spirecomm.spire', 'spirecomm.communication'],
    url='https://github.com/ForgottenArbiter/spirecomm',
    license='MIT License',
    author='ForgottenArbiter',
    author_email='forgottenarbiter@gmail.com',
    description='A package for interfacing with Slay the Spire through Communication Mod',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ]
)
