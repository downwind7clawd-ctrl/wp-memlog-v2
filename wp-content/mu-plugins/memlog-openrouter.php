<?php
/**
 * Plugin Name: Memlog OpenRouter
 * Description: Routes ClassifAI API through OpenRouter
 * NOTE: Set OPENROUTER_API_KEY in .env file
 */

add_filter("classifai_openai_api_request_post_url", function($url, $options, $feature) {
    return "https://openrouter.ai/api/v1/chat/completions";
}, 10, 3);

add_filter("classifai_openai_api_request_headers", function($headers, $options, $feature) {
    $api_key = getenv('OPENROUTER_API_KEY');
    if (!$api_key) {
        // Fallback to WP option if env not set
        $api_key = get_option('wp_memlog_openrouter_key', '');
    }
    if ($api_key) {
        $headers["Authorization"] = "Bearer " . $api_key;
    }
    $headers["HTTP-Referer"] = "http://127.0.0.1:8080";
    $headers["X-Title"] = "wp-memlog";
    return $headers;
}, 10, 3);

add_filter("classifai_openai_message_content", function($content, $message, $feature) {
    return json_encode([
        "model" => "openai/gpt-oss-120b:free",
        "messages" => $message,
        "max_tokens" => 1000
    ]);
}, 10, 3);

// Bypass authentication completely
add_filter("classifai_feature_excerpt_generation_is_feature_enabled", function($is_enabled, $settings) {
    return true;
}, 10, 2);

add_filter("classifai_openai_chatgpt_authenticated", function($authenticated, $settings) {
    return true;
}, 10, 2);