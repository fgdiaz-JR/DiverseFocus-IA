/**
 * API configuration constants.
 */

const DEV_API_BASE_URL = 'http://localhost:8000';
const PROD_API_BASE_URL = 'https://api.diversefocus.io';

// Switch to PROD_API_BASE_URL when building for production.
export const API_BASE_URL = __DEV__ ? DEV_API_BASE_URL : PROD_API_BASE_URL;

export const API_TIMEOUT_MS = 30_000;
