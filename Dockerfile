FROM wordpress:6.7.2-php8.2-apache

# Install WP-CLI and fix permissions for non-root user
USER root
RUN curl -sSL https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar -o /usr/local/bin/wp \
    && chmod +x /usr/local/bin/wp \
    && chown -R www-data:www-data /var/www/html/wp-content/uploads \
    && chown -R www-data:www-data /var/www/html/wp-content/mu-plugins \
    && chmod -R 775 /var/www/html/wp-content/uploads \
    && chmod -R 755 /var/www/html/wp-content/mu-plugins
