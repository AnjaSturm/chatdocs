#!/bin/bash

if [[ ! -f control/delete-this-to-download-again ]]; then
  python -m chatdocs download
  touch control/delete-this-to-download-again
fi

python -m chatdocs ui
