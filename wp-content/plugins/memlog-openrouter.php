<?php
/**
 * Plugin Name: Memlog OpenRouter
 * Description: Routes ClassifAI API through OpenRouter
 */

add_filter('classifai_openai_api_request_post_url', function($url, $options, $feature) {
    return 'https://openrouter.ai/api/v1/chat/completions';
}, 10, 3);

add_filter('classifai_openai_api_request_headers', function($headers, $options, $feature) {
    $api_key = getenv('OPENROUTER_API_KEY');
    if (!$api_key) {
        error_log('wp-memlog: OPENROUTER_API_KEY not set');
        return $headers;
    }
    $headers['Authorization'] = 'Bearer ' . $api_key;
    $headers['HTTP-Referer'] = 'http://127.0.0.1:8080';
    $headers['X-Title'] = 'wp-memlog';
    return $headers;
}, 10, 3);

add_filter('classifai_openai_message_content', function($content, $message, $feature) {
    return json_encode([
        'model' => 'openai/gpt-oss-120b:free',
        'messages' => $message,
        'max_tokens' => 1000
    ]);
}, 10, 3);

add_filter('classifai_openai_json_body', function($body, $feature) {
    $body['model'] = 'openai/gpt-oss-120b:free';
    return $body;
}, 10, 2);