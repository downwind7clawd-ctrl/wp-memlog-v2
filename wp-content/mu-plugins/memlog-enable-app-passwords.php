<?php
/**
 * Plugin Name: Enable Application Passwords
 * Description: Force enable application passwords
 */

add_filter('application_passwords_enabled', '__return_true');
add_filter('application_passwords_available', '__return_true');

# Also check if there's a nonce check issue and bypass
remove_action('login_init', 'wp_application_passwords_init');