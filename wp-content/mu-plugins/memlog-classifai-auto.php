<?php
/**
 * Plugin Name: Memlog ClassifAI Auto
 * Description: Automatically process private posts with ClassifAI
 */

add_action('save_post', function($post_id, $post, $update) {
    if ($post->post_status !== 'private') {
        return;
    }
    
    update_post_meta($post_id, '_classifai_process_content', 'yes');
    update_post_meta($post_id, 'classifai_enable_excerpt_generation', 'yes');
    update_post_meta($post_id, 'classifai_enable_classification', 'yes');
    update_post_meta($post_id, 'classifai_run_classification', 'yes');
}, 20, 3);