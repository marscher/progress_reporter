updating tqdm subtree
---------------------

1. clone the repo:

  git clone https://github.com/tqdm/tqdm

2. split subtree

  cd tqdm
  git checkout release-tag
  git subtree split -p tqdm -b lib

3. add slitted subtree in this repo

  git subtree add --squash -p progress_reporter/_vendor/tqdm tqdm lib 

