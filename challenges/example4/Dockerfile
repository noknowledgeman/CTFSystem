FROM ubuntu:22.04

# 1. Install packages
RUN apt-get update && \
    apt-get install -y apache2 vsftpd apache2-utils ftp && \
    rm -rf /var/lib/apt/lists/*

# 2. Configure Apache (Web) - Stays in /app
RUN htpasswd -b -c /etc/apache2/.htpasswd admin 123456
RUN echo "Listen 8080" >> /etc/apache2/ports.conf
COPY config/000-default.conf /etc/apache2/sites-available/000-default.conf
RUN a2ensite 000-default.conf
COPY src/ /app/
# Web folder needs to be owned by Apache user
RUN chown -R www-data:www-data /app

# 3. Configure FTP (The Fix)
COPY config/vsftpd.conf /etc/vsftpd.conf

# CRITICAL 1: Create the empty privilege separation directory
RUN mkdir -p /var/run/vsftpd/empty

# CRITICAL 2: The FTP Root must be owned by ROOT and NOT writable
# We create /srv/ftp, make root the owner, and remove write permissions (555)
RUN mkdir -p /srv/ftp && \
    chown root:root /srv/ftp && \
    chmod 555 /srv/ftp

# 4. Create the Hint File
# We write the file directly here. The file itself can be readable (644).
RUN echo "The username for the website is 'admin'." > /srv/ftp/note.txt && \
    chmod 644 /srv/ftp/note.txt

# 5. Open Ports
EXPOSE 8080 21 30000-30010

# 6. Start Services
# We start vsftpd manually in the background
CMD /usr/sbin/vsftpd /etc/vsftpd.conf & /usr/sbin/apache2ctl -D FOREGROUND