import json
import uuid
import secrets
import requests
from queue import Queue
from threading import Thread, Event
from functools import partial
from typing import Any, Dict
from .embeddings import get_embeddings
from quart import Quart, jsonify, render_template, request, send_from_directory, session
import chromadb
from langchain.vectorstores.base import VectorStore


# from quart_cors import cors
from quart_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)
from rich import print
from langchain.llms.base import LLM
from langchain.embeddings.base import Embeddings



from .chains import get_retrieval_qa
from .add import add, delete, addApi, Chroma_client
from .llms import get_llm
from .vectorstores import get_collection, get_vectorstore




from werkzeug.utils import secure_filename
from pathlib import Path

DOCUMENT_DIRECTORY = Path(__file__).resolve().parent.parent / "documents"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
def get_directory(directory):
    return DOCUMENT_DIRECTORY / directory

# def initialize_company(config: Dict[str, Any], company_name: str, llm: LLM, dictionary: dict, embeddings: Embeddings):
#     directory = get_directory(company_name)
#     if not directory.is_dir():
#         directory.mkdir(parents=True, exist_ok=True)
#     print(str(directory), "DIRECTORY")
#     print(company_name, "COMPANY_NAME")
#     add(config=config, source_directory=str(directory), collection_name=company_name)
#     collection = get_collection(config, company_name, embeddings)
#     # qa for company
#     qa = get_retrieval_qa(config, llm, collection)
#     dictionary[company_name] = {"collection": collection, "source_directory": directory, "qa": qa}


def initialize_company(config: Dict[str, Any], company_name: str, llm: LLM, dictionary: dict, embeddings: Embeddings, vectorstore: VectorStore):
    directory = get_directory(company_name)
    if not directory.is_dir():
        directory.mkdir(parents=True, exist_ok=True)
    vectorstore._client.create_collection(name=company_name, embedding_function=embeddings)
    vectorstore.persist()
    collection = get_collection(config, company_name, embeddings)
    qa = get_retrieval_qa(config, llm, collection)
    dictionary[company_name] = {"collection": collection, "source_directory": directory, "qa": qa}
    
    
def initialize_company2(config: Dict[str, Any], company_name: str, llm: LLM, dictionary: dict, embeddings: Embeddings):
    vectorstore = get_vectorstore(config, embeddings)
    if company_name in [collection.name for collection in vectorstore._client.list_collections()]:
        print("already there")
        return
    directory = get_directory(company_name)
    if not directory.is_dir():
        directory.mkdir(parents=True, exist_ok=True)
    vectorstore._client.create_collection(name=company_name, embedding_function=embeddings)
    vectorstore.persist()
    vectorstore = None
    collection = get_collection(config, company_name, embeddings)
    qa = get_retrieval_qa(config, llm, collection)
    dictionary[company_name] = {"collection": collection, "source_directory": directory, "qa": qa}


def ui(config: Dict[str, Any]) -> None:
    llm = get_llm(config)
    embeddings = get_embeddings(config)
    # embeddings3 = get_embeddings(config) #why do more embeddings not make a differnece?
    

    # vectorstore = get_vectorstore(config, embeddings) # find better way to get collections that takes less memory
    # company_names = [collection.name for collection in vectorstore._client.list_collections()]
    # print(company_names, "COMPANY_NAMES")
    company_names = ['e27bca47-6121-11ee-a514-1ed95c0119b6'] # test user
    user_labels = {}
    session_context = {}
    
    company_dict = {}
    for company in company_names:
        collection = get_collection(config, company, embeddings)
        company_dict[company] = {"collection": collection, "source_directory": get_directory(company), "qa": get_retrieval_qa(config, llm, collection)}
    
    q = Queue()

    def worker() -> None:
        while True:
            do = q.get()
            do()
            q.task_done()
            
    Thread(target=worker, daemon=True).start()
    
    # Block until all tasks are done.
    def putWorkInQueueAndWaitForDone(id: int, query: str, company_name: str):
        event = Event()
        qa = get_retrieval_qa(config, llm, get_collection(config, "cat", embeddings))
        # qa = company_dict[company_name]["qa"]
        task = {'id': id, 'query': query}
        q.put(partial(work, event, qa, task))
        event.wait()
        return task
        
    def work(event, qa, task):
        task['result'] = qa(task['query'])
        event.set()
        
    app = Quart(__name__, template_folder="data")
    app.config["SECRET_KEY"] = secrets.token_hex(16)
    app.config["JWT_ALGORITHM"] = "RS512"
    app.config["JWT_DECODE_AUDIENCE"] = "cms"
    app.config["JWT_IDENTITY_CLAIM"] = "uuid"
    app.config["JWT_PUBLIC_KEY"] = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvTwOh74XQpC5E8w5qmmc
