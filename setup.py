import io, re, glob, os
from setuptools import setup

package_name = 'usta_tennis'
init_py = io.open('{}/__init__.py'.format(package_name)).read()
metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_py))
metadata['doc'] = re.findall('"""(.+)"""', init_py)[0]
SETUP_PTH = os.path.dirname(os.path.abspath(__file__))

setup(
    name = package_name,
    version = metadata['version'],
    description = metadata['doc'],
    author = metadata['author'],
    author_email = metadata['email'],
    url = metadata['url'],
    packages = [
        package_name, '{}.tests'.format(package_name),
        'scraper', 'scraper.spiders'
    ],
    install_requires = [
        'appnope', 'attrs', 'backports-abc', 'beautifulsoup4', 'cffi',
        'cryptography', 'cssselect', 'cycler', 'decorator', 'entrypoints',
        'idna', 'inflect', 'ipykernel', 'ipython', 'ipython-genutils',
        'ipywidgets', 'Jinja2', 'jsonschema', 'jupyter', 'jupyter-client',
        'jupyter-console', 'jupyter-core', 'lxml', 'MarkupSafe', 'matplotlib',
        'mistune', 'nbconvert', 'nbformat', 'networkx', 'notebook', 'numpy',
        'parsel', 'pexpect', 'pickleshare', 'prompt-toolkit', 'ptyprocess',
        'pyasn1', 'pyasn1-modules', 'pycparser', 'PyDispatcher', 'Pygments',
        'pymongo', 'pyOpenSSL', 'pyparsing', 'python-dateutil', 'pytz',
        'PyYAML', 'pyzmq', 'qtconsole', 'queuelib', 'requests', 'Scrapy',
        'service-identity', 'simplegeneric', 'six', 'terminado', 'tornado',
        'traitlets', 'Twisted', 'w3lib', 'wcwidth', 'widgetsnbextension',
        'zope.interface',
    ],
    license = 'MIT',
    keywords = ['USTA', 'tennis', 'NTRP', 'rating', 'ranking'],
    scripts = glob.glob(os.path.join(SETUP_PTH, "scripts", "*")),
)
