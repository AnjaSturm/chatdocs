FROM python:3

# follow https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html to use GPU with this Dockerfile

WORKDIR /usr/src/app

RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get install unzip

RUN pip install --no-cache-dir "chromadb>=0.3.0,<0.4.0"
RUN pip install --no-cache-dir "ctransformers>=0.2.12,<0.3.0"
RUN pip install --no-cache-dir "deepmerge>=1.1.0,<2.0.0"
RUN pip install --no-cache-dir "InstructorEmbedding>=1.0.1,<2.0.0"
RUN pip install --no-cache-dir "langchain>=0.0.181"
RUN pip install --no-cache-dir "pyyaml>=6.0"
RUN pip install --no-cache-dir "quart>=0.18.3,<0.19.0"
RUN pip install --no-cache-dir "sentence-transformers>=2.2.2,<3.0.0"
RUN pip install --no-cache-dir "tqdm>=4.64.1,<5.0.0"
RUN pip install --no-cache-dir "typer>=0.9.0"
RUN pip install --no-cache-dir "typing-extensions>=4.4.0,<5.0.0"
RUN pip install --no-cache-dir "extract-msg>=0.41.0,<0.42.0"
RUN pip install --no-cache-dir "pandoc>=2.3,<3.0.0"
RUN pip install --no-cache-dir "pypandoc>=1.11,<2.0.0"
RUN pip install --no-cache-dir "pdfminer.six==20221105"
RUN pip install --no-cache-dir "unstructured>=0.6.0,<0.7.0"
RUN pip install --no-cache-dir "argilla==1.8.0"

RUN pip install -U --no-cache-dir "transformers==4.31.0"
RUN pip install -U --no-cache-dir "accelerate==0.21.0"
RUN pip install -U --no-cache-dir "einops==0.6.1"
RUN pip install -U --no-cache-dir "langchain==0.0.240"
RUN pip install -U --no-cache-dir "xformers==0.0.20"
RUN pip install -U --no-cache-dir "bitsandbytes==0.41.0"

RUN wget -O quantization.zip https://github.com/AnjaSturm/chatdocs/archive/refs/heads/quantization.zip && unzip quantization.zip && mv chatdocs-quantization/chatdocs chatdocs && rm -rf quantization.zip chatdocs-quantization

ENV PYTHONPATH=/usr/src/app
EXPOSE 5000
VOLUME ["/root/.cache/torch", "/root/.cache/huggingface", "/usr/src/app/documents", "/usr/src/app/db", "/usr/src/app/control"]

COPY startup.bash /usr/src/app/startup.bash
CMD [ "./startup.bash" ]
