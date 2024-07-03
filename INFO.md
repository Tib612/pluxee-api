pants is here:
/home/tib612/.local/bin/pants


Add this in ~/.bashrc:
export PATH="$HOME/.local/bin:$PATH"


You can run the pre-commit manually using:
pre-commit run --all-files --show-diff-on-failure