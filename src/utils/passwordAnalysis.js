/**
 * Password Analysis Utility
 * Implements Step 1 (Pattern Analysis) and Step 2 (Effective Search Space Estimation)
 */

// Common weak passwords and dictionary terms
const COMMON_DICTIONARY = [
    'password', 'pass', 'admin', 'welcome', 'login', 'security',
    'qwerty', 'letmein', 'iloveyou', 'monkey', 'dragon',
    'football', 'baseball', 'master', 'shadow', 'sunshine',
    'princess', 'trustno1'
];

// Keyboard rows for adjacency checking
const KEYBOARD_ROWS = [
    '1234567890',
    'qwertyuiop',
    'asdfghjkl',
    'zxcvbnm'
];



// Common year patterns (19xx or 20xx)
const YEAR_PATTERN_REGEX = /(19\d{2}|20\d{2})/;

// Common date patterns (DD/MM/YYYY, MM-DD-YY, or continuous digits like 19052005)
const DATE_PATTERN_REGEX = /(\d{2}[\/\-.]\d{2}[\/\-.]\d{2,4})|(\d{4}[\/\-.]\d{2}[\/\-.]\d{2})|(\d{8})/;

// Common leetspeak substitutions (normalization)
const SUBSTITUTIONS = {
    '@': 'a',
    '0': 'o',
    '1': 'l',
    '3': 'e',
    '4': 'a',
    '5': 's',
    '$': 's',
    '7': 't',
    '!': 'i'
};

// Character class detection helpers
const CHAR_CLASSES = {
    lowercase: /[a-z]/,
    uppercase: /[A-Z]/,
    digits: /[0-9]/,
    symbols: /[^A-Za-z0-9]/
};

// Minimum security thresholds (policy-level)
const PASSWORD_POLICY = {
    minLength: 8,
    recommendedLength: 12,
    minCharClasses: 3
};

/**
 * Step 1: Password Pattern Analysis
 */
