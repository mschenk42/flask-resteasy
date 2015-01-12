from distutils.core import setup

setup(
    name='Flask-RestEasy',
    version='0.0.1',
    packages=['flask_resteasy'],
    author='Michael Schenk',
    author_email='',
    description='',
    url='',
    zip_safe=False,
    include_package_data=True,
    license='BSD',
    platforms='any',
    install_requires=['Flask', 'Flask-SQLAlchemy', 'inflection'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Frameworks",
        "License :: OSI Approved :: BSD License",
    ],
)