OclCU8sf8oC0UFbtgFQUWTED/vw2LxJ8F8ZihM1qm9B9dbVPeTcsWtEe5SqWj3S9
bu/UttZYkVL3SRCQyIFCoKWYpC84dLSwxEe1Ewht0sfbwrjxSoG0ajGLqc/dywII
1xTeeS75WXrHy0toLbmMiKN218nK2wY2qQySLuIx/Kmz72UwlU05RGS4Oq/Fh4pt
UijGy2974VspHY+XrggzbKT2wzo8GNiFx16vuZdPNyXrZxUkqKjNZxpXvpJQ5YW6
3Jm4bg0RUZn3/ALa0bVsSkJ5Nt0itNNIwX5Bq/TkmMnlqGghk+CL3nTJpWRLworT
/wIDAQAB
-----END PUBLIC KEY-----
    """
    jwt = JWTManager(app)

    def getUserLabels(userid, token):
        r = requests.post()

    @app.get("/")
    @jwt_required
    async def index():
        return await render_template("index.html")
    
    
    @app.route("/dict", methods=["GET"])
    @jwt_required
    async def get_dict():
        print(company_dict, "COMPANY_DICT")
        return "COMPANY_DICT", 200
    
    @app.route("/init", methods=["POST"])
    @jwt_required
    async def init():
        company_name = get_jwt_identity()
        if company_name in company_dict:
            return "company already initialized"
        initialize_company2(config, company_name, llm, company_dict, embeddings)
        return "initialized company", company_name, "successfully", 200
    

    @app.route("/vectorstore", methods=["POST", "DELETE"])
    @jwt_required
    async def manage_collection():
        company_name = get_jwt_identity()
        if company_name not in company_dict:
            return "company not initialized"
        
        if request.method == "POST":            
            company_directory = company_dict[company_name]["source_directory"]
            company_collection = company_dict[company_name]["collection"]
            company_dict[company_name]["collection"] = None
            
            #add(config=config, source_directory=str(company_directory), collection_name=company_name)
            addApi(config=config, source_directory=str(company_directory), collection_name=company_name)
            # vectorstore.persist()
            new_collection = get_collection(config, company_name, embeddings)
            new_qa = get_retrieval_qa(config, llm, new_collection)
            company_dict[company_name]["collection"] = new_collection
            company_dict[company_name]["qa"] = new_qa
            
            return "added files to vectorstore successfully", 200
    
        elif request.method == "DELETE":
            #delete(config=config, collection_name=company_name, vectorstore=vectorstore)
            return "deleted collection successfully", 200
        
    # TODO
    @app.route("/vectorstore/<filename>", methods=["DELETE"])
    @jwt_required
    async def delete_file_from_collection():
        company_name = get_jwt_identity()
        if company_name not in company_dict:
            return "company", company_name, "not initialized"
    
        delete(vectorstore=vectorstore, collection_name=company_name, embeddings=embeddings)
        return "deleted file from collection successfully", 200

        
    # TODO: use str8labs media server
    @app.route("/files", methods=["GET", "POST", "DELETE"])
    @jwt_required
    async def manage_files():
        
        company_name = get_jwt_identity()
        if company_name not in company_dict:
            return "company not initialized"
        company_directory = company_dict[company_name]["source_directory"]
        
        # TODO: very slow. especially with large file size -> use chunking on client side + upload to cloud storage? (data security issues??)
        # TODO: only allow for admin    
        if request.method == "POST":
            
            # multiple files
            # files = await request.files
            # if 'file' not in files:
            #     return 'No file', 401
            # file_list = files.getlist('file')
            # for file in file_list:
            #     filename = file.filename
            #     if filename == '':
            #         continue
            #         # return 'No file selected', 401
            #     if file and allowed_file(filename):
            #         file_directory = company_directory / secure_filename(filename)
            #         if file_directory.is_file():
            #             continue
            #             # return 'file already exists', 409
            #         await file.save(file_directory)
            # config = get_config()
            # add(config=config, source_directory=str(company_directory), collection_name=company_name) # does this make sense here? Or should it be done in a separate thread? Or should we use a seperate button for this?
            # return "db created/updated successfully", 201
            
            req = await request.files
            if 'file' not in req:
                return 'No file', 401
            file = req['file']
            filename = file.filename
            if filename == '':
                return 'No file selected', 401
            if file and allowed_file(filename):
                file_directory = company_directory / secure_filename(filename)
                if file_directory.is_file():
                    return 'file already exists', 409
                await file.save(file_directory)
            return "file uploaded sucessfully", 201
            
                
        elif request.method == "GET":
            files = []
            for file in company_directory.glob('*'):
                if file.is_file():
                    files.append(file.name)
            return jsonify({"files": files}), 201
        
        # TODO: only allow for admin    
        elif request.method == "DELETE":
            if not company_directory.is_dir():
                return "directory not found", 404
            for file in company_directory.glob('*'):
                if file.is_file():
                    file.unlink()
            company_directory.rmdir()
            return "files deleted successfully", 200
        
    # TODO: use str8labs media server
    @app.route('/files/<filename>', methods=["GET", "DELETE"])
    @jwt_required
    async def manage_file(filename):
        company_name = get_jwt_identity()
        if company_name not in company_dict:
            return "company not initialized"
        company_directory = company_dict[company_name]["source_directory"]
        
        if request.method == "GET":
            return await send_from_directory(company_directory,
                               filename)
            
        # TODO: only allow for admin    
        elif request.method == "DELETE":
            if not company_directory.is_dir():
                return "directory not found", 404
            file_directory = company_directory / secure_filename(filename)
            if file_directory.is_file():
                file_directory.unlink()
                return "file deleted successfully", 200
            return "file not found", 404
    
        
    @app.route("/query", methods=["POST", "GET"])
    @jwt_required
    async def query():
        company_name = get_jwt_identity()
        print("company_name: " + str(company_name))
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        print("Query for session id " + session_id)
        if (session_id not in session_context):
            print("Generating new session data")
            session_context[session_id] = { "qa": get_retrieval_qa(config, llm, get_collection(config, company_name, embeddings)), "user_labels": {} }
        else:
            print("Using existing session data")
        print("Session data for current request: " + str(session_context[session_id]))
        
        req = await request.form
        id, query = req["id"], req["query"]
        data = putWorkInQueueAndWaitForDone(id, query, company_name)
        res = {"id": id}
        res["result"] = data["result"]["result"]
        res["sources"] = sources = []
        for doc in data["result"]["source_documents"]:
            source, content = doc.metadata["source"], doc.page_content
            sources.append({"source": source, "content": content})
    
        print(res, "RES")
        return json.dumps(res)
            

    host, port = config["host"], config["port"]
    app.run(host=host, port=port, use_reloader=False, debug=True)
