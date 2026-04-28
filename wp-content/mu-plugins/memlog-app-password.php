<?php
/**
 * Plugin Name: Memlog App Password
 * Description: Add application passwords for memlog users via REST API
 */

add_action('rest_api_init', function() {
    register_rest_route('memlog/v1', '/setup', [
        'methods' => 'POST',
        'callback' => 'memlog_setup_users',
        'permission_callback' => function() {
            return current_user_can('manage_options');
        }
    ]);
});

function memlog_setup_users() {
    $results = [];
    
    // Create reader user if not exists
    if (!username_exists('memlog-reader')) {
        $user_id = wp_create_user('memlog-reader', 'reader123', 'reader@example.com');
        if (!is_wp_error($user_id)) {
            $user = new WP_User($user_id);
            $user->set_role('memlog_reader');
            $results['reader'] = 'Created';
        }
    } else {
        $results['reader'] = 'Already exists';
    }
    
    // Enable application passwords feature
    update_option('application_passwords_enabled', true);
    update_option('application_passwords_author_dictionaries', ['localhost', '127.0.0.1', '::1']);
    
    return rest_ensure_response($results);
}
add_action('init', function() {
    update_option('application_passwords_enabled', true);
});