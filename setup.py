
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

if __name__ == "__main__":

    setup(
	    name="avatario-python-sdk",
    	version="0.1.1",
    	setup_requires=["setuptools>=45", "wheel"],
        author="OneZot Team",
    	author_email="info@onezot.com",
    	description="Python SDK for Avatario services",
    	long_description=long_description,
    	long_description_content_type="text/markdown",
    	url="https://github.com/onezot-python-sdk",
    	packages=find_packages(),
    	license="Apache-2.0",
        classifiers=[
            "Intended Audience :: Developers",
        	"Programming Language :: Python :: 3",
        	"Operating System :: OS Independent",
    	],
        project_urls={
            "Documentation": "https://docs.avatario.io",
            "Source": "https://github.com/avatario-python-sdk",
            "Bug Tracker": "https://github.com/avatario-python-sdk/issues",
            "Changelog": "https://github.com/avatario-python-sdk/blob/main/CHANGELOG.md",
        },
    	python_requires=">=3.8",
    	install_requires=[
            "livekit",
            "livekit-api",
            "requests"
        ],
    )
