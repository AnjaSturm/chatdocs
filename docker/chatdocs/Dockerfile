FROM python:3

# follow https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html to use GPU with this Dockerfile

WORKDIR /usr/src/app

RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get install unzip

RUN pip install --timeout=900 --no-cache-dir \
	"chromadb>=0.3.0,<0.4.0" \
	"ctransformers>=0.2.12,<0.3.0" \
	"deepmerge>=1.1.0,<2.0.0"\
        "InstructorEmbedding>=1.0.1,<2.0.0"\
        "langchain>=0.0.181"\
        "pyyaml>=6.0"\
        "quart>=0.18.3,<0.19.0"\
        "sentence-transformers>=2.2.2,<3.0.0"\
        "tqdm>=4.64.1,<5.0.0"\
        "typer>=0.9.0"\
        "typing-extensions>=4.4.0,<5.0.0"\
        "extract-msg>=0.41.0,<0.42.0"\
        "pandoc>=2.3,<3.0.0"\
        "pypandoc>=1.11,<2.0.0"\
        "pdfminer.six==20221105"\
        "unstructured>=0.6.0,<0.7.0"\
        "argilla==1.8.0"

RUN pip install --timeout=900 -U --no-cache-dir \
	"transformers==4.31.0" \
	"accelerate==0.21.0" \
	"einops==0.6.1" \
	"langchain==0.0.240" \
	"xformers==0.0.20" \
	"bitsandbytes==0.41.0"

RUN wget -O quantization.zip https://github.com/AnjaSturm/chatdocs/archive/refs/heads/quantization.zip && unzip quantization.zip && mv chatdocs-quantization/chatdocs chatdocs && rm -rf quantization.zip chatdocs-quantization

ENV PYTHONPATH=/usr/src/app
EXPOSE 5000
VOLUME ["/root/.cache/torch", "/root/.cache/huggingface", "/usr/src/app/documents", "/usr/src/app/db", "/usr/src/app/control"]

COPY startup.bash /usr/src/app/startup.bash
CMD [ "./startup.bash" ]