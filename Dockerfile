ARG TERRAFORM_VERSION=0.14.9
ARG PACKER_VERSION=1.7.1
ARG PYTHON_VERSION=3.9-buster

FROM hashicorp/terraform:$TERRAFORM_VERSION
FROM hashicorp/packer:$PACKER_VERSION
FROM python:$PYTHON_VERSION

COPY --from=0 /bin/terraform /bin/terraform
COPY --from=1 /bin/packer /bin/packer

RUN pip3 install --no-cache-dir --upgrade pip && \
  pip3 install --no-cache-dir boto3

CMD ["/bin/bash"]
