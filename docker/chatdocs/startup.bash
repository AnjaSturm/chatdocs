#!/bin/bash

if [[ ! -f control/delete-this-to-download-again ]]; then
  echo Using auth token ${AUTHTOKEN} for download
  python -m chatdocs download
  touch control/delete-this-to-download-again
fi

if [[ ! -f control/delete-this-to-add-documents-again ]]; then
  python -m chatdocs add documents/
  touch control/delete-this-to-add-documents-again
fi

python -m chatdocs ui
