from setuptools import setup, find_packages

setup(
    name="craft_common",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "django>=4.0",
        "djangorestframework>=3.14.0",
        "djangorestframework-simplejwt>=5.3.0",
        "pika>=1.3.2",
        "pydantic>=2.0.0",
        "cryptography>=41.0.0",
    ],
)
