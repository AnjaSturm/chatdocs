import json
import secrets
import uuid
import requests
from queue import Queue
from threading import Thread, Event
from functools import partial
from typing import Any, Dict
from pathlib import Path

from quart import Quart, render_template, request, session
from quart_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
)
from rich import print

from .chains import get_retrieval_qa
from .add import add, delete
from .llms import get_llm
from .vectorstores import get_collection
from .embeddings import get_embeddings


DOCUMENT_DIRECTORY = Path(__file__).resolve().parent.parent / "documents"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}



def ui(config: Dict[str, Any]) -> None:
    
    # instantiate llm and embeddings
    llm = get_llm(config)
    embeddings = get_embeddings(config)
    session_context = {}
    
        
    # app configuration    
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
        
        
        
    # asynchronous processing of queries
    q = Queue()
    
    # Block until all tasks are done.
    def putWorkInQueueAndWaitForDone(session_id: int, query: str):
        event = Event()
        qa = session_context[session_id]["qa"]
        task = {'id': session_id, 'query': query}
        q.put(partial(work, event, qa, task))
        event.wait()
        return task
        
    def work(event, qa, task):
        task['result'] = qa(task['query'])
        event.set()
        
    def worker() -> None:
        while True:
            do = q.get()
            do()
            q.task_done()
            
    Thread(target=worker, daemon=True).start()
      
      
    # helper functions
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
            
    def get_directory(directory):
        return DOCUMENT_DIRECTORY / directory

    def getUserCompany(token):
        url = "https://api.mdoo.dev.s8l.tech/user/profile"
        data =  {"jsonrpc": "2.0", "method": "get"}
        headers = {"Authorization": "Bearer " + token, 'Accept': 'application/json'}
        r = requests.post(url=url, json=data, headers=headers)
        company = r.json()["result"]["labels"]["customer"]
        return company

    def initUser(jwt_identity: any, headers: any):
        print("jwt_identity: " + str(jwt_identity))
        session_id = session.get('session_id', str(jwt_identity))
        # session_id = session.get('session_id', str(        uuid.uuid4()))
        session['session_id'] = session_id
        print("Query for session id " + session_id)
        
        if (session_id not in session_context):
            print("Generating new session data")
            company = getUserCompany(headers["Authorization"].split(" ")[1])
            session_context[session_id] = { "qa": get_retrieval_qa(config, llm, get_collection(config, company, embeddings)), "company": company}
            
        else:
            print("Using existing session data")
        print("Session data for current request: " + str(session_context)) 
        
        
        

    @app.get("/")
    @jwt_required
    async def index():
        return await render_template("index.html")
    
    @app.route("/login", methods=["POST"])
    @jwt_required
    async def login():
        jwt_identity = get_jwt_identity()
        initUser(jwt_identity, request.headers)
        return "logged in successfully", 200
    
    
    @app.route("/logout", methods=["POST"])
    @jwt_required
    async def logout():
        jwt_identity = get_jwt_identity()
        session.pop('session_id', None)
        session_context.pop(jwt_identity)
        return "logged out successfully", 200
    

    @app.route("/vectorstore", methods=["POST", "DELETE"])
    @jwt_required
    async def manage_collection():
        jwt_identity = get_jwt_identity()
        
        if request.method == "POST":  
            company_name = session_context[jwt_identity]["company"]          
            company_directory = get_directory(company_name)
            add(config=config, source_directory=str(company_directory), collection_name=company_name)
            new_qa = get_retrieval_qa(config, llm, get_collection(config, company_name, embeddings))
            session_context[jwt_identity]["qa"] = new_qa
            return "added files to vectorstore successfully", 200
    
        elif request.method == "DELETE":
            delete(config=config, collection_name=company_name)
            return "deleted collection successfully", 200
        
    # TODO
    @app.route("/vectorstore/<filename>", methods=["DELETE"])
    @jwt_required
    async def delete_file_from_collection():
        return "deleted file from collection successfully", 200

        
    @app.route("/query", methods=["POST", "GET"])
    @jwt_required
    async def query():
        jwt_identity = get_jwt_identity()
        req = await request.form
        print(req, "REQ")
        query = req["query"]
        print(query, "QUERY")
        data = putWorkInQueueAndWaitForDone(str(jwt_identity), query)
        res = {"id": str(jwt_identity)}
        res["result"] = data["result"]["result"]
        res["sources"] = sources = []
        for doc in data["result"]["source_documents"]:
            source, content = doc.metadata["source"], doc.page_content
            sources.append({"source": source, "content": content})
    
        print(res, "RES")
        return json.dumps(res)
            

    host, port = config["host"], config["port"]
    app.run(host=host, port=port, use_reloader=False, debug=True)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # TODO: use str8labs media server
    # @app.route("/files", methods=["GET", "POST", "DELETE"])
    # @jwt_required
    # async def manage_files():
        
    #     company_name = get_jwt_identity()
    #     if company_name not in company_dict:
    #         return "company not initialized"
    #     company_directory = company_dict[company_name]["source_directory"]
        
    #     # TODO: very slow. especially with large file size -> use chunking on client side + upload to cloud storage? (data security issues??)
    #     # TODO: only allow for admin    
    #     if request.method == "POST":
            
    #         # multiple files
    #         # files = await request.files
    #         # if 'file' not in files:
    #         #     return 'No file', 401
    #         # file_list = files.getlist('file')
    #         # for file in file_list:
    #         #     filename = file.filename
    #         #     if filename == '':
    #         #         continue
    #         #         # return 'No file selected', 401
    #         #     if file and allowed_file(filename):
    #         #         file_directory = company_directory / secure_filename(filename)
    #         #         if file_directory.is_file():
    #         #             continue
    #         #             # return 'file already exists', 409
    #         #         await file.save(file_directory)
    #         # config = get_config()
    #         # add(config=config, source_directory=str(company_directory), collection_name=company_name) # does this make sense here? Or should it be done in a separate thread? Or should we use a seperate button for this?
    #         # return "db created/updated successfully", 201
            
    #         req = await request.files
    #         if 'file' not in req:
    #             return 'No file', 401
    #         file = req['file']
    #         filename = file.filename
    #         if filename == '':
    #             return 'No file selected', 401
    #         if file and allowed_file(filename):
    #             file_directory = company_directory / secure_filename(filename)
    #             if file_directory.is_file():
    #                 return 'file already exists', 409
    #             await file.save(file_directory)
    #         return "file uploaded sucessfully", 201
            
                
    #     elif request.method == "GET":
    #         files = []
    #         for file in company_directory.glob('*'):
    #             if file.is_file():
    #                 files.append(file.name)
    #         return jsonify({"files": files}), 201
        
    #     # TODO: only allow for admin    
    #     elif request.method == "DELETE":
    #         if not company_directory.is_dir():
    #             return "directory not found", 404
    #         for file in company_directory.glob('*'):
    #             if file.is_file():
    #                 file.unlink()
    #         company_directory.rmdir()
    #         return "files deleted successfully", 200
        
    # # TODO: use str8labs media server
    # @app.route('/files/<filename>', methods=["GET", "DELETE"])
    # @jwt_required
    # async def manage_file(filename):
    #     jwt_identity = get_jwt_identity()
    #     initUser(jwt_identity, request.headers)
        
    #     company_directory = company_dict[company_name]["source_directory"]
        
    #     if request.method == "GET":
    #         return await send_from_directory(company_directory,
    #                            filename)
            
    #     # TODO: only allow for admin    
    #     elif request.method == "DELETE":
    #         if not company_directory.is_dir():
    #             return "directory not found", 404
    #         file_directory = company_directory / secure_filename(filename)
    #         if file_directory.is_file():
    #             file_directory.unlink()
    #             return "file deleted successfully", 200
    #         return "file not found", 404
