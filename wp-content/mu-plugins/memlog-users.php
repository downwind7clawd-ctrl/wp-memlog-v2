<?php
/**
 * Plugin Name: Memlog Users
 * Description: Create memlog users with application passwords
 */

if (get_option('memlog_setup_done')) {
    return;
}

function memlog_create_users() {
    // Create writer user
    $writer_username = 'memlog-writer';
    $writer_email = 'writer@example.com';
    $writer_pass = 'writer123';
    
    if (!username_exists($writer_username)) {
        $user_id = wp_create_user($writer_username, $writer_pass, $writer_email);
        if (!is_wp_error($user_id)) {
            $user = new WP_User($user_id);
            $user->set_role('memlog_writer');
            
            // Create application password
            $app_password = wp_generate_password(16, false);
            update_user_meta($user_id, 'application_passwords', [
                [
                    'uuid' => wp_generate_uuid4(),
                    'app_id' => '',
                    'name' => 'writer-app-password',
                    'password' => $app_password,
                    'created' => time(),
                    'last_used' => '',
                    'last_ip' => '',
                ]
            ]);
            
            error_log("Created writer user. App password: $app_password");
        }
    }
    
    // Create reader user
    $reader_username = 'memlog-reader';
    $reader_email = 'reader@example.com';
    $reader_pass = 'reader123';
    
    if (!username_exists($reader_username)) {
        $user_id = wp_create_user($reader_username, $reader_pass, $reader_email);
        if (!is_wp_error($user_id)) {
            $user = new WP_User($user_id);
            $user->set_role('memlog_reader');
        }
    }
}
add_action('init', 'memlog_create_users');