from setuptools import setup, find_packages

with open("README.md") as readme_file:
    README = readme_file.read()

setup_args = dict(
    name='health_monitor',
    version='1.0.0',
    description='Herramienta de monitoreo de salidas internacionales basado en analisis de tráfico Netflow para descongestión automática.',
    long_description_content_type="text/markdown",
    long_description=README,
    license='MIT',
    packages=find_packages(),
    author='Gustavo Santiago',
    author_email='jcdaniel14@gmail.com',
    keywords=['netflow', 'monitoring', 'networking', "devnet"],
    url='https://gitlab.telconet.ec/gsantiago/2021.git',
)

install_requires = [
    "colorlog~=4.7.2"
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)