FROM alpine:3.12
MAINTAINER Scott Pierce <ddrscott@gmail.com>

RUN apk add --update \
    w3m \
    && rm -rf /var/cache/apk/*

ADD bin/ /bin/
