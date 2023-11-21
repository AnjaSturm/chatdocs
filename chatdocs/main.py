from pathlib import Path
from typing import Optional
from chatdocs.embeddings import get_embeddings
from chatdocs.vectorstores import get_collection

import typer
from typing_extensions import Annotated

from .config import get_config

app = typer.Typer()

ConfigPath = Annotated[
    Optional[Path],
    typer.Option(
        "--config",
        "-c",
        help="The path to a chatdocs.yml configuration file.",
    ),
]


@app.command()
def download(config: ConfigPath = None):
    from .download import download

    config = get_config()
    download(config=config)


@app.command()
def add(
    directory: Annotated[
        Path,
        typer.Argument(help="The path to a directory containing documents."),
    ],
    company_name: Annotated[str, typer.Argument(help="The name of the collection.")],
    config: ConfigPath = None,
):
    from .add import add
    
    config = get_config()
    # embeddings = get_embeddings(config)
    # collection = get_collection(config, company_name, embeddings)
    
    # add(config=config, source_directory=str(directory), collection=collection, collection_name=company_name)
    add(config=config, source_directory=str(directory), collection_name=company_name)


@app.command()
def chat(
    query: Annotated[
        Optional[str],
        typer.Argument(
            help="The query to use for retrieval. If not specified, runs in interactive mode."
        ),
    ] = None,
    config: ConfigPath = None,
):
    from .chat import chat

    config = get_config()
    chat(config=config, query=query)


@app.command()
def api(config: ConfigPath = None):
    from .api import api

    config = get_config()
    api(config=config)
