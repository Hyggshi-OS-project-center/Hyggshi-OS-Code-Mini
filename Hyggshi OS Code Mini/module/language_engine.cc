// Minimal native helper (placeholder) for language switching.
// This file is not required to build the Python app; it's a stub showing
// how you could implement a native extension to manage language packs,
// caching, or fast loading if needed.

#include <string>

extern "C" {

// Return the current language code (e.g., "en_US").
const char* get_current_language() {
    return "en_US"; // placeholder
}

// Set the current language code. Returns 0 on success.
int set_current_language(const char* lang) {
    // TODO: persist to config or signal the Python app
    (void)lang;
    return 0;
}

}


