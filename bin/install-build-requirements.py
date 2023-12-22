import subprocess
import sys
try:
    import tomllib as toml
    mode = 'rb'
except ImportError:
    import toml
    mode = 'r'


with open("pyproject.toml", mode) as f:
    pyproject = toml.load(f)

# Install required dependencies
requirements = pyproject['build-system']['requires']

with open('requirements.txt', 'w') as f:
    f.write("\n".join(requirements))

subprocess.run(
    " ".join([
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        "requirements.txt",
    ]),
    shell=True,
    check=True,
)
