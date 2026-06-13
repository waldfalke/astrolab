const axios = require('axios');

// These dummy values must match the ones in the mock-api server.js
const DUMMY_PREIMAGE = 'dummy_preimage_secret_value';
const API_ENDPOINT = 'http://mock-api:3000/sun_sign';

async function getPaidResource() {
  console.log(`[AGENT] 1. Пытаюсь получить доступ к платному ресурсу: ${API_ENDPOINT}`);
  
  try {
    // Первая попытка без авторизации
    await axios.get(API_ENDPOINT);
  } catch (error) {
    if (error.response && error.response.status === 402) {
      console.log('[AGENT] 2. Получен ответ 402 Payment Required. Это ожидаемо.');
      
      const wwwAuthenticateHeader = error.response.headers['www-authenticate'];
      console.log(`[AGENT] 3. Получен заголовок с "счетом": ${wwwAuthenticateHeader}`);

      // В реальном клиенте здесь была бы логика парсинга счета и оплаты.
      // В нашем dummy-клиенте мы просто извлекаем токен и используем захардкоженный preimage.
      const tokenMatch = wwwAuthenticateHeader.match(/token="([^"]+)"/);
      if (!tokenMatch) {
        console.error('[AGENT] Ошибка: не удалось найти токен в заголовке WWW-Authenticate.');
        return;
      }
      const token = tokenMatch[1];
      console.log(`[AGENT] 4. Извлечен токен: ${token}. "Оплачиваю" счет, используя секретный preimage.`);

      const l402Header = `L402 ${token}:${DUMMY_PREIMAGE}`;
      console.log(`[AGENT] 5. Формирую заголовок авторизации: ${l402Header}`);

      try {
        console.log('[AGENT] 6. Делаю повторный запрос с оплатой...');
        const finalResponse = await axios.get(API_ENDPOINT, {
          headers: {
            'Authorization': l402Header
          }
        });

        console.log('[AGENT] 7. УСПЕХ! Ресурс получен.');
        console.log('-------------------------------------------');
        console.log('          ДОКАЗАТЕЛЬСТВО ВИДЕНИЯ:');
        console.log(JSON.stringify(finalResponse.data, null, 2));
        console.log('-------------------------------------------');

      } catch (finalError) {
        console.error(`[AGENT] Ошибка на втором запросе: ${finalError.message}`);
      }
    } else {
      console.error(`[AGENT] Неожиданная ошибка: ${error.message}`);
    }
  }
}

getPaidResource();
