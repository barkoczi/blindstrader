FROM php:8.3-fpm-alpine AS base

# Install system dependencies
RUN apk add --no-cache \
    linux-headers \
    autoconf \
    g++ \
    make \
    librdkafka-dev \
    oniguruma-dev \
    libxml2-dev \
    libzip-dev \
    icu-dev \
    zip \
    unzip \
    git \
    curl

# Install PHP extensions
RUN docker-php-ext-install \
    pdo \
    pdo_mysql \
    mbstring \
    exif \
    pcntl \
    bcmath \
    xml \
    zip \
    intl \
    opcache

# Install Redis extension
RUN pecl install redis && docker-php-ext-enable redis

# Install rdkafka extension
RUN pecl install rdkafka && docker-php-ext-enable rdkafka

# Configure opcache for production
COPY docker/opcache.ini /usr/local/etc/php/conf.d/opcache.ini

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Copy composer files first for layer caching
COPY composer.json composer.lock ./

RUN composer install \
    --ignore-platform-req=ext-rdkafka \
    --no-dev \
    --no-scripts \
    --no-autoloader \
    --prefer-dist \
    --no-interaction

# Copy application code
COPY . .

# Remove any locally-generated bootstrap cache files (they may reference
# dev-only providers like laravel/pail that are absent in --no-dev installs)
RUN rm -f bootstrap/cache/packages.php bootstrap/cache/services.php

# Generate optimised autoloader
RUN composer dump-autoload --optimize --no-dev

# Set permissions
RUN chown -R www-data:www-data /app/storage /app/bootstrap/cache \
    && chmod -R 775 /app/storage /app/bootstrap/cache

EXPOSE 9000

CMD ["php-fpm"]
