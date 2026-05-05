<?php
/**
 * Plugin Name: Memlog App Password Creator
 * Description: Create application passwords programmatically
 */

function memlog_create_app_passwords() {
    global $wpdb;
    
    $users = [
        'memlog-writer' => 'writer',
        'memlog-reader' => 'reader'
    ];
    
    foreach ($users as $username => $name) {
        $user = get_user_by('login', $username);
        if ($user) {
            $password = wp_generate_password(16, false);
            $hashed = wp_hash($password);
            
            // Store application password
            $app_passwords = get_user_meta($user->ID, 'application_passwords', true);
            if (!is_array($app_passwords)) {
                $app_passwords = [];
            }
            
            $app_passwords[] = [
                'uuid' => wp_generate_uuid4(),
                'app_id' => '',
                'name' => $name . '-app-password',
                'password' => $hashed,
                'created' => time(),
                'last_used' => '',
                'last_ip' => '',
            ];
            
            update_user_meta($user->ID, 'application_passwords', $app_passwords);
            error_log("Created $username app password");
        }
    }
}

if (!get_option('memlog_app_passwords_created')) {
    memlog_create_app_passwords();
    update_option('memlog_app_passwords_created', true);
}