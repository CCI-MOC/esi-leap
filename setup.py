import setuptools

# In python < 2.7.4, a lazy loading of package `pbr` will break
# setuptools if some other modules registered functions in `atexit`.
# solution from: http://bugs.python.org/issue15881#msg170215
try:
    import multiprocessing  # noqa pylint: disable=unused-import
except ImportError:
    pass

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(
    setup_requires=['pbr>=2.0.0'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    pbr=True)
