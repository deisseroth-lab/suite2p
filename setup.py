import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="suite2p",
    version="0.7.4",
    author="Marius Pachitariu and Carsen Stringer",
    author_email="marius10p@gmail.com",
    description="Pipeline for calcium imaging",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MouseLand/suite2p",
    packages=setuptools.find_packages(),
    setup_requires=[
      'pytest-runner',
    ],
    install_requires=[
      'numpy>=1.16',
      'numba>=0.43.1',
      'matplotlib',
      'scipy',
      'h5py',
      'scikit-learn',
      'natsort',
      'rastermap>0.1.0',
      'tifffile',
      'scanimage-tiff-reader',
    ],
    tests_require=[
      'pytest'
    ],
    extras_require={
      "docs": [
        'sphinx>=3.0',
        'sphinxcontrib-apidoc',
        'sphinx_rtd_theme',
      ]
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
      entry_points = {
        'console_scripts': [
          'suite2p = suite2p.__main__:parse_arguments',
        ]
        },
)