export const analyzePasswordPatterns = (password, email = '') => {
    const lowerPass = password.toLowerCase();
    const emailPrefix = email ? email.split('@')[0].toLowerCase() : '';

    const profile = {
        dictionary_word: false,
        name_reuse: false,
        numeric_suffix: false,
        keyboard_pattern: false,
        repeated_pattern: false,
        year_pattern: false,
        date_pattern: false
    };

    // Normalize password for reuse check (remove common substitutions)
    let normalizedPass = lowerPass;
    Object.entries(SUBSTITUTIONS).forEach(([leet, plain]) => {
        normalizedPass = normalizedPass.split(leet).join(plain);
    });

    // 1. Dictionary words
    profile.dictionary_word = COMMON_DICTIONARY.some(word => lowerPass.includes(word) || normalizedPass.includes(word));

    // 2. Username / email reuse (Aggressive Substring Matching)
    if (emailPrefix) {
        const uppercasePrefix = emailPrefix.toUpperCase().trim();
        const uppercasePass = password.toUpperCase();

        // Helper to check for persistent reuse (4+ character chunks)
        const checkAggressiveReuse = (prefix, pass) => {
            // Check direct inclusion
            if (prefix.length >= 4 && pass.includes(prefix)) return true;

            // Check sliding window of 4-5 characters from prefix
            const minChunk = 4;
            for (let i = 0; i <= prefix.length - minChunk; i++) {
                const chunk = prefix.substring(i, i + minChunk);
                if (pass.includes(chunk)) return true;
            }
            return false;
        };

        if (checkAggressiveReuse(uppercasePrefix, uppercasePass)) {
            profile.name_reuse = true;
        }

        // Also check parts split by dots/dashes
        const parts = uppercasePrefix.split(/[._-]/);
        if (parts.length > 1) {
            const hasPartReuse = parts.some(part => part.length >= 4 && uppercasePass.includes(part));
            if (hasPartReuse) {
                profile.name_reuse = true;
            }
        }
    }

    // 3. Numeric suffixes (2-4 digits)
    const numericSuffixMatch = password.match(/\d{2,4}$/);
    if (numericSuffixMatch) {
        profile.numeric_suffix = true;
    }

    // 4. Dynamic Keyboard patterns (4+ consecutive adjacent keys)
    const hasInvalidKeyboardPattern = (str) => {
        if (!str || str.length < 4) return false;
        const lowerStr = str.toLowerCase();
        let consecutiveCount = 1;
        for (let i = 1; i < lowerStr.length; i++) {
            const prevChar = lowerStr[i - 1];
            const currChar = lowerStr[i];
            let isAdjacent = false;
            for (const row of KEYBOARD_ROWS) {
                const prevIndex = row.indexOf(prevChar);
                const currIndex = row.indexOf(currChar);
                if (prevIndex !== -1 && currIndex !== -1) {
                    if (Math.abs(currIndex - prevIndex) === 1) {
                        isAdjacent = true;
                    }
                    break;
                }
            }
            if (isAdjacent) {
                consecutiveCount++;
                if (consecutiveCount > 3) return true;
            } else {
                consecutiveCount = 1;
            }
        }
        return false;
    };
    profile.keyboard_pattern = hasInvalidKeyboardPattern(password);

    // 5. Dynamic Sequential patterns (3+ chars)
    const checkSequential = (str) => {
        if (str.length < 3) return false;
        for (let i = 0; i <= str.length - 3; i++) {
            const char1 = str.charCodeAt(i);
            const char2 = str.charCodeAt(i + 1);
            const char3 = str.charCodeAt(i + 2);
            // Check ascending (abc, 123)
            if (char2 === char1 + 1 && char3 === char2 + 1) return true;
            // Check descending (cba, 321)
            if (char2 === char1 - 1 && char3 === char2 - 1) return true;
        }
        return false;
    };
    profile.sequential_pattern = checkSequential(lowerPass);

    // 6. Character Repetition (User-provided logic: >2 repeats)
    const hasInvalidRepetition = (str) => {
        if (!str || str.length === 0) return false;
        let repeatCount = 1;
        for (let i = 1; i < str.length; i++) {
            if (str[i] === str[i - 1]) {
                repeatCount++;
                if (repeatCount > 2) return true;
            } else {
                repeatCount = 1;
            }
        }
        return false;
    };
    profile.repeated_pattern = hasInvalidRepetition(password);

    // 7. Year patterns
    profile.year_pattern = YEAR_PATTERN_REGEX.test(password);

    // 8. Date patterns
    profile.date_pattern = DATE_PATTERN_REGEX.test(password);

    return profile;
};

/**
 * Step 2: Effective Search Space Estimation
 */
export const estimateSearchSpace = (password, patterns) => {
    const length = password.length;
    let charset_size = 0;

    const hasLower = CHAR_CLASSES.lowercase.test(password);
    const hasUpper = CHAR_CLASSES.uppercase.test(password);
    const hasDigit = CHAR_CLASSES.digits.test(password);
    const hasSymbol = CHAR_CLASSES.symbols.test(password);

    if (hasLower) charset_size += 26;
    if (hasUpper) charset_size += 26;
    if (hasDigit) charset_size += 10;
    if (hasSymbol) charset_size += 32;

    const raw_search_space = Math.pow(charset_size, length);

    let total_penalty = 1;

    if (patterns.dictionary_word) total_penalty *= Math.pow(10, 6);
    if (patterns.numeric_suffix) total_penalty *= Math.pow(10, 3);
    if (patterns.year_pattern) total_penalty *= Math.pow(10, 3);
    if (patterns.date_pattern) total_penalty *= Math.pow(10, 4);
    if (patterns.name_reuse) total_penalty *= Math.pow(10, 5);
    if (patterns.keyboard_pattern) total_penalty *= Math.pow(10, 4);
    if (patterns.sequential_pattern) total_penalty *= Math.pow(10, 3);
    if (patterns.repeated_pattern) total_penalty *= Math.pow(10, 3);

    const effective_search_space = raw_search_space / total_penalty;

    return {
        charset_size,
        password_length: length,
        raw_search_space,
        effective_search_space
    };
};

/**
 * Estimation of Crack Times and Risk
 */
