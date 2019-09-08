import pip
from setuptools import find_packages, setup

if tuple(map(int, pip.__version__.split("."))) >= (10, 0, 0):
    from pip._internal.download import PipSession
    from pip._internal.req import parse_requirements
else:
    from pip.download import PipSession
    from pip.req import parse_requirements

requirements = parse_requirements("requirements.txt", session=PipSession())
reqs = [str(ir.req) for ir in requirements]

setup(
    name="alexa_youtube_webserver",
    url="https://github.com/ndg63276/alexa-youtube",
    python_requires=">=3.7",
    install_requires=reqs,
    setup_requires=["setupmeta"],
    extras_require={"test": ["tox"]},
    packages=find_packages(exclude=("tests",)),
    entry_points={},
    include_package_data=True,
    versioning="build-id",
    zip_safe=False,
)
