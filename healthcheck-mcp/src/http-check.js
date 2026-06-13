const axios = require('axios');

async function checkHttpEndpoint(url, timeout = 1000) {
    try {
        const response = await axios.get(url, { timeout });
        if (response.status >= 200 && response.status < 300) {
            return true;
        }
        throw new Error(`HTTP endpoint ${url} returned status ${response.status}`);
    } catch (error) {
        throw new Error(`HTTP endpoint ${url} failed: ${error.message}`);
    }
}

module.exports = { checkHttpEndpoint };
