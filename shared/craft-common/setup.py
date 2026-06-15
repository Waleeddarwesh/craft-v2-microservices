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
        "deep-translator>=1.11.4",
        "drf-spectacular>=0.26.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-instrumentation-django>=0.41b0",
        "opentelemetry-instrumentation-requests>=0.41b0",
        "opentelemetry-exporter-otlp>=1.20.0",
    ],
)
