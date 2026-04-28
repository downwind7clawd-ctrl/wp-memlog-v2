<?php
/**
 * Plugin Name: Memlog OpenRouter
 * Description: Routes ClassifAI API through OpenRouter
 */

add_filter("classifai_openai_api_request_post_url", function($url, $options, $feature) {
    return "https://openrouter.ai/api/v1/chat/completions";
}, 10, 3);

add_filter("classifai_openai_api_request_headers", function($headers, $options, $feature) {
    $headers["Authorization"] = "Bearer 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";
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