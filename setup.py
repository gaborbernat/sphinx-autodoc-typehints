# coding=utf-8

from setuptools import setup

setup(
    name="sphinx-autodoc-types",
    use_scm_version=True,
    description="Type hints (PEP 484) support for the Sphinx autodoc extension (comments too)",
    author="Bernat Gabor",
    author_email="bgabor8@bloomberg.net",
    url="https://github.com/gaborbernat/sphinx-autodoc-typehints",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Sphinx :: Extension",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Framework :: Sphinx :: Extension",
        "Topic :: Documentation :: Sphinx",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    license="MIT",
    zip_safe=True,
    py_modules=["sphinx_autodoc_typehints"],
    setup_requires=["setuptools_scm >= 1.7.0"],
    install_requires=["Sphinx >= 2.0.0, < 3", "pytypes >= 1.0b5, <2"],
    extras_require={"testing": ["pytest >= 3.0.7, < 4"], ':python_version < "3.5"': ["typing >= 3.5.3, <4"]},
)
