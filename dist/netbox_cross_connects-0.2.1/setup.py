from setuptools import find_packages, setup

setup(
    name='netbox-cross-connects',
    version='0.2.1',
    description='NetBox plugin for managing cross connects.',
    packages=find_packages(exclude=('netbox_cross_connects.tests', 'netbox_cross_connects.tests.*')),
    include_package_data=True,
    install_requires=['Pillow'],
    package_data={
        'netbox_cross_connects': [
            'templates/**/*.html',
            'static/**/*.js',
            'docs/**/*.md',
        ],
    },
    python_requires='>=3.10',
)
