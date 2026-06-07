cd "$(git rev-parse --show-toplevel)" && rm -rf ./dist && python -m build && twine upload dist/*
