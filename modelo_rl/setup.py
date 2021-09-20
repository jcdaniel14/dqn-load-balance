from setuptools import setup, find_packages

with open("README.md") as readme_file:
    README = readme_file.read()

setup_args = dict(
    name='modelo_rl',
    version='1.0.0',
    description='Herramienta de toma de decisiones de salidas internacionales basado en analisis de aprendizaje por refuerzo para descongestión automática.',
    long_description_content_type="text/markdown",
    long_description=README,
    license='MIT',
    packages=find_packages(),
    author='Gustavo Santiago, Rosa Campaña',
    author_email='jcdaniel14@gmail.com, rosacampana@gmail.com',
    keywords=['netflow', 'reinforcement learning', 'networking', "machine learning"],
    url='https://gitlab.telconet.ec/jcdaniel14/dqn-load-balance.git',
)

install_requires = [
    "matplotlib==3.4.2",
    "numpy==1.21.0",
    "pandas==1.3.2",
    "Pillow==8.2.0",
    "plotly==5.3.0",
    "pyparsing==2.4.7",
    "python-dateutil==2.8.1",
    "pytz==2021.1",
    "scipy==1.7.1",
    "seaborn==0.11.2",
    "six==1.16.0",
    "tenacity==8.0.1",
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)