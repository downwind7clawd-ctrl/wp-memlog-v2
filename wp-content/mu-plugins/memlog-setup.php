<?php
/**
 * Plugin Name: Memlog Create App Passwords
 * Description: Create app passwords on activation
 */

function memlog_do_setup() {
    // Enable application passwords
    update_option('application_passwords_enabled', true);
    
    // Create reader user if needed
    if (!username_exists('memlog-reader')) {
        $user_id = wp_create_user('memlog-reader', 'reader123', 'reader@example.com');
        if (!is_wp_error($user_id)) {
            $user = new WP_User($user_id);
            $user->set_role('memlog_reader');
        }
    }
    
    // Get writer user
    $writer = get_user_by('login', 'memlog-writer');
    if ($writer) {
        $password = wp_generate_password(20, true, true);
        $hashed = wp_hash($password);
        
        $app_passwords = get_user_meta($writer->ID, 'application_passwords', true);
        if (!is_array($app_passwords)) {
            $app_passwords = [];
        }
        
        $app_passwords[] = [
            'uuid' => wp_generate_uuid4(),
            'name' => 'memlog-writer',
            'password' => $hashed,
            'created' => time(),
        ];
        
        update_user_meta($writer->ID, 'application_passwords', $app_passwords);
        error_log("MEMLOG WRITER APP PASSWORD: $password");
    }
    
    // Get reader user
    $reader = get_user_by('login', 'memlog-reader');
    if ($reader) {
        $password = wp_generate_password(20, true, true);
        $hashed = wp_hash($password);
        
        $app_passwords = get_user_meta($reader->ID, 'application_passwords', true);
        if (!is_array($app_passwords)) {
            $app_passwords = [];
        }
        
        $app_passwords[] = [
            'uuid' => wp_generate_uuid4(),
            'name' => 'memlog-reader',
            'password' => $hashed,
            'created' => time(),
        ];
        
        update_user_meta($reader->ID, 'application_passwords', $app_passwords);
        error_log("MEMLOG READER APP PASSWORD: $password");
    }
}

memlog_do_setup();