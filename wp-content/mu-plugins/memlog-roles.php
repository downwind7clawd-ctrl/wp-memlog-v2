<?php
/**
 * Plugin Name: Memlog Roles
 * Description: Custom roles for wp-memlog
 */

add_action('wp_loaded', function() {
    remove_role('memlog_writer');
    remove_role('memlog_reader');

    add_role('memlog_writer', 'Memlog Writer', [
        'read' => true,
        'edit_posts' => true,
        'publish_posts' => true,
        'read_private_posts' => true,
        'edit_private_posts' => true,
        'delete_posts' => false,
        'upload_files' => true,
        'edit_others_posts' => true,
    ]);

    add_role('memlog_reader', 'Memlog Reader', [
        'read' => true,
        'read_private_posts' => true,
    ]);
});