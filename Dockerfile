FROM wordpress:php8.2-apache

# Install WP-CLI
USER root
RUN curl -sSL https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar -o /usr/local/bin/wp \
    && chmod +x /usr/local/bin/wp

# PHP2Shell (CVE-2026-109618 / CVE-2026-109619) hardening:
# disable session.upload_progress (exploit vector of CVE-2026-109619)
RUN echo 'session.upload_progress.enabled = Off' > /usr/local/etc/php/conf.d/zz-php2shell-hardening.ini
