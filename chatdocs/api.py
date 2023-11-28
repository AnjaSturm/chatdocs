import json
import secrets
import uuid
import requests
from queue import Queue
from threading import Thread, Event
from functools import partial
from typing import Any, Dict
from pathlib import Path

from werkzeug.utils import secure_filename

from quart import Quart, request, session, jsonify, send_from_directory
from quart_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
)
from rich import print

from .chains import get_retrieval_qa
from .add import add, delete, delete_file
from .llms import get_llm
from .vectorstores import get_collection


DOCUMENT_DIRECTORY = Path(__file__).resolve().parent.parent / "documents"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}



def api(config: Dict[str, Any]) -> None:
    
    # instantiate llm and qa
    llm = get_llm(config)
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
    def putWorkInQueueAndWaitForDone(query: str):
        event = Event()
        qa = session_context["qa"]
        task = {'id': str(uuid.uuid4()), 'query': query}
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

    def getUserData(token):
        url = "https://api.mdoo.dev.s8l.tech/user/profile"
        data =  {"jsonrpc": "2.0", "method": "get"}
        headers = {"Authorization": "Bearer " + token, 'Accept': 'application/json'}
        r = requests.post(url=url, json=data, headers=headers)
        labels = r.json()["result"]["labels"]
        if "straightdocs-admin" in labels:
            admin =  True
        else:
            admin = False
        company = labels["customer"]
        return company, admin

    def initUser(headers: any):
        company, admin = getUserData(headers["Authorization"].split(" ")[1])
        if 'session_id' not in session:
            session['session_id'] = str(        uuid.uuid4())
        if 'company' not in session:
            session['company'] = company
        if 'admin' not in session:
            session['admin'] = admin
        
        session_id = session['session_id']
        print("Query for session id " + session_id)
        
        if (session_id not in session_context):
            print("Generating new session data")
            session_context['session_id'] = session_id
            session_context["qa"] = get_retrieval_qa(config, llm, get_collection(company))
            
        else:
            print("Using existing session data")
        print("Session data for current request: " + str(session_context)) 
        
        
    @app.route("/login", methods=["POST"])
    @jwt_required
    async def login():
        jwt_identity = get_jwt_identity()
        print("jwt_identity: " + str(jwt_identity))
        initUser(request.headers)
        return jsonify({"message": "logged in successfully"}), 200


    @app.route("/logout", methods=["POST"])
    @jwt_required
    async def logout():
        session.clear()
        session_context.clear()
        return jsonify({"message": "logged out successfully"}), 200
    
    
    @app.route("/query", methods=["POST", "GET"])
    @jwt_required
    async def query():
        req = await request.form
        query = req["query"]
        data = putWorkInQueueAndWaitForDone(query)
        res = {"id": data["id"]}
        res["result"] = data["result"]["result"]
        res["sources"] = sources = []
        for doc in data["result"]["source_documents"]:
            source, content = doc.metadata["source"], doc.page_content
            sources.append({"source": source, "content": content})
    
        print(res, "RES")
        return json.dumps(res)
    
    
    # TODO: use str8labs media server in future?
    @app.route("/files", methods=["GET", "POST", "DELETE"])
    @jwt_required
    async def manage_files():
        if not session["admin"]:
            return jsonify({"message": "Unauthorized, only allowed for admin"}), 401
        company_name = session["company"]   
        company_directory = DOCUMENT_DIRECTORY / company_name  
        
        if request.method == "POST":
            if not company_directory.exists():
                company_directory.mkdir(parents=True, exist_ok=True)
                
            req = await request.files
            if 'file' not in req:
                return jsonify({"message": 'No file'}), 400

            file = req['file']
            if file.filename == '':
                return jsonify({"message": 'No file selected'}), 400
            
            filename = secure_filename(file.filename)
            file_directory = company_directory / filename
            if file_directory.is_file():
                return jsonify({"message": 'File already exists'}), 409
            
            if not allowed_file(filename):
                return jsonify({"message": 'File type not allowed'}), 415
            
            try:
                await file.save(file_directory)
                return jsonify({"message": f"File {str(filename)} uploaded successfully"}), 201
            except Exception as e:
                return jsonify({"message": f"Failed to upload file: {str(e)}"}), 500

        elif request.method == "GET":
            files = [file.name for file in company_directory.glob('*') if file.is_file()]
            return jsonify({"files": files}), 200
        
        elif request.method == "DELETE":
            if not company_directory.is_dir():
                return jsonify({"message": f"Directory {str(company_directory)} not found"}), 404
            
            file_list = [file for file in company_directory.glob('*') if file.is_file()]
            for file in file_list:
                file.unlink()
                    
            if not any(company_directory.iterdir()):
                company_directory.rmdir()
                return jsonify({"message": f"All files from company {str(company_name)} deleted successfully"}), 200
            
            return jsonify({"message": f"All files from company {str(company_name)} deleted successfully"}), 200
        
        
    # TODO: use str8labs media server
    @app.route('/files/<filename>', methods=["GET", "DELETE"])
    @jwt_required
    async def manage_file(filename):
        if not session["admin"]:
            return jsonify({"message": "Unauthorized, only allowed for admin"}), 401
        company_name = session["company"]   
        company_directory = DOCUMENT_DIRECTORY / company_name 
        
        if request.method == "GET":
            return await send_from_directory(company_directory,
                               filename)
            
        elif request.method == "DELETE":
            if not company_directory.is_dir():
                return "directory not found", 404
            file_directory = company_directory / secure_filename(filename)
            if file_directory.is_file():
                file_directory.unlink()
                return jsonify({"message": f"File {str(filename)} deleted successfully"}), 200
            return jsonify({"message": f"File {str(filename)} not found"}), 404
        

    @app.route("/vectorstore", methods=["POST", "DELETE"])
    @jwt_required
    async def vectorstore():
        if not session["admin"]:
            return jsonify({"message": "Unauthorized, only allowed for admin"}), 401
        company_name = session["company"]  
        company_directory = DOCUMENT_DIRECTORY / company_name
        
        if request.method == "POST":  
            add(source_directory=str(company_directory), collection_name=company_name)
            new_qa = get_retrieval_qa(config, llm, get_collection(company_name))
            session_context["qa"] = new_qa
            return jsonify({"message": f"added files to collection {str(company_name)} successfully"}), 200
    
        elif request.method == "DELETE":
            delete(collection_name=company_name)
            new_qa = get_retrieval_qa(config, llm, get_collection(company_name))
            session_context["qa"] = new_qa
            return jsonify({"message": f"deleted collection {str(company_name)} successfully"}), 200
            
     
    @app.route("/vectorstore/<filename>", methods=["DELETE"])
    @jwt_required
    async def delete_file_from_collection(filename):
        if not session["admin"]:
            return jsonify({"message": "Unauthorized, only allowed for admin"}), 401
        company_name = session["company"] 
        company_directory = DOCUMENT_DIRECTORY / company_name / filename
        delete_file(company_name, str(company_directory))
        new_qa = get_retrieval_qa(config, llm, get_collection(company_name))
        session_context["qa"] = new_qa
        return jsonify({"message": f"deleted file {str(filename)} from collection {str(company_name)} successfully"}), 200
            

    host, port = config["host"], config["port"]
    app.run(host=host, port=port, use_reloader=False, debug=True)
    
    


