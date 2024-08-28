cd "$(dirname "$0")" || exit
cd ..
pytest
pylint $(git ls-files '*.py')
flake8 $(git ls-files '*.py') --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
#j2lint $(git ls-files '*.j2') --verbose
