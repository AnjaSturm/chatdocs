FROM debian:stable-slim

RUN apt-get -y update && apt-get -y dist-upgrade
RUN apt-get -y install lighttpd

RUN rm -rf /var/www/html/*
# RUN mkdir /var/www/html/documents
# ADD documents.conf /etc/lighttpd/conf-enabled/

EXPOSE 80

VOLUME ["/var/www/html/documents", "/var/log/lighttpd"]

CMD ["lighttpd", "-D", "-f", "/etc/lighttpd/lighttpd.conf"]