export const evaluateSecurityMetrics = (password, email = '') => {
    const patterns = analyzePasswordPatterns(password, email);
    const spaceMetrics = estimateSearchSpace(password, patterns);

    const { effective_search_space } = spaceMetrics;

    /**
     * MODEL B — Hash-Cost-Based Model (Industry-aligned)
     * Assumption: Each password guess requires running a memory-hard hash (e.g., Argon2 or scrypt).
     * hash_cost_seconds: Average time taken for one high-security hash verification.
     */
    const hash_cost_seconds = 0.1; // 100 ms per guess baseline

    // 1. Classical Crack Time Estimation
    // Formula: classical_time = N * hash_cost_seconds
    // This represents the total time required to brute-force the effective search space.
    const classicalCrackTimeSeconds = effective_search_space * hash_cost_seconds;

    // 2. Quantum Crack Time Estimation (Grover's Algorithm)
    // Grover's algorithm provides a quadratic speedup for unstructured search,
    // reducing the effective search space from N to √N.
    // Crucially, quantum computers still incur the same hash verification cost per guess.
    // Formula: quantum_time = √N * hash_cost_seconds
    const quantumSearchSpace = Math.sqrt(effective_search_space);
    const quantumCrackTimeSeconds = quantumSearchSpace * hash_cost_seconds;

    /**
     * SECURITY MODEL NOTES:
     * 1. Grover's Speedup: Grover's algorithm reduces the "bits of security" by half.
     *    A 64-bit entropy password becomes 32-bit for a quantum attacker.
     * 2. Resistance: Strong passwords (high entropy) can still result in extremely 
     *    large quantum crack times because √N remains vast for large N.
     * 3. Risk Mapping: We use risk buckets (LOW/MEDIUM/HIGH) because exact year 
     *    predictions are speculative and depend on future hardware availability.
     */

    // Final Risk Classification (User-provided logic)
    const classifyRisk = (classicalSeconds, quantumSeconds) => {
        let classicalScore;
        if (classicalSeconds < 3600) { // < 1 hour
            classicalScore = 3;
        } else if (classicalSeconds < 30 * 24 * 3600) { // < 30 days
            classicalScore = 2;
        } else {
            classicalScore = 1;
        }

        let quantumScore;
        if (quantumSeconds < 24 * 3600) { // < 1 day
            quantumScore = 3;
        } else if (quantumSeconds < 365 * 24 * 3600) { // < 1 year
            quantumScore = 2;
        } else {
            quantumScore = 1;
        }

        const finalScore = Math.max(classicalScore, quantumScore);
        if (finalScore === 3) return { label: "HIGH", score: 90 };
        if (finalScore === 2) return { label: "MEDIUM", score: 50 };
        return { label: "LOW", score: 10 };
    };

    const risk = classifyRisk(classicalCrackTimeSeconds, quantumCrackTimeSeconds);
    const riskScore = risk.score;
    const riskLabel = risk.label;

    // Decision Logic based on Risk Label
    let decision = "None (Low Risk)";
    if (riskLabel === "HIGH") {
        decision = "OTP + Biometrics (Level 2)";
    } else if (riskLabel === "MEDIUM") {
        decision = "OTP (Level 1)";
    } else {
        decision = "None (Low Risk)";
    }

    return {
        patterns,
        spaceMetrics,
        classicalCrackTimeSeconds,
        quantumCrackTimeSeconds,
        riskScore,
        riskLabel,
        decision
    };
};

/**
 * Format seconds into a human-readable time string
 */
export const formatTime = (seconds) => {
    if (seconds < 1) return "< 1 second";
    if (seconds < 60) return `${Math.round(seconds)} seconds`;
    if (seconds < 3600) return `${Math.round(seconds / 60)} minutes`;
    if (seconds < 86400) return `${Math.round(seconds / 3600)} hours`;
    if (seconds < 31536000) return `${Math.round(seconds / 86400)} days`;

    const years = Math.round(seconds / 31536000);
    if (years < 1000) return `${years} years`;
    if (years < 1000000) return `${Math.round(years / 1000)}k years`;
    if (years < 1000000000) return `${Math.round(years / 1000000)}M years`;
    return "Centuries";
};
