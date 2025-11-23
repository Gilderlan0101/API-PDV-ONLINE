import os

from setuptools import find_packages, setup


# Ler dependências do requirements.txt
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]


# Ler README
def read_readme():
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    return 'Qodo PDV - Sistema completo de Ponto de Venda'


setup(
    name='Qodo-pdv',
    version='0.1.0',
    description='Sistema completo de PDV (Ponto de Venda) com múltiplos recursos e integrações',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='Qodo Tech',
    author_email='dacruzgg01@gmail.com',
    url='https://github.com/seu-usuario/qodo-pdv',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    package_data={
        '': ['*.md', '*.txt'],
        'static': ['logo/*.png'],
    },
    include_package_data=True,
    install_requires=[
        'fastapi>=0.100.0',
        'sqlalchemy>=2.0.0',
        'sqlmodel>=0.0.24',
        'tortoise-orm>=0.25.1',
        'pydantic>=2.0.0',
        'pydantic-br>=1.1.0',
        'python-jose>=3.5.0',
        'bcrypt>=4.0.0',
        'redis>=4.5.0',
        'requests>=2.28.0',
        'qrcode>=8.0',
        'fpdf>=1.7.0',
        'reportlab>=4.0.0',
        'pandas>=2.0.0',
        'python-multipart>=0.0.6',
        'python-dateutil>=2.8.0',
        'validate-docbr>=1.11.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=1.0.0',
        ],
        'mysql': [
            'aiomysql>=0.2.0',
            'pymysql>=1.0.0',
        ],
        'sqlite': [
            'aiosqlite>=0.18.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'qodo-pdv=Main:main [假设 Main.py 有 main 函数]',
            'qodo-api=Main:start_server',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Office/Business :: Financial :: Point-Of-Sale',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='pdv ponto-de-venda venda checkout fastapi sqlite mysql',
    python_requires='>=3.8',
    project_urls={
        'Documentation': 'https://qodo-pdv.readthedocs.io',
        'Source': 'https://github.com/seu-usuario/qodo-pdv',
        'Tracker': 'https://github.com/seu-usuario/qodo-pdv/issues',
    },
)
