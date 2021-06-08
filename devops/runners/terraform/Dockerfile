FROM hashicorp/terraform:light

RUN  apk update && apk add git

COPY . .

RUN mkdir /repo && chmod +x /run.sh

WORKDIR /repo

ENTRYPOINT ["/run.sh"]